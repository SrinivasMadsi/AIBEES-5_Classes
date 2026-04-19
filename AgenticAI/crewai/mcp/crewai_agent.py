"""
============================================================
FILE    : crewai_agent.py
PURPOSE : CrewAI Agent calling MCP Server using mcp library
RUN     : python mcp_server.py first, then python crewai_agent.py
============================================================
"""

import os
import asyncio
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from mcp.client.sse import sse_client
from mcp import ClientSession

load_dotenv()

llm = LLM(
    model="gemini/gemini-2.5-pro",
    api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

# ── Call MCP tool using mcp library's own SSE client ──────
"""
async means that the function is asynchronous and can be awaited.
sse_client is a context manager that connects to the MCP server's SSE(Server-Sent Events) endpoint.
ClientSession is used to interact with the MCP server, allowing us to call tools defined on the server.
The call_mcp_tool_async function connects to the MCP server, initializes a session, and calls a specified tool with given arguments. It then returns the result from the tool call.
"""
async def call_mcp_tool_async(tool_name: str, arguments: dict) -> str:
    """Calls MCP server using official mcp SSE client."""
    async with sse_client("http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments)
            if result.content:
                return result.content[0].text
            return "No result returned"

def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    # asyncio makes wait for the async function to complete and returns the result
    """Sync wrapper to call async MCP function from sync CrewAI tools."""
    return asyncio.run(call_mcp_tool_async(tool_name, arguments))


# ── Tools — logic lives in MCP server, called via URL ─────

@tool("Delivery Checker")
def check_delivery(pincode: str) -> str:
    """Checks if delivery is available for a given pincode."""
    return call_mcp_tool("check_delivery", {"pincode": pincode})

@tool("Menu Fetcher")
def get_menu(category: str) -> str:
    """Gets pizza menu items for a given category veg or non-veg."""
    return call_mcp_tool("get_menu", {"category": category})


# ── Agent ──────────────────────────────────────────────────
agent = Agent(
    role="Pizza Order Assistant",
    goal="Help customers check delivery availability and show pizza menu",
    backstory="You are a helpful pizza shop assistant at Domino's pizza shop.",
    tools=[check_delivery, get_menu],
    llm=llm
)

# ── Task ───────────────────────────────────────────────────
task = Task(
    description="""
        Customer request:
        Their pincode is {pincode}.
        They are interested in {category} pizzas.
        Check delivery availability and show the menu.
    """,
    expected_output="Delivery status and list of available pizzas in the category",
    agent=agent
)

# ── Crew ───────────────────────────────────────────────────
crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff(inputs={"pincode": "12345", "category": "non-veg"})

print("\n" + "="*50)
print("  RESULT")
print("="*50)
print(result)