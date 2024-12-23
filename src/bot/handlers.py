from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
import pytz
from typing import Optional
from src.utils.helpers import authorized_only

class CommandHandlers:
    def __init__(self, bot):
        self.bot = bot

    @authorized_only()
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
/add_task <title> [due_date] - Add a new task (due_date format: YYYY-MM-DD HH:MM)
/list_tasks - List all incomplete tasks
/complete_task <number> - Mark a task as complete
/clear_tasks - Remove all completed tasks
/pause_notifications - Pause proactive messages
/resume_notifications - Resume proactive messages
        """
        await update.message.reply_text(help_text)

    @authorized_only()
    async def add_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(
                "Please provide a task title. Format: /add_task <title> [due_date]"
            )
            return

        # Parse due date if provided
        due_date: Optional[datetime] = None
        task_title_parts = []
        
        for arg in context.args:
            if arg.count('-') == 2 and len(arg) == 10:  # Possible date
                try:
                    date_str = ' '.join(context.args[context.args.index(arg):])
                    due_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M')
                    due_date = pytz.UTC.localize(due_date)
                    break
                except ValueError:
                    task_title_parts.append(arg)
            else:
                task_title_parts.append(arg)

        task_title = ' '.join(task_title_parts)
        task = self.bot.task_manager.add_task(user_id, task_title, due_date)
        
        response = f"Task added: {task.title}"
        if due_date:
            response += f"\nDue date: {due_date.strftime('%Y-%m-%d %H:%M')}"
            
        await update.message.reply_text(response)

    @authorized_only()
    async def list_tasks(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        tasks = self.bot.task_manager.get_tasks(user_id)
        
        if not tasks:
            await update.message.reply_text("You have no pending tasks.")
            return

        response = "Your current tasks:\n"
        for i, task in enumerate(tasks, 1):
            response += f"\n{i}. {task.title}"
            if task.due_date:
                response += f" (Due: {task.due_date.strftime('%Y-%m-%d %H:%M')})"
                
        await update.message.reply_text(response)

    @authorized_only()
    async def complete_task(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("Please specify the task number to complete.")
            return

        try:
            task_index = int(context.args[0]) - 1
            if self.bot.task_manager.complete_task(user_id, task_index):
                await update.message.reply_text("Task marked as complete!")
            else:
                await update.message.reply_text("Invalid task number.")
        except ValueError:
            await update.message.reply_text("Please provide a valid task number.")

    @authorized_only()
    async def pause_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.bot.scheduler.stop_scheduling(user_id)
        await update.message.reply_text(
            "Fine! I'll stop checking up on you... but don't blame me if you fall behind!"
        )

    @authorized_only()
    async def resume_notifications(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        self.bot.scheduler.start_scheduling(user_id, self.bot.send_proactive_message)
        await update.message.reply_text(
            "I-it's not like I wanted to help you stay on track or anything..."
        ) 