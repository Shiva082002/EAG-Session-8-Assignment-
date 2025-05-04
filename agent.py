# agent.py

import asyncio
import yaml
import logging
from core.loop import AgentLoop
from core.session import MultiMCP

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def log(stage: str, msg: str):
    """Simple timestamped console logger."""
    import datetime
    now = datetime.datetime.now().strftime("%H:%M:%S")
    msg_str = f"[{now}] [{stage}] {msg}"
    print(msg_str)
    logger.info(msg_str)


async def main(get_user_input=None):
    logger.info("🧠 Cortex-R Agent Ready")
    
    # Get user input either from command line or custom function
    if get_user_input:
        user_input = await get_user_input()
        logger.info(f"Received user input: {user_input}")
    else:
        user_input = input("🧑 What do you want to solve today? → ")

    # Load MCP server configs from profiles.yaml
    try:
        with open("config/profiles.yaml", "r") as f:
            profile = yaml.safe_load(f)
            mcp_servers = profile.get("mcp_servers", [])
            logger.info(f"Loaded {len(mcp_servers)} MCP server configurations")
    except Exception as e:
        logger.error(f"Failed to load profiles.yaml: {e}")
        return "I'm having trouble accessing my configuration. Please try again later."

    try:
        multi_mcp = MultiMCP(server_configs=mcp_servers)
        logger.info("Initializing MultiMCP...")
        await multi_mcp.initialize()
        logger.info("MultiMCP initialized successfully")

        agent = AgentLoop(
            user_input=user_input,
            dispatcher=multi_mcp
        )

        logger.info("Running agent loop...")
        final_response = await agent.run()
        response_text = final_response.replace("FINAL_ANSWER:", "").strip()
        
        if not get_user_input:
            print("\n💡 Final Answer:\n", response_text)
        
        logger.info(f"Agent response: {response_text}")
        return response_text

    except Exception as e:
        error_msg = f"Agent failed: {e}"
        log("fatal", error_msg)
        logger.error(error_msg, exc_info=True)
        return "I encountered an error while processing your request. Please try again later."


if __name__ == "__main__":
    asyncio.run(main())


# Find the ASCII values of characters in INDIA and then return sum of exponentials of those values.
# How much Anmol singh paid for his DLF apartment via Capbridge? 
# What do you know about Don Tapscott and Anthony Williams?
# What is the relationship between Gensol and Go-Auto?
# which course are we teaching on Canvas LMS?
# Summarize this page: https://theschoolof.ai/
# What is the log value of the amount that Anmol singh paid for his DLF apartment via Capbridge? 