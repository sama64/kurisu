from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
import json
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
import pytz
from tzlocal import get_localzone

logger = logging.getLogger(__name__)

class PersonalGoogleAuth:
    """Handles authentication for personal Google account access."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/calendar.readonly',
        'https://www.googleapis.com/auth/fitness.sleep.read',
        'https://www.googleapis.com/auth/tasks.readonly'
    ]

    def __init__(self):
        self.credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH')
        self.token_path = os.getenv('GOOGLE_TOKEN_PATH')
        self._creds = None
        self._services = {}

    @staticmethod
    def generate_persistent_token(credentials_path: str, token_save_path: str) -> None:
        """
        Generate a persistent refresh token. Run this locally ONCE to get a long-lived token.
        
        Args:
            credentials_path: Path to your OAuth client credentials file
            token_save_path: Where to save the generated token
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_path,
            scopes=PersonalGoogleAuth.SCOPES,
            # Request offline access for refresh token
            redirect_uri='http://localhost:0'
        )
        
        # Enable offline access and force approval prompt
        creds = flow.run_local_server(
            port=0,
            access_type='offline',
            prompt='consent'
        )
        
        # Save the credentials
        with open(token_save_path, 'w') as token:
            token.write(creds.to_json())
        
        print(f"Persistent token generated and saved to {token_save_path}")
        print("You can now copy this file to your server")

    def authenticate(self) -> None:
        """Authenticate using saved refresh token."""
        try:
            if not os.path.exists(self.token_path):
                raise FileNotFoundError(
                    "Token file not found. Run generate_persistent_token() locally first."
                )

            self._creds = Credentials.from_authorized_user_file(
                self.token_path, 
                self.SCOPES
            )

            # Refresh if expired
            if self._creds.expired:
                self._creds.refresh(Request())
                # Save the refreshed credentials
                with open(self.token_path, 'w') as token:
                    token.write(self._creds.to_json())

        except RefreshError as e:
            logger.error(f"Token refresh failed: {e}")
            raise Exception(
                "Refresh token has expired or been revoked. "
                "Need to generate a new token locally."
            )
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise

    def get_service(self, service_name: str, version: str):
        """Get or create a Google service client."""
        service_key = f"{service_name}_{version}"
        
        if service_key not in self._services:
            if not self._creds or self._creds.expired:
                self.authenticate()
            
            self._services[service_key] = build(
                service_name,
                version,
                credentials=self._creds
            )
        
        return self._services[service_key]

# Service methods implementation
    def get_calendar_events(self) -> str:
        """Fetch today's calendar events."""
        try:
            service = self.get_service('calendar', 'v3')
            
            local_tz = get_localzone()
            now = datetime.now(local_tz)
            start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            events_result = service.events().list(
                calendarId='primary',
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(),
                maxResults=10,
                singleEvents=True,
                orderBy='startTime',
                timeZone=str(local_tz)
            ).execute()

            return self._format_calendar_events(events_result.get('items', []))

        except HttpError as e:
            logger.error(f"Calendar API error: {e}")
            if e.status_code == 401:
                self.authenticate()
                return self.get_calendar_events()
            return "Unable to fetch calendar events"

    def get_sleep_data(self) -> list:
        """Fetch sleep data for the last 24 hours."""
        try:
            service = self.get_service('fitness', 'v1')
            
            end_time = datetime.now(pytz.UTC)
            start_time = end_time - timedelta(days=1)
            
            body = {
                "aggregateBy": [{
                    "dataTypeName": "com.google.sleep.segment"
                }],
                "startTimeMillis": int(start_time.timestamp() * 1000),
                "endTimeMillis": int(end_time.timestamp() * 1000),
            }

            response = service.users().dataset().aggregate(
                userId="me",
                body=body
            ).execute()
            
            return self._process_sleep_data(response)

        except HttpError as e:
            logger.error(f"Fitness API error: {e}")
            if e.status_code == 401:
                self.authenticate()
                return self.get_sleep_data()
            return []

    def get_tasks(self) -> str:
        """Fetch tasks from all lists."""
        try:
            service = self.get_service('tasks', 'v1')
            
            # Get all task lists
            task_lists = service.tasklists().list().execute()
            
            return self._format_tasks(service, task_lists.get('items', []))

        except HttpError as e:
            logger.error(f"Tasks API error: {e}")
            if e.status_code == 401:
                self.authenticate()
                return self.get_tasks()
            return "Unable to fetch tasks"

    @staticmethod
    def _format_calendar_events(events):
        if not events:
            return "No events scheduled for today."
        
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Convert strings to datetime objects
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            
            formatted_events.append(
                f"{event['summary']} from "
                f"{start_dt.strftime('%I:%M %p')} to "
                f"{end_dt.strftime('%I:%M %p')}"
            )
        
        return "Today's events: " + ", ".join(formatted_events)

    @staticmethod
    def _process_sleep_data(response):
        sleep_segments = []
        
        for bucket in response.get('bucket', []):
            for dataset in bucket.get('dataset', []):
                for point in dataset.get('point', []):
                    start_nanos = int(point['startTimeNanos'])
                    end_nanos = int(point['endTimeNanos'])
                    
                    start_time = datetime.fromtimestamp(
                        start_nanos // 1_000_000_000,
                        pytz.UTC
                    )
                    end_time = datetime.fromtimestamp(
                        end_nanos // 1_000_000_000,
                        pytz.UTC
                    )
                    
                    duration = (end_time - start_time).total_seconds() / 3600
                    
                    sleep_segments.append({
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration
                    })
        
        return sleep_segments

    @staticmethod
    def _format_tasks(service, task_lists):
        if not task_lists:
            return "No task lists found."
        
        formatted_tasks = ["Tasks:"]
        
        for task_list in task_lists:
            tasks = service.tasks().list(
                tasklist=task_list['id']
            ).execute()
            
            for task in tasks.get('items', []):
                status = "✓" if task.get('status') == 'completed' else "○"
                due_date = task.get('due', 'No due date')
                if due_date != 'No due date':
                    due_date = datetime.fromisoformat(
                        due_date.rstrip('Z')
                    ).strftime('%Y-%m-%d')
                
                formatted_tasks.append(
                    f"{status} {task.get('title', 'Untitled')} "
                    f"(Due: {due_date})"
                )
        
        return "\n".join(formatted_tasks)