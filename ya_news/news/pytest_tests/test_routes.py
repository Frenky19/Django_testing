import pytest
from http import HTTPStatus
from django.urls import reverse
from django.contrib.auth import get_user_model


User = get_user_model()


@pytest.mark.django_db
def test_pages_availability(client, news_object):
    """Тест доступности страниц."""
    # Набор страниц для проверки
    pages = [
        ('news:home', None),
        ('news:detail', (news_object.id,)),
        ('users:login', None),
        ('users:logout', None),
        ('users:signup', None),
    ]

    for name, args in pages:
        # Генерация адреса с помощью reverse
        url = reverse(name, args=args)
        # Отправка GET-запроса
        response = client.get(url)
        # Проверка статуса ответа
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    'user, expected_status',
    [
        ('author', HTTPStatus.OK),
        ('not_author', HTTPStatus.NOT_FOUND),
    ],
)
def test_availability_for_comment_edit_and_delete(
    client, user, expected_status, request, comment
):
    """Тест доступности страниц редактирования и удаления комментариев."""
    # Получаем пользователя из фикстуры
    test_user = request.getfixturevalue(user)
    # Логиним пользователя
    client.force_login(test_user)

    # Проверяем доступы для страниц редактирования и удаления комментариев
    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        response = client.get(url)
        assert response.status_code == expected_status


@pytest.mark.django_db
def test_redirect_for_anonymous_client(client, comment):
    """Тест редиректа для анонимных пользователей на страницы авторизации."""
    login_url = reverse('users:login')

    for name in ('news:edit', 'news:delete'):
        url = reverse(name, args=(comment.id,))
        # Ожидаемый редирект с параметром next
        redirect_url = f'{login_url}?next={url}'
        response = client.get(url)
        # Проверка, что редирект ведёт на страницу логина
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == redirect_url
