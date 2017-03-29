from datetime import timedelta

from django.conf import settings
from django.contrib.gis.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from .constants import DELAY_SETTING


class DataSource(models.Model):
    id = models.CharField(max_length=16, verbose_name=_('ID'), primary_key=True)
    name = models.CharField(max_length=100, verbose_name=_('name'))

    class Meta:
        verbose_name = _('data source')
        verbose_name_plural = _('data sources')

    def __str__(self):
        return '%s (%s)' % (self.name, self.id)


class Vehicle(models.Model):
    data_source = models.ForeignKey(DataSource, related_name='vehicles', on_delete=models.PROTECT)
    origin_id = models.CharField(max_length=32, verbose_name=_('origin ID'), db_index=True)
    last_location = models.ForeignKey(
        'Location', verbose_name=_('last_location'), related_name='last_location_vehicle', null=True, blank=True,
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _('vehicle')
        verbose_name_plural = _('vehicles')
        unique_together = ('data_source', 'origin_id')
        ordering = ('-last_location__timestamp',)

    def __str__(self):
        return str(self.id)

    def update_last_location(self):
        if hasattr(settings, DELAY_SETTING):
            delay = getattr(settings, DELAY_SETTING) or 0
        else:
            delay = 15 * 60  # default 15 mins

        delay_timestamp = now() - timedelta(seconds=delay)
        self.last_location = self.locations.filter(timestamp__lte=delay_timestamp).order_by('timestamp').last()
        self.save(update_fields=('last_location',))

    @property
    def available_locations(self):
        locations = self.locations
        if self.last_location:
            locations = locations.filter(timestamp__lte=self.last_location.timestamp)
        return locations

    @classmethod
    def update_last_locations(cls):
        """
        Update (if needed) delayed last location of all vehicles that aren't up to date.

        If location delay is enabled this needs to be called periodically to
        get locations actually updated in the API.
        """
        vehicles_with_new_locations = cls.objects.annotate(
            latest_timestamp=models.Max('locations__timestamp')
        ).exclude(
            last_location__timestamp=models.F('latest_timestamp')
        )
        for vehicle in vehicles_with_new_locations:
            vehicle.update_last_location()


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
    timestamp = models.DateTimeField(verbose_name=_('timestamp'), db_index=True)
    coords = models.PointField(verbose_name=_('coordinates'), srid=4326)
    vehicle = models.ForeignKey(Vehicle, verbose_name=_('vehicle'), related_name='locations', on_delete=models.PROTECT)
    events = models.ManyToManyField(EventType, verbose_name=_('events'), related_name='locations', blank=True)

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        unique_together = ('timestamp', 'vehicle')
        ordering = ('timestamp',)

    def __str__(self):
        return '%s %s %s' % (self.coords.y, self.coords.x, self.timestamp)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.timestamp < self.vehicle.locations.last().timestamp:
            # for some reason creating a location which isn't the latest, no further action required
            return

        delay = getattr(settings, DELAY_SETTING, 15 * 60)
        if delay and self.timestamp > (now() - timedelta(seconds=delay)):
            # the new location cannot be shown yet
            return

        # the new location can be shown normally
        self.vehicle.last_location = self
        self.vehicle.save(update_fields=('last_location',))
