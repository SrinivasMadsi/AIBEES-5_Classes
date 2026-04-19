"""
============================================================
FILE      : mcp_server.py
PURPOSE   : MCP Server — exposes pizza shop tools as MCP endpoints
            Run this file FIRST before running the CrewAI client
RUN       : python mcp_server.py
============================================================
"""

from mcp.server.fastmcp import FastMCP

# ── Create MCP Server ──────────────────────────────────────
mcp = FastMCP("Pizza Shop Tools")


# ── Tool 1: Check Delivery ─────────────────────────────────
@mcp.tool()
def check_delivery(pincode: str) -> str:
    """Checks if delivery is available for a given pincode."""
    available_pincodes = ["12345", "67890", "54321"]
    if pincode in available_pincodes:
        return f"Delivery is available for pincode {pincode}."
    else:
        return f"Sorry, delivery is not available for pincode {pincode}."


# ── Tool 2: Get Menu ───────────────────────────────────────
@mcp.tool()
def get_menu(category: str) -> str:
    """Gets pizza menu items for a given category — veg or non-veg."""
    menu = {
        "veg"    : ["Margherita - $5", "Farmhouse - $7", "Peppy Paneer - $8"],
        "non-veg": ["Pepperoni - $6", "Chicken Supreme - $8", "Meat Lovers - $10"]
    }
    items = menu.get(category.lower())
    if items:
        return f"Available {category} pizzas: " + ", ".join(items)
    else:
        return f"Category '{category}' not found. Try 'veg' or 'non-veg'."


# ── Run Server ─────────────────────────────────────────────
if __name__ == "__main__":
    print("="*50)
    print("  Pizza Shop MCP Server starting...")
    print("  Listening on: http://localhost:8000/sse")
    print("  Tools: check_delivery, get_menu")
    print("="*50)
    mcp.run(transport="sse")