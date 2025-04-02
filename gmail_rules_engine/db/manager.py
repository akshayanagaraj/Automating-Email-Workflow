import logging
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from gmail_rules_engine.db.models import Base, Email, RuleExecution

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, connection_string: str):
        """
        Initialize the database manager with a connection string.

        Args:
            connection_string: SQLAlchemy connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables if they don't exist."""
        Base.metadata.create_all(self.engine)

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.Session()

    def store_email(self, email_data: Dict[str, Any]) -> Optional[Email]:
        """
        Store an email in the database.

        Args:
            email_data: Dictionary containing email information

        Returns:
            Email object if successful, None otherwise
        """
        session = self.get_session()
        try:
            # Check if email already exists
            existing_email = (
                session.query(Email)
                .filter_by(message_id=email_data["message_id"])
                .first()
            )

            if existing_email:
                # Update existing email if needed
                for key, value in email_data.items():
                    if key != "message_id" and hasattr(existing_email, key):
                        setattr(existing_email, key, value)
                email = existing_email
            else:
                # Create new email
                email = Email(**email_data)
                session.add(email)

            session.commit()
            return email
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error storing email: {str(e)}")
            return None
        finally:
            session.close()

    def get_emails_by_criteria(
        self, criteria: Dict[str, Any], limit: int = 100, offset: int = 0
    ) -> List[Email]:
        """
        Get emails matching the given criteria.

        Args:
            criteria: Dictionary of criteria to filter emails
            limit: Maximum number of emails to return
            offset: Number of emails to skip

        Returns:
            List of Email objects
        """
        session = self.get_session()
        try:
            query = session.query(Email)

            # Apply filters
            for key, value in criteria.items():
                if hasattr(Email, key):
                    query = query.filter(getattr(Email, key) == value)

            # Apply limit and offset
            query = query.limit(limit).offset(offset)

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving emails: {str(e)}")
            return []
        finally:
            session.close()

    def update_email(self, email_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an email with the given updates.

        Args:
            email_id: ID of the email to update
            updates: Dictionary of fields to update

        Returns:
            True if successful, False otherwise
        """
        session = self.get_session()
        try:
            email = session.query(Email).filter_by(id=email_id).first()
            if not email:
                return False

            for key, value in updates.items():
                if hasattr(email, key):
                    setattr(email, key, value)

            session.commit()
            return True
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error updating email: {str(e)}")
            return False
        finally:
            session.close()

    def log_rule_execution(
        self, email_id: int, rule_id: str, actions_taken: Dict[str, Any]
    ) -> Optional[RuleExecution]:
        """
        Log a rule execution for a specific email.

        Args:
            email_id: ID of the email
            rule_id: ID of the rule
            actions_taken: Dictionary of actions taken

        Returns:
            RuleExecution object if successful, None otherwise
        """
        session = self.get_session()
        try:
            rule_execution = RuleExecution(
                email_id=email_id, rule_id=rule_id, actions_taken=actions_taken
            )
            session.add(rule_execution)
            session.commit()
            return rule_execution
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error logging rule execution: {str(e)}")
            return None
        finally:
            session.close()

    def get_emails_for_rule_processing(
        self, days_back: int = 7, processed_rule_ids: Optional[List[str]] = None
    ) -> List[Email]:
        """
        Get emails that need rule processing.

        Args:
            days_back: Number of days to look back
            processed_rule_ids: List of rule IDs that have already been processed

        Returns:
            List of Email objects
        """
        session = self.get_session()
        try:
            query = session.query(Email).filter(
                Email.received_date >= datetime.now() - timedelta(days=days_back)
            )

            if processed_rule_ids:
                # Exclude emails that have already been processed by these rules
                subquery = session.query(RuleExecution.email_id).filter(
                    RuleExecution.rule_id.in_(processed_rule_ids)
                )
                query = query.filter(~Email.id.in_(subquery))

            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving emails for rule processing: {str(e)}")
            return []
        finally:
            session.close()
    def get_emails_for_rule(self, rule: Dict[str, Any]) -> List[Email]:
        """
        Get emails that potentially match a specific rule.
        
        Args:
            rule: Rule dictionary with conditions
            
        Returns:
            List of Email objects
        """
        session = self.get_session()
        try:
            # Start with base query including date range filter
            query = session.query(Email)
            
            # Get rule conditions and predicate
            conditions = rule.get("conditions", [])
            predicate = rule.get("predicate", "all").lower()
            
            # Skip if no conditions
            if not conditions:
                return []
            
            # For "all" predicate, we can apply all conditions to the database query
            # For "any" predicate, we need to use SQLAlchemy's OR operator
            from sqlalchemy import or_, and_
            
            db_conditions = []
            
            for condition in conditions:
                field = condition.get("field")
                pred = condition.get("predicate")
                value = condition.get("value")
                
                if not field or not pred or value is None:
                    continue
                    
                # Map field to database column
                if field == "from":
                    column = Email.from_address
                elif field == "to":
                    column = Email.to_address
                elif field == "subject":
                    column = Email.subject
                elif field == "message":
                    column = Email.body
                elif field == "received_date":
                    column = Email.received_date
                else:
                    continue
                    
                # Apply appropriate predicate
                if field == "received_date":
                    if pred == "less_than_days":
                        days = int(value)
                        date_threshold = datetime.now() - timedelta(days=days)
                        db_conditions.append(Email.received_date > date_threshold)
                    elif pred == "greater_than_days":
                        days = int(value)
                        date_threshold = datetime.now() - timedelta(days=days)
                        db_conditions.append(Email.received_date < date_threshold)
                    elif pred == "less_than_months":
                        months = int(value)
                        date_threshold = datetime.now() - timedelta(days=months*30)
                        db_conditions.append(Email.received_date > date_threshold)
                    elif pred == "greater_than_months":
                        months = int(value)
                        date_threshold = datetime.now() - timedelta(days=months*30)
                        db_conditions.append(Email.received_date < date_threshold)
                else:
                    # String predicates
                    if pred == "contains":
                        db_conditions.append(column.ilike(f'%{value}%'))
                    elif pred == "does_not_contain":
                        db_conditions.append(~column.ilike(f'%{value}%'))
                    elif pred == "equals":
                        db_conditions.append(func.lower(column) == func.lower(value))
                    elif pred == "does_not_equal":
                        db_conditions.append(func.lower(column) != func.lower(value))
            
            # Apply conditions based on predicate
            if predicate == "all" and db_conditions:
                query = query.filter(and_(*db_conditions))
            elif predicate == "any" and db_conditions:
                query = query.filter(or_(*db_conditions))
            
            # Check if this rule has already been applied to these emails
            subquery = session.query(RuleExecution.email_id).filter(
                RuleExecution.rule_id == rule["id"]
            )
            query = query.filter(~Email.id.in_(subquery))
            
            print(f"Query: {query.all()}, Rule: {rule}")
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving emails for rule: {str(e)}")
            return []
        finally:
            session.close()
        
    def bulk_log_rule_executions(self, batch_executions: List[Dict[str, Any]]):
        """
        Log multiple rule executions in a single transaction.
        
        Args:
            batch_executions: List of execution records
        """
        session = self.get_session()
        try:
            rule_executions = [
                RuleExecution(
                    email_id=execution["email_id"],
                    rule_id=execution["rule_id"],
                    actions_taken=execution["actions_taken"]
                )
                for execution in batch_executions
            ]
            
            session.bulk_save_objects(rule_executions)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Error bulk logging rule executions: {str(e)}")
        finally:
            session.close()