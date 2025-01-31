from http import HTTPStatus

import pytest

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


pytestmark = pytest.mark.django_db


def test_user_can_create_comment(author_client, urls, news_object, author):
    """Авторизированнный пользователь может создавать комментарии."""
    Comment.objects.all().delete()
    form_data = {'text': 'Текст комментария'}
    response = author_client.post(urls['detail'], data=form_data)
    comment_count = Comment.objects.count()
    assert comment_count == 1
    assert response.status_code == HTTPStatus.FOUND
    detail_url = (urls['detail'] + '#comments')
    assert response.url == detail_url
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news_object
    assert comment.author == author


def test_user_cant_use_bad_words(author_client, urls):
    """Проверяем, что комментарий не содержит 'плохие слова'."""
    comment_count_before = Comment.objects.count()
    bad_words = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(urls['detail'], data=bad_words)
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before
    assert 'form' in response.context
    form = response.context['form']
    assert form.errors['text'] == [WARNING]


def test_author_can_delete_comment(author_client, urls):
    """Автор может удалять свои комментарии."""
    comment_count_before = Comment.objects.count()
    response = author_client.post(urls['delete'])
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before - 1
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == (urls['detail'] + '#comments')


def test_user_cant_delete_comment_of_another_user(not_author_client, urls):
    """Не автор не может удалять чужие комментарии."""
    comment_count_before = Comment.objects.count()
    response = not_author_client.post(urls['delete'])
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_author_can_edit_comment(author_client, urls, comment):
    """Автор может редактировать свои комментарии."""
    new_text = 'Обновлённый комментарий'
    response = author_client.post(
        urls['edit'], data={'text': new_text}
    )
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == (urls['detail'] + '#comments')
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment_from_db.text == new_text
    assert comment_from_db.author == comment.author
    assert comment_from_db.news == comment.news


def test_user_cant_edit_comment_of_another_user(
        urls, not_author_client, comment
):
    """Не автор не может редактировать чужие комментарии."""
    new_text = 'Обновлённый комментарий'
    response = not_author_client.post(
        urls['edit'], data={'text': new_text}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment_from_db.text == comment.text
    assert comment_from_db.author == comment.author
    assert comment_from_db.news == comment.news
