import pytest
from django.conf import settings

from news.forms import CommentForm


pytestmark = pytest.mark.django_db


def test_news_count(client, urls, news):
    """Проверяет, что на главной отображается нужное количество новостей."""
    response = client.get(urls['home'])
    news_count = response.context['object_list'].count()
    assert news_count == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(client, urls, news):
    """Проверяет порядок новостей на главной странице (по убыванию по дате)."""
    response = client.get(urls['home'])
    object_list = response.context['object_list']
    all_dates = [news.date for news in object_list]
    sorted_dates = sorted(all_dates, reverse=True)
    assert all_dates == sorted_dates


def test_comments_order(client, urls, news_with_comments):
    """Проверяет порядок комментариев на странице детали новости (по дате)."""
    response = client.get(urls['detail'](news_with_comments.id))
    assert 'news' in response.context
    all_comments = response.context['news'].comment_set.order_by('created')
    all_dates = [comment.created for comment in all_comments]
    sorted_dates = sorted(all_dates)
    assert all_dates == sorted_dates


def test_anonymous_client_has_no_form(client, urls, news_with_comments):
    """Анонимный пользователь не видит форму для комментариев."""
    response = client.get(urls['detail'](news_with_comments.id))
    assert 'form' not in response.context


def test_authorized_client_has_form(
        not_author_client, urls, news_with_comments
):
    """Авторизованный пользователь видит форму для комментариев."""
    response = not_author_client.get(urls['detail'](news_with_comments.id))
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
