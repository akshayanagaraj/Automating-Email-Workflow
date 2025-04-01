import os
import pickle
from pathlib import Path
from typing import Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

# Gmail API scopes required for this application
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

class GmailAuth:
    def __init__(
        self, 
        credentials_path: str, 
        token_path: str
    ):
        """
        Initialize Gmail authentication.
        
        Args:
            credentials_path: Path to the credentials.json file
            token_path: Path to store the token.json file
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        
    def get_service(self) -> Optional[Resource]:
        """
        Get an authenticated Gmail API service.
        
        Returns:
            Gmail API service object if successful, None otherwise
        """
        credentials = self._get_credentials()
        if not credentials:
            return None
            
        try:
            service = build('gmail', 'v1', credentials=credentials)
            return service
        except Exception as e:
            print(f"Error building Gmail service: {str(e)}")
            return None
            
    def _get_credentials(self) -> Optional[Credentials]:
        """
        Get and refresh OAuth 2.0 credentials.
        
        Returns:
            Credentials object if successful, None otherwise
        """
        credentials = None
        
        # Check if token file exists
        token_path = Path(self.token_path)
        if token_path.exists():
            with open(token_path, 'rb') as token:
                credentials = pickle.load(token)
        
        # If there are no valid credentials, get new ones
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {str(e)}")
                    return self._get_new_credentials()
            else:
                return self._get_new_credentials()
                
        # Save the credentials for future use
        with open(token_path, 'wb') as token:
            pickle.dump(credentials, token)
            
        return credentials
        
    def _get_new_credentials(self) -> Optional[Credentials]:
        """
        Get new OAuth 2.0 credentials via user authorization.
        
        Returns:
            Credentials object if successful, None otherwise
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, SCOPES
            )
            credentials = flow.run_local_server(port=0)
            
            # Save the credentials for future use
            with open(self.token_path, 'wb') as token:
                pickle.dump(credentials, token)
                
            return credentials
        except Exception as e:
            print(f"Error getting new credentials: {str(e)}")
            return None