"""RTC diagnostics: stale cloud payloads must never look like drifting clocks."""
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import pytest

from test_adaptive_polling import coordinator as coordinator_module, PACKAGE
from importlib import import_module

RTCMonitor = import_module(f"{PACKAGE}.rtc_monitor").RTCMonitor

START = datetime(2026, 11, 1, 9, 47, tzinfo=ZoneInfo('Europe/Berlin'))


def sample(seconds=0, offset=3, source='xhr'):
    clock = START + timedelta(seconds=seconds, minutes=offset)
    return {'connection_status': 'online', 'device_timestamp': 100000 + seconds,
            'time_display': clock.strftime('%H:%M'), 'data_source': source}


def observe(monitor, seconds, offset=3, **kwargs):
    return monitor.observe(sample(seconds, offset, **kwargs), START + timedelta(seconds=seconds), seconds)


def test_baseline_signed_offset_and_no_small_offset_warning():
    monitor = RTCMonitor()
    assert observe(monitor, 0)['rtc_offset'] is None
    assert observe(monitor, 30) == {'rtc_offset': 3, 'rtc_warning': False}
    assert observe(monitor, 60, -3)['rtc_offset'] == -3


@pytest.mark.parametrize('offset', [6, 30, -6, -30])
def test_persistent_warning_and_recovery(offset):
    monitor = RTCMonitor()
    for seconds in range(0, 211, 30):
        state = observe(monitor, seconds, offset)
        assert state['rtc_warning'] is (None if seconds == 0 else seconds >= 210)
    assert observe(monitor, 240, 0) == {'rtc_offset': 0, 'rtc_warning': False}
    assert observe(monitor, 270, offset)['rtc_warning'] is False


def test_minute_tolerance_and_transient_warning():
    monitor = RTCMonitor()
    for seconds in range(0, 301, 30):
        assert observe(monitor, seconds, 5)['rtc_warning'] in (None, False)
    assert observe(monitor, 330, 30)['rtc_warning'] is False
    assert observe(monitor, 360, 0)['rtc_warning'] is False


def test_repeated_payload_does_not_recompute_or_rearm_warning():
    monitor = RTCMonitor()
    observe(monitor, 0, 30)
    observe(monitor, 30, 30)
    for seconds in [60, 90, 149]:
        assert monitor.observe(sample(30, 30), START + timedelta(seconds=seconds), seconds) == {'rtc_offset': 30, 'rtc_warning': False}
    for seconds in [150, 180, 600]:
        assert monitor.observe(sample(30, 30), START + timedelta(seconds=seconds), seconds) == {'rtc_offset': None, 'rtc_warning': None}
    assert observe(monitor, 630, 30)['rtc_offset'] is None
    assert observe(monitor, 660, 30)['rtc_warning'] is False


@pytest.mark.parametrize('bad', [None, '', '24:00', '12:60', '1:02', '12:00:00', 123])
def test_invalid_clock(bad):
    monitor = RTCMonitor()
    observe(monitor, 0)
    data = sample(30)
    data['time_display'] = bad
    assert monitor.observe(data, START, 30)['rtc_offset'] is None


@pytest.mark.parametrize('stamp', [None, 0, -1, True, '123', 1.5])
def test_invalid_timestamp(stamp):
    data = sample()
    data['device_timestamp'] = stamp
    assert RTCMonitor().observe(data, START, 0)['rtc_offset'] is None


def test_offline_source_changes_and_device_clock_adjustment_reset():
    monitor = RTCMonitor()
    observe(monitor, 0)
    observe(monitor, 30)
    assert monitor.observe({'connection_status': 'offline'}, START, 40)['rtc_warning'] is None
    assert observe(monitor, 60)['rtc_offset'] is None
    assert observe(monitor, 90)['rtc_offset'] == 3
    assert observe(monitor, 120, source='bridge')['rtc_offset'] is None
    assert observe(monitor, 150, source='bridge')['rtc_offset'] == 3
    data = sample(180, source='bridge')
    data['device_timestamp'] += 1800
    assert monitor.observe(data, START + timedelta(seconds=180), 180)['rtc_offset'] is None
    data = sample(210, 30, source='bridge')
    data['device_timestamp'] += 1800
    assert monitor.observe(data, START + timedelta(seconds=210), 210)['rtc_offset'] == 30


@pytest.mark.parametrize(('host', 'device', 'offset'), [('23:59', '00:02', 3), ('00:01', '23:58', -3)])
def test_midnight(host, device, offset):
    monitor = RTCMonitor()
    h, m = map(int, host.split(':'))
    now = START.replace(hour=h, minute=m)
    data = sample()
    data['time_display'] = device
    monitor.observe(data, now - timedelta(seconds=30), 0)
    data['device_timestamp'] += 30
    assert monitor.observe(data, now, 30)['rtc_offset'] == offset


def test_host_clock_and_timezone_changes_reset():
    monitor = RTCMonitor()
    observe(monitor, 0)
    observe(monitor, 30)
    assert monitor.observe(sample(60), START + timedelta(seconds=360), 60)['rtc_offset'] is None
    assert monitor.observe(sample(90), START.astimezone(ZoneInfo('UTC')), 90)['rtc_offset'] is None


def coordinator():
    module = coordinator_module
    obj = module.SpeidelBraumeisterDataCoordinator(None, None, 'TEST')
    obj.hass = SimpleNamespace(config=SimpleNamespace(time_zone='Europe/Berlin'))
    return module, obj


async def test_xhr_samples_reach_diagnostics_and_offline_clears():
    module, obj = coordinator()
    obj._fetch_bridge = AsyncMock(return_value=None)
    obj.web_auth = SimpleNamespace(get_device_status=AsyncMock())
    with patch.object(module, 'datetime') as clock, patch.object(module, 'monotonic') as mono:
        for seconds in [0, 30, 60]:
            clock.now.return_value = START + timedelta(seconds=seconds)
            mono.return_value = seconds
            obj.web_auth.get_device_status.return_value = {**sample(seconds), 'temperature': 20}
            result = await obj._async_update_data()
        assert result['rtc_offset'] == 3
        assert result['rtc_warning'] is False
        obj.web_auth.get_device_status.return_value = None
        assert (await obj._async_update_data())['rtc_offset'] is None


async def test_bridge_samples_and_mqtt_do_not_retain_diagnostics():
    module, obj = coordinator()
    obj._fetch_bridge = AsyncMock()
    with patch.object(module, 'datetime') as clock, patch.object(module, 'monotonic') as mono:
        for seconds in [0, 30]:
            clock.now.return_value = START + timedelta(seconds=seconds)
            mono.return_value = seconds
            obj._fetch_bridge.return_value = sample(seconds, source='bridge')
            result = await obj._async_update_data()
        assert result['rtc_offset'] == 3
        obj.data = result
        obj.async_set_updated_data = lambda value: setattr(obj, 'data', value)
        obj.update_from_mqtt({'temperature': 20})
        assert obj.data['rtc_offset'] is None
        assert obj.data['rtc_warning'] is None


async def test_diagnostic_entities_registration_and_unknown_states():
    """Exercise the actual descriptions and entity properties at the HA boundary."""
    import importlib
    import sys
    import types
    from conftest import ROOT
    from enum import StrEnum

    class EntityCategory(StrEnum):
        DIAGNOSTIC = "diagnostic"

    def mod(name, **attrs):
        result = types.ModuleType(name)
        result.__dict__.update(attrs)
        return result

    class Entity:
        def __init__(self, coordinator, key):
            self.coordinator = coordinator

    package = mod('rtc_entities')
    package.__path__ = [str(ROOT / 'custom_components' / 'speidel_braumeister')]
    stubs = {
        'rtc_entities': package,
        'rtc_entities.coordinator': mod('coordinator', SpeidelBraumeisterDataCoordinator=object),
        'rtc_entities.entity': mod('entity', SpeidelBraumeisterEntity=Entity),
        'homeassistant.config_entries': mod('config', ConfigEntry=object),
        'homeassistant.core': mod('core', HomeAssistant=object),
        'homeassistant.helpers.entity': mod('entity', EntityCategory=EntityCategory),
        'homeassistant.helpers.entity_platform': mod('platform', AddEntitiesCallback=object),
        'homeassistant.components.sensor': mod('sensor', SensorEntity=type('Sensor', (), {}), SensorEntityDescription=SimpleNamespace),
        'homeassistant.components.binary_sensor': mod('binary', BinarySensorEntity=type('Binary', (), {}), BinarySensorEntityDescription=SimpleNamespace),
    }
    with patch.dict(sys.modules, stubs):
        sensors = importlib.import_module('rtc_entities.sensor')
        binaries = importlib.import_module('rtc_entities.binary_sensor')
        obj = SimpleNamespace(data={'rtc_offset': 30, 'rtc_warning': True})
        hass = SimpleNamespace(data={'speidel_braumeister': {'test': obj}})
        entry = SimpleNamespace(entry_id='test')
        entities = []
        await sensors.async_setup_entry(hass, entry, entities.extend)
        await binaries.async_setup_entry(hass, entry, entities.extend)
        offset = next(e for e in entities if e.entity_description.key == 'rtc_offset')
        warning = next(e for e in entities if e.entity_description.key == 'rtc_warning')
        # HA registry requires an enum instance; an equal string is rejected.
        for entity in (offset, warning):
            category = entity.entity_description.entity_category
            assert isinstance(category, EntityCategory)
            assert category is EntityCategory.DIAGNOSTIC
        assert offset.entity_description.native_unit_of_measurement == 'min'
        assert warning.entity_description.device_class == 'problem'
        assert offset.native_value == 30
        assert warning.is_on is True
        obj.data = {'rtc_offset': None, 'rtc_warning': None}
        assert offset.native_value is None
        assert warning.is_on is None
        obj.data = None
        assert warning.is_on is None


@pytest.mark.parametrize("stamp,expected", [("1793511000", 1793511000), ("invalid", None), ("", None)])
def test_beta_xhr_parser_exposes_timestamp_without_changing_session(stamp, expected):
    from test_adaptive_polling import web, payload
    raw = payload().split(';')
    raw[2] = stamp
    data = web.SpeidelWebAuth('', '')._parse_xhr_response(';'.join(raw))
    assert data['device_timestamp'] == expected
    assert data['session_id'] == stamp
    assert data['time_display'] == '12:00'


async def test_beta_real_xhr_parser_reaches_rtc_monitor():
    from test_adaptive_polling import web, payload
    module, obj = coordinator()
    obj._fetch_bridge = AsyncMock(return_value=None)
    obj.web_auth = SimpleNamespace(get_device_status=AsyncMock())
    parser = web.SpeidelWebAuth('', '')
    with patch.object(module, 'datetime') as clock, patch.object(module, 'monotonic') as mono:
        for seconds in [0, 30, 60]:
            raw = payload().split(';')
            raw[2] = str(100000 + seconds)
            fields = raw[3].split('X')
            fields[1] = (START + timedelta(seconds=seconds, minutes=3)).strftime('%H:%M')
            raw[3] = 'X'.join(fields)
            obj.web_auth.get_device_status.return_value = parser._parse_xhr_response(';'.join(raw))
            clock.now.return_value = START + timedelta(seconds=seconds)
            mono.return_value = seconds
            result = await obj._async_update_data()
        assert result['rtc_offset'] == 3
        assert result['rtc_warning'] is False


@pytest.mark.parametrize("code,clock_text,flags,target,elapsed", [
    (101, '11:25', 'ph', None, None),
    (2810, '11:26', 'PH', 1200, 1004),
    (101, 'invalid', '??', None, None),
])
async def test_xhr_display_attributes_reach_card_sensor(code, clock_text, flags, target, elapsed):
    from test_adaptive_polling import web, payload
    module, obj = coordinator()
    obj._fetch_bridge = AsyncMock(return_value=None)
    raw = payload(code, indicators=flags).split(';')
    raw[2] = '100000'
    fields = raw[3].split('X')
    fields[1] = clock_text
    raw[3] = 'X'.join(fields)
    parsed = web.SpeidelWebAuth('', '')._parse_xhr_response(';'.join(raw))
    obj.web_auth = SimpleNamespace(get_device_status=AsyncMock(return_value=parsed))
    result = await obj._async_update_data()
    assert result['display_clock'] == (clock_text if clock_text != 'invalid' else None)
    assert result['display_pump_flag'] == (flags[0] if flags != '??' else None)
    assert result['display_heater_flag'] == (flags[1] if flags != '??' else None)
    assert result['display_time_target_seconds'] == target
    assert result['display_time_elapsed_seconds'] == elapsed
    assert result['rtc_offset'] is None  # Clock display is independent of RTC baseline.
    obj.web_auth.get_device_status.return_value = None
    offline = await obj._async_update_data()
    assert offline.get('display_clock') is None
