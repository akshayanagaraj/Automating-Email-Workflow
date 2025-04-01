import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_env_file(env_file: str = ".env") -> Dict[str, str]:
    """
    Load environment variables from a .env file.

    Args:
        env_file: Path to the .env file

    Returns:
        Dictionary of environment variables
    """
    env_vars = {}

    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip().strip("'\"")

    return env_vars


def get_db_connection_string(env_vars: Dict[str, str]) -> str:
    """
    Get the database connection string from environment variables.

    Args:
        env_vars: Dictionary of environment variables

    Returns:
        SQLAlchemy connection string
    """
    host = env_vars.get("DB_HOST", "localhost")
    port = env_vars.get("DB_PORT", "5432")
    dbname = env_vars.get("DB_NAME", "gmail_rules_engine")
    user = env_vars.get("DB_USER", "postgres")
    password = env_vars.get("DB_PASSWORD", "")

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def get_label_id_by_name(gmail_service: Any, label_name: str) -> Optional[str]:
    """
    Get a Gmail label ID by its name.

    Args:
        gmail_service: Authenticated Gmail API service
        label_name: Name of the label

    Returns:
        Label ID if found, None otherwise
    """
    try:
        results = gmail_service.users().labels().list(userId="me").execute()
        labels = results.get("labels", [])

        for label in labels:
            if label["name"].lower() == label_name.lower():
                return label["id"]

        return None
    except Exception as e:
        logging.error(f"Error getting label ID: {str(e)}")
        return None


def create_default_rules_file(file_path: str) -> None:
    """
    Create a default rules file if it doesn't exist.

    Args:
        file_path: Path to the rules file
    """
    if os.path.exists(file_path):
        return

    default_rules = [
        {
            "id": "rule_1",
            "name": "Mark important emails as read",
            "predicate": "all",
            "conditions": [
                {
                    "field": "from",
                    "predicate": "contains",
                    "value": "important@example.com",
                },
                {"field": "subject", "predicate": "contains", "value": "Important"},
            ],
            "actions": [{"type": "mark_as_read", "value": None}],
        },
        {
            "id": "rule_2",
            "name": "Move newsletters to newsletter label",
            "predicate": "any",
            "conditions": [
                {"field": "from", "predicate": "contains", "value": "newsletter"},
                {"field": "subject", "predicate": "contains", "value": "Newsletter"},
            ],
            "actions": [{"type": "move_message", "value": "CATEGORY_PROMOTIONS"}],
        },
    ]

    with open(file_path, "w") as f:
        json.dump(default_rules, f, indent=2)
