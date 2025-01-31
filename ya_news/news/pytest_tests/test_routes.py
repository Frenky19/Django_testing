from http import HTTPStatus

import pytest


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'user, page, expected_status',
    [
        ('client', 'home', HTTPStatus.OK),
        ('client', 'detail', HTTPStatus.OK),
        ('client', 'login', HTTPStatus.OK),
        ('client', 'logout', HTTPStatus.OK),
        ('client', 'signup', HTTPStatus.OK),
        ('author_client', 'edit', HTTPStatus.OK),
        ('author_client', 'delete', HTTPStatus.OK),
        ('not_author_client', 'edit', HTTPStatus.NOT_FOUND),
        ('not_author_client', 'delete', HTTPStatus.NOT_FOUND),
    ],
)
def test_pages_availability(
    urls, request, client, user,
    page, expected_status
):
    """
    Тест доступности страниц.

    - Общих страниц (без авторизации или с авторизацией).
    - Страниц редактирования и удаления комментариев.
    """
    client = request.getfixturevalue(user)
    response = client.get(urls[page])
    assert response.status_code == expected_status


@pytest.mark.parametrize('page', ['edit', 'delete'])
def test_redirect_for_anonymous_client(page, urls, client):
    """Тест редиректа для анонимных пользователей на страницы авторизации."""
    login_url = urls['login']
    page_url = urls[page]
    redirect_url = f'{login_url}?next={page_url}'
    response = client.get(page_url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == redirect_url
