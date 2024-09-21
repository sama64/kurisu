from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import pytz
from tzlocal import get_localzone

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/fitness.sleep.read']

def get_creds():
  """Return OAuth credentials."""
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
  
  return creds

def authenticate_google_calendar():
  """Authenticate and return Google Calendar API service."""
  creds = get_creds()
  
  service = build('calendar', 'v3', credentials=creds)
  return service

def authenticate_google_fitness():
  """Authenticate and return Google Fitness API service."""
  creds = get_creds()
  
  service = build('fitness', 'v1', credentials=creds)
  return service

def get_calendar_events():
  """Fetch today's calendar events."""
  service = authenticate_google_calendar()
  
  local_tz = get_localzone()
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

def get_sleep_data():
    """Fetch sleep data for the last 24 hours."""
    fitness_service = authenticate_google_fitness()
    
    end_time = datetime.now(pytz.UTC)
    start_time = end_time - timedelta(days=1)
    
    body = {
        "aggregateBy": [{
            "dataTypeName": "com.google.sleep.segment"
        }],
        "startTimeMillis": int(start_time.timestamp() * 1000),
        "endTimeMillis": int(end_time.timestamp() * 1000),
    }

    response = fitness_service.users().dataset().aggregate(userId="me", body=body).execute()
    
    sleep_periods = []
    for bucket in response.get('bucket', []):
        for dataset in bucket.get('dataset', []):
            for point in dataset.get('point', []):
                start_time_nanos = int(point['startTimeNanos'])
                end_time_nanos = int(point['endTimeNanos'])
                start_time = datetime.fromtimestamp(start_time_nanos // 1000000000, pytz.UTC)
                end_time = datetime.fromtimestamp(end_time_nanos // 1000000000, pytz.UTC)
                duration = (end_time - start_time).total_seconds() / 3600  # duration in hours
                
                sleep_periods.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration': duration
                })
    
    return sleep_periods