from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import os
import pytz
from tzlocal import get_localzone

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/fitness.sleep.read', 'https://www.googleapis.com/auth/tasks.readonly']

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
# def get_creds():
#     """Return OAuth credentials."""
#     creds = None
    
#     # Check if token.json exists
#     if os.path.exists('token.json'):
#         try:
#             creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            
#             # Attempt to refresh the token if it's expired
#             if creds and creds.expired and creds.refresh_token:
#                 creds.refresh(Request())
#         except RefreshError:
#             # If refresh fails, we'll need to re-authenticate
#             os.remove('token.json')
#             creds = None

#     # If creds is None (either file didn't exist or refresh failed), run the OAuth flow
#     if not creds or not creds.valid:
#         flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
#         creds = flow.run_local_server(port=0)
        
#         # Save the new credentials
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
    
#     return creds

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

def authenticate_google_tasks():
  """Authenticate and return Google Tasks API service."""
  creds = get_creds()
  
  service = build('tasks', 'v1', credentials=creds)
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
    """Fetch and aggregate sleep data for the last 24 hours."""
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
    
    sleep_segments = []
    for bucket in response.get('bucket', []):
        for dataset in bucket.get('dataset', []):
            for point in dataset.get('point', []):
                start_time_nanos = int(point['startTimeNanos'])
                end_time_nanos = int(point['endTimeNanos'])
                start_time = datetime.fromtimestamp(start_time_nanos // 1000000000, pytz.UTC)
                end_time = datetime.fromtimestamp(end_time_nanos // 1000000000, pytz.UTC)
                
                sleep_segments.append({
                    'start_time': start_time,
                    'end_time': end_time
                })
    
    # Sort segments by start time
    sleep_segments.sort(key=lambda x: x['start_time'])
    
    # Aggregate segments into complete sleep periods
    sleep_periods = []
    current_period = None
    
    for segment in sleep_segments:
        if current_period is None:
            current_period = segment.copy()
        elif (segment['start_time'] - current_period['end_time']).total_seconds() <= 1800:  # 30 minutes threshold
            current_period['end_time'] = segment['end_time']
        else:
            sleep_periods.append(current_period)
            current_period = segment.copy()
    
    if current_period:
        sleep_periods.append(current_period)
    
    # Calculate duration for each sleep period
    for period in sleep_periods:
        duration = (period['end_time'] - period['start_time']).total_seconds() / 3600  # duration in hours
        period['duration'] = duration
    
    return sleep_periods

def get_tasks():
    """Retrieve tasks from Google Tasks API and return them as a formatted string."""
    service = authenticate_google_tasks()

    # Get all task lists
    results = service.tasklists().list().execute()
    task_lists = results.get('items', [])

    if not task_lists:
        return "No task lists found."

    all_tasks = []

    for task_list in task_lists:
        list_name = task_list['title']
        list_id = task_list['id']

        # Get tasks for each task list
        tasks = service.tasks().list(tasklist=list_id).execute()
        tasks = tasks.get('items', [])

        if tasks:
            all_tasks.append(f"\nUser Tasks:")
            for task in tasks:
                task_title = task.get('title', 'Untitled')
                due_date = task.get('due', 'No due date')
                if due_date != 'No due date':
                    due_date = datetime.fromisoformat(due_date.rstrip('Z')).strftime('%Y-%m-%d')
                
                # Check if the task is completed
                task_status = task.get('status', 'needsAction')  # default to 'needsAction' if 'status' is not available
                status_label = "(Completed)" if task_status == 'completed' else "(Not Completed)"
                
                # Get task creation time
                created_time = task.get('created', None)
                if created_time:
                    created_time = datetime.fromisoformat(created_time.rstrip('Z')).strftime('%H:%M')

                # Format output with creation time, due date, and completion status
                all_tasks.append(f"  - {task_title} (Created: {created_time}, Due: {due_date}) {status_label}")

    if not all_tasks:
        return "No tasks found in any list."

    return "\n".join(all_tasks)


if __name__ == '__main__':
  print(get_tasks())