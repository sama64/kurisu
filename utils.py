import re
import requests
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
    timestamp = f"{datetime.now().strftime("%a, %Y-%m-%d %H:%M")}"
    return timestamp

def get_time_now():
    return datetime.now().strftime("%H:%M")

def fetch_usage(generation_id: str, api_key: str):
    """Fetches and prints the token usage details for a given generation ID."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    usage_url = f"https://openrouter.ai/api/v1/generation?id={generation_id}"
    
    # Make the API request to fetch usage details
    response = requests.get(usage_url, headers=headers)
    
    if response.status_code == 200:
        usage_data = response.json()["data"]
        input_tokens = usage_data.get("tokens_prompt", 0)
        output_tokens = usage_data.get("tokens_completion", 0)
        total_tokens = input_tokens + output_tokens

        print(f"Input tokens: {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Total tokens used: {total_tokens}")
    else:
        raise Exception(f"Failed to fetch usage details. Status code: {response.status_code}")


if __name__ == "__main__":
  print(get_timestamp())