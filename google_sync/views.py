from __future__ import annotations

import logging
import secrets

from django.conf import settings
from django.contrib.auth import get_user_model, login
from django.core import signing
from django.shortcuts import redirect
from django.db.utils import OperationalError
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from googleapiclient.discovery import build

from events.models import Event
from .models import GoogleOAuthToken
from .services import (
    build_event_payload_from_model,
    get_google_credentials,
    get_google_oauth_flow,
    store_credentials,
    to_google_event_body,
)

logger = logging.getLogger(__name__)


class GoogleOAuthStartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        flow = get_google_oauth_flow()
        # Use a signed state that encodes the user id so callback can recover user
        # even if session cookies are lost during the OAuth redirect.
        state_payload = {
            'uid': request.user.id,
            'nonce': secrets.token_urlsafe(16),
        }
        signed_state = signing.dumps(state_payload, salt='google-oauth-state')
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',
            state=signed_state,
        )
        request.session['google_oauth_state'] = state
        return redirect(authorization_url)


class GoogleOAuthCallbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        try:
            state_from_session = request.session.get('google_oauth_state')
            state_from_query = request.GET.get('state') or None
            state = state_from_query or state_from_session
            if not state_from_query:
                # Session state missing - could be caused by cookies disabled
                # or using a different host (0.0.0.0 vs localhost). Log and
                # attempt to continue with state from query as a best-effort fallback.
                logger.warning('OAuth callback reached without session state; attempting fallback')
                if not state:
                    return Response({'detail': 'Missing OAuth state.'}, status=status.HTTP_400_BAD_REQUEST)

            disable_state_check = False
            if settings.DEBUG and state_from_query:
                if not state_from_session or state_from_session != state_from_query:
                    # In local dev, tolerate state mismatch to avoid blocking OAuth due to session churn.
                    # This should not be enabled in production.
                    logger.warning('OAuth state mismatch in DEBUG; bypassing state check')
                    disable_state_check = True

            flow = get_google_oauth_flow(
                state=state_from_query if state_from_query else state,
                disable_state_check=disable_state_check,
            )

            user_for_token = request.user if request.user.is_authenticated else None
            if not user_for_token:
                # Try to recover user from a signed state (query first, then session)
                for candidate_state in (state_from_query, state_from_session):
                    if not candidate_state:
                        continue
                    try:
                        payload = signing.loads(candidate_state, salt='google-oauth-state', max_age=600)
                        user_id = payload.get('uid')
                        if user_id:
                            user_for_token = get_user_model().objects.get(id=user_id)
                            break
                    except Exception:
                        logger.warning('Failed to validate signed OAuth state')

            if not user_for_token:
                return Response({'detail': 'Authentication required for OAuth callback.'}, status=status.HTTP_403_FORBIDDEN)

            # If OAuth completed without an authenticated session, log the user in
            if not request.user.is_authenticated:
                login(request, user_for_token)

            # Fetch token from the callback
            authorization_response = request.build_absolute_uri()
            logger.info(f"OAuth callback received from: {authorization_response[:100]}")

            flow.fetch_token(authorization_response=authorization_response)
            creds = flow.credentials

            # Store credentials
            store_credentials(user_for_token, creds)
            logger.info(f"OAuth token stored for user {user_for_token.username}")

            # Redirect to dashboard
            return redirect('/dashboard.html')

        except Exception as exc:
            logger.exception('OAuth callback failed')
            error_message = str(exc)

            # Show a more actionable HTML error with retry link
            return Response(
                f'''
                <html>
                    <head><title>Google Calendar Connection Failed</title></head>
                    <body style="font-family: Arial; padding: 40px; text-align: center; color: #333;">
                        <h1 style="color:#d9534f">❌ Connection Failed</h1>
                        <p style="color: #666; font-size: 16px; max-width:720px; margin:0 auto;">{error_message}</p>
                        <p style="margin-top: 20px;">
                            <a href="/connect_to_calendar.html" style="color: #ff6b6b; font-weight:600; text-decoration:none;">Retry Connect</a>
                            &nbsp;•&nbsp;
                            <a href="/dashboard.html" style="color: #666;">Back to Dashboard</a>
                        </p>
                        <hr style="margin: 40px 0; border: none; border-top: 1px solid #eee;">
                        <div style="color: #999; font-size: 13px; max-width:720px; margin:0 auto;">Possible causes:
                            <ul style="text-align:left; display:inline-block; margin-top:12px;">
                                <li>Cookies/session not preserved between redirect (use http://localhost:8000).</li>
                                <li>Browser blocked third-party cookies or SameSite restrictions.</li>
                                <li>OAUTHLIB_INSECURE_TRANSPORT not set for local HTTP.</li>
                            </ul>
                            <div style="margin-top:12px;">Tip: prefer opening <strong>http://localhost:8000</strong> (not 0.0.0.0) in your browser when testing OAuth.</div>
                        </div>
                    </body>
                </html>
                ''',
                status=status.HTTP_400_BAD_REQUEST
            )


class GoogleEventSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        event_id = request.data.get('event_id')
        if not event_id:
            return Response({'ok': False, 'error': 'event_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            event = Event.objects.get(id=event_id, user=request.user)
        except Event.DoesNotExist:
            return Response({'ok': False, 'error': 'Event not found'}, status=status.HTTP_404_NOT_FOUND)

        if not GoogleOAuthToken.objects.filter(user=request.user).exists():
            return Response({'ok': False, 'error': 'google_not_connected'}, status=status.HTTP_403_FORBIDDEN)

        try:
            creds = get_google_credentials(request.user)
        except Exception as exc:
            logger.exception('Failed to load Google credentials')
            return Response({'ok': False, 'error': 'google_auth_failed'}, status=status.HTTP_401_UNAUTHORIZED)

        payload = build_event_payload_from_model(event)
        body = to_google_event_body(payload)

        calendar_id = request.data.get('calendar_id') or 'primary'
        service = build('calendar', 'v3', credentials=creds)
        action = 'insert'
        try:
            if event.google_event_id:
                action = 'update'
                result = service.events().update(
                    calendarId=calendar_id,
                    eventId=event.google_event_id,
                    body=body,
                ).execute()
            else:
                result = service.events().insert(
                    calendarId=calendar_id,
                    body=body,
                    sendUpdates='none',
                ).execute()
                event.google_event_id = result.get('id')
                event.save(update_fields=['google_event_id'])
        except Exception as exc:
            logger.exception('Google Calendar sync failed')
            print("Google Calendar sync failed:", str(exc))
            return Response({'ok': False, 'error': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({
            'ok': True,
            'google_event_id': event.google_event_id,
            'htmlLink': result.get('htmlLink'),
            'action': action,
        })


class GoogleOAuthStatusView(APIView):
    """Return whether the current user has valid Google OAuth credentials."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            first_login = request.query_params.get('first_login') == '1'
            try:
                profile = getattr(request.user, 'profile', None)
            except OperationalError:
                # Migration not applied yet; treat as no profile data.
                profile = None
            connected = False
            account_email = None

            if not GoogleOAuthToken.objects.filter(user=request.user).exists():
                response = {'ok': True, 'connected': False}
                if first_login and profile and not profile.google_connect_prompted:
                    profile.google_connect_prompted = True
                    profile.save(update_fields=['google_connect_prompted'])
                    response['should_prompt'] = True
                elif first_login:
                    response['should_prompt'] = False
                return Response(response)

            # Try to load/refresh credentials. If this raises, treat as disconnected.
            try:
                creds = get_google_credentials(request.user)
                # Attempt to read the primary calendar to obtain the user's account id/email
                try:
                    service = build('calendar', 'v3', credentials=creds)
                    primary = service.calendarList().get(calendarId='primary').execute()
                    account_email = primary.get('id') or primary.get('summary')
                except Exception:
                    account_email = None
                connected = True
            except Exception:
                connected = False

            response = {'ok': True, 'connected': connected, 'account_email': account_email}
            if first_login:
                should_prompt = False
                if profile and not profile.google_connect_prompted:
                    if not connected:
                        should_prompt = True
                    profile.google_connect_prompted = True
                    profile.save(update_fields=['google_connect_prompted'])
                response['should_prompt'] = should_prompt
            return Response(response)

        except Exception as exc:
            logger.exception('Failed to determine Google OAuth status')
            return Response({'ok': False, 'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleOAuthDisconnectView(APIView):
    """Disconnect Google OAuth for the current user by deleting stored credentials."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = GoogleOAuthToken.objects.filter(user=request.user).first()
            if not token:
                return Response({'ok': True, 'disconnected': True})

            # Optionally try to revoke token at Google (best-effort)
            try:
                import requests
                revoke_url = 'https://oauth2.googleapis.com/revoke'
                params = {'token': token.access_token}
                requests.post(revoke_url, params=params, timeout=5)
            except Exception:
                # Ignore network/revoke failures; proceed to delete local token
                logger.debug('Failed to revoke token with Google; proceeding to delete locally')

            token.delete()
            return Response({'ok': True, 'disconnected': True})
        except Exception as exc:
            logger.exception('Failed to disconnect Google OAuth')
            return Response({'ok': False, 'error': str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
