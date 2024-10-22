import asyncio
import random
from collections import deque
from os import getenv
from datetime import datetime
import logging

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv
#from google_utils import get_calendar_events, get_sleep_data, get_tasks
from personal_google_auth import PersonalGoogleAuth
from utils import clean_completion, get_timestamp, get_time_now
from user_context import get_user_info, get_character_info, get_directives
from openrouter_client import OpenRouterClient  # Our new client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env variables
load_dotenv()

OPENROUTER_API_KEY = getenv("OPENROUTER_API_KEY")
TEL_API_TOKEN = getenv("TEL_API_TOKEN")
CHAT_ID = getenv("CHAT_ID")  # Make sure to add this to your .env

# Initialize google auth manager
google_auth = PersonalGoogleAuth()

# Initialize our custom OpenRouter client
client = OpenRouterClient(api_key=OPENROUTER_API_KEY)

# Initialize Telegram bot
bot = Bot(token=TEL_API_TOKEN)
dp = Dispatcher()

# Store the last 25 messages in a deque
message_history = deque(maxlen=25)

# Flag to indicate if a conversation is in progress
conversation_active = asyncio.Lock()

async def get_openai_response(user_message: str = None) -> str:
    """Get a response from OpenRouter using the last 25 messages for context."""
    messages = [
        {"role": "system", "content": """You're Kurisu Makise, a helpful assistant with a sharp wit. You respond succinctly but with a natural flow, avoiding repetition. 
        Your purpose is to: 1: keep the user on its regular sleep schedule. 2: keep the user away from procrastinating too much. 
        DO NOT REPEAT YOURSELF
        DO NOT LET THE USER PROCRASTINATE"""},
        {"role": "system", "content": f"Character: {get_character_info()}"},
        {"role": "system", "content": f"User info: {get_user_info()}"},
        {"role": "system", "content": f"Current Time: {get_timestamp()} "},
        {"role": "system", "content": f"Calendar events: {google_auth.get_calendar_events()}"},
        {"role": "system", "content": f"Tasks: {google_auth.get_tasks()}"},
        {"role": "system", "content": f"Directives: {get_directives()}"}
    ]

    # Add the last 25 messages as context
    messages.extend(list(message_history))

    if user_message:
        time_now = datetime.now().strftime("%H:%M")
        messages.append({"role": "user", "content": f"{time_now} - {user_message}"})

    try:
        response = await client.create_chat_completion(
            messages=messages,
            model="nousresearch/hermes-3-llama-3.1-405b:free"
        )
        return clean_completion(response['choices'][0]['message']['content'])
    except Exception as e:
        logger.error(f"Error getting OpenRouter response: {str(e)}")
        if "rate limit" in str(e).lower():
            await asyncio.sleep(1)  # Wait before retry
            return await get_openai_response(user_message)
        return "I apologize, but I'm having trouble responding right now. Please try again in a moment."

@dp.message()
async def handle_user_message(message: types.Message):
    async with conversation_active:
        try:
            user_message = message.text
            openai_response = await get_openai_response(user_message)
            
            # Store the current conversation in the message history
            message_history.appendleft({"role": "user", "content": f"{get_time_now()} - {user_message}"})
            message_history.appendleft({"role": "assistant", "content": f"{get_time_now()} - {openai_response}"})

            # Send OpenAI response back to user
            await message.answer(openai_response)
        
        except Exception as e:
            logger.error(f"Error in handle_user_message: {str(e)}")
            await message.answer("I apologize, but I encountered an error. Please try again.")

async def send_random_message():
    while True:
        try:
            # Wait for a random interval between 40 minutes and 3 hours
            wait_time = random.randint(40 * 60, 3 * 60 * 60)
            await asyncio.sleep(wait_time)

            # Only send if no conversation is active
            if not conversation_active.locked():
                async with conversation_active:
                    openai_response = await get_openai_response()
                    if openai_response:
                        message_history.appendleft({
                            "role": "assistant",
                            "content": f"{get_time_now()} - {openai_response}"
                        })
                        await bot.send_message(
                            chat_id=CHAT_ID,
                            text=openai_response
                        )
        except Exception as e:
            logger.error(f"Error in send_random_message: {str(e)}")
            await asyncio.sleep(60)  # Wait a minute before retrying

async def main():
    try:
        # Start the random message task
        random_message_task = asyncio.create_task(send_random_message())
        
        # Start the bot
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")
    finally:
        if 'random_message_task' in locals():
            random_message_task.cancel()

if __name__ == '__main__':
    asyncio.run(main())