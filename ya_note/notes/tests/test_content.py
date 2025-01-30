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
        cls.author = User.objects.create_user(username='Автор')
        cls.not_author = User.objects.create_user(username='Не автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author,
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
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
        response = self.author_client.get(self.notes_url)
        notes = response.context['object_list']
        self.assertIn(self.note, notes)

    def test_note_not_in_list_for_another_user(self):
        """Список заметок не доступен другому пользователю"""
        response = self.not_author_client.get(self.notes_url)
        notes = response.context['object_list']
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
                response = self.author_client.get(page['url'])
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
