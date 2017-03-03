from .constants import EVENT_TYPES
from .models import EventType


def populate_event_types():
    for event_type in EVENT_TYPES:
        EventType.objects.update_or_create(identifier=event_type['identifier'], defaults=event_type)
