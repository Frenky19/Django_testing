from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

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
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        cls.pages_for_anonymous = {
            reverse('notes:home'),
            reverse('users:login'),
            reverse('users:logout'),
            reverse('users:signup'),
        }
        cls.pages_for_not_author = {
            reverse('notes:list'),
            reverse('notes:add'),
            reverse('notes:success'),
        }
        cls.pages_for_author = {
            reverse('notes:detail', args=(cls.note.slug,)),
            reverse('notes:edit', args=(cls.note.slug,)),
            reverse('notes:delete', args=(cls.note.slug,)),
        }
        cls.pages_with_redirect_for_anonymous = {
            reverse('notes:detail', args=(cls.note.slug,)),
            reverse('notes:edit', args=(cls.note.slug,)),
            reverse('notes:delete', args=(cls.note.slug,)),
            reverse('notes:add'),
            reverse('notes:success'),
            reverse('notes:list')
        }
        cls.login_url = reverse('users:login')


class RoutesTests(BaseTestCase):
    """Класс, тестирующий маршруты приложения"""

    def test_pages_availability_for_anonymous_user(self):
        """Страницы доступны анонимному пользователю."""
        for page in self.pages_for_anonymous:
            with self.subTest(page=page):
                response = self.client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_not_author_user(self):
        """Страницы доступны авторизованному пользователю."""
        for page in self.pages_for_not_author:
            with self.subTest(page=page):
                response = self.not_author_client.get(page)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """
        Доступ к страницам заметок корректно обрабатывается
        для автора и не автора.
        """
        users_statuses = [
            (self.not_author_client, HTTPStatus.NOT_FOUND),
            (self.author_client, HTTPStatus.OK)
        ]
        for client, expected_status in users_statuses:
            for page in self.pages_for_author:
                with self.subTest(client=client, page=page):
                    response = client.get(page)
                    self.assertEqual(response.status_code, expected_status)

    def test_redirects_for_anonymous_user(self):
        """
        Редиректы дял анонимного пользователя

        Анонимный пользователь перенаправляется на страницу логина
        со всех страниц, требующих авторизации.
        """
        for page in self.pages_with_redirect_for_anonymous:
            with self.subTest(page=page):
                expected_url = f'{self.login_url}?next={page}'
                response = self.client.get(page)
                self.assertRedirects(response, expected_url)
