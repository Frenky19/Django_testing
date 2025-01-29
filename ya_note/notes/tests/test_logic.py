from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class BaseTestCase(TestCase):
    """Базовый тестовый класс, используемый другими классами"""

    @classmethod
    def setUpTestData(cls):
        # Тестовые данные, которые будут использоваться всеми тестами
        cls.author = User.objects.create_user(username='Автор')
        cls.not_author = User.objects.create_user(username='Не автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )
        # Данные формы для создания/редактирования заметки
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        # Авторизуем клиента для автора
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Авторизуем клиента как не автора
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        # Используемые маршруты
        cls.notes_url = reverse('notes:list')
        cls.note_add_url = reverse('notes:add')
        cls.note_edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.note_delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')
        cls.login_url = reverse('users:login')


class LogicTests(BaseTestCase):
    """Класс, тестирующий логику приложения"""

    def setUp(self):
        """Очищает все динамически создаваемые данные"""
        super().setUp()
        Note.objects.exclude(pk=self.note.pk).delete()

    def test_user_can_create_note(self):
        """Авторизированный пользователь может создать заметку."""
        # Сохраняем количество заметок до выполнения действия
        notes_count_before = Note.objects.count()
        response = self.author_client.post(
            self.note_add_url, data=self.form_data
        )
        self.assertRedirects(response, self.success_url)
        # Сохраняем количество заметок после выполнения действия
        notes_count_after = Note.objects.count()
        # Проверяем, что количество заметок увеличилось на 1
        self.assertEqual(notes_count_after, notes_count_before + 1)
        # Получаем последнюю добавленную заметку
        new_note = Note.objects.last()
        # Проверка, что новая заметка содержит правильные данные
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        # Сохраняем количество заметок до выполнения действия
        notes_count_before = Note.objects.count()
        response = self.client.post(self.note_add_url, data=self.form_data)
        # Ожидаемый редирект
        expected_url = f'{self.login_url}?next={self.note_add_url}'
        self.assertRedirects(response, expected_url)
        # Сохраняем количество заметок после выполнения действия
        notes_count_after = Note.objects.count()
        # Проверка, что в базе осталась только исходная заметка
        self.assertEqual(notes_count_after, notes_count_before)

    def test_not_unique_slug(self):
        """Нельзя создать заметку с неуникальным slug."""
        # Сохраняем количество заметок до выполнения действия
        notes_count_before = Note.objects.count()
        # Устанавливаем slug, уже существующий в базе
        self.form_data['slug'] = self.note.slug
        # Пытаемся отправить форму
        response = self.author_client.post(
            self.note_add_url, data=self.form_data
        )
        # Сохраняем количество заметок после выполнения действия
        notes_count_after = Note.objects.count()
        # Проверяем, что количество заметок в базе не изменилось
        self.assertEqual(notes_count_after, notes_count_before)
        # Проверка, что форма выдает ошибку для поля slug
        form_errors = response.context['form'].errors['slug']
        self.assertIn(self.note.slug + WARNING, form_errors)

    def test_empty_slug(self):
        """Если slug пустой, он генерируется автоматически."""
        # Сохраняем количество заметок до выполнения действия
        notes_count_before = Note.objects.count()
        # Удаление slug из данных формы
        self.form_data.pop('slug')
        response = self.author_client.post(self.note_add_url, self.form_data)
        # Сохраняем количество заметок после выполнения действия
        notes_count_after = Note.objects.count()
        # Проверка редиректа после успешного добавления
        self.assertRedirects(response, self.success_url)
        # Проверка, что заметка добавилась в базу
        self.assertEqual(notes_count_after, notes_count_before + 1)
        new_note = Note.objects.last()
        # Проверка, что slug сгенерировался автоматически на основе заголовка
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор заметки может редактировать её."""
        # Отправляем обновленные данные
        response = self.author_client.post(
            self.note_edit_url, data=self.form_data
        )
        self.assertRedirects(response, self.success_url)
        # Обновляем заметку из базы
        note_from_db = Note.objects.get(id=self.note.id)
        # Проверяем, что изменения сохранены
        self.assertEqual(note_from_db.title, self.form_data['title'])
        self.assertEqual(note_from_db.text, self.form_data['text'])
        self.assertEqual(note_from_db.slug, self.form_data['slug'])
        self.assertEqual(note_from_db.author, self.author)

    def test_other_user_cant_edit_note(self):
        """Не автор не может редактировать заметку."""
        # Отправка данных от другого пользователя
        response = self.not_author_client.post(
            self.note_edit_url, data=self.form_data
        )
        # Проверяем, что вернулся 404
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем заметку из базы
        note_from_db = Note.objects.get(id=self.note.id)
        # Убедимся, что данные заметки не изменились
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)
        self.assertEqual(note_from_db.author, self.author)

    def test_author_can_delete_note(self):
        """Автор заметки может её удалить."""
        # Сохраняем количество заметок до выполнения действия
        notes_count_before = Note.objects.count()
        # Удаление заметки
        response = self.author_client.post(self.note_delete_url)
        # Сохраняем количество заметок после выполнения действия
        notes_count_after = Note.objects.count()
        # Проверка редиректа
        self.assertRedirects(response, self.success_url)
        # Убедимся, что заметок в базе больше нет
        self.assertEqual(notes_count_after, notes_count_before - 1)

    def test_other_user_cant_delete_note(self):
        """Не автор не может удалить чужую заметку."""
        # Сохраняем количество заметок до выполнения действия
        notes_count_before = Note.objects.count()
        # Пытаемся удалить заметку от имени не автора
        response = self.not_author_client.post(self.note_delete_url)
        # Сохраняем количество заметок после выполнения действия
        notes_count_after = Note.objects.count()
        # Проверяем, что возвращается 404 ошибка
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка все еще существует
        self.assertEqual(notes_count_after, notes_count_before)
