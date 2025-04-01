import logging
from typing import Dict, Any, Optional, Union

from gmail_rules_engine.db.models import Email
from gmail_rules_engine.email_fetcher import EmailFetcher

logger = logging.getLogger(__name__)

class ActionHandler:
    def __init__(
        self, 
        email_fetcher: EmailFetcher, 
        db_manager: Any
    ):
        """
        Initialize the action handler.
        
        Args:
            email_fetcher: EmailFetcher instance
            db_manager: DatabaseManager instance
        """
        self.email_fetcher = email_fetcher
        self.db_manager = db_manager
        
    def handle_action(
        self, 
        email: Email, 
        action_type: str, 
        action_value: Any
    ) -> bool:
        """
        Handle an action for an email.
        
        Args:
            email: Email object
            action_type: Type of action to perform
            action_value: Value for the action
            
        Returns:
            True if the action was successful, False otherwise
        """
        if action_type == "mark_as_read":
            return self._mark_as_read(email)
        elif action_type == "mark_as_unread":
            return self._mark_as_unread(email)
        elif action_type == "move_message":
            return self._move_message(email, action_value)
        else:
            logger.warning(f"Unknown action type: {action_type}")
            return False
            
    def _mark_as_read(self, email: Email) -> bool:
        """
        Mark an email as read.
        
        Args:
            email: Email object
            
        Returns:
            True if successful, False otherwise
        """
        if email.is_read:
            # Already read, no action needed
            return True
        self.email_fetcher.mark_as_read(email.message_id)
        
        self.db_manager.update_email(email.id, {"is_read": True})
        return True
    def _mark_as_unread(self, email: Email) -> bool:
        """
        Mark an email as unread.    
        """
        if not email.is_read:
            # Already not read, no action needed
            return True
        self.email_fetcher.mark_as_unread(email.message_id)
        self.db_manager.update_email(email.id, {"is_read": False})
        return True
    def _move_message(self, email: Email, label_id: str) -> bool:
        """
        Move an email to a different label. 
        """ 
        if label_id in email.labels:
            # Already in the target label, no action needed
            return True
        self.email_fetcher.move_message(email.message_id, label_id)
        self.db_manager.update_email(email.id, {"labels": email.labels + [label_id]})
        return True
    