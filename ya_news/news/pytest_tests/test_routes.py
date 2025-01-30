from http import HTTPStatus

import pytest


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'user, page, expected_status',
    [
        (None, 'home', HTTPStatus.OK),
        (None, 'detail', HTTPStatus.OK),
        (None, 'login', HTTPStatus.OK),
        (None, 'logout', HTTPStatus.OK),
        (None, 'signup', HTTPStatus.OK),
        ('author_client', 'edit', HTTPStatus.OK),
        ('author_client', 'delete', HTTPStatus.OK),
        ('not_author_client', 'edit', HTTPStatus.NOT_FOUND),
        ('not_author_client', 'delete', HTTPStatus.NOT_FOUND),
    ],
)
def test_pages_availability(
    clean_db, urls, request, client, user,
    page, expected_status, news_object, comment
):
    """
    Тест доступности страниц:
    - Общих страниц (без авторизации или с авторизацией).
    - Страниц редактирования и удаления комментариев.
    """
    if user is not None:
        client = request.getfixturevalue(user)
    if page in ['edit', 'delete']:
        page_url = urls[page](comment.id)
    elif page == 'detail':
        page_url = urls[page](news_object.id)
    else:
        page_url = urls[page]
    response = client.get(page_url)
    assert response.status_code == expected_status


def test_redirect_for_anonymous_client(clean_db, urls, client, comment):
    """Тест редиректа для анонимных пользователей на страницы авторизации."""
    for page in (urls['edit'](comment.id,), urls['delete'](comment.id,)):
        login_url = urls['login']
        redirect_url = f'{login_url}?next={page}'
        response = client.get(page)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == redirect_url
