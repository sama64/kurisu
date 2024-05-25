# import json
import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser
from urllib.parse import urlparse
from time import perf_counter
import re

# Receives url, returns bucket names: afk_bucket_name, window_bucket_name, web_bucket_name
def get_bucket_names(api_url):
  try:
    # Get buckets metadata
    response = requests.get(f"{api_url}/buckets/")

    if response.status_code == 200:
      buckets = response.json()
      afk_bucket_name = None
      window_bucket_name = None
      web_bucket_name = None

      # Get bucket names
      for bucket_name in buckets:
        if bucket_name.startswith("aw-watcher-afk"):
          afk_bucket_name = bucket_name
        elif bucket_name.startswith("aw-watcher-window"):
          window_bucket_name = bucket_name
        elif bucket_name.startswith("aw-watcher-web"):
          web_bucket_name = bucket_name

      return afk_bucket_name, window_bucket_name, web_bucket_name
  except:
    raise RuntimeError("Error retrieving bucket metadata")


def get_bucket_events(api_url, bucket_name, hours):
  try:
    # Get the current time in UTC
    current_time_utc = datetime.now(timezone.utc)
    
    # Calculate the threshold time in UTC
    threshold_time_utc = current_time_utc - timedelta(hours=hours)

    params = {
    "start": threshold_time_utc.isoformat(),
    "end": current_time_utc.isoformat()
    }

    response = requests.get(f"{api_url}/buckets/{bucket_name}/events", params=params)
    if response.status_code == 200:
      response = response.json()
      events = remove_duration_zero(response)

      return events

  except:
    raise RuntimeError("Error retrieving bucket events")

def get_domain_from_url(url):
  parsed_url = urlparse(url)
  # Extract the hostname
  hostname = parsed_url.hostname
  if hostname:
    # Split the hostname by dots
    parts = hostname.split('.')
    # If the hostname has more than two parts (e.g., subdomain.domain.com), ignore the subdomains
    if len(parts) > 2:
      domain = '.'.join(parts[-2:])
    else:
      domain = hostname
    return domain
  return ''

def remove_duration_zero(events):
  result = [event for event in events if event['duration'] != 0]
  return result

def clean_special_characters(events):
  cleaned_events = []
  for event in events:
    event['data']['title'] = re.sub(r'^[^a-zA-Z0-9]+\s*', '', event['data']['title'])
    cleaned_events.append(event)
  return cleaned_events

def merge_similar_events(raw_events):
  if not raw_events:
    return []
  
  events = clean_special_characters(raw_events)
  
  merged_events = []
  current_event = None
  
  for event in events:
    if current_event is None:
      current_event = event
      continue
    
    # Check if the current event should be merged with the previous one
    if (event['data']['app'] == current_event['data']['app'] and 
      event['data']['title'] == current_event['data']['title']):
      # Merge the durations and update the timestamp and id to the current event
      current_event['duration'] += event['duration']
      current_event['timestamp'] = event['timestamp']
      current_event['id'] = event['id']
    else:
      # Add the current event to the merged list and start a new current event
      merged_events.append(current_event)
      current_event = event
  
  # Don't forget to add the last current event to the merged list
  if current_event is not None:
    merged_events.append(current_event)
  
  return merged_events

# Receives afk_activity and window_activity events. Returns a list of non-afk window events + afk events in order 
def merge_afk_window_activity(afk_activity, window_activity):
  # Step 1: Merge consecutive AFK events
  merged_afk = []
  prev_afk = None
  for event in afk_activity:
    if prev_afk and prev_afk['data']['status'] == 'afk' and event['data']['status'] == 'afk':
      prev_afk['duration'] += event['duration']
    else:
      merged_afk.append(event)
      prev_afk = event

  # Step 2: Merge AFK and window events
  merged_events = []
  afk_idx = 0
  win_idx = 0

  while afk_idx < len(merged_afk) and win_idx < len(window_activity):
    afk_event = merged_afk[afk_idx]
    win_event = window_activity[win_idx]

    afk_start = datetime.fromisoformat(afk_event['timestamp']).replace(tzinfo=timezone.utc)
    afk_end = afk_start + timedelta(seconds=afk_event['duration'])
    win_start = datetime.fromisoformat(win_event['timestamp']).replace(tzinfo=timezone.utc)
    win_end = win_start + timedelta(seconds=win_event['duration'])

    if win_end <= afk_start:
      merged_events.append({**win_event, 'watcher': 'window'})
      win_idx += 1
    elif win_start >= afk_end:
      merged_events.append({**afk_event, 'watcher': 'afk'})
      afk_idx += 1
    elif win_start < afk_start and win_end > afk_end:
      win_event['duration'] -= afk_event['duration']
      merged_events.append({**afk_event, 'watcher': 'afk'})
      afk_idx += 1
    elif win_start < afk_start < win_end:
      win_event['duration'] = (afk_start - win_start).total_seconds()
      merged_events.append({**win_event, 'watcher': 'window'})
      merged_events.append({**afk_event, 'watcher': 'afk'})
      win_idx += 1
      afk_idx += 1
    else:  # afk_start < win_start and afk_end < win_end
      afk_event['duration'] = (win_start - afk_start).total_seconds()
      merged_events.append({**afk_event, 'watcher': 'afk'})
      win_event['timestamp'] = (afk_end + timedelta(seconds=1)).isoformat()
      win_event['duration'] -= afk_event['duration']
      merged_events.append({**win_event, 'watcher': 'window'})
      afk_idx += 1
      win_idx += 1

    # Add remaining events
    merged_events.extend([{**event, 'watcher': 'afk'} for event in merged_afk[afk_idx:]])
    merged_events.extend([{**event, 'watcher': 'window'} for event in window_activity[win_idx:]])

    return merged_events


if __name__ == '__main__':
  url = "http://localhost:5600/api/0"
  afk_bucket_name, window_bucket_name, web_bucket_name = get_bucket_names(url)

  window_activity_raw = get_bucket_events(url, window_bucket_name, 0.5)

  window_activity = merge_similar_events(window_activity_raw)
  afk_activity = get_bucket_events(url, afk_bucket_name, 0.5)

  relevant_events = merge_afk_window_activity(afk_activity, window_activity)

  time_passed = 0

  for event in window_activity:
    # Parse the timestamp
    event_time = parser.isoparse(event['timestamp'])
    # Convert the event time to the local time zone
    local_time = event_time.astimezone()
    # Format the local time in AM/PM format
    formatted_time = local_time.strftime('%Y-%m-%d %I:%M:%S %p')
    # Print the time and title
    #print(f"{formatted_time} - {event['data']['title']}")
    time_passed += event['duration']
    print(event)

  #print(f"Total computor time: {time_passed}")
