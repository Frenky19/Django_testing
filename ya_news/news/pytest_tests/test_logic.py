from http import HTTPStatus

import pytest

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


pytestmark = pytest.mark.django_db


def test_user_can_create_comment(
        clean_db, author_client, urls, news_object, author
):
    comment_count_before = Comment.objects.count()
    form_data = {'text': 'Текст комментария'}
    response = author_client.post(
        urls['detail'](news_object.id), data=form_data
    )
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before + 1
    assert response.status_code == HTTPStatus.FOUND
    detail_url = urls['detail'](news_object.id)
    assert response.url == f'{detail_url}#comments'
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news_object
    assert comment.author == author


def test_user_cant_use_bad_words(clean_db, author_client, urls, news_object):
    """Проверяем, что комментарий не содержит 'плохие слова'"""
    comment_count_before = Comment.objects.count()
    bad_words = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    response = author_client.post(
        urls['detail'](news_object.id), data=bad_words
    )
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before
    assert 'form' in response.context
    form = response.context['form']
    assert form.errors['text'] == [WARNING]


def test_author_can_delete_comment(
        clean_db, author_client, urls, comment
):
    comment_count_before = Comment.objects.count()
    response = author_client.post(urls['delete'](comment.id))
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before - 1
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == (urls['detail'](comment.news.id) + '#comments')


def test_user_cant_delete_comment_of_another_user(
        clean_db, not_author_client, urls, comment
):
    comment_count_before = Comment.objects.count()
    response = not_author_client.post(urls['delete'](comment.id))
    comment_count_after = Comment.objects.count()
    assert comment_count_after == comment_count_before
    assert response.status_code == HTTPStatus.NOT_FOUND


def test_author_can_edit_comment(
        clean_db, author_client, urls, comment, client
):
    new_text = 'Обновлённый комментарий'
    response = author_client.post(
        urls['edit'](comment.id), data={'text': new_text}
    )
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == (urls['detail'](comment.news.id) + '#comments')
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment_from_db.text == new_text
    assert comment_from_db.author == comment.author
    assert comment_from_db.news == comment.news


def test_user_cant_edit_comment_of_another_user(
        clean_db, urls, not_author_client, comment
):
    new_text = 'Обновлённый комментарий'
    response = not_author_client.post(
        urls['edit'](comment.id), data={'text': new_text}
    )
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment_from_db.text == comment.text
    assert comment_from_db.author == comment.author
    assert comment_from_db.news == comment.news
