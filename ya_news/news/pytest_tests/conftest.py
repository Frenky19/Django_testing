from datetime import timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News
from .utils import today


User = get_user_model()


@pytest.fixture
def clean_db(db):
    """Удаляем все данные, связанные с тестируемыми моделями."""
    Comment.objects.all().delete()
    News.objects.all().delete()


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
    News.objects.bulk_create([
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today_date - timedelta(days=index)
        ) for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ])


@pytest.fixture
def news_with_comments(db, news_object, author):
    """Создает новость с комментариями."""
    now = timezone.now()
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE):
        comment = Comment.objects.create(
            news=news_object, author=author, text=f'Текст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
    return news_object


@pytest.fixture
def urls():
    return {
        'home': reverse('news:home'),
        'detail': lambda id: reverse('news:detail', args=[id]),
        'edit': lambda id: reverse('news:edit', args=[id]),
        'delete': lambda id: reverse('news:delete', args=[id]),
        'login': reverse('users:login'),
        'logout': reverse('users:logout'),
        'signup': reverse('users:signup'),
    }
