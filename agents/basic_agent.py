import sys
import asyncio
import warnings

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

warnings.filterwarnings(
    "ignore",
    message="there are non-text parts in the response"
)

def get_weather(city: str) -> str:
    return f"☀️  Weather in {city}: Sunny"

agent = LlmAgent(
    name="weather_agent",
    description="Checks weather for a city",
    model="gemini-2.5-pro",
    tools=[get_weather],
)

APP_NAME = "weather_app"
USER_ID = "cli_user"
SESSION_ID = "weather_session"

session_service = InMemorySessionService()

runner = Runner(
    agent=agent,
    app_name=APP_NAME,
    session_service=session_service,
)

async def run_query_async(city: str) -> str:
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    content = types.Content(
        role="user",
        parts=[types.Part(text=city)],
    )

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content,
    ):

        if event.is_final_response():
            tool_text = None
            model_text = None

            for part in event.content.parts:
                # Tool result (function output)
                if hasattr(part, "function_response") and part.function_response:
                    tool_text = part.function_response.get("response")

                # Model text (paraphrase)
                if hasattr(part, "text") and part.text:
                    model_text = part.text

            # Prefer tool output if present
            return tool_text or model_text

    return "❌ No response from agent"

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 basic_agent.py <CITY_NAME>")
        sys.exit(1)

    city = " ".join(sys.argv[1:])  # supports "New York"
    result = asyncio.run(run_query_async(city))

    print("\n" + "=" * 40)
    print("🌍  WEATHER CHECK RESULT")
    print("=" * 40)
    print(result)
    print("=" * 40 + "\n")


if __name__ == "__main__":
    main()
