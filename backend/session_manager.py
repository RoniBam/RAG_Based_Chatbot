import streamlit as st
import json
import time
from typing import Optional, Dict, Any

class SessionManager:
    def __init__(self):
        self.session_timeout = 600  # 10 minutes
    
    def set_user_session(self, user_data: Dict[str, Any]):
        """Set user session data"""
        session_data = {
            'authenticated': True,
            'user_data': user_data,
            'last_activity': time.time(),
            'current_page': 'main'
        }
        # Store in session state
        for key, value in session_data.items():
            st.session_state[key] = value
    
    def get_user_session(self) -> Optional[Dict[str, Any]]:
        """Get current user session data"""
        if st.session_state.get('authenticated', False):
            return {
                'authenticated': st.session_state.get('authenticated'),
                'user_data': st.session_state.get('user_data'),
                'last_activity': st.session_state.get('last_activity'),
                'current_page': st.session_state.get('current_page', 'main')
            }
        return None
    
    def is_session_valid(self) -> bool:
        """Check if current session is valid and not timed out"""
        if not st.session_state.get('authenticated', False):
            return False
        
        last_activity = st.session_state.get('last_activity', 0)
        current_time = time.time()
        
        if current_time - last_activity > self.session_timeout:
            self.clear_session()
            return False
        
        # Update last activity
        st.session_state['last_activity'] = current_time
        return True
    
    def clear_session(self):
        """Clear all session data"""
        keys_to_remove = [
            'authenticated', 'user_data', 'last_activity', 
            'current_page', 'auth_mode', 'chat_history',
            'current_answer', 'current_question'
        ]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
    
    def update_activity(self):
        """Update the last activity timestamp"""
        if st.session_state.get('authenticated', False):
            st.session_state['last_activity'] = time.time()
