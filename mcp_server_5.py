import os
from mcp.server.fastmcp import FastMCP
import logging
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sheets_mcp_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Google Sheets API configuration
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Add test users who are allowed to access the application
AUTHORIZED_USERS = [
    'shivangyadav1508@gmail.com'
]

# Create an MCP server
mcp = FastMCP("SheetsMCP", host="0.0.0.0", port=8051)

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
        
        if hasattr(creds, 'id_token') and creds.id_token:
            user_email = creds.id_token.get('email')
            if user_email not in AUTHORIZED_USERS:
                raise Exception(f"User {user_email} is not authorized")
            logger.info(f"Authorized user {user_email} authenticated")
        
        return creds
        
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        if os.path.exists(token_path):
            os.remove(token_path)
        raise

# Initialize services
try:
    credentials = get_google_credentials()
    sheets_service = build('sheets', 'v4', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)
    logger.info("Google services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {str(e)}")
    raise

@mcp.tool()
async def process_result(result: dict) -> dict:
    """Store result in Google Sheets and return shareable link
    
    Args:
        result: Dictionary containing the result data to store
    
    Returns:
        Dictionary containing status and spreadsheet link
    """
    try:
        # Create a new spreadsheet
        spreadsheet = {
            'properties': {
                'title': f'F1 Standings {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            }
        }
        spreadsheet = sheets_service.spreadsheets().create(body=spreadsheet).execute()
        spreadsheet_id = spreadsheet.get('spreadsheetId')
        
        # Make the spreadsheet public using Drive API
        permission = {
            'type': 'anyone',
            'role': 'reader',
            'allowFileDiscovery': False
        }
        drive_service.permissions().create(
            fileId=spreadsheet_id,
            body=permission,
            fields='id'
        ).execute()
        
        # Create DataFrame from markdown data
        if 'markdown' in result:
            # Split the markdown string into lines and clean up
            lines = result['markdown'].strip().split('\\n')
            # Process each line: split by semicolon and clean up
            data = []
            for line in lines:
                parts = [p.strip() for p in line.split(';') if p.strip()]
                data.append(parts)  # Take only first 5 fields
            
            # Create DataFrame
            df = pd.DataFrame(data, columns=["Position", "Driver", "Country", "Team", "Points"])
            
            # Prepare values for Sheets
            values = [df.columns.tolist()] + df.values.tolist()
        else:
            # Fallback if result is not markdown
            df = pd.DataFrame([result]) if not isinstance(result, pd.DataFrame) else result
            values = [df.columns.tolist()] + df.values.tolist()
        
        # Update spreadsheet with values
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
        
        logger.info(f"Successfully created spreadsheet: {spreadsheet['properties']['title']}")
        
        return {
            "status": "success",
            "spreadsheet_link": file.get('webViewLink'),
            "spreadsheet_id": spreadsheet_id
        }
        
    except Exception as e:
        error_msg = f"Error processing result: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

if __name__ == "__main__":
    # Run with SSE transport
    mcp.run() 