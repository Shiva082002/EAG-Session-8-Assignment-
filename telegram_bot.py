import os
import asyncio
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from agent import main as agent_main

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Dictionary to store user sessions
user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    logger.info(f"Start command received from user {user.id}")
    await update.message.reply_text(
        f'Hi {user.first_name}! I am Cortex-R, your AI assistant. '
        'You can ask me anything and I will help you solve it step by step.'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    logger.info(f"Help command received from user {update.effective_user.id}")
    await update.message.reply_text(
        'I am here to help you solve problems step by step. '
        'Just send me your question or task, and I will work on it using various tools and reasoning.'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the user message and process it through the agent."""
    user_id = update.effective_user.id
    message = update.message.text
    
    logger.info(f"Received message from user {user_id}: {message}")

    # Show typing indicator
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        # Create a custom input function for the agent
        async def get_user_input():
            return message

        logger.info("Calling agent_main with message")
        # Run the agent with the user's message
        response = await agent_main(get_user_input)
        logger.info(f"Agent response: {response}")

        # Send the response back to the user
        await update.message.reply_text(response)

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await update.message.reply_text(
            "I encountered an error while processing your request. Please try again later."
        )

def main() -> None:
    """Start the bot."""
    try:
        # Get the token from environment variables
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
            return

        logger.info("Starting the bot...")
        # Create the Application and pass it your bot's token
        application = Application.builder().token(token).build()

        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Bot handlers registered, starting polling...")
        # Start the Bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)

if __name__ == '__main__':
    main() 