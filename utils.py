import re
from datetime import datetime

def clean_completion(text):
  # Regular expression to match the timestamp pattern at the start of the text
  pattern = r'^\d{2}:\d{2}\s*-\s*'
  
  # Use re.sub to remove the timestamp if it exists at the beginning
  cleaned_text = re.sub(pattern, '', text.strip())
  
  return cleaned_text

def format_message_with_time(content, timestamp=None):
  """Formats the message with hour:minute or returns the content as is if no timestamp is provided."""
  if timestamp:
    message_time = datetime.fromtimestamp(timestamp).strftime("%H:%M")
    return f"{message_time} - {content}"
  return content

def get_timestamp():
  return datetime.now().strftime("%Y-%m-%d %H:%M")

def get_time_now():
  return datetime.now().strftime("%H:%M")