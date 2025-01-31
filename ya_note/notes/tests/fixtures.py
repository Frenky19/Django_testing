from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class BaseTestCase(TestCase):
    """Базовый тестовый класс, используемый другими классами."""

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
        cls.note_detail_url = reverse('notes:detail', args=(cls.note.slug,))
        cls.note_edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.note_delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.success_url = reverse('notes:success')
        cls.login_url = reverse('users:login')
        cls.home_url = reverse('notes:home')
        cls.logout_url = reverse('users:logout')
        cls.signup_url = reverse('users:signup')
        cls.pages_for_anonymous = (
            cls.home_url,
            cls.login_url,
            cls.logout_url,
            cls.signup_url,
        )
        cls.pages_for_not_author = (
            cls.notes_url,
            cls.note_add_url,
            cls.success_url,
        )
        cls.pages_for_author = (
            cls.note_detail_url,
            cls.note_edit_url,
            cls.note_delete_url,
        )
        cls.pages_with_redirect_for_anonymous = (
            cls.note_detail_url,
            cls.note_edit_url,
            cls.note_delete_url,
            cls.note_add_url,
            cls.success_url,
            cls.notes_url,
        )
