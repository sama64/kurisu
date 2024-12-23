from datetime import datetime
from typing import List, Dict, Optional
import json
import os

class Task:
    def __init__(self, title: str, due_date: Optional[datetime] = None, completed: bool = False):
        self.title = title
        self.due_date = due_date
        self.completed = completed
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed": self.completed,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Task':
        task = cls(data["title"])
        task.completed = data["completed"]
        task.created_at = datetime.fromisoformat(data["created_at"])
        if data["due_date"]:
            task.due_date = datetime.fromisoformat(data["due_date"])
        return task

class TaskManager:
    def __init__(self, storage_dir: str = "data"):
        self.storage_dir = storage_dir
        self.tasks: Dict[int, List[Task]] = {}
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_user_file(self, user_id: int) -> str:
        return os.path.join(self.storage_dir, f"tasks_{user_id}.json")
    
    def load_tasks(self, user_id: int):
        file_path = self._get_user_file(user_id)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                data = json.load(f)
                self.tasks[user_id] = [Task.from_dict(task_data) for task_data in data]
    
    def save_tasks(self, user_id: int):
        file_path = self._get_user_file(user_id)
        with open(file_path, 'w') as f:
            json.dump([task.to_dict() for task in self.tasks.get(user_id, [])], f)
    
    def add_task(self, user_id: int, title: str, due_date: Optional[datetime] = None) -> Task:
        if user_id not in self.tasks:
            self.tasks[user_id] = []
        
        task = Task(title, due_date)
        self.tasks[user_id].append(task)
        self.save_tasks(user_id)
        return task
    
    def get_tasks(self, user_id: int, include_completed: bool = False) -> List[Task]:
        tasks = self.tasks.get(user_id, [])
        if not include_completed:
            tasks = [task for task in tasks if not task.completed]
        return tasks
    
    def complete_task(self, user_id: int, task_index: int) -> bool:
        if user_id in self.tasks and 0 <= task_index < len(self.tasks[user_id]):
            self.tasks[user_id][task_index].completed = True
            self.save_tasks(user_id)
            return True
        return False 