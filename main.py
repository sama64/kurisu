import asyncio
import random
from collections import deque
from os import getenv
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
from openai import OpenAI
from google_utils import get_calendar_events, get_sleep_data
from utils import clean_completion, format_message_with_time, get_timestamp, get_time_now

# Load env variables
load_dotenv()

OPENROUTER_API_KEY = getenv("OPENROUTER_API_KEY")
TEL_API_TOKEN = getenv("TEL_API_TOKEN")

# Initialize OpenAI client
client = OpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=OPENROUTER_API_KEY,
)

# Initialize Telegram bot
bot = Bot(token=TEL_API_TOKEN)
dp = Dispatcher()

# Store the last 10 messages in a deque
message_history = deque(maxlen=10)

# Flag to indicate if a conversation is in progress
conversation_in_progress = asyncio.Event()

def get_openai_response(user_message: str):
    """Get a response from OpenAI using the last 10 messages for context."""
    messages = [
        {"role": "system", "content": """You're Kurisu Makise, a helpful assistant with a sharp wit. You respond succinctly but with a natural flow, avoiding repetition. 
        Your purpose is to: 1: keep the user on its regular sleep schedule. 2: keep the user away from procrastinating too much. 
        DO NOT BE REPETITIVE"""},
        {"role": "system", "content": f"Current Time: {get_timestamp()}"},
        {"role": "system", "content": get_calendar_events()} 
    ]
    
    # Add the last 10 messages as context
    for msg in message_history:
        messages.append(msg)

    time_now = datetime.now().strftime("%H:%M")

    messages.append({"role": "user", "content": f"{time_now} - {user_message}"})

    # Create the OpenAI request
    response = client.chat.completions.create(
        model="nousresearch/hermes-3-llama-3.1-405b:free",
        messages=messages,
        temperature=0.7,            
        top_p=0.9,                  # nucleus sampling for diversity
        max_tokens=150,             # response length limit
        frequency_penalty=0.4,      # discourages repetitive word usage
        presence_penalty=0.3        # discourages topic repetition
    )
    return clean_completion(response.choices[0].message.content)

@dp.message()
async def handle_user_message(message: types.Message):
    conversation_in_progress.set()
    user_message = message.text

    # test
    sleep_data = get_sleep_data()
    for period in sleep_data:
        print(f"Sleep period: {period['start_time'].strftime('%Y-%m-%d %H:%M')} to {period['end_time'].strftime('%Y-%m-%d %H:%M')}")
        print(f"Duration: {period['duration']:.2f} hours")
        print("---")

    # Get the OpenAI response
    openai_response = await asyncio.to_thread(get_openai_response, user_message)

    # Store the current conversation in the message history
    message_history.appendleft({"role": "user", "content": f"{get_time_now()} - {user_message}"})
    message_history.appendleft({"role": "assistant", "content": f"{get_time_now()} - {openai_response}"})

    # Send OpenAI response back to user
    await message.answer(openai_response)
    conversation_in_progress.clear()

async def send_random_message():
    while True:
        # Wait for a random interval between 40 minutes and 2 hours
        wait_time = random.randint(40 * 60, 2 * 60 * 60)
        await asyncio.sleep(wait_time)

        # Check if a conversation is in progress
        if not conversation_in_progress.is_set():
            random_message = await asyncio.to_thread(get_openai_response, "Generate a random thought or observation as Kurisu Makise.")
            message_history.appendleft({"role": "assistant", "content": f"{get_time_now()} - {random_message}"})
            await bot.send_message(chat_id=YOUR_CHAT_ID, text=random_message)

async def main():
    # Start the random message task
    asyncio.create_task(send_random_message())
    
    # Start the bot
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
