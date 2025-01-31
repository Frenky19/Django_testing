from notes.forms import NoteForm
from .fixtures import BaseTestCase


class ContentTests(BaseTestCase):
    """Класс, тестирующий контент приложения."""

    def test_note_in_context_object_list(self):
        """
        Отдельная заметка передаётся на страницу со списком заметок.

        Также список заметок доступен автору.
        """
        response = self.author_client.get(self.notes_url)
        notes = response.context['object_list']
        self.assertIn(self.note, notes)

    def test_note_not_in_list_for_another_user(self):
        """Список заметок не доступен другому пользователю."""
        response = self.not_author_client.get(self.notes_url)
        notes = response.context['object_list']
        self.assertNotIn(self.note, notes)

    def test_note_pages_contain_correct_form(self):
        """Страницы создания и редактирования содержат корректные формы."""
        pages = (
                (self.note_add_url, 'создание заметки'),
                (self.note_edit_url, 'редактирование заметки'),
        )
        for url, name in pages:
            with self.subTest(page=name):
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
