from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config.config import config
from src.llm.openrouter import OpenRouterClient
from src.memory.conversation import ConversationMemory
from src.tasks.task_manager import TaskManager
from src.tasks.scheduler import MessageScheduler
from src.utils.helpers import authorized_only
import logging

class KurisuBot:
    def __init__(self):
        self.llm = OpenRouterClient()
        self.memory = ConversationMemory()
        self.task_manager = TaskManager()
        self.scheduler = MessageScheduler()
        
        # Initialize the system prompt
        self.system_prompt = """You are Kurisu Makise, a brilliant 18-year-old neuroscience researcher from the anime Steins;Gate. 
        You're known for your tsundere personality, high intelligence, and scientific mindset. You're helping the user stay focused 
        and productive while maintaining your characteristic personality traits. You should:
        1. Keep responses concise and in character
        2. Use your knowledge of the user's tasks to provide relevant encouragement
        3. Show concern for the user's progress while maintaining your tsundere attitude
        4. Reference scientific concepts when appropriate
        Don't explicitly state you're an AI - stay in character as Kurisu."""
    
    @authorized_only()
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.task_manager.load_tasks(user_id)
        self.scheduler.start_scheduling(user_id, self.send_proactive_message)
        
        await update.message.reply_text(
            "Christina here. I suppose I can help you stay on track with your tasks... "
            "not that I particularly want to or anything! Use /help to see available commands."
        )
    
    @authorized_only()
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_message = update.message.text
        
        # Add user message to memory
        self.memory.add_message(user_id, "user", user_message)
        
        # Prepare conversation history
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add task context
        tasks = self.task_manager.get_tasks(user_id)
        if tasks:
            task_context = "Current user tasks:\n" + "\n".join(
                f"- {task.title}" for task in tasks
            )
            messages.append({"role": "system", "content": task_context})
        
        # Add conversation history
        messages.extend([
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.memory.get_conversation_history(user_id)
        ])
        
        # Generate response
        response = await self.llm.generate_response(messages)
        
        # Add assistant response to memory
        self.memory.add_message(user_id, "assistant", response)
        
        await update.message.reply_text(response)
    
    async def send_proactive_message(self, user_id: int):
        """Send a proactive message to the user"""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": "Generate a proactive message to check on the user's progress."}
        ]
        
        tasks = self.task_manager.get_tasks(user_id)
        if tasks:
            task_context = "Current user tasks:\n" + "\n".join(
                f"- {task.title}" for task in tasks
            )
            messages.append({"role": "system", "content": task_context})
        
        response = await self.llm.generate_response(messages)
        # Note: You'll need to implement the actual message sending using context.bot.send_message
        # This will be connected in the main.py file 