from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, time
import re
from zoneinfo import ZoneInfo

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow

from .models import GoogleOAuthToken


@dataclass
class GoogleEventPayload:
    summary: str
    start: datetime
    end: datetime
    time_zone: str
    all_day: bool = False
    location: str | None = None
    description: str | None = None
    attendees: list[str] | None = None
    reminder_minutes: int | None = None


def _trim_text(value: str | None, max_chars: int) -> str | None:
    if not value:
        return value
    if len(value) <= max_chars:
        return value
    # Keep room for ellipsis
    return value[: max_chars - 1].rstrip() + "…"


def _extract_valid_emails(raw: str | None) -> list[str]:
    if not raw:
        return []
    # Split by common separators, then validate with a simple email regex.
    parts = re.split(r'[,\n;，、\s]+', raw)
    email_re = re.compile(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
    emails = []
    for part in parts:
        token = part.strip()
        if token and email_re.match(token):
            emails.append(token)
    return emails


def get_google_oauth_flow(state: str | None = None, *, disable_state_check: bool = False) -> Flow:
    scopes = settings.GOOGLE_OAUTH_SCOPES
    if isinstance(scopes, str):
        scopes = [s for s in scopes.split(',') if s]
    flow = Flow.from_client_secrets_file(
        settings.GOOGLE_OAUTH_CLIENT_JSON_PATH,
        scopes=scopes,
        state=state,
        redirect_uri=settings.GOOGLE_OAUTH_REDIRECT_URI if disable_state_check else None,
    )
    flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
    if disable_state_check:
        flow.state = None
    return flow


def store_credentials(user, credentials: Credentials) -> GoogleOAuthToken:
    token, _ = GoogleOAuthToken.objects.get_or_create(user=user)
    token.access_token = credentials.token
    token.refresh_token = credentials.refresh_token or token.refresh_token
    token.token_uri = credentials.token_uri
    token.client_id = credentials.client_id
    token.client_secret = credentials.client_secret
    token.scopes = ' '.join(credentials.scopes or [])
    token.expiry = credentials.expiry
    token.save()
    return token


def get_google_credentials(user) -> Credentials:
    token = GoogleOAuthToken.objects.get(user=user)
    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri=token.token_uri,
        client_id=token.client_id,
        client_secret=token.client_secret,
        scopes=token.scopes.split(' '),
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        store_credentials(user, creds)
    return creds


def build_event_payload_from_model(event) -> GoogleEventPayload:
    tz_name = settings.TIME_ZONE or 'UTC'
    tz = ZoneInfo(tz_name)
    start_dt = datetime.combine(event.date, event.start_time, tzinfo=tz)
    end_dt = start_dt + timedelta(minutes=event.duration)
    is_all_day = event.start_time == time(0, 0) and event.duration >= 1440
    attendees = None
    if event.participants:
        emails = _extract_valid_emails(event.participants)
        if emails:
            attendees = emails

    return GoogleEventPayload(
        summary=_trim_text(event.title, 1024),
        location=_trim_text(event.location, 1024),
        description=_trim_text(event.description, 8000),
        start=start_dt,
        end=end_dt,
        time_zone=tz_name,
        all_day=is_all_day,
        attendees=attendees,
        reminder_minutes=event.reminder if event.reminder is not None else None,
    )


def to_google_event_body(payload: GoogleEventPayload) -> dict:
    if payload.all_day:
        start_date = payload.start.date().isoformat()
        end_date = (payload.start.date() + timedelta(days=1)).isoformat()
        body = {
            'summary': payload.summary,
            'start': {'date': start_date},
            'end': {'date': end_date},
        }
    else:
        body = {
            'summary': payload.summary,
            'start': {'dateTime': payload.start.isoformat(), 'timeZone': payload.time_zone},
            'end': {'dateTime': payload.end.isoformat(), 'timeZone': payload.time_zone},
        }
    if payload.location:
        body['location'] = payload.location
    if payload.description:
        body['description'] = payload.description
    if payload.attendees:
        body['attendees'] = [{'email': email} for email in payload.attendees]
    if payload.reminder_minutes is not None:
        body['reminders'] = {
            'useDefault': False,
            'overrides': [{'method': 'popup', 'minutes': int(payload.reminder_minutes)}],
        }
    return body
