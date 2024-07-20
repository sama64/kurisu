# import json
import requests
from datetime import datetime, timedelta, timezone
from dateutil import parser
from urllib.parse import urlparse
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

def remove_incognito(events):
  result = [event for event in events if event['data']['incognito'] == False]
  return result

def remove_new_tabs(events):
  result = [event for event in events if event['data']['url'] != "chrome://newtab/"]
  return result

def remove_short_events(events, min_duration=60):
  result = [event for event in events if event['duration'] >= min_duration]
  return result

def clean_special_characters(events):
  cleaned_events = []
  for event in events:
    event['data']['title'] = re.sub(r'^[^a-zA-Z0-9]+\s*', '', event['data']['title'])
    cleaned_events.append(event)
  return cleaned_events

def filter_web_events(web_events):
  web_events = remove_incognito(web_events)
  web_events = remove_new_tabs(web_events)
  web_events = remove_short_events(web_events, 60)

  return web_events


if __name__ == '__main__':
  url = "http://localhost:5600/api/0"
  afk_bucket_name, window_bucket_name, web_bucket_name = get_bucket_names(url)

  web_activity_raw = get_bucket_events(url, web_bucket_name, 0.5)
  web_activity = filter_web_events(web_activity_raw)

  for event in web_activity:
    event_time = parser.isoparse(event['timestamp'])
    local_time = event_time.astimezone()

    formatted_time = local_time.strftime('%I:%M %p')
    domain = get_domain_from_url(event['data']['url'])

    duration = int(event['duration'] / 60)

    print(f"{formatted_time}: Activity ({duration}min) '{event['data']['title']}' (Browser, {domain})")
    #print(event)

#11:14pm: Activity (120s) "Python GUI with Tkinter - Full Course" (Browser, youtube.com)


