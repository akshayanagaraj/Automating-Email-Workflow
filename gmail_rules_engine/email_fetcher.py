import base64
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import email
from email.utils import parsedate_to_datetime

from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class EmailFetcher:
    """
    Fetches emails from Gmail using the Gmail API.
    """

    def __init__(self, gmail_service):
        """
        Initialize EmailFetcher with the Gmail API service.

        Args:
            gmail_service: Authenticated Gmail API service instance.
        """
        self.gmail_service = gmail_service

    def fetch_emails(self, max_results=100):
        """
        Fetch emails from Gmail.

        Args:
            max_results: Maximum number of emails to fetch.

        Returns:
            List of email data.
        """
        try:
            response = self.gmail_service.users().messages().list(userId="me", maxResults=max_results).execute()
            messages = response.get("messages", [])
            logging.info(f"Fetched {len(messages)} emails.")
            return messages
        except Exception as e:
            logging.error(f"Failed to fetch emails: {e}")
            return []

    def fetch_emails(
        self, 
        max_results: int = 100, 
        query: str = "", 
        include_body: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from Gmail inbox.
        
        Args:
            max_results: Maximum number of emails to fetch
            query: Gmail search query
            include_body: Whether to include the email body
            
        Returns:
            List of dictionaries containing email data
        """
        try:
            # Get message IDs
            response = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = response.get('messages', [])
            if not messages:
                logger.info("No messages found.")
                return []
                
            # Fetch full message details
            emails = []
            for message in messages:
                email_data = self._get_email_data(message['id'], include_body)
                if email_data:
                    emails.append(email_data)
                    
            return emails
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return []
            
    def _get_email_data(
        self, 
        message_id: str, 
        include_body: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed email data for a specific message.
        
        Args:
            message_id: Gmail message ID
            include_body: Whether to include the email body
            
        Returns:
            Dictionary containing email data if successful, None otherwise
        """
        try:
            # Get the message
            message = self.gmail_service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Extract headers
            headers = {}
            for header in message['payload']['headers']:
                headers[header['name'].lower()] = header['value']
                
            # Extract email data
            email_data = {
                'message_id': message['id'],
                'thread_id': message['threadId'],
                'from_address': headers.get('from', ''),
                'to_address': headers.get('to', ''),
                'subject': headers.get('subject', ''),
                'received_date': self._parse_date(headers.get('date', '')),
                'is_read': 'UNREAD' not in message['labelIds'],
                'labels': message['labelIds'],
                'raw_data': message
            }
            
            # Extract body if requested
            if include_body:
                email_data['body'] = self._get_email_body(message)
                
            return email_data
        except HttpError as error:
            logger.error(f"An error occurred while fetching email {message_id}: {error}")
            return None
            
    def _get_email_body(self, message: Dict[str, Any]) -> str:
        """
        Extract email body from a message.
        
        Args:
            message: Gmail message object
            
        Returns:
            Email body as plain text
        """
        body = ""
        
        # Check for multipart or single part message
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = self._decode_body(part['body'].get('data', ''))
                    break
        elif message['payload']['mimeType'] == 'text/plain':
            body = self._decode_body(message['payload']['body'].get('data', ''))
            
        return body
        
    def _decode_body(self, encoded_data: str) -> str:
        """
        Decode base64 encoded email body.
        
        Args:
            encoded_data: Base64 encoded string
            
        Returns:
            Decoded string
        """
        if not encoded_data:
            return ""
            
        try:
            decoded_bytes = base64.urlsafe_b64decode(encoded_data)
            return decoded_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Error decoding email body: {str(e)}")
            return ""
            
    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string from email headers.
        
        Args:
            date_str: Date string in email header format
            
        Returns:
            Datetime object
        """
        if not date_str:
            return datetime.now()
            
        try:
            return parsedate_to_datetime(date_str)
        except Exception as e:
            logger.error(f"Error parsing date: {str(e)}")
            return datetime.now()
            
    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark an email as read.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"An error occurred while marking email as read: {error}")
            return False
            
    def mark_as_unread(self, message_id: str) -> bool:
        """
        Mark an email as unread.
        
        Args:
            message_id: Gmail message ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"An error occurred while marking email as unread: {error}")
            return False
            
    def move_message(self, message_id: str, label_id: str) -> bool:
        """
        Move an email to a different label.
        
        Args:
            message_id: Gmail message ID
            label_id: Gmail label ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use this before trying to apply the label
            leabelId = self.create_label_if_not_exists( label_id)
            self.gmail_service.users().messages().modify(
                userId='me',
                id=message_id,
                body={
                    'addLabelIds': [leabelId],
                    'removeLabelIds': ['INBOX']
                }
            ).execute()
            return True
        except HttpError as error:
            logger.error(f"An error occurred while moving email: {error}")
            return False
        
    def create_label_if_not_exists(self, label_name):
        try:
            # Try to find the label first
            results = self.gmail_service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            
            # Check if label exists
            for label in labels:
                if label['name'] == label_name:
                    return label['id']
            
            # If not found, create it
            label_object = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            created_label = self.gmail_service.users().labels().create(userId='me', body=label_object).execute()
            return created_label['id']
            
        except Exception as error:
            print(f'An error occurred: {error}')
            return None

