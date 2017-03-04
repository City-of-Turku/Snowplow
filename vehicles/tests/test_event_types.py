from vehicles.constants import EVENT_TYPES
from vehicles.models import EventType
from vehicles.utils import populate_event_types


def _check_event_types():
    for event_type_data in EVENT_TYPES:
        event_type = EventType.objects.get(identifier=event_type_data['identifier'])
        assert event_type.name_fi == event_type_data.get('name_fi', '')
        assert event_type.name_en == event_type_data.get('name_en', '')


def test_event_types_are_populated():
    assert EventType.objects.count() == len(EVENT_TYPES)
    _check_event_types()


def test_populate_event_types_can_be_run_multiple_times():
    populate_event_types()
    populate_event_types()
    populate_event_types()

    assert EventType.objects.count() == len(EVENT_TYPES)
    _check_event_types()


def test_other_event_types_arent_affected_by_populate_event_types():
    EventType.objects.create(
        identifier='xxx',
        name_fi='uusi tyyppi',
        name_en='new type',
    )
    populate_event_types()

    assert EventType.objects.count() == len(EVENT_TYPES) + 1
    new_event_type = EventType.objects.get(identifier='xxx')
    assert new_event_type.name_fi == 'uusi tyyppi'
    assert new_event_type.name_en == 'new type'
