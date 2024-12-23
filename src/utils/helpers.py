from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from config.config import config

def authorized_only():
    def decorator(func):
        @wraps(func)
        async def wrapped(self, update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            
            if chat_id != config.ALLOWED_CHAT_ID:
                await update.message.reply_text("Unauthorized access.")
                return
            
            return await func(self, update, context, *args, **kwargs)
        return wrapped
    return decorator 