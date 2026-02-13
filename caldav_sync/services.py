from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
import fcntl
import os
import secrets
import tempfile

from passlib.apache import HtpasswdFile
from caldav import DAVClient
from caldav.lib.error import AuthorizationError
from icalendar import Calendar, Event as ICalEvent

from events.models import Event

def generate_radicale_password(length: int = 32) -> str:
    # Sensitive credential; consider encrypting at rest in the future.
    token = secrets.token_urlsafe(length)
    if len(token) < length:
        token = secrets.token_urlsafe(length + 8)
    return token


def resolve_htpasswd_path() -> str:
    if settings.RADICALE_HTPASSWD_PATH:
        return settings.RADICALE_HTPASSWD_PATH

    config_path = settings.RADICALE_CONFIG_PATH
    if not config_path:
        return ''

    try:
        with open(config_path, 'r', encoding='utf-8') as config_file:
            for line in config_file:
                line = line.strip()
                if line.startswith('htpasswd_filename'):
                    _, value = line.split('=', 1)
                    return value.strip()
    except FileNotFoundError:
        return ''

    return ''


def ensure_radicale_user(username: str, password: str) -> bool:
    htpasswd_path = resolve_htpasswd_path()
    if not htpasswd_path:
        raise FileNotFoundError('Radicale htpasswd file not configured')
    if settings.RADICALE_HTPASSWD_ENCRYPTION == 'plain':
        return _ensure_plain_user(htpasswd_path, username, password)

    ht = HtpasswdFile(
        htpasswd_path,
        new=not os.path.exists(htpasswd_path),
    )
    if not ht.check_password(username, password):
        ht.set_password(username, password)
        ht.save()
        return True
    return False


def _ensure_plain_user(htpasswd_path: str, username: str, password: str) -> bool:
    parent_dir = os.path.dirname(htpasswd_path) or '.'
    if not os.path.isdir(parent_dir):
        raise FileNotFoundError(f'Radicale htpasswd directory not found: {parent_dir}')

    lock_path = f'{htpasswd_path}.lock'
    updated = False
    created = False

    with open(lock_path, 'a', encoding='utf-8') as lock_handle:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
        lines = []
        if os.path.exists(htpasswd_path):
            with open(htpasswd_path, 'r', encoding='utf-8') as handle:
                lines = handle.read().splitlines()

        new_lines = []
        for line in lines:
            if not line.strip():
                continue
            if ':' not in line:
                new_lines.append(line)
                continue
            existing_user, _ = line.split(':', 1)
            if existing_user == username:
                new_lines.append(f'{username}:{password}')
                updated = True
            else:
                new_lines.append(line)

        if not updated:
            new_lines.append(f'{username}:{password}')
            created = True

        fd, tmp_path = tempfile.mkstemp(prefix='.htpasswd.', dir=parent_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as tmp_handle:
                tmp_handle.write('\n'.join(new_lines) + '\n')
                tmp_handle.flush()
                os.fsync(tmp_handle.fileno())
            os.replace(tmp_path, htpasswd_path)
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    return created and not updated


def get_caldav_client(username: str, password: str) -> DAVClient:
    return DAVClient(
        settings.RADICALE_BASE_URL,
        username=username,
        password=password,
        ssl_verify_cert=settings.RADICALE_VERIFY_SSL,
    )


def get_or_create_calendar(client: DAVClient, calendar_name: str):
    principal = client.principal()
    calendars = principal.calendars()
    for cal in calendars:
        if getattr(cal, 'name', None) == calendar_name:
            return cal
    return principal.make_calendar(name=calendar_name)


def ensure_user_calendar(username: str, password: str, calendar_name: str | None = None):
    client = get_caldav_client(username, password)
    calendar_name = calendar_name or settings.RADICALE_DEFAULT_CALENDAR
    try:
        calendar = get_or_create_calendar(client, calendar_name)
    except AuthorizationError as exc:
        raise PermissionError('Radicale authorization failed (401/403)') from exc
    except Exception as exc:
        raise RuntimeError(f'Failed to ensure Radicale calendar: {exc}') from exc

    calendar_url = str(getattr(calendar, 'url', None) or getattr(calendar, 'href', ''))
    return calendar, calendar_url


def build_ics(event: Event) -> str:
    tz = ZoneInfo(settings.TIME_ZONE or 'UTC')
    start_dt = datetime.combine(event.date, event.start_time, tzinfo=tz)
    end_dt = start_dt + timedelta(minutes=event.duration)

    cal = Calendar()
    cal.add('prodid', '-//AutoPlan AI//Smart Calendar Hub//')
    cal.add('version', '2.0')

    ical_event = ICalEvent()
    ical_event.add('summary', event.title)
    ical_event.add('dtstart', start_dt)
    ical_event.add('dtend', end_dt)
    if event.location:
        ical_event.add('location', event.location)
    if event.description:
        ical_event.add('description', event.description)
    if event.category:
        ical_event.add('categories', [event.category])

    cal.add_component(ical_event)
    return cal.to_ical().decode('utf-8')


def sync_event_to_caldav(event: Event, username: str, password: str):
    client = get_caldav_client(username, password)
    calendar = get_or_create_calendar(client, settings.RADICALE_DEFAULT_CALENDAR)
    ics = build_ics(event)

    if event.caldav_href:
        remote_event = calendar.event_by_url(event.caldav_href)
        remote_event.data = ics
        remote_event.save()
        event.caldav_uid = getattr(remote_event, 'uid', None) or event.caldav_uid
        event.caldav_href = str(getattr(remote_event, 'url', None) or getattr(remote_event, 'href', '')) or event.caldav_href
        event.save(update_fields=['caldav_uid', 'caldav_href'])
        return remote_event

    created = calendar.add_event(ics)
    event.caldav_uid = getattr(created, 'uid', None) or event.caldav_uid
    event.caldav_href = str(getattr(created, 'url', None) or getattr(created, 'href', '')) or event.caldav_href
    event.save(update_fields=['caldav_uid', 'caldav_href'])
    return created
