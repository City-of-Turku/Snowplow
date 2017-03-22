import pytz

from django.contrib.gis.geos import Point

import factory
from faker import Faker

from .models import DataSource, EventType, Location, Vehicle

fake = Faker()


class DataSourceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = DataSource

    id = factory.Sequence(lambda n: 'test_ds_%d' % n)


class VehicleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Vehicle

    data_source = factory.SubFactory(DataSourceFactory)
    origin_id = factory.Sequence(lambda n: 'test_origin_id_%d' % n)


def get_timestamp(o):
    timestamp = fake.date_time_this_decade(before_now=True, after_now=False, tzinfo=pytz.UTC)
    if o.year:
        timestamp = timestamp.replace(year=o.year)
    return timestamp


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    class Params:
        year = None

    coords = factory.LazyFunction(lambda: Point(60.454510 + fake.random.uniform(0.001, 0.01),
                                                22.264824 + fake.random.uniform(0.001, 0.01)))
    vehicle = factory.SubFactory(VehicleFactory)
    timestamp = factory.LazyAttribute(get_timestamp)
