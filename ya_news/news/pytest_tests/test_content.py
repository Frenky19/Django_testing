import pytest
from django.conf import settings
from django.urls import reverse

from news.forms import CommentForm
from .utils import today, tomorrow, yesterday

@pytest.mark.django_db
def test_news_count(client, news):
    """Проверяет, что на главной отображается нужное количество новостей."""
    home_url = reverse('news:home')
    response = client.get(home_url)
    object_list = response.context['object_list']
    news_count = len(object_list)
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, news):
    """Проверяет порядок новостей на главной странице (по убыванию по дате)."""
    home_url = reverse('news:home')
    response = client.get(home_url)
    object_list = response.context['object_list']
    # Получаем даты новостей
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    # Проверяем, что даты отсортированы правильно
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_comments_order(client, news_with_comments):
    """Проверяет порядок комментариев на странице детали новости (по дате)."""
    news, _, _ = news_with_comments
    detail_url = reverse('news:detail', args=(news.id,))
    response = client.get(detail_url)
    # Проверяем, что объект новости существует в контексте
    assert 'news' in response.context
    # Получаем объект новости
    news_context = response.context['news']
    # Получаем все комментарии к новости
    all_comments = news_context.comment_set.all()
    # Собираем даты всех комментариев
    all_dates = [comment.created for comment in all_comments]
    # Сортируем временные метки
    sorted_dates = sorted(all_dates)
    # Проверяем, что даты отсортированы правильно
    assert all_dates == sorted_dates


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, news_with_comments):
    """Анонимный пользователь не видит форму для комментариев."""
    news, _, _ = news_with_comments
    detail_url = reverse('news:detail', args=(news.id,))
    response = client.get(detail_url)
    # Проверяем, что в контексте нет формы
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(client, news_with_comments):
    """Авторизованный пользователь видит форму для комментариев."""
    news, author, _ = news_with_comments
    detail_url = reverse('news:detail', args=(news.id,))
    # Авторизуем клиента
    client.force_login(author)
    response = client.get(detail_url)
    # Проверяем, что форма присутствует в контексте
    assert 'form' in response.context
    # Проверяем, что форма имеет правильный тип
    assert isinstance(response.context['form'], CommentForm)
