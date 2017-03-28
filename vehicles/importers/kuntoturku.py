import logging
from datetime import datetime

import requests
from django.conf import ImproperlyConfigured, settings
from django.db import transaction
from django.utils import timezone

from vehicles.constants import IGNORE_LOCATIONS_WITHOUT_EVENTS_SETTING
from vehicles.models import EventType, Location, Vehicle

from .base import BaseVehicleImporter

logger = logging.getLogger(__name__)

# mapping from KuntoTurku events to our supported events
EVENT_MAPPING = {
    'Auraus': 'au',
    'Hiekoitus': 'hi',
    'Hiekoitus 1': 'hi',
    'Hiekoitushiekan poisto': 'hn',
    'Huoltoajo1': None,
    'Huoltoajo2': None,
    'Höyläys': 'hs',
    'Lakaisu1': 'hj',  # TODO correct?
    'Lakaisu2': 'hj',  # TODO correct?
    'Lakaisu3': 'hj',  # TODO correct?
    'Lakaisu4': 'hj',  # TODO correct?
    'Lehtien keruu': None,
    'Lehtien murskaus': None,
    'Maalaus1': None,
    'Maalaus2': None,
    'Maalaus3': None,
    'Maalaus4': None,
    'Nostintyö': None,
    'Pesu': 'pe',
    'pesu1': 'pe',
    'Polanteen poisto': None,
    'Roskien keruu1': None,
    'Roskien keruu2': None,
    'Roskien keruu3': None,
    'Roskien keruu4': None,
    'siirtymäajo': None,
    'Siirtymäajo': None,
    'Sorastus': None,
    'Suolaus': 'su',
    'SyväSuolaus': 'su',  # TODO correct?
    'Testiajo': None,
    'Testiajo2': None,
    'työajo': None,
    'Työajo': None,
    'Virheralueiden hoito': None,
    'Ylläpito': None,
    'Ylläpitotyöt': None,
}


class KuntoTurkuImporter(BaseVehicleImporter):
    id = 'kuntoturku'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.url = self.settings.get('URL')
        if not self.url:
            raise ImproperlyConfigured('"URL" is required.')

        self.event_mapping = {
            key: EventType.objects.get(identifier=value)
            for key, value in EVENT_MAPPING.items() if value
        }

    def fetch_data(self):
        logger.debug('Fetching data from %s' % self.url)
        response = requests.get(self.url, timeout=self.run_interval / 2.0)
        response.raise_for_status()
        return response.json()

    def update_models(self, vehicle_data):
        logger.debug('Updating models')
        num_of_new_locations = 0
        num_of_ignored_locations = 0
        ignore_locations_without_events = getattr(settings, IGNORE_LOCATIONS_WITHOUT_EVENTS_SETTING, True)

        for vehicle_datum in vehicle_data:
            location_datum = vehicle_datum['last_location']

            events = []

            for original_event in location_datum['events']:
                event = self.event_mapping.get(original_event)
                if event:
                    events.append(event)
                else:
                    logger.debug('Unknown event %s' % original_event)

            if not events and ignore_locations_without_events:
                num_of_ignored_locations += 1
                continue

            timestamp = timezone.make_aware(datetime.strptime(location_datum['timestamp'], '%Y-%m-%d %H:%M:%S'))

            vehicle, created = Vehicle.objects.get_or_create(
                data_source=self.data_source,
                origin_id=vehicle_datum['id'],
            )

            if created:
                logger.debug('New vehicle %s' % vehicle)

            location, created = Location.objects.get_or_create(
                vehicle=vehicle,
                timestamp=timestamp,
                defaults=dict(
                    coords='POINT %s' % location_datum['coords'],
                )
            )

            if created:
                location.events = events
                num_of_new_locations += 1

        num_of_locations = len(vehicle_data)

        if num_of_new_locations:
            logger.info(
                'Number of new locations %d (total %s ignored %s)' %
                (num_of_new_locations, num_of_locations, num_of_ignored_locations)
            )
        else:
            ignored_msg = ' (%d ignored)' % num_of_ignored_locations if num_of_ignored_locations else ''
            logger.info('No locations' + ignored_msg)

    def run(self):
        vehicle_data = self.fetch_data()

        with transaction.atomic():
            self.update_models(vehicle_data)
