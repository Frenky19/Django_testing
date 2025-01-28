from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class RoutesTestCase(TestCase):

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

        # Авторизуем клиента как автора
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Авторизуем клиента как не автора
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        # Клиент без авторизации
        cls.anonymous_client = Client()

    def test_pages_availability_for_anonymous_user(self):
        """Страницы доступны анонимному пользователю."""
        # Публичные страницы
        pages = ['notes:home', 'users:login', 'users:logout', 'users:signup']
        for page in pages:
            # Проверяем каждую страницу
            with self.subTest(page=page):
                url = reverse(page)
                # GET-запрос анонимным пользователем
                response = self.anonymous_client.get(url)
                # Проверяем, что статус 200
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_auth_user(self):
        """Страницы доступны авторизованному пользователю."""
        # Страницы только для авторизованных пользователей
        pages = ['notes:list', 'notes:add', 'notes:success']
        for page in pages:
            # Проверяем каждую страницу
            with self.subTest(page=page):
                url = reverse(page)
                # GET-запрос авторизованным пользователем
                response = self.not_author_client.get(url)
                # Проверяем, что статус 200
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_different_users(self):
        """
        Доступ к страницам заметок корректно обрабатывается
        для автора и не автора.
        """
        users_statuses = [
            # Не автор должен получать 404
            (self.not_author_client, HTTPStatus.NOT_FOUND),
            # Автор должен получать доступ
            (self.author_client, HTTPStatus.OK)
        ]
        # Проверяемые страницы
        pages = ['notes:detail', 'notes:edit', 'notes:delete']
        for client, expected_status in users_statuses:
            for page in pages:
                # Проверяем каждое сочетание
                with self.subTest(client=client, page=page):
                    url = reverse(page, args=(self.note.slug,))
                    # GET-запрос от конкретного клиента
                    response = client.get(url)
                    # Проверяем соответствие ожидаемому статусу
                    self.assertEqual(response.status_code, expected_status)

    def test_redirects_for_anonymous_user(self):
        """
        Редиректы дял анонимного пользователя

        Анонимный пользователь перенаправляется на страницу логина
        со всех страниц, требующих авторизации.
        """
        login_url = reverse('users:login')
        # Страницы, требующие авторизации
        pages = {
            'notes:detail': (self.note.slug,),
            'notes:edit': (self.note.slug,),
            'notes:delete': (self.note.slug,),
            'notes:add': None,
            'notes:success': None,
            'notes:list': None,
        }
        for page, args in pages.items():
            # Проверяем каждую страницу
            with self.subTest(page=page):
                url = reverse(page, args=args)
                # Ожидаемый редирект на страницу логина с next
                expected_url = f'{login_url}?next={url}'
                # GET-запрос от анонимного пользователя
                response = self.anonymous_client.get(url)
                # Проверяем редирект к странице логина
                self.assertRedirects(response, expected_url)
