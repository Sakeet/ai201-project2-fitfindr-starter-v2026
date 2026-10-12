"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

─────────────────────────────────────────────────────────────────────────────
HOW EACH CRITERION IS COUNTED (decided before the first run)

  Criterion 1 — scenario "matching query completes", 5 tries.
                A try PASSES if the run did not stop early and the session
                has a non-empty fit_card.

  Criterion 2 — scenario "impossible query stops early", 5 tries.
                A try PASSES if the run stopped early with an error message
                naming what to change, and the trace shows no suggest_outfit
                step.

  Criteria 3, 4, 5 — the five "item N of 5" scenarios below. Each one is a
                different matching query with an "under $X" phrase, so they
                give five different items. For these three criteria,
                Try N = item N of 5, judged on its FIRST run. run_eval.py
                runs each one five times; the other four runs are extra
                evidence, and any failure in them is reported too.

    Criterion 3 PASSES if the id in the select_item trace step equals the
                item_id in the suggest_outfit trace step.
    Criterion 4 PASSES if the fit card mentions the item's price AND its
                platform (the selected_item line shows both).
    Criterion 5 PASSES if every price in the search_listings trace step is
                <= the X in the query.
─────────────────────────────────────────────────────────────────────────────
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },

    # Five different matching queries, each with "under $X".
    # Judged against criteria 3, 4 and 5 (see the counting rule above).
    {
        "name": "item 1 of 5 (criteria 3, 4, 5)",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "item 2 of 5 (criteria 3, 4, 5)",
        "query": "silk slip dress under $40",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # Size before price on purpose: the trace in Milestone 2 showed the
        # parser leaves "under $X" in the description for queries like this.
        "name": "item 3 of 5 (criteria 3, 4, 5)",
        "query": "denim jacket size M under $50",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "item 4 of 5 (criteria 3, 4, 5)",
        "query": "cargo pants under $35",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        "name": "item 5 of 5 (criteria 3, 4, 5)",
        "query": "501 jeans under $45",
        "wardrobe": "example",
        "criterion": 3,
    },

    # The empty-wardrobe failure mode was triggered by hand in Milestone 2
    # (see README, Loop Trace). Left out here to keep the run's model calls
    # down; it isn't one of the five criteria.
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems