from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class NoteTests(TestCase):

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

    def setUp(self):
        """
        Инициализация пользователей.

        Инициализирует клиентов для анонимного пользователя, авторизованного
        автора и другого пользователя перед каждым тестом.
        """
        # Авторизуем клиента для автора
        self.author_client = Client()
        self.author_client.force_login(self.author)
        # Авторизуем клиента как не автора
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)
        # Клиент без авторизации
        self.client = Client()

    def test_user_can_create_note(self):
        """Авторизированный пользователь может создать заметку."""
        url = reverse('notes:add')
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        # Проверка, что в базе теперь 2 заметки (старая + новая)
        self.assertEqual(Note.objects.count(), 2)
        # Получаем последнюю добавленную заметку
        new_note = Note.objects.last()
        # Проверка, что новая заметка содержит правильные данные
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        url = reverse('notes:add')
        response = self.client.post(url, data=self.form_data)
        login_url = reverse('users:login')
        # Ожидаемый редирект
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        # Проверка, что в базе осталась только исходная заметка
        self.assertEqual(Note.objects.count(), 1)

    def test_not_unique_slug(self):
        """Нельзя создать заметку с неуникальным slug."""
        url = reverse('notes:add')
        # Устанавливаем slug, уже существующий в базе
        self.form_data['slug'] = self.note.slug
        # Пытаемся отправить форму
        response = self.author_client.post(url, data=self.form_data)
        # Проверка, что форма выдает ошибку для поля slug
        form_errors = response.context['form'].errors['slug']
        self.assertIn(self.note.slug + WARNING, form_errors)
        # Проверка, что число записей в базе не изменилось
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Если slug пустой, он генерируется автоматически."""
        url = reverse('notes:add')
        # Удаление slug из данных формы
        self.form_data.pop('slug')
        response = self.author_client.post(url, self.form_data)
        # Проверка редиректа после успешного добавления
        self.assertRedirects(response, reverse('notes:success'))
        # Проверка, что заметка добавилась в базу
        self.assertEqual(Note.objects.count(), 2)
        new_note = Note.objects.last()
        # Проверка, что slug сгенерировался автоматически на основе заголовка
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор заметки может редактировать её."""
        url = reverse('notes:edit', args=(self.note.slug,))
        # Отправляем обновленные данные
        response = self.author_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        # Обновляем заметку из базы
        self.note.refresh_from_db()
        # Проверяем, что изменения сохранены
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])

    def test_other_user_cant_edit_note(self):
        """Не автор не может редактировать заметку."""
        url = reverse('notes:edit', args=(self.note.slug,))
        # Отправка данных от другого пользователя
        response = self.not_author_client.post(url, data=self.form_data)
        # Проверяем, что вернулся 404
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Получаем заметку из базы
        note_from_db = Note.objects.get(id=self.note.id)
        # Убедимся, что данные заметки не изменились
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)

    def test_author_can_delete_note(self):
        """Автор заметки может её удалить."""
        url = reverse('notes:delete', args=(self.note.slug,))
        # Удаление заметки
        response = self.author_client.post(url)
        # Проверка редиректа
        self.assertRedirects(response, reverse('notes:success'))
        # Убедимся, что заметок в базе больше нет
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Не автор не может удалить чужую заметку."""
        url = reverse('notes:delete', args=(self.note.slug,))
        # Пытаемся удалить заметку от имени не автора
        response = self.not_author_client.post(url)
        # Проверяем, что возвращается 404 ошибка
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка все еще существует
        self.assertEqual(Note.objects.count(), 1)
