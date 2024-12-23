from typing import List, Dict, Optional
from datetime import datetime

class ConversationMemory:
    def __init__(self, max_messages: int = 30):
        self.max_messages = max_messages
        self.conversations: Dict[int, List[Dict]] = {}
    
    def add_message(self, user_id: int, role: str, content: str):
        if user_id not in self.conversations:
            self.conversations[user_id] = []
            
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversations[user_id].append(message)
        
        # Keep only the last max_messages
        if len(self.conversations[user_id]) > self.max_messages:
            self.conversations[user_id] = self.conversations[user_id][-self.max_messages:]
    
    def get_conversation_history(self, user_id: int) -> List[Dict]:
        return self.conversations.get(user_id, [])
    
    def clear_history(self, user_id: int):
        self.conversations[user_id] = [] 