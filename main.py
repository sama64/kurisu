from openai import OpenAI
from dotenv import load_dotenv
from os import getenv
import asyncio
from collections import deque
from aiogram import Bot, Dispatcher, types

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

def get_openai_response(user_message: str):
    """Get a response from OpenAI using the last 10 messages for context"""
    messages = [
        {"role": "system", "content": "You're Kurisu Makise, a helpful and succinct assistant."}
    ]
    
    # Add the last 10 messages as context
    for msg in message_history:
        messages.append(msg)

    messages.append({"role": "user", "content": user_message})

    # Create the OpenAI request
    response = client.chat.completions.create(
        model="nousresearch/hermes-2-theta-llama-3-8b",
        messages=messages,
        temperature=0.7
    )
    return response.choices[0].message.content

@dp.message()
async def handle_user_message(message: types.Message):
    user_message = message.text

    # Get the OpenAI response
    openai_response = await asyncio.to_thread(get_openai_response, user_message)
    
    # Store the current conversation in the message history
    message_history.appendleft({"role": "user", "content": user_message})
    message_history.appendleft({"role": "assistant", "content": openai_response})

    # Send OpenAI response back to user
    await message.answer(openai_response)

async def main():
    # Start the bot
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())