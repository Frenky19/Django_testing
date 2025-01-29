from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.forms import NoteForm
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
            author=cls.author,
        )
        # Авторизуем клиента как автора
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Авторизуем клиента как не автора
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        # Используемые маршруты
        cls.notes_url = reverse('notes:list')
        cls.note_add_url = reverse('notes:add')
        cls.note_edit_url = reverse('notes:edit', args=(cls.note.slug,))


class ContentTests(BaseTestCase):
    """Класс, тестирующий контент приложения"""

    def test_note_in_context_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок

        Также список заметок доступен автору
        """
        # Автор запрашивает список заметок.
        response = self.author_client.get(self.notes_url)
        notes = response.context['object_list']
        # Проверяем, что заметка присутствует в object_list.
        self.assertIn(self.note, notes)

    def test_note_not_in_list_for_another_user(self):
        """Список заметок не доступен другому пользователю"""
        # Не автор запрашивает список заметок.
        response = self.not_author_client.get(self.notes_url)
        notes = response.context['object_list']
        # Проверяем, что заметка не видна другому пользователю.
        self.assertNotIn(self.note, notes)

    def test_note_pages_contain_correct_form(self):
        """Страницы создания и редактирования содержат корректные формы"""
        pages = [
            {
                'url': self.note_add_url,
                'name': 'создание заметки',
            },
            {
                'url': self.note_edit_url,
                'name': 'редактирование заметки',
            },
        ]
        for page in pages:
            with self.subTest(page=page['name']):
                # Автор запрашивает страницу.
                response = self.author_client.get(page['url'])
                # Проверяем, есть ли объект формы в контексте.
                self.assertIn('form', response.context)
                # Проверяем, что форма принадлежит нужному классу.
                self.assertIsInstance(response.context['form'], NoteForm)
