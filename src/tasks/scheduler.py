import asyncio
import random
from datetime import datetime, time
from typing import Callable, Dict, Optional
from config.config import config

class MessageScheduler:
    def __init__(self):
        self.scheduled_tasks: Dict[int, asyncio.Task] = {}
        
    async def schedule_messages(
        self,
        user_id: int,
        callback: Callable,
        start_time: Optional[time] = time(9, 0),  # 9 AM
        end_time: Optional[time] = time(22, 0)    # 10 PM
    ):
        """Schedule random messages for a user within the specified time window"""
        while True:
            now = datetime.now().time()
            
            # Only send messages during active hours
            if start_time <= now <= end_time:
                # Random delay between min and max interval
                delay = random.randint(
                    config.PROACTIVE_MESSAGE_MIN_INTERVAL,
                    config.PROACTIVE_MESSAGE_MAX_INTERVAL
                )
                
                await asyncio.sleep(delay)
                await callback(user_id)
            else:
                # Wait until start_time of next day
                tomorrow = datetime.now().replace(
                    hour=start_time.hour,
                    minute=start_time.minute,
                    second=0
                )
                wait_seconds = (tomorrow - datetime.now()).seconds
                await asyncio.sleep(wait_seconds)
    
    def start_scheduling(
        self,
        user_id: int,
        callback: Callable,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None
    ):
        """Start scheduling messages for a user"""
        if user_id in self.scheduled_tasks:
            self.scheduled_tasks[user_id].cancel()
        
        task = asyncio.create_task(
            self.schedule_messages(user_id, callback, start_time, end_time)
        )
        self.scheduled_tasks[user_id] = task
    
    def stop_scheduling(self, user_id: int):
        """Stop scheduling messages for a user"""
        if user_id in self.scheduled_tasks:
            self.scheduled_tasks[user_id].cancel()
            del self.scheduled_tasks[user_id] 