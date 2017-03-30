import logging
from collections import defaultdict
from datetime import datetime, timedelta

import dateutil.parser
from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions, serializers, viewsets

import timelib

from .constants import DEFAULT_LIMIT_SETTING
from .models import EventType, Location, Vehicle

logger = logging.getLogger(__name__)


class LocalTimeField(serializers.DateTimeField):
    def to_representation(self, value):
        return timezone.localtime(value) if value else None


class LocationSerializer(serializers.ModelSerializer):
    coords = serializers.SerializerMethodField()
    events = serializers.SerializerMethodField()
    timestamp = LocalTimeField()

    class Meta:
        model = Location
        fields = ('timestamp', 'coords', 'events')

    def get_coords(self, instance):
        return [instance.coords.x, instance.coords.y]

    def get_events(self, instance):
        prefetched_events = self.context.get('prefetched_events')

        if prefetched_events is None:
            # Fallback to fetching events here. This should not normally happen.
            logger.debug("Something seems to be wrong, LocationSerializer didn't get prefetched events.")
            return [event.identifier for event in instance.events.all()]

        return prefetched_events[instance.id]


class VehicleSerializer(serializers.ModelSerializer):
    last_location = serializers.SerializerMethodField()
    location_history = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Prefetch event identifiers for faster access

        self._prefetched_events = defaultdict(list)

        if self.context['action'] == 'list':
            location_ids = [vehicle.last_location.id for vehicle in self.instance]
        else:
            locations = self.instance.available_locations.order_by('-id')
            location_ids = locations.values_list('id', flat=True).distinct()

        event_dict = {ev.id: ev.identifier for ev in EventType.objects.all()}
        self._prefetched_events = defaultdict(list)

        through_objects = Location.events.through.objects.filter(location_id__in=location_ids)
        for key, value in through_objects.values_list('location_id', 'eventtype_id'):
            self._prefetched_events[key].append(event_dict[value])

    class Meta:
        model = Vehicle
        fields = ('id', 'last_location', 'location_history')

    def get_last_location(self, instance):
        return LocationSerializer(
            instance.last_location, context={'prefetched_events': self._prefetched_events}
        ).data

    def get_location_history(self, instance):
        if self.context['action'] == 'list':
            return []

        query_params = self.context['query_params']
        since = query_params.get('since')
        history = query_params.get('history')

        if not (since or history):
            return []

        locations = instance.available_locations.order_by('-timestamp')

        if since:
            locations = locations.filter(timestamp__gte=since)
        if history:
            locations = locations[:history]

        data = LocationSerializer(
            reversed(locations), many=True, context={'prefetched_events': self._prefetched_events}
        ).data

        return data

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        temporal_resolution = self.context['query_params'].get('temporal_resolution')
        if temporal_resolution:
            out = []
            for location in representation['location_history']:
                if not out:
                    out.append(location)
                    continue
                delta = location['timestamp'] - out[-1]['timestamp']
                if delta < timedelta(seconds=temporal_resolution):
                    continue
                out.append(location)
            representation['location_history'] = out

        return representation


class VehicleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicle.objects.exclude(last_location__isnull=True).select_related('last_location')
    serializer_class = VehicleSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parsed_query_params = {}

    def parse_query_params(self):  # noqa C901
        query_params = {}

        since = self.request.query_params.get('since')
        if since:
            try:
                # first try to parse since with dateutil in case it is a datetime
                since_datetime = dateutil.parser.parse(since)
            except ValueError:
                try:
                    # normally we get here if since has a relative value, try to parse
                    # it with timelib
                    since_datetime = datetime.fromtimestamp(timelib.strtotime(bytes(since, 'utf-8')))
                except ValueError:
                    raise exceptions.ValidationError('Invalid value for since parameter.')

            # local timezone is assumed if no timezone is given
            if not since_datetime.tzinfo:
                since_datetime = timezone.make_aware(since_datetime)

            query_params['since'] = since_datetime

        for int_param in ('history', 'limit', 'temporal_resolution'):
            value = self.request.query_params.get(int_param)
            if value:
                try:
                    query_params[int_param] = int(value)
                except ValueError:
                    raise exceptions.ValidationError('Invalid value for %s parameter.' % int_param)

        self.parsed_query_params = query_params

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['query_params'] = self.parsed_query_params
        context['action'] = self.action
        return context

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == 'list':
            since = self.parsed_query_params.get('since')
            if since:
                queryset = queryset.filter(last_location__timestamp__gte=since)

            default_limit = getattr(settings, DEFAULT_LIMIT_SETTING, 10)
            limit = self.parsed_query_params.get('limit') or default_limit
            queryset = queryset[:limit]

        return queryset

    def list(self, request):
        self.parse_query_params()
        return super().list(request)

    def retrieve(self, request, pk=None):
        self.parse_query_params()
        return super().retrieve(request, pk)
