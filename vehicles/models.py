from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _


class DataSource(models.Model):
    id = models.CharField(max_length=16, verbose_name=_('ID'), primary_key=True)
    name = models.CharField(max_length=100, verbose_name=_('name'))

    class Meta:
        verbose_name = _('data source')
        verbose_name_plural = _('data sources')

    def __str__(self):
        return '%s (%s)' % (self.name, self.id)


class Vehicle(models.Model):
    last_timestamp = models.DateTimeField(verbose_name=_('last timestamp'), null=True, blank=True)
    data_source = models.ForeignKey(DataSource, related_name='vehicles', on_delete=models.PROTECT)
    origin_id = models.CharField(max_length=32, verbose_name=_('origin ID'), db_index=True)

    class Meta:
        verbose_name = _('vehicle')
        verbose_name_plural = _('vehicles')
        unique_together = ('data_source', 'origin_id')

    def __str__(self):
        return str(self.id)


class EventType(models.Model):
    identifier = models.CharField(max_length=16, verbose_name=_('identifier'), unique=True)
    name_fi = models.CharField(max_length=100, verbose_name=_('name in Finnish'), blank=True)
    name_en = models.CharField(max_length=100, verbose_name=_('name in English'), blank=True)

    class Meta:
        verbose_name = _('event')
        verbose_name_plural = _('events')

    def __str__(self):
        return '%s (%s)' % (self.name_fi or self.name_en, self.identifier)


class Location(models.Model):
    timestamp = models.DateTimeField(verbose_name=_('timestamp'))
    coords = models.PointField(verbose_name=_('coordinates'), srid=4326)
    vehicle = models.ForeignKey(Vehicle, verbose_name=_('vehicle'), related_name='locations', on_delete=models.PROTECT)
    events = models.ManyToManyField(EventType, verbose_name=_('events'), related_name='locations', blank=True)

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        unique_together = ('timestamp', 'vehicle')

    def __str__(self):
        return '%s %s %s' % (self.vehicle_id, self.coords, self.timestamp)
