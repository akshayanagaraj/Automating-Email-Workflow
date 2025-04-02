import os
import argparse
import logging
import time
import schedule
from typing import Dict, Any, Optional

from gmail_rules_engine.utils.helpers import (
    setup_logging,
    load_env_file,
    get_db_connection_string,
    create_default_rules_file,
)
from gmail_rules_engine.auth import GmailAuth
from gmail_rules_engine.email_fetcher import EmailFetcher
from gmail_rules_engine.db.manager import DatabaseManager
from gmail_rules_engine.rule_engine import RuleEngine
from gmail_rules_engine.actions import ActionHandler


def fetch_and_store_emails(
    email_fetcher: EmailFetcher, db_manager: DatabaseManager, max_results: int = 100
) -> int:
    """
    Fetch emails from Gmail and store them in the database.

    Args:
        email_fetcher: EmailFetcher instance
        db_manager: DatabaseManager instance
        max_results: Maximum number of emails to fetch

    Returns:
        Number of emails stored
    """
    # Fetch emails
    emails = email_fetcher.fetch_emails(max_results=max_results)

    # Process emails in batches for bulk insertion
    stored_count = 0
    batch_size = 100
    email_batches = [
        emails[i : i + batch_size] for i in range(0, len(emails), batch_size)
    ]

    for batch in email_batches:
        # Check which emails already exist to avoid duplicates
        message_ids = [email_data["message_id"] for email_data in batch]
        existing_emails = db_manager.get_existing_emails_by_message_ids(message_ids)
        existing_message_ids = {email.message_id for email in existing_emails}

        # Separate new emails and updates
        new_emails = []
        updates = []

        for email_data in batch:
            if email_data["message_id"] in existing_message_ids:
                updates.append(email_data)
            else:
                new_emails.append(email_data)

        # Bulk insert new emails
        if new_emails:
            db_manager.bulk_insert_emails(new_emails)
            stored_count += len(new_emails)

        # Bulk update existing emails if needed
        if updates:
            db_manager.bulk_update_emails(updates)
            # Don't increment stored_count for updates

    logging.info(f"Stored {stored_count} new emails in the database")
    return stored_count


def process_rules(rule_engine: RuleEngine, action_handler: ActionHandler) -> int:
    """
    Process rules on emails in the database.

    Args:
        rule_engine: RuleEngine instance
        action_handler: ActionHandler instance

    Returns:
        Number of actions performed
    """
    processed_count = rule_engine.process_emails(action_handler.handle_action)
    logging.info(f"Processed {processed_count} emails with rules")
    return processed_count


def run_job(
    email_fetcher: EmailFetcher,
    db_manager: DatabaseManager,
    rule_engine: RuleEngine,
    action_handler: ActionHandler,
    max_results: int = 100,
) -> None:
    """
    Run the main job - fetch, store, and process emails.

    Args:
        email_fetcher: EmailFetcher instance
        db_manager: DatabaseManager instance
        rule_engine: RuleEngine instance
        action_handler: ActionHandler instance
        max_results: Maximum number of emails to fetch
    """
    logging.info("Starting job")
    fetch_and_store_emails(email_fetcher, db_manager, max_results)
    process_rules(rule_engine, action_handler)
    logging.info("Job completed")


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Gmail Rules Engine")
    parser.add_argument("--env-file", default=".env", help="Path to the .env file")
    parser.add_argument(
        "--rules-file", default="rules.json", help="Path to the rules JSON file"
    )
    parser.add_argument(
        "--max-results", type=int, default=100, help="Maximum number of emails to fetch"
    )
    parser.add_argument(
        "--interval", type=int, default=5, help="Interval in minutes to run the job"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level",
    )
    parser.add_argument("--run-once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    # Set up logging
    setup_logging(args.log_level)

    # Load environment variables
    env_vars = load_env_file(args.env_file)

    # Create default rules file if it doesn't exist
    create_default_rules_file(args.rules_file)

    # Set up database
    db_connection_string = get_db_connection_string(env_vars)
    db_manager = DatabaseManager(db_connection_string)
    db_manager.create_tables()

    # Set up Gmail API
    credentials_path = env_vars.get("GMAIL_CREDENTIALS_PATH", "credentials.json")
    token_path = env_vars.get("GMAIL_TOKEN_PATH", "token.json")
    gmail_auth = GmailAuth(credentials_path, token_path)
    gmail_service = gmail_auth.get_service()

    if not gmail_service:
        logging.error("Failed to authenticate with Gmail API")
        return

    # Set up email fetcher
    email_fetcher = EmailFetcher(gmail_service)

    # Set up rule engine
    rule_engine = RuleEngine(db_manager, args.rules_file)

    # Set up action handler
    action_handler = ActionHandler(email_fetcher, db_manager)

    # Run job
    if args.run_once:
        run_job(
            email_fetcher, db_manager, rule_engine, action_handler, args.max_results
        )
    else:
        # Schedule job to run at intervals
        schedule.every(args.interval).minutes.do(
            run_job,
            email_fetcher=email_fetcher,
            db_manager=db_manager,
            rule_engine=rule_engine,
            action_handler=action_handler,
            max_results=args.max_results,
        )

        # Run job immediately
        run_job(
            email_fetcher, db_manager, rule_engine, action_handler, args.max_results
        )

        # Keep the script running
        logging.info(f"Scheduled job to run every {args.interval} minutes")
        while True:
            schedule.run_pending()
            time.sleep(1)


if __name__ == "__main__":
    main()
