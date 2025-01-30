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
        cls.author = User.objects.create_user(username='Автор')
        cls.not_author = User.objects.create_user(username='Не автор')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note-slug',
            author=cls.author
        )
        cls.form_data = {
            'title': 'Новый заголовок',
            'text': 'Новый текст',
            'slug': 'new-slug'
        }
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
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
        notes_count_before = Note.objects.count()
        response = self.author_client.post(
            self.note_add_url, data=self.form_data
        )
        self.assertRedirects(response, self.success_url)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before + 1)
        new_note = Note.objects.last()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимный пользователь не может создать заметку."""
        notes_count_before = Note.objects.count()
        response = self.client.post(self.note_add_url, data=self.form_data)
        expected_url = f'{self.login_url}?next={self.note_add_url}'
        self.assertRedirects(response, expected_url)
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)

    def test_not_unique_slug(self):
        """Нельзя создать заметку с неуникальным slug."""
        notes_count_before = Note.objects.count()
        self.form_data['slug'] = self.note.slug
        response = self.author_client.post(
            self.note_add_url, data=self.form_data
        )
        notes_count_after = Note.objects.count()
        self.assertEqual(notes_count_after, notes_count_before)
        form_errors = response.context['form'].errors['slug']
        self.assertIn(self.note.slug + WARNING, form_errors)

    def test_empty_slug(self):
        """Если slug пустой, он генерируется автоматически."""
        notes_count_before = Note.objects.count()
        self.form_data.pop('slug')
        response = self.author_client.post(self.note_add_url, self.form_data)
        notes_count_after = Note.objects.count()
        self.assertRedirects(response, self.success_url)
        self.assertEqual(notes_count_after, notes_count_before + 1)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_author_can_edit_note(self):
        """Автор заметки может редактировать её."""
        response = self.author_client.post(
            self.note_edit_url, data=self.form_data
        )
        self.assertRedirects(response, self.success_url)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, self.form_data['title'])
        self.assertEqual(note_from_db.text, self.form_data['text'])
        self.assertEqual(note_from_db.slug, self.form_data['slug'])
        self.assertEqual(note_from_db.author, self.author)

    def test_other_user_cant_edit_note(self):
        """Не автор не может редактировать заметку."""
        response = self.not_author_client.post(
            self.note_edit_url, data=self.form_data
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id)
        self.assertEqual(note_from_db.title, self.note.title)
        self.assertEqual(note_from_db.text, self.note.text)
        self.assertEqual(note_from_db.slug, self.note.slug)
        self.assertEqual(note_from_db.author, self.author)

    def test_author_can_delete_note(self):
        """Автор заметки может её удалить."""
        notes_count_before = Note.objects.count()
        response = self.author_client.post(self.note_delete_url)
        notes_count_after = Note.objects.count()
        self.assertRedirects(response, self.success_url)
        self.assertEqual(notes_count_after, notes_count_before - 1)

    def test_other_user_cant_delete_note(self):
        """Не автор не может удалить чужую заметку."""
        notes_count_before = Note.objects.count()
        response = self.not_author_client.post(self.note_delete_url)
        notes_count_after = Note.objects.count()
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(notes_count_after, notes_count_before)
