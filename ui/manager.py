import os
import json
from datetime import datetime
from typing import Dict, List

class ChatManager:
    def __init__(self, chats_dir: str = "saved_chats"):
        self.chats_dir = chats_dir
        os.makedirs(self.chats_dir, exist_ok=True)
    
    def save_chat(self, chat_id: str, messages: List[Dict]):
        """Save chat messages to a JSON file"""
        if not messages:
            return
        
        # Create chat data structure
        chat_data = {
            "chat_id": chat_id,
            "timestamp": datetime.now().isoformat(),
            "messages": messages,
            "title": self._generate_chat_title(messages)
        }
        
        # Save to file
        file_path = os.path.join(self.chats_dir, f"{chat_id}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
    
    def load_chats(self) -> Dict:
        """Load all saved chats from the directory"""
        chats = {}
        
        # List all JSON files in the chats directory
        for filename in os.listdir(self.chats_dir):
            if filename.endswith('.json'):
                file_path = os.path.join(self.chats_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        chat_data = json.load(f)
                        chat_id = chat_data.get('chat_id', filename[:-5])  # Remove .json
                        chats[chat_id] = chat_data
                except Exception as e:
                    print(f"Error loading chat {filename}: {e}")
        
        return chats
    
    def delete_chat(self, chat_id: str) -> bool:
        """Delete a chat file"""
        try:
            file_path = os.path.join(self.chats_dir, f"{chat_id}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting chat {chat_id}: {e}")
            return False
    
    def _generate_chat_title(self, messages: List[Dict]) -> str:
        """Generate a title for the chat based on the first user message"""
        # Find the first user message
        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                # Truncate to first 50 characters
                title = content[:50] + ("..." if len(content) > 50 else "")
                return title
        
        # Fallback title if no user messages found
        return f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"