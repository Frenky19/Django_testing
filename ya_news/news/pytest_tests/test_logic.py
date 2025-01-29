from http import HTTPStatus

import pytest
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment
from .utils import today, tomorrow, yesterday

@pytest.mark.django_db
def test_user_can_create_comment(auth_client, news_object):
    client, user = auth_client
    url = reverse('news:detail', args=(news_object.id,))
    form_data = {'text': 'Текст комментария'}
    # Отправляем POST-запрос
    response = client.post(url, data=form_data)
    # Проверка редиректа
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{url}#comments'
    # Проверка создания комментария
    comments_count = Comment.objects.count()
    assert comments_count == 1
    # Проверка содержимого комментария
    comment = Comment.objects.get()
    assert comment.text == 'Текст комментария'
    assert comment.news == news_object
    assert comment.author == user


@pytest.mark.django_db
def test_user_cant_use_bad_words(auth_client, news_object):
    """Проверяем, что комментарий не содержит 'плохие слова'"""
    client, _ = auth_client
    url = reverse('news:detail', args=(news_object.id,))
    bad_words = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    # Отправляем запрос с использованием плохих слов
    response = client.post(url, data=bad_words)
    # Проверяем, что форма вернула соответствующую ошибку
    assert 'form' in response.context
    form = response.context['form']
    assert form.errors['text'] == [WARNING]
    # Проверяем, что комментарий не создан
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_delete_comment(author, comment, client):
    client.force_login(author)
    delete_url = reverse('news:delete', args=(comment.id,))
    comments_url = (
        reverse('news:detail', args=(comment.news.id,))
        + '#comments'
    )
    # Удаляем комментарий
    response = client.post(delete_url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == comments_url
    # Убедимся, что комментарий удалён
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(not_author_client, comment):
    delete_url = reverse('news:delete', args=(comment.id,))
    # Пытаемся удалить комментарий от чужого лица
    response = not_author_client.post(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Убедимся, что комментарий остался
    assert Comment.objects.count() == 1


@pytest.mark.django_db
def test_author_can_edit_comment(author, comment, client):
    client.force_login(author)
    edit_url = reverse('news:edit', args=(comment.id,))
    comments_url = (
        reverse('news:detail', args=(comment.news.id,))
        + '#comments'
    )
    new_text = 'Обновлённый комментарий'
    response = client.post(edit_url, data={'text': new_text})
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == comments_url
    # Проверяем, что текст комментария обновился
    comment.refresh_from_db()
    assert comment.text == new_text


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(not_author_client, comment):
    edit_url = reverse('news:edit', args=(comment.id,))
    # Пытаемся отредактировать комментарий от чужого лица
    new_text = 'Обновлённый комментарий'
    response = not_author_client.post(edit_url, data={'text': new_text})
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Убедимся, что текст остался прежним
    comment.refresh_from_db()
    assert comment.text == 'Текст комментария'
