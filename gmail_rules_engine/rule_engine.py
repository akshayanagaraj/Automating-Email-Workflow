import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta, timezone
import re

from gmail_rules_engine.db.manager import DatabaseManager
from gmail_rules_engine.db.models import Email

logger = logging.getLogger(__name__)


class RuleEngine:
    def __init__(self, db_manager: DatabaseManager, rules_file_path: str):
        """
        Initialize the rule engine.

        Args:
            db_manager: Database manager instance
            rules_file_path: Path to the rules JSON file
        """
        self.db_manager = db_manager
        self.rules_file_path = rules_file_path
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """
        Load rules from the JSON file.

        Returns:
            List of rule dictionaries
        """
        try:
            with open(self.rules_file_path, "r") as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading rules: {str(e)}")
            return []

    def process_emails(self, action_handler: Callable) -> int:
        """
        Process rules against emails in the database.

        Args:
            action_handler: Callable to handle actions

        Returns:
            Number of emails processed
        """
        processed_count = 0

        for rule in self.rules:
            # Get emails that potentially match this rule's criteria
            potential_matches = self.db_manager.get_emails_for_rule(rule)

            # For efficiency, process emails in batches
            batch_actions = []

            for email in potential_matches:
                actions_taken = self._execute_actions(email, rule, action_handler)

                # If actions were taken, prepare for batch logging
                if actions_taken:
                    batch_actions.append(
                        {
                            "email_id": email.id,
                            "rule_id": rule["id"],
                            "actions_taken": actions_taken,
                        }
                    )
                    processed_count += 1

        # Bulk log rule executions if any
        if batch_actions:
            self.db_manager.bulk_log_rule_executions(batch_actions)

        return processed_count

    def _execute_actions(
        self, email: Email, rule: Dict[str, Any], action_handler: Callable
    ) -> Dict[str, Any]:
        """
        Execute actions for a matching rule.

        Args:
            email: Email object
            rule: Rule dictionary
            action_handler: Callable to handle actions

        Returns:
            Dictionary of actions taken
        """
        actions = rule.get("actions", [])
        actions_taken = {}

        for action in actions:
            action_type = action.get("type")
            action_value = action.get("value")

            if not action_type:
                continue

            result = action_handler(email, action_type, action_value)
            if result:
                actions_taken[action_type] = action_value

        return actions_taken
