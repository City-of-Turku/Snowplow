import pytest


@pytest.fixture(autouse=True)
def no_more_mark_django_db(transactional_db):
    pass
