from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone

from news.models import News, Comment


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
def auth_client(db, django_user_model):
    """Фикстура для авторизованного клиента."""
    author = django_user_model.objects.create(username='Автор')
    client = Client()
    client.force_login(author)
    return client, author


@pytest.fixture
def not_author_client(db):
    """Фикстура для создания клиента не автора."""
    not_author = User.objects.create(username='Не автор')
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
def today():
    return datetime.today()


@pytest.fixture
def yesterday(today):
    return today - timedelta(days=1)


@pytest.fixture
def tomorrow(today):
    return today + timedelta(days=1)


@pytest.fixture
def news(db, today):
    """Создает тестовые новости для главной страницы."""
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            # Для каждой новости уменьшаем дату на index дней от today
            date=today - timedelta(days=index)
        ) for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def news_with_comments(db):
    """Создает новость с комментариями."""
    news = News.objects.create(title='Тестовая новость', text='Просто текст.')
    author = User.objects.create(username='Комментатор')
    now = timezone.now()
    # Создаем комментарии
    comments = []
    for index in range(settings.NEWS_COUNT_ON_HOME_PAGE):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Текст {index}',
        )
        # Устанавливаем время создания комментария
        comment.created = now + timedelta(days=index)
        # Сохраняем изменения
        comment.save()
        comments.append(comment)
    return news, author, comments
