"""
main.py
-------
Core agent logic for CityPilot: a LangChain agent with two tools
(live weather + latest news) for any city, plus an optional human-in-the-loop
approval layer for tool calls when run from the terminal.

"""

from dotenv import load_dotenv
import os
import requests

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import tool
from langchain_core.messages import ToolMessage
from tavily import TavilyClient
from langchain.agents import create_agent
from langchain.agents.middleware import wrap_tool_call


# =========================
# 🌦️ Weather Tool
# =========================
@tool
def get_weather(city: str) -> str:
    """Get current weather of a city"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city},IN&appid={api_key}&units=metric"

    response = requests.get(url, timeout=10)
    data = response.json()

    if str(data.get("cod")) != "200":
        return f"Error: {data.get('message', 'Could not fetch weather')}"

    temp = data["main"]["temp"]
    desc = data["weather"][0]["description"]
    return f"Weather in {city}: {desc}, {temp}°C"


# =========================
# 📰 News Tool (Tavily)
# =========================
def _get_tavily_client() -> TavilyClient:
    return TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def get_news(city: str) -> str:
    """Get latest news about a city"""
    client = _get_tavily_client()
    response = client.search(
        query=f"latest news in {city}",
        search_depth="basic",
        max_results=3,
    )

    results = response.get("results", [])
    if not results:
        return f"No news found for {city}"

    news_list = []
    for r in results:
        title = r.get("title", "No title")
        url = r.get("url", "")
        snippet = r.get("content", "")
        news_list.append(f"- {title}\n  🔗 {url}\n  📝 {snippet[:100]}...")

    return f"Latest news in {city}:\n\n" + "\n\n".join(news_list)


TOOLS = [get_weather, get_news]
SYSTEM_PROMPT = "You are a helpful city assistant. Use tools to answer questions about weather and news for cities."


def extract_text(content) -> str:
    """
    Normalize a model message's .content into a plain string.

    Some providers (like Gemini via langchain-google-genai) return content
    as a list of content blocks — e.g.
    [{'type': 'text', 'text': '...', 'extras': {...}}] — instead of a plain
    string the way Mistral did. Without this, the raw Python structure gets
    printed/rendered instead of just the answer text.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                parts.append(block.get("text", ""))
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


# =========================
# 🧠 LLM Setup
# =========================
def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash")


# =========================
# 🛂 Human-in-the-loop approval (CLI only)
# =========================
@wrap_tool_call
def human_approval(request, handler):
    """Ask for human approval before every tool call (blocking — CLI use only)."""
    tool_name = request.tool_call["name"]
    confirm = input(f"Agent wants to call '{tool_name}'. Approve? (yes/no): ")
    if confirm.lower() != "yes":
        return ToolMessage(
            content="Tool call denied by user.",
            tool_call_id=request.tool_call["id"],
        )
    return handler(request)


def build_agent(with_cli_approval: bool = False):
    """
    Factory for the agent so both the CLI and the Streamlit UI can build
    their own instance with the middleware that suits their execution model.

    with_cli_approval=True   -> blocking input() approval (terminal only)
    with_cli_approval=False  -> no blocking middleware (safe for web apps)
    """
    middleware = [human_approval] if with_cli_approval else []
    return create_agent(
        get_llm(),
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=middleware,
    )


# =========================
# 💻 CLI entry point
# =========================
if __name__ == "__main__":
    agent = build_agent(with_cli_approval=True)

    print("CityPilot | type exit to quit")
    while True:
        user_input = input("You : ")
        if user_input.lower() == "exit":
            break

        result = agent.invoke({"messages": [{"role": "user", "content": user_input}]})
        print("bot : ", extract_text(result["messages"][-1].content))