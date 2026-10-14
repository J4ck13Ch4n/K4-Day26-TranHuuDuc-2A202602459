"""
Weather Agent - Connects to Remote MCP Server on Cloud Run
Successfully connects to custom MCP HTTP endpoints!
"""
import logging
import os
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv(usecwd=True))

# Setup API Key & base URL fallback for Gemini
if not os.getenv("GOOGLE_API_KEY") and os.getenv("LLM_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["LLM_API_KEY"]
if not os.getenv("GEMINI_API_KEY") and os.getenv("LLM_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["LLM_API_KEY"]
if not os.getenv("GOOGLE_GEMINI_BASE_URL"):
    os.environ["GOOGLE_GEMINI_BASE_URL"] = "https://api.shopaikey.com"

from google.adk import Agent
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset, StreamableHTTPConnectionParams

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Mặc định: server chạy local. Deploy lên Cloud Run thì đặt MCP_SERVER_URL trong .env
# (ví dụ: https://<service>.run.app/mcp). verify_setup.py đọc cùng biến này.
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8085/mcp")

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý thời tiết thông minh và thân thiện. "
    "Sử dụng các công cụ MCP được cung cấp (get_current_weather, get_forecast, health_check) để trả lời người dùng. "
    "Luôn trả lời bằng tiếng Việt tự nhiên, kèm emoji phù hợp (🌤️ 🌧️ ❄️ 💨), "
    "đầy đủ thông tin nhiệt độ, độ ẩm, sức gió và đưa ra lời khuyên thực tế khi cần thiết."
)

logger.info(f"🌐 Initializing weather agent with remote MCP server")
logger.info(f"📡 MCP Server: {MCP_SERVER_URL}")

try:
    # Create connection parameters for the remote MCP server
    connection_params = StreamableHTTPConnectionParams(
        url=MCP_SERVER_URL,
        timeout=30.0,  # Increased timeout for Cloud Run cold starts
    )
    
    # Create the MCP toolset - this will connect to the remote server
    logger.info("🔌 Connecting to MCP server...")
    weather_tools = McpToolset(
        connection_params=connection_params,
    )
    logger.info("✅ MCP toolset created successfully")
    
    # Create the agent with remote MCP tools
    root_agent = Agent(
        name="weather_agent",
        description="Trợ lý thông tin và dự báo thời tiết qua giao thức MCP",
        instruction=SYSTEM_INSTRUCTION,
        model="gemini-2.5-flash",
        tools=[weather_tools],
    )
    logger.info("✅ Weather agent initialized with remote MCP tools:")
    logger.info("   - get_current_weather(city)")
    logger.info("   - get_forecast(city, days)")
    logger.info("   - health_check()")
    logger.info("🎉 Remote MCP connection successful!")
    
except Exception as e:
    logger.error(f"❌ Failed to connect to remote MCP server: {e}")
    logger.error(f"   Server URL: {MCP_SERVER_URL}")
    import traceback
    traceback.print_exc()
    
    # Create a fallback agent without tools
    logger.warning("⚠️  Creating fallback agent without MCP tools")
    root_agent = Agent(
        name="weather_agent",
        description="Trợ lý thời tiết (chế độ dự phòng không có tools)",
        instruction=SYSTEM_INSTRUCTION,
        model="gemini-2.5-flash",
    )

