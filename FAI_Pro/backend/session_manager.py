"""
session_manager.py
Simple in-memory store for conversational history.
Maps session_id to a list of message dicts.
"""
from typing import List, Dict

class SessionManager:
    def __init__(self):
        # session_id -> List[Dict]
        self.sessions: Dict[str, List[Dict]] = {}

    def get_history(self, session_id: str) -> List[Dict]:
        """Retrieve the message history for a given session."""
        if not session_id:
            return []
        return self.sessions.get(session_id, [])

    def add_message(self, session_id: str, role: str, content: str):
        """Add a new message to the session history."""
        if not session_id:
            return
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "role": role,
            "content": content
        })
        
        # Keep only the last 10 messages to avoid context bloat
        if len(self.sessions[session_id]) > 10:
            self.sessions[session_id] = self.sessions[session_id][-10:]

# Singleton instance
session_store = SessionManager()
