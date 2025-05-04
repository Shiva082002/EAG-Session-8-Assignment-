import os
from mcp.server.fastmcp import FastMCP
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import sys
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('email_mcp_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

# Validate email credentials
if not SENDER_EMAIL or not SENDER_PASSWORD:
    raise ValueError("Email credentials not found in environment variables!")

# Create an MCP server
mcp = FastMCP("EmailMCP")

@mcp.tool()
async def send_email(recipient_email: str,user_input: str="", subject: str = "AI Assistant Results", content: dict = None) -> dict:
    """Send email with the Google Sheets result
    
    Args:
        recipient_email: Email address of the recipient
        user_input: The original user input Received by Agent
        subject: Email subject line (optional)
        content: Dictionary containing email content (optional)
    
    Returns:
        Dictionary containing status and message
    """
    try:
        if not recipient_email:
            raise ValueError("Recipient email is required")
            
        if content is None:
            content = {}

        # Get current timestamp
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create message
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = recipient_email
        message["Subject"] = subject

        # Create HTML body
        html_content = f"""
            <html>
                <body>
                    <h2>Query Results</h2>
                    <p><strong>User Input:</strong> {user_input}</p>
                    <p><strong>Spreadsheet Link:</strong> <a href="{content.get('spreadsheet_link', '#')}">View Results</a></p>
                    <p><strong>Timestamp:</strong> {current_time}</p>
                    <hr>
                    <p>This is an automated message from your AI Assistant.</p>
                </body>
            </html>
            """
        
        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(message)

        success_msg = f"Email sent successfully to {recipient_email}"
        logger.info(success_msg)
        return {
            "status": "success",
            "message": success_msg,
            "timestamp": current_time,
        }

    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

if __name__ == "__main__":
    print("mcp_server_4.py starting")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
        print("\nShutting down...") 