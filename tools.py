"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str
"""

import re

import config  # noqa: F401 — you'll use this in search_listings
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

_SIZE_SPLIT = re.compile(r"[\s/()]+")


def _size_tokens(size: str) -> set[str]:
    """Break a size string into lowercase tokens: 'M/L' -> {'m', 'l'}."""
    return {t for t in _SIZE_SPLIT.split(size.lower()) if t}


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    Matching rule (see README Tool Inventory for the full spec):
        - price: kept when listing price <= max_price (if given)
        - size: kept when the searched size token appears among the listing's
          size tokens (if given) — "M" matches "M/L" and "S/M", not "XL"
        - score: count of description keywords found in title + description +
          style_tags; zero-scoring listings are dropped
        - order: highest score first, then lowest price first on ties

    Returns an empty list when nothing matches — never None, never raises.
    """
    listings = load_listings()

    size_query = size.strip().lower() if size else None
    keywords = [w for w in re.findall(r"[a-z0-9]+", description.lower()) if w]

    scored: list[tuple[int, dict]] = []
    for listing in listings:
        if max_price is not None and listing["price"] > max_price:
            continue

        if size_query is not None:
            if size_query not in _size_tokens(listing["size"]):
                continue

        haystack = " ".join(
            [
                listing["title"],
                listing["description"],
                " ".join(listing["style_tags"]),
            ]
        ).lower()
        score = sum(1 for kw in keywords if kw in haystack)
        if score == 0:
            continue

        scored.append((score, listing))

    scored.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    With an empty wardrobe, returns general styling advice instead of raising
    or returning "".
    """
    items = wardrobe.get("items", [])

    if not items:
        prompt = (
            f"A user is considering buying this thrifted item:\n"
            f"- {new_item['title']} ({new_item['category']}), "
            f"colors: {', '.join(new_item['colors'])}, "
            f"style: {', '.join(new_item['style_tags'])}, "
            f"${new_item['price']:.2f}\n\n"
            f"They have no other wardrobe items logged yet. Suggest one or "
            f"two general outfit directions for this piece on its own — "
            f"what to pair it with in general terms (not specific items they "
            f"don't have)."
        )
        system = (
            "You are a thrifting stylist. Give concrete, wearable outfit "
            "ideas in 2-4 sentences. Do not invent specific items the user "
            "does not have."
        )
        return generate(prompt, system=system)

    wardrobe_lines = []
    for item in items:
        notes = f" — {item['notes']}" if item.get("notes") else ""
        wardrobe_lines.append(
            f"- {item['name']} ({item['category']}), "
            f"colors: {', '.join(item['colors'])}, "
            f"style: {', '.join(item['style_tags'])}{notes}"
        )

    prompt = (
        f"A user is considering buying this thrifted item:\n"
        f"- {new_item['title']} ({new_item['category']}), "
        f"colors: {', '.join(new_item['colors'])}, "
        f"style: {', '.join(new_item['style_tags'])}, "
        f"${new_item['price']:.2f}\n\n"
        f"Here is their existing wardrobe:\n"
        + "\n".join(wardrobe_lines)
        + "\n\nSuggest one or two outfits that combine the new item with "
        "specific pieces from their wardrobe above, naming each piece by "
        "name."
    )
    system = (
        "You are a thrifting stylist. Give concrete outfit combinations in "
        "2-4 sentences, naming specific wardrobe items by name. Do not invent "
        "items that are not listed."
    )
    return generate(prompt, system=system)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    If `outfit` is empty or whitespace, returns a descriptive message rather
    than raising or calling the model.
    """
    if not outfit or not outfit.strip():
        return (
            f"No outfit suggestion was available for "
            f"{new_item.get('title', 'this item')}, so no caption could be "
            f"written."
        )

    prompt = (
        f"Write a short social media caption for this thrifted find:\n"
        f"- Item: {new_item['title']}\n"
        f"- Price: ${new_item['price']:.2f}\n"
        f"- Platform: {new_item['platform']}\n"
        f"- Outfit idea: {outfit}\n\n"
        f"The caption should read like a real post, not a product "
        f"description. Mention the price and the platform once each, and be "
        f"specific about the vibe."
    )
    system = (
        "You write short, casual social media captions for thrifted fashion "
        "finds, 2-4 sentences, in a real human voice."
    )
    return generate(prompt, system=system)

# ── Tool 4 (stretch): compare_price ─────────────────────────────────────────

def compare_price(item: dict) -> str:
    """
    Compare an item's price against the average price of other listings in
    the same category.

    Args:
        item: a listing dict — the item to compare.

    Returns:
        A one-sentence comparison, e.g. "At $15.00, this is 32% below the
        average price for tops ($22.14)." If there are no other listings in
        the same category, returns a message saying there's nothing to
        compare it to.
    """
    listings = load_listings()
    same_category = [
        listing for listing in listings
        if listing["category"] == item["category"] and listing["id"] != item["id"]
    ]

    if not same_category:
        return (
            f"No other {item['category']} listings to compare "
            f"{item['title']} against."
        )

    avg_price = sum(listing["price"] for listing in same_category) / len(same_category)
    diff_pct = ((item["price"] - avg_price) / avg_price) * 100

    if diff_pct < -5:
        comparison = f"{abs(diff_pct):.0f}% below"
    elif diff_pct > 5:
        comparison = f"{diff_pct:.0f}% above"
    else:
        comparison = "about the same as"

    return (
        f"At ${item['price']:.2f}, this is {comparison} the average price "
        f"for {item['category']} (${avg_price:.2f})."
    )