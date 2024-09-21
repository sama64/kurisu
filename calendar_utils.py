from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import pytz

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def authenticate_google_calendar():
  """Authenticate and return Google Calendar API service."""
  creds = None
  
  # Check if token.json exists, if not, run the OAuth flow
  if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
  else:
    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
      token.write(creds.to_json())
  
  # Refresh the token if it's expired
  if creds and creds.expired and creds.refresh_token:
    creds.refresh(Request())
  
  service = build('calendar', 'v3', credentials=creds)
  return service

from datetime import datetime, timedelta
import pytz

def get_calendar_events():
  """Fetch today's calendar events."""
  service = authenticate_google_calendar()
  
  local_tz = pytz.timezone('America/Sao_Paulo')  # use your timezone here
  now = datetime.now(local_tz).isoformat()
  end_of_day = (datetime.now(local_tz) + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()

  events_result = service.events().list(
    calendarId='primary', timeMin=now, timeMax=end_of_day,
    maxResults=10, singleEvents=True, orderBy='startTime', timeZone='America/Sao_Paulo').execute()
  events = events_result.get('items', [])

  if not events:
    return "No events for today."
  
  event_descriptions = []
  for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))

    # format the start and end times
    start_dt = datetime.fromisoformat(start).astimezone(local_tz).strftime('%I:%M %p')
    end_dt = datetime.fromisoformat(end).astimezone(local_tz).strftime('%I:%M %p')
    date = datetime.fromisoformat(start).astimezone(local_tz).strftime('%d-%m-%Y')

    # calculate duration
    duration = datetime.fromisoformat(end).astimezone(local_tz) - datetime.fromisoformat(start).astimezone(local_tz)

    event_descriptions.append(f"{event['summary']} on {date} from {start_dt} to {end_dt} (Duration: {duration})")
  
  return "Today's events: " + ", ".join(event_descriptions)