import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch

from gmail_rules_engine.rule_engine import RuleEngine
from gmail_rules_engine.db.models import Email


class TestRuleEngine(unittest.TestCase):
    def setUp(self):
        self.db_manager = Mock()
        self.rule_engine = RuleEngine(self.db_manager, "tests/test_rules.json")

        # Mock the _load_rules method to return test rules
        self.rule_engine._load_rules = Mock(
            return_value=[
                {
                    "id": "test_rule_1",
                    "name": "Test Rule 1",
                    "predicate": "all",
                    "conditions": [
                        {"field": "from", "predicate": "contains", "value": "test"},
                        {
                            "field": "subject",
                            "predicate": "contains",
                            "value": "important",
                        },
                    ],
                    "actions": [{"type": "mark_as_read", "value": None}],
                },
                {
                    "id": "test_rule_2",
                    "name": "Test Rule 2",
                    "predicate": "any",
                    "conditions": [
                        {
                            "field": "from",
                            "predicate": "contains",
                            "value": "newsletter",
                        },
                        {
                            "field": "subject",
                            "predicate": "contains",
                            "value": "newsletter",
                        },
                    ],
                    "actions": [{"type": "move_message", "value": "LABEL_1"}],
                },
            ]
        )
        self.rule_engine.rules = self.rule_engine._load_rules()

    def test_evaluate_condition_string_contains(self):
        # Create a mock email
        email = Mock(spec=Email)
        email.from_address = "test@example.com"

        # Test condition
        condition = {"field": "from", "predicate": "contains", "value": "test"}

        # Check if the condition is met
        result = self.rule_engine._evaluate_condition(email, condition)
        self.assertTrue(result)

    def test_evaluate_condition_string_does_not_contain(self):
        # Create a mock email
        email = Mock(spec=Email)
        email.from_address = "user@example.com"

        # Test condition
        condition = {"field": "from", "predicate": "does_not_contain", "value": "test"}

        # Check if the condition is met
        result = self.rule_engine._evaluate_condition(email, condition)
        self.assertTrue(result)

    def test_evaluate_condition_string_equals(self):
        # Create a mock email
        email = Mock(spec=Email)
        email.subject = "Test Subject"

        # Test condition
        condition = {"field": "subject", "predicate": "equals", "value": "test subject"}

        # Check if the condition is met
        result = self.rule_engine._evaluate_condition(email, condition)
        self.assertTrue(result)

    def test_evaluate_condition_date_less_than_days(self):
        # Create a mock email with a recent date
        email = Mock(spec=Email)
        email.received_date = datetime.now(timezone.utc) - timedelta(days=2)

        # Test condition
        condition = {
            "field": "received_date",
            "predicate": "less_than_days",
            "value": "5",
        }

        # Check if the condition is met
        result = self.rule_engine._evaluate_condition(email, condition)
        self.assertTrue(result)

    def test_evaluate_rule_all_conditions_met(self):
        # Create a mock email that matches all conditions
        email = Mock(spec=Email)
        email.from_address = "test@example.com"
        email.subject = "This is an important email"

        # Test rule with "all" predicate
        rule = self.rule_engine.rules[0]

        # Check if the rule matches
        result = self.rule_engine._evaluate_rule(email, rule)
        self.assertTrue(result)

    def test_evaluate_rule_all_conditions_not_met(self):
        # Create a mock email that matches only one condition
        email = Mock(spec=Email)
        email.from_address = "test@example.com"
        email.subject = "Regular email"

        # Test rule with "all" predicate
        rule = self.rule_engine.rules[0]

        # Check if the rule matches
        result = self.rule_engine._evaluate_rule(email, rule)
        self.assertFalse(result)

    def test_evaluate_rule_any_conditions_met(self):
        # Create a mock email that matches one condition
        email = Mock(spec=Email)
        email.from_address = "user@example.com"
        email.subject = "Newsletter update"

        # Test rule with "any" predicate
        rule = self.rule_engine.rules[1]

        # Check if the rule matches
        result = self.rule_engine._evaluate_rule(email, rule)
        self.assertTrue(result)

    def test_execute_actions(self):
        # Create a mock email
        email = Mock(spec=Email)
        email.id = 1

        # Create a mock action handler
        action_handler = Mock(return_value=True)

        # Test rule
        rule = {"id": "test_rule", "actions": [{"type": "mark_as_read", "value": None}]}

        # Execute actions
        result = self.rule_engine._execute_actions(email, rule, action_handler)

        # Check if action handler was called with correct parameters
        action_handler.assert_called_once_with(email, "mark_as_read", None)

        # Check if actions were recorded correctly
        self.assertEqual(result, {"mark_as_read": None})

    def test_process_emails(self):
        # Create some mock emails
        email1 = Mock(spec=Email)
        email1.id = 1
        email1.from_address = "test@example.com"
        email1.subject = "This is an important email"

        email2 = Mock(spec=Email)
        email2.id = 2
        email2.from_address = "newsletter@example.com"
        email2.subject = "Regular email"

        # Set up the mock database manager
        self.db_manager.get_emails_for_rule_processing.return_value = [email1, email2]

        # Create a mock action handler
        action_handler = Mock(return_value=True)

        # Process emails
        processed_count = self.rule_engine.process_emails(action_handler)

        # Check if the correct number of emails were processed
        self.assertEqual(processed_count, 2)

        # Check if log_rule_execution was called
        self.assertEqual(self.db_manager.log_rule_execution.call_count, 2)


if __name__ == "__main__":
    unittest.main()
