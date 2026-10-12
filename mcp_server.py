"""
Your MCP server. ← UNIT 4, MILESTONE 1

Right now your tools only exist inside your own program. Nothing else can reach
them. MCP is an agreed shape you wrap a tool in so that anything speaking the
same protocol can call it — your agent today, a different agent tomorrow,
someone else's app after that.

This server offers two tools:

  • search_listings — moved onto MCP in Milestone 1.
  • compare_price   — moved onto MCP as unit 4 stretch 1.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers
"""

from mcp.server.fastmcp import FastMCP

from tools import search_listings as _search_listings_impl
from tools import compare_price as _compare_price_impl

# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Searches 40 secondhand clothing listings for items matching a free-text
    keyword description, such as "vintage graphic tee".
    `size` is optional: a size like "M", matched case-insensitively against the
    listing's size tokens, so "M" matches "M/L" and "S/M" but not "XL".
    `max_price` is optional: the highest price allowed, in US dollars, inclusive.
    Returns a list of listing dicts, best keyword match first and cheapest on
    ties. Each has id, title, description, category, style_tags, size, condition,
    price, colors, brand (often null), and platform.
    If nothing matches, returns an empty list [] rather than an error.
    """
    return _search_listings_impl(description, size, max_price)


@mcp.tool()
def compare_price(item: dict) -> str:
    """
    Compares one listing's price with the average price of the OTHER listings
    in the same category (e.g. "tops", "bottoms", "outerwear").
    `item` is a whole listing dict exactly as search_listings returns it; the
    fields used are id, title, category, and price (a number, in US dollars).
    Returns one sentence, e.g. "At $15.00, this is 32% below the average price
    for tops ($22.21)." Within 5% either way it says "about the same as".
    If no other listing shares the item's category, returns a sentence saying
    there is nothing to compare it against, rather than an error.
    """
    return _compare_price_impl(item)


if __name__ == "__main__":
    mcp.run()
