from datetime import datetime, timedelta


def today():
    return datetime.today()


def yesterday(today):
    return today - timedelta(days=1)


def tomorrow(today):
    return today + timedelta(days=1)
