from datetime import datetime

from news.models import Comment, News


def today():
    return datetime.today()


def clean_db(db):
    """Удаляем все данные, связанные с тестируемыми моделями."""
    Comment.objects.all().delete()
    News.objects.all().delete()
