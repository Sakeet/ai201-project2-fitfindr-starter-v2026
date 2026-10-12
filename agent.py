import re
import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card, compare_price
from generate import ModelUnavailable
from mcp_client import call_tool, MCPError

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "price_comparison": None,    # what compare_price returned (stretch)
        "error": None,               # set when the run ended early
    }

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.
    """
    session = new_session(query, wardrobe)
    iteration = 0

    # 1. Parse the query into description / size / max_price.
    iteration += 1
    trace.check_iterations(iteration)

    size_match = re.search(r"\bsize\s+([A-Za-z0-9/.]+)", query, re.I)
    size = size_match.group(1) if size_match else None

    price_match = re.search(
        r"(?:under|below|less than)\s*\$?\s*(\d+(?:\.\d+)?)", query, re.I
    )
    max_price = float(price_match.group(1)) if price_match else None

    description = query
    if size_match:
        description = description[: size_match.start()] + description[size_match.end():]
    if price_match:
        description = description[: price_match.start()] + description[price_match.end():]
    description = re.sub(r"\s+", " ", description).strip()

    session["parsed"] = {
        "description": description,
        "size": size,
        "max_price": max_price,
    }

    trace.step("parse_query", inputs=repr(query), returned=str(session["parsed"]))

    # SECOND BRANCH: no real description left to search on.
    if not description:
        session["error"] = (
            "Please describe what you're looking for — a size or a price "
            "alone isn't enough to search on."
        )
        return session

    # 2. Search.
    iteration += 1
    trace.check_iterations(iteration)

    try:
        results = call_tool("search_listings", {
            "description": description,
            "size": size,
            "max_price": max_price,
        })
    except MCPError as exc:
        session["error"] = f"The listing search couldn't be reached: {exc}"
        return session

    session["search_results"] = results

    trace.step(
        "search_listings (via MCP)",
        inputs=str({"description": description, "size": size, "max_price": max_price}),
        returned=(
            f"{len(results)} listings, prices {[r['price'] for r in results]}: "
            + ", ".join(r["title"] for r in results[:3])
        ),
    )

    # THIS IS THE BRANCH.
    if not results:
        session["error"] = (
            "No listings matched. Try raising the price limit, dropping the "
            "size filter, or using fewer or different keywords."
        )
        return session

    # 3. Pick the first result (best score, cheapest on ties).
    session["selected_item"] = results[0]
    trace.step(
        "select_item",
        inputs="first of search_results",
        returned=str({"id": session["selected_item"]["id"],
                      "title": session["selected_item"]["title"]}),
    )

    # 4. Suggest an outfit.
    iteration += 1
    trace.check_iterations(iteration)

    try:
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )
        trace.step(
            "suggest_outfit",
            inputs=str({"item_id": session["selected_item"]["id"],
                        "item": session["selected_item"]["title"],
                        "wardrobe_items": len(session["wardrobe"].get("items", []))}),
            returned=session["outfit_suggestion"],
        )
    except ModelUnavailable as exc:
        session["error"] = str(exc)
        return session

    # 5. Write the fit card.
    iteration += 1
    trace.check_iterations(iteration)

    try:
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )
        trace.step(
            "create_fit_card",
            inputs=str({"item": session["selected_item"]["title"], "outfit": "(from suggest_outfit)"}),
            returned=session["fit_card"],
        )
    except ModelUnavailable as exc:
        session["error"] = str(exc)
        return session

    # 6. Compare the price (stretch: fourth tool).
    iteration += 1
    trace.check_iterations(iteration)

    try:
        session["price_comparison"] = compare_price(session["selected_item"])
        trace.step(
            "compare_price",
            inputs=str({"item": session["selected_item"]["title"]}),
            returned=session["price_comparison"],
        )
    except ModelUnavailable as exc:
        session["error"] = str(exc)
        return session

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")
    print(f"  price:    {session['price_comparison']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )