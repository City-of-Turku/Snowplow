import pytest
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def no_more_mark_django_db(transactional_db):
    pass


@pytest.fixture(autouse=True)
def set_faker_random_seed():
    # set seed to make tests more deterministic
    from vehicles.factories import fake
    fake.seed(777)
