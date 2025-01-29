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
        # Используемые маршруты для анонимного клиента:
        cls.pages_for_anonymous = [
            'notes:home', 'users:login', 'users:logout', 'users:signup'
        ]
        # Для авторизированного клиента (не автора):
        cls.pages_for_not_author = ['notes:list', 'notes:add', 'notes:success']
        # Для автора заметки:
        cls.pages_for_author = ['notes:detail', 'notes:edit', 'notes:delete']
        # Страницы для редиректа анонимного клиента:
        cls.pages_with_redirect_for_anonymous = {
            'notes:detail': (cls.note.slug,),
            'notes:edit': (cls.note.slug,),
            'notes:delete': (cls.note.slug,),
            'notes:add': None,
            'notes:success': None,
            'notes:list': None,
        }
        # Редирект на страницу логина:
        cls.login_url = reverse('users:login')


class RoutesTests(BaseTestCase):
    """Класс, тестирующий маршруты приложения"""

    def test_pages_availability_for_anonymous_user(self):
        """Страницы доступны анонимному пользователю."""
        for page in self.pages_for_anonymous:
            # Проверяем каждую страницу
            with self.subTest(page=page):
                url = reverse(page)
                # GET-запрос анонимным пользователем
                response = self.client.get(url)
                # Проверяем, что статус 200
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_not_author_user(self):
        """Страницы доступны авторизованному пользователю."""
        for page in self.pages_for_not_author:
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
        for client, expected_status in users_statuses:
            for page in self.pages_for_author:
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
        # Страницы, требующие авторизации
        for page, args in self.pages_with_redirect_for_anonymous.items():
            # Проверяем каждую страницу
            with self.subTest(page=page):
                url = reverse(page, args=args)
                # Ожидаемый редирект на страницу логина с next
                expected_url = f'{self.login_url}?next={url}'
                # GET-запрос от анонимного пользователя
                response = self.client.get(url)
                # Проверяем редирект к странице логина
                self.assertRedirects(response, expected_url)
