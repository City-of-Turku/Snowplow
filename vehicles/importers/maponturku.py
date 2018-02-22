import logging
import pytz
from datetime import datetime

import requests
from django.conf import ImproperlyConfigured, settings
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

import time
import datetime as dt

from vehicles.constants import IGNORE_LOCATIONS_WITHOUT_EVENTS_SETTING
from vehicles.models import EventType, Location, Vehicle

from .base import BaseVehicleImporter

logger = logging.getLogger(__name__)

# mapping from Mapon events to our supported events

EVENT_MAPPING = {
    'Liukkauden torjunta': 'ha',
    'LAKAISU': 'hj',
    'Auraus': 'au',
    'Etuaura': 'au',
    'HIEKOITUS': 'hi',
    'Höyläys': 'hs',
    'Sivuharja': 'hj',
}


class MaponImporter(BaseVehicleImporter):
    id = 'maponturku'

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

        now = dt.datetime.utcnow()
        updated_after = now - timedelta(minutes=1)

        for vehicle_datum in vehicle_data['data']['units']:
            datet = datetime.strptime(vehicle_datum['last_update'], "%Y-%m-%dT%H:%M:%SZ")
            if updated_after < datet:
                events = []
                for state in vehicle_datum.get('io_din',[]):
                    if state['state']==1:
                        event = self.event_mapping.get(str(state['label']))
                        if event:
                            events.append(event)
                        else:
                            logger.debug('Unknown event %s' % state['label'])

                if not events and ignore_locations_without_events:
                    num_of_ignored_locations += 1
                    continue

                vehicle, created = Vehicle.objects.get_or_create(
                    data_source=self.data_source,
                    origin_id=vehicle_datum['unit_id'],
                )

                if created:
                    logger.debug('New vehicle_datum %s' % vehicle)
                    
                utc = pytz.utc
                
                ts = datet
                ts = datet.replace(tzinfo=pytz.UTC)

                location, created = Location.objects.get_or_create(
                    vehicle=vehicle,
                    timestamp=ts,
                    defaults=dict(
                        coords='POINT ('+str(vehicle_datum['lng'])+' '+str(vehicle_datum['lat'])+')' 
                    )
                )

                if created:
                    location.events = events
                    num_of_new_locations += 1

        num_of_locations = len(vehicle_data['data']['units'])

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
