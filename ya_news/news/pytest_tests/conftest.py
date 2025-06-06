from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from news.models import Comment, News
from .utils import today


User = get_user_model()


@pytest.fixture
def news_object(db):
    """Фикстура для создания тестовой новости."""
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def author(db):
    """Фикстура для создания тестового автора."""
    return User.objects.create(username='Автор')


@pytest.fixture
def not_author(db):
    """Фикстура для создания тестового читателя."""
    return User.objects.create(username='Не автор')


@pytest.fixture
def author_client(db, author):
    """Фикстура для авторизованного клиента."""
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture
def not_author_client(db, not_author):
    """Фикстура для создания клиента не автора."""
    client = Client()
    client.force_login(not_author)
    return client


@pytest.fixture
def comment(news_object, author):
    """Фикстура для создания тестового комментария к новости."""
    return Comment.objects.create(
        news=news_object, author=author, text='Текст комментария'
    )


@pytest.fixture
def news(db):
    """Создает тестовые новости для главной страницы."""
    today_date = today()
    News.objects.bulk_create(
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today_date - timedelta(days=index)
        ) for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )


@pytest.fixture
def urls(comment):
    return {
        'home': reverse('news:home'),
        'detail': reverse('news:detail', args=[comment.id]),
        'edit': reverse('news:edit', args=[comment.id]),
        'delete': reverse('news:delete', args=[comment.id]),
        'login': reverse('users:login'),
        'logout': reverse('users:logout'),
        'signup': reverse('users:signup'),
    }
