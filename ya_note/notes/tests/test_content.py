from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class ContentTestCase(TestCase):

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

    def test_note_in_context_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок

        Также список заметок доступен автору
        """
        url = reverse('notes:list')
        # Автор запрашивает список заметок.
        response = self.author_client.get(url)
        object_list = response.context['object_list']
        # Проверяем, что заметка присутствует в object_list.
        self.assertIn(self.note, object_list)

    def test_note_not_in_list_for_another_user(self):
        """Список заметок не доступен другому пользователю"""
        url = reverse('notes:list')
        # Не автор запрашивает список заметок.
        response = self.not_author_client.get(url)
        object_list = response.context['object_list']
        # Проверяем, что заметка не видна другому пользователю.
        self.assertNotIn(self.note, object_list)

    def test_create_note_page_contains_form(self):
        """Страница создания заметки содержит корректную форму"""
        url = reverse('notes:add')
        # Автор запрашивает страницу создания заметки.
        response = self.author_client.get(url)
        # Проверяем, есть ли объект формы в контексте.
        self.assertIn('form', response.context)
        # Проверяем, что форма принадлежит нужному классу.
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_edit_note_page_contains_form(self):
        """Страница редактирования заметки содержит корректную форму"""
        url = reverse('notes:edit', args=(self.note.slug,))
        # Автор запрашивает страницу редактирования заметки.
        response = self.author_client.get(url)
        # Проверяем, есть ли объект формы в контексте.
        self.assertIn('form', response.context)
        # Проверяем, что форма принадлежит нужному классу.
        self.assertIsInstance(response.context['form'], NoteForm)
