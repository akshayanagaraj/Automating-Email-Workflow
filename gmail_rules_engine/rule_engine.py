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

        # Define predicates
        self.string_predicates = {
            "contains": lambda field, value: value.lower() in field.lower(),
            "does_not_contain": lambda field, value: value.lower() not in field.lower(),
            "equals": lambda field, value: field.lower() == value.lower(),
            "does_not_equal": lambda field, value: field.lower() != value.lower(),
        }

        self.date_predicates = {
            "less_than_days": lambda date, days: (
                datetime.now(timezone.utc) - date
            ).days
            < int(days),
            "greater_than_days": lambda date, days: (
                datetime.now(timezone.utc) - date
            ).days
            > int(days),
            "less_than_months": lambda date, months: (
                datetime.now(timezone.utc) - date
            ).days
            < int(months) * 30,
            "greater_than_months": lambda date, months: (
                datetime.now(timezone.utc) - date
            ).days
            > int(months) * 30,
        }

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

    def _evaluate_rule(self, email: Email, rule: Dict[str, Any]) -> bool:
        """
        Evaluate if an email matches a rule.

        Args:
            email: Email object
            rule: Rule dictionary

        Returns:
            True if the email matches the rule, False otherwise
        """
        conditions = rule.get("conditions", [])
        if not conditions:
            return False

        predicate = rule.get("predicate", "all").lower()

        if predicate == "all":
            return all(
                self._evaluate_condition(email, condition) for condition in conditions
            )
        elif predicate == "any":
            return any(
                self._evaluate_condition(email, condition) for condition in conditions
            )
        else:
            logger.warning(f"Unknown predicate: {predicate}")
            return False

    def _evaluate_condition(self, email: Email, condition: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition against an email.

        Args:
            email: Email object
            condition: Condition dictionary

        Returns:
            True if the condition is met, False otherwise
        """
        field = condition.get("field")
        predicate = condition.get("predicate")
        value = condition.get("value")

        if not field or not predicate or value is None:
            return False

        # Get the field value from the email
        field_value = self._get_field_value(email, field)
        if field_value is None:
            return False

        # Apply the appropriate predicate
        if field == "received_date":
            predicate_func = self.date_predicates.get(predicate)
            if predicate_func:
                return predicate_func(field_value, value)
        else:
            predicate_func = self.string_predicates.get(predicate)
            if predicate_func:
                return predicate_func(field_value, value)

        logger.warning(f"Unknown predicate: {predicate} for field: {field}")
        return False

    def _get_field_value(
        self, email: Email, field: str
    ) -> Optional[Union[str, datetime]]:
        """
        Get the value of a field from an email.

        Args:
            email: Email object
            field: Field name

        Returns:
            Field value or None if not found
        """
        if field == "from":
            return email.from_address
        elif field == "to":
            return email.to_address
        elif field == "subject":
            return email.subject
        elif field == "message":
            return email.body
        elif field == "received_date":
            return email.received_date
        else:
            logger.warning(f"Unknown field: {field}")
            return None

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
