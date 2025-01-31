from http import HTTPStatus

from .fixtures import BaseTestCase


class RoutesTests(BaseTestCase):
    """Класс, тестирующий маршруты приложения."""

    def test_pages_availability_for_anonymous_user(self):
        """Предоставляет различный доступ к страницам в зависимоcти от прав."""
        users_statuses = [

            (self.client, self.pages_for_anonymous, HTTPStatus.OK),
            (self.not_author_client, self.pages_for_not_author, HTTPStatus.OK),
            (
                self.not_author_client,
                self.pages_for_author,
                HTTPStatus.NOT_FOUND
            ),
            (self.author_client, self.pages_for_author, HTTPStatus.OK),
        ]
        for client, pages, expected_status in users_statuses:
            for page in pages:
                with self.subTest(client=client, page=page):
                    response = client.get(page)
                    self.assertEqual(response.status_code, expected_status)

    def test_redirects_for_anonymous_user(self):
        """
        Редиректы дял анонимного пользователя.

        Анонимный пользователь перенаправляется на страницу логина
        со всех страниц, требующих авторизации.
        """
        for page in self.pages_with_redirect_for_anonymous:
            with self.subTest(page=page):
                expected_url = f'{self.login_url}?next={page}'
                response = self.client.get(page)
                self.assertRedirects(response, expected_url)
