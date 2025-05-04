import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Google Sheets API configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_google_credentials():
    """Get or refresh Google API credentials"""
    creds = None
    token_path = 'token.json'
    
    try:
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            logger.info("Found existing credentials")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials")
                creds.refresh(Request())
            else:
                logger.info("Initiating new OAuth flow")
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', 
                    SCOPES,
                    redirect_uri='http://localhost:64405'
                )
                creds = flow.run_local_server(
                    port=64405,
                    prompt='consent',
                    access_type='offline'
                )
                logger.info("New credentials obtained")
            
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
                logger.info("Credentials saved to token.json")
        
        return creds
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise

def test_create_sheet():
    """Test function to create a sheet and write hello"""
    try:
        # Get credentials
        credentials = get_google_credentials()
        
        # Initialize services
        sheets_service = build('sheets', 'v4', credentials=credentials)
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Create timestamp for spreadsheet title
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        title = f"Test_Sheet_{timestamp}"
        
        # Create new spreadsheet
        spreadsheet = {
            'properties': {'title': title}
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet['spreadsheetId']
        
        # Write "hello" to cell A1
        values = [["hello"]]
        sheets_service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id,
            range='A1',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        
        # Get shareable link
        file = drive_service.files().get(
            fileId=spreadsheet_id,
            fields='webViewLink'
        ).execute()
        
        logger.info(f"Successfully created test spreadsheet: {title}")
        logger.info(f"Spreadsheet link: {file.get('webViewLink')}")
        
        return {
            "status": "success",
            "spreadsheet_link": file.get('webViewLink'),
            "spreadsheet_id": spreadsheet_id
        }
        
    except Exception as e:
        error_msg = f"Error in test_create_sheet: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

if __name__ == "__main__":
    print("Starting Google Sheets test...")
    result = test_create_sheet()
    print("\nTest Result:", result) 