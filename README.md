# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr is a thrifting agent. A user types what they want in plain language — for example "vintage graphic tee under $30, size M" — and the agent searches a file of 40 secondhand listings, picks the best match, suggests one or two outfits that use pieces from the user's own wardrobe, and writes a short caption they could post about the find. If nothing matches, the agent stops before it suggests an outfit and tells the user what to change, rather than guessing.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the 40 listings for items that match a free-text description, optionally narrowed by size and a price ceiling, and returns the best matches first.
- **Inputs:** `description` (str) — keywords describing what the user wants; `size` (str or None, default None) — a size to filter by; `max_price` (float or None, default None) — the highest price allowed, inclusive.
- **Returns:** A list of listing dicts, at most `config.SEARCH_RESULT_LIMIT` of them. Each dict is a whole listing with the fields `id` (str), `title` (str), `description` (str), `category` (str), `style_tags` (list of str), `size` (str), `condition` (str), `price` (float), `colors` (list of str), `brand` (str, or `None` for most listings), and `platform` (str). How it decides what to include and in what order: a listing is kept when `price <= max_price` (if `max_price` is given); the listing's `size` is lowercased and split on whitespace, `/`, `(` and `)` into tokens, and kept when the searched size (lowercased) equals one of those tokens — so `M` matches `M`, `M/L` and `S/M`, but not `XL`; listings are scored by how many description keywords appear in the title, description and style tags, zero-scoring listings are dropped, and the rest are sorted by score (highest first), then by price (lowest first) to break ties.
- **When it has nothing:** Returns an empty list `[]` — never `None` and never an exception. The planning loop branches on this.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the new item, naming pieces the user already owns.
- **Inputs:** `new_item` (dict) — one listing dict, exactly as `search_listings` returned it; `wardrobe` (dict) — a dict with an `items` key holding a list of wardrobe items, where each item has `id` (str), `name` (str), `category` (str), `colors` (list of str), `style_tags` (list of str), and `notes` (str or `None`).
- **Returns:** A non-empty string containing one or two outfit suggestions, each naming specific wardrobe pieces by their `name`.
- **When it has nothing:** When `wardrobe["items"]` is an empty list, it returns a non-empty string of general styling advice for the new item on its own, with no wardrobe pieces named. It never returns `""` and never raises because the wardrobe is empty.

### `create_fit_card`

- **What it does:** Asks the model to write a short caption, in the voice of a social media post, about the find.
- **Inputs:** `outfit` (str) — the string returned by `suggest_outfit`; `new_item` (dict) — the same listing dict that went into `suggest_outfit`.
- **Returns:** A string of two to four sentences that mentions the item, its price and its platform once each, and is specific about the vibe. Because it comes from the model, the wording can differ from run to run for the same input.
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns a descriptive message string saying there was no outfit to write a caption about, without calling the model and without raising. The planning loop never reaches this case on its own, because it only calls this tool after `suggest_outfit` has returned.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, set `session["error"]` to a message naming what the user could change (raise the price limit, drop the size, or use fewer or different keywords) and return the session without calling `suggest_outfit` or `create_fit_card`. Otherwise, store the results in `session["search_results"]`, put the first result (the best score, and the cheapest when scores tie) in `session["selected_item"]`, and go on to `suggest_outfit`, then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** With regular expressions. A price ceiling is read from phrases like "under $30", "below 30" or "less than $30" and becomes a float `max_price`; a size is read from "size M" and becomes the `size` string; whatever is left of the query after those two phrases are removed becomes the `description`. If a query has no price or no size, that value is `None`, and `search_listings` skips that filter.

**What moves through the session:** `query` is stored first, then `parsed` (description, size, max_price), then `search_results`, then `selected_item`, then `outfit_suggestion`, then `fit_card`. `wardrobe` is stored at the start. `error` stays `None` unless the run stops early. Each tool reads its inputs back out of the session rather than receiving them directly: `suggest_outfit` gets `session["selected_item"]` and `session["wardrobe"]`, and `create_fit_card` gets `session["outfit_suggestion"]` and `session["selected_item"]`.

---

## Sample Run

**One full query**

```
$ python agent.py

=== A query the data can match ===
  found:    Mesh Long-Sleeve Top — Black — $15.0 on depop
  outfit:   Layer the mesh long-sleeve top directly over the white ribbed tank top, and pair them with the baggy straight-leg jeans secured by the brown leather belt. Finish this grunge-meets-streetwear look by stepping into the black combat boots and accessorizing with the black crossbody bag.

            Alternatively, create a contrasting y2k texture play by layering the black cropped zip hoodie open over the mesh long-sleeve top, paired with the wide-leg khaki trousers. Complete the outfit with the chunky white sneakers and the black crossbody bag.
  fit card: Literally obsessed with this black mesh long-sleeve for only $15. Throw it over a white tank with some baggy denim and combat boots for the ultimate 90s grunge moment, or go full Y2K with some khaki trousers. Already listed this bad boy on Depop if you need it in your rotation! ✨
  price:    At $15.00, this is 32% below the average price for tops ($22.21).

=== A query it can't ===
  stopped: No listings matched. Try raising the price limit, dropping the size filter, or using fewer or different keywords.
  fit_card is None — it should still be None here
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[8 matching listing dicts returned, each with a title containing "tee" or a tee-related style tag, all priced at or under $30, sorted by keyword score then price — e.g. {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'price': 15.0, 'platform': 'depop', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], ...}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Pair the Vintage Levi's 501 Jeans with the fitted White ribbed tank top tucked in, layered under the slightly cropped Vintage black denim jacket, and finish the look with the chunky white sneakers. For a streetwear edge, wear the Vintage Levi's 501 Jeans with the Black cropped zip hoodie and lace-up Black combat boots.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Nothing beats the ultimate 90s slouch of a broken-in pair of vintage 501s. Just add your favorite beat-up white sneakers and you've got that effortless off-duty model vibe locked down. Snag these medium wash beauties on my Depop right now for just $38.
```

---

## Stretch Feature: A Second Branch (declared before building)

**Declared:** In addition to the required empty-search branch, I added a second branch that checks whether anything meaningful is left to search on *before* calling `search_listings` at all.

**The condition:** After stripping out the size and price phrases from the query, if the remaining `description` is empty — e.g. a query like "under $30" with no actual item description — the loop stops immediately and asks the user to describe what they're looking for, without ever calling `search_listings`.

**Why this is a different branch from the required one:** The required branch handles `search_listings` running and legitimately finding nothing. This branch catches a different failure earlier — a query with no real content to search on in the first place. The two are observably different: in the required branch, `session["search_results"]` holds the (empty) return value of a real search call; in this branch, `search_listings` is never invoked, so there was nothing to search with.

**Run showing the branch taken:**

```
$ python -c "from agent import run_agent; from utils.data_loader import get_example_wardrobe; s = run_agent('under `$30', get_example_wardrobe()); print(s['error']); print('search_results:', s['search_results']); print('fit_card:', s['fit_card'])"
Please describe what you're looking for — a size or a price alone isn't enough to search on.
search_results: []
fit_card: None
```

---

## Stretch Feature: A Fourth Tool (declared before building)

**Declared:** `compare_price(item: dict) -> str` — compares the selected item's price against the average price of other listings in the same category, and returns a one-sentence comparison.

**What it returns:** A string like "At $15.00, this is 32% below the average price for tops ($22.21)." If there are no other listings in the same category, it returns a message saying there's nothing to compare the item against, rather than raising or dividing by zero.

**Where it's wired in:** `agent.py::run_agent`, as a sixth step right after `create_fit_card`, storing its result in `session["price_comparison"]`.

**Run showing the tool being called:** see the `price:` line in the Sample Run above — it's produced by this tool, called automatically as the final step of the happy path.

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I was working in what turned out to be a stale, nested clone of this repo — in a folder with no `.venv` and a commit history that didn't match what I'd actually pushed. I asked Claude to help me figure out why `pip show google-genai` said the package wasn't found even though `test.py` had passed earlier.
- *What came back:* Claude had me run `git remote -v` and `git log --oneline -5` in that folder. The remote was correct, but the log showed commits like "initial commit" and "updates" instead of my real Milestone 2 commit — meaning this was a different, out-of-date checkout of the same repo, not the one I'd been working in.
- *What I changed:* I ran `git pull` to bring that folder up to date, rebuilt `.venv` there, reinstalled `requirements.txt`, and copied a fresh `.env` with my API key. After that, `test.py` passed 10/10 and the tool tests worked.

**Moment 2**

- *What I asked for:* After wiring up `run_agent()` in `agent.py`, running `python agent.py` produced zero output and exited with code 0 — no error, no print statements, nothing. I asked Claude to help me figure out why.
- *What came back:* Claude walked me through checking, in order: whether the file was actually saved (it was), whether the module imported cleanly (it did, with `python -c "import agent"`), and finally the literal last 25 lines of the file on disk with `Get-Content agent.py -Tail 25`. That showed the entire `_show()` function and the `if __name__ == "__main__":` block had been deleted — they weren't in the file at all, which explained why nothing printed when the script ran directly.
- *What I changed:* I re-added `_show()` and the `__main__` block at the bottom of `agent.py`. I also found, while doing that, that `new_session()` was missing entirely (an earlier edit had dropped it too), so I added that back as well. After the fix, `python agent.py` ran both example paths correctly — the happy path completing all three tools, and the empty-search path stopping early with `fit_card` still `None`.

**Unit 4 — Moment 3**

- *What I asked for:* At the start of unit 4, `python app.py ask` printed "The planning loop isn't built yet" and every tool in my `tools.py` was a stub, even though I had finished unit 3. I asked Claude what to do, and we started rebuilding the tools. When `git push` was then rejected, I asked Claude why.
- *What came back:* Claude had me run `git fetch` and `git log --oneline main..origin/main`. That listed nine commits on GitHub that my local folder didn't have, including "Milestone 4: build and test all three tools" and "Milestone 5: wire the planning loop". My finished unit 3 work was on GitHub; this folder was an out-of-date copy. Claude told me not to force-push or rebase, because that could overwrite the history that proves my criteria came before my results.
- *What I changed:* I saved the rebuilt work on a backup branch (`git branch backup-oct11`), then ran `git reset --hard origin/main` so my folder matched what I'd submitted. Everything in unit 4 was then done on the agent I actually submitted in unit 3, as the assignment requires.

**Unit 4 — Moment 4**

- *What I asked for:* After adding `trace.step()` calls, the trace showed dicts only as their key names ("dict with keys: description, size, max_price"). Claude suggested passing the inputs as strings so the actual values would print, and I reran the empty-search query with `--trace`.
- *What came back:* The trace now showed `out: {'description': 'designer ballgown under $5', ...}`. Claude pointed out that "under $5" should not have been in the description, and explained why: the parser cut the size phrase first, then cut the price phrase using positions measured on the original query. It suggested not fixing it yet, but writing it down and seeing whether the test run showed it mattering.
- *What I changed:* Nothing at first. I put the scenario "denim jacket size M under $50" (size before price) into `scenarios.py` on purpose. The before-run showed it returning a mesh top. A direct call to `search_listings` with and without the word "under" proved the leaked word was the cause. That became my one improvement: cutting the later match first. In the after-run the same query returned a denim vest.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Unit 4 Stretch Features (declaration)

**A note on timing, so the commit history reads correctly.** I wrote this declaration before building any of the three stretch features, and meant to commit it on its own first. That commit didn't happen: when I ran `git commit` for it, git reported "nothing to commit" because I hadn't pasted the new README into the file, and I didn't notice. The stretch code was then committed first: stretch 1 and 2 in `b56b2de`, stretch 3 in the "Stretch 3: search ignores filler words…" commit. This declaration only reached the repository in the same commit as the results write-up further down. `git log -S "Stretch Features (declaration)"` will show that. I'm stating it plainly rather than rewriting the history. Whether the stretch features count under the "declared before building" rule is the grader's call. The text of the declaration below is unchanged from what I wrote before building.

Each feature gets a results section further down, saying what it changed.

**Stretch 1: A second tool moved onto MCP.** I'll register `compare_price` in `mcp_server.py` alongside `search_listings`, with a description and typed input, and change `agent.py::run_agent` to call it through `call_tool("compare_price", ...)` instead of directly. The trace step will be labelled `compare_price (via MCP)`, so a run shows it going through the MCP path. I picked `compare_price` because, like `search_listings`, it doesn't call a model.

**Stretch 2: Retry with looser constraints.** When `search_listings` returns nothing *and* the query had a size, `run_agent` will search once more with the same description and price but **no size filter**. If the retry finds something, the agent continues and tells the user which constraint it dropped ("No listings in size XXS — showing other sizes instead."). If the retry also finds nothing, it stops as before, and the message says the size filter was already dropped. It retries at most once, and only the size is dropped, never the price. The trace will show both searches, labelled so the dropped constraint is visible. I'll add a diagnostic scenario to `scenarios.py` with a size that doesn't exist for an item that does, so the run log shows the retry.

**Stretch 3: A second measured improvement.** From my diagnosis and "What's Still Broken" #1: `tools.py::search_listings` counts every word of the description as a keyword, including filler like "for" and "looking", and matches with a substring test, so "under" matches "underneath" and "tee" matches "streetwear". I'll change it to ignore common filler words and match whole words. To measure it the way I measured the first improvement, I'll do a full run **before** this change (run #3, after stretches 1 and 2 are in) and a full run **after** it (run #4), with the same scenarios. I'll add a diagnostic scenario using the agent's own example query, "looking for a vintage graphic tee under $30", which picked a Mesh Long-Sleeve Top in my unit 3 Sample Run. Run #4's log will be in the same table format, and I'll say whether the change helped, including if it made anything worse.

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

Produced by `python run_eval.py --label before` (`run_eval.py::main`), caching off, temperature 0.9. Full output: `results/run_2026-10-11_2133_before.md`.

**How the tries are counted** (written into `scenarios.py` and committed before the run):

- Criteria 1 and 2 each have one scenario, run 5 times. Each run is one try.
- Criteria 3, 4 and 5 are about five *different* items, so they share five scenarios ("item 1 of 5" … "item 5 of 5"), each a different matching query with an "under $X" phrase. For these, **Try N = item N's first run**. `run_eval.py` runs each item five times; I checked the other four runs too and report anything they show.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item stays the same across tool calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item's price and platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The agent respects the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Items used for criteria 3–5: (1) "vintage graphic tee under $30" → Y2K Baby Tee, `lst_002`; (2) "silk slip dress under $40" → 90s Silk Slip Dress, `lst_013`; (3) "denim jacket size M under $50" → Mesh Long-Sleeve Top, `lst_017`; (4) "cargo pants under $35" → Low-Rise Cargo Pants, `lst_011`; (5) "501 jeans under $45" → Vintage Levi's 501 Jeans, `lst_001`.

**Real output from one try per criterion.** All of it comes from `run_eval.py::run_once`, which calls `agent.py::run_agent`. The trace lines come from the `trace.step()` calls in `agent.py::run_agent`, and the fit cards from `tools.py::create_fit_card`.

*Criterion 1, "matching query completes", Try 1:*

```
- stopped early: no
- selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
- search_results: 10

Fit card:
Found the ultimate 2000s butterfly tee and honestly, I'm never taking it off. Throw it on with baggy denim and chunky sneakers for that effortless off-duty model look. Grab it on my Depop right now for just $18 before I change my mind and keep it! 🦋✨
```

*Criterion 2, "impossible query stops early", Try 1:*

```
- stopped early: yes — No listings matched. Try raising the price limit, dropping the size filter, or using fewer or different keywords.
- selected_item: (none)
- search_results: 0

[1] parse_query
      in:  'designer ballgown size XXS under $5'
      out: {'description': 'designer ballgown under $5', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  {'description': 'designer ballgown under $5', 'size': 'XXS', 'max_price': 5.0}
      out: 0 listings, prices []:
```

*Criterion 3, "item 4 of 5", Try 1:*

```
[3] select_item
      in:  first of search_results
      out: {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki'}
[4] suggest_outfit
      in:  {'item_id': 'lst_011', 'item': 'Low-Rise Cargo Pants — Khaki', 'wardrobe_items': 10}
```

*Criterion 4, "item 4 of 5", Try 1* (price $27.0, platform poshmark):

```
Can we talk about these khaki low-rise cargos? Found them for just $27 on Poshmark and honestly, they're the ultimate 90s skater-girl dream. Just throw on a basic ribbed tank, chunky sneakers, and a vintage jacket and you've got that effortless off-duty model vibe totally locked down.
```

*Criterion 5, "item 2 of 5", Try 1* (ceiling $40):

```
[2] search_listings (via MCP)
      in:  {'description': 'silk slip dress', 'size': None, 'max_price': 40.0}
      out: 4 listings, prices [30.0, 12.0, 28.0, 38.0]: 90s Silk Slip Dress — Floral, Midi Length, Leather Belt — Brown, …
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | All 5 runs of "vintage graphic tee under $30" ended with `stopped early: no` and a non-empty fit card. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | All 5 runs stopped with the "No listings matched…" message, and every trace ends at `[2] search_listings`, with no `suggest_outfit` step. |
| 3 | The selected item stays the same across tool calls | 5 of 5 | MET (5/5) | For each of the 5 items, the `id` in the `select_item` trace step equals the `item_id` in the `suggest_outfit` step (`lst_002`, `lst_013`, `lst_017`, `lst_011`, `lst_001`). |
| 4 | The fit card names the item's price and platform | 4 of 5 | MET (5/5) | Each of the 5 fit cards contains the item's price ($18, $30, $15.00, $27, $38) and its platform (Depop ×4, Poshmark ×1), checked against the `selected_item` line. |
| 5 | The agent respects the price ceiling | 5 of 5 | MET (5/5) | In each `search_listings` trace step, every price in the list is ≤ the query's X (max 26 ≤ 30, 38 ≤ 40, 45 ≤ 50, 32 ≤ 35, 38 ≤ 45). |

**Diagnoses**

**I missed nothing, and my targets were too low.** Every criterion was met at 5/5, including the two whose target was 4 of 5. The extra runs agree: across all 30 runs that reached a model, every id matched, every fit card named its price and platform, and every price was under its ceiling. But the run also shows a real failure that no criterion caught.

**What no criterion caught: the agent returned the wrong kind of item.** "denim jacket size M under $50" returned a **Mesh Long-Sleeve Top** in all 5 runs. It passed criteria 3, 4 and 5 anyway, because none of them checks that the item is what the user asked for. Criterion 1 is the one I'd tighten: "returns a fit card" only checks that the loop finished, not that it found the right thing. A tighter version: *for 5 matching queries that name a kind of item, the selected item's title or category is that kind of item, in at least 4 of 5 tries.*

**Diagnosis of the wrong item.** Two places, one chain:

1. **The loop's parse step** (`agent.py::run_agent`). The query has a size *before* a price. `run_agent()` cuts the size phrase out first, then cuts the price phrase using positions that `re.search` measured on the *original* query. Removing the size has already shifted the text left, so the second cut lands in the wrong place and leaves "under" behind. The trace shows it: `out: {'description': 'denim jacket under', 'size': 'M', 'max_price': 50.0}`. The same bug turns "designer ballgown size XXS under $5" into the description `'designer ballgown under $5'`.
2. **The search tool's scoring** (`tools.py::search_listings`). It counts every word of the description as a keyword, with no list of filler words to ignore, and matches with a substring test (`kw in haystack`). So the leaked "under" scores a point for the Mesh Long-Sleeve Top, whose description says "layering **under** a graphic tee", though it contains neither "denim" nor "jacket". It ties with the denim items on score, and the tie-break (cheapest first) puts it first at $15.

I confirmed which link matters by calling the search tool directly with and without the leaked word:

```
$ python -c "from tools import search_listings as s; print([r['title'] for r in s('denim jacket', 'M', 50.0)]); print([r['title'] for r in s('denim jacket under', 'M', 50.0)])"
['Denim Vest — Medium Wash, Studded', 'Shacket — Olive Canvas', '90s Track Jacket — Navy/White Stripe']
['Mesh Long-Sleeve Top — Black', 'Denim Vest — Medium Wash, Studded', 'Shacket — Olive Canvas', '90s Track Jacket — Navy/White Stripe']
```

Without "under", the mesh top isn't returned at all. With it, the mesh top comes first. So for this query the leaked word is the entire cause. The pattern: both links are the same weakness, filler words in the description being treated as meaningful. The same thing explains my unit 3 Sample Run, where "looking **for** a vintage graphic tee" also picked the mesh top ("Great **for** layering").

**One more thing the run showed: a model error, handled.** Item 1, run 4 (not one of the counted tries) stopped with `Couldn't reach the model: 500 INTERNAL`. That's an error on the model service's side, not in my code. The agent caught it as `ModelUnavailable` in `agent.py::run_agent` and stopped with a message instead of crashing. It's also why the run made 59 model calls instead of 60. If it had happened in a counted try for criterion 1, that try would have been a FAIL, which is the kind of thing the 4-of-5 target was there to allow for.


---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

Produced by `trace.step()` calls in `agent.py::run_agent`, one after each step, printed by `python app.py ask '...' --trace`. Step `[2]` is the MCP call: `run_agent()` calls `search_listings` through `mcp_client.call_tool`, not directly.

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace
[1] parse_query
     in:  'vintage graphic tee under $30'
     out: {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
[2] search_listings (via MCP)
     in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
     out: 10 listings: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg St…
[3] suggest_outfit
     in:  {'item': 'Y2K Baby Tee — Butterfly Print', 'wardrobe_items': 10}
     out: Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans and the chunky white sneakers for a …
[4] create_fit_card
     in:  {'item': 'Y2K Baby Tee — Butterfly Print', 'outfit': '(from suggest_outfit)'}
     out: Found the ultimate butterfly baby tee and I'm literally obsessed. Perfect fit for that effortless 2000s mall r…
[5] compare_price
     in:  {'item': 'Y2K Baby Tee — Butterfly Print'}
     out: At $18.00, this is 18% below the average price for tops ($22.00).

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the Y2K Baby Tee — Butterfly Print with the baggy straight-leg jeans and the chunky white sneakers for a classic Y2K streetwear look. Layer the slightly cropped Vintage black denim jacket on top and accessorize with the black crossbody bag.

  Fit card: Found the ultimate butterfly baby tee and I'm literally obsessed. Perfect fit for that effortless 2000s mall rat aesthetic, especially styled with baggy denim and chunky kicks. Grab it on my Depop for just $18 before I change my mind and keep it.

0 model calls this session, 2 served from cache
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
     in:  'designer ballgown size XXS under $5'
     out: {'description': 'designer ballgown under $5', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
     in:  {'description': 'designer ballgown under $5', 'size': 'XXS', 'max_price': 5.0}
     out: 0 listings:

  No listings matched. Try raising the price limit, dropping the size filter, or using fewer or different keywords.

0 model calls this session
```

The empty-search trace stops after step `[2]`: the branch in `run_agent()` returns before `suggest_outfit`, so no model is called. The happy path runs all five steps.

**What the trace showed that I hadn't seen before.** In the empty-search run, `parse_query` read the size (`XXS`) and the price (`5.0`) correctly, but left `under $5` in the description. `run_agent()` cuts the size phrase out of the query first, and then cuts the price phrase using positions that `re.search` measured on the *original* query. Because removing the size has already shifted the text to the left, those positions point past the end of the shorter string, so nothing gets removed. This happens whenever a query has a size before a price. I haven't changed it here. It's a candidate for my one improvement, depending on what the test run shows. *(It became my improvement in Milestone 5; see The Improvement.)*

**Failure modes, triggered on purpose**

| Failure | How I triggered it | What the agent said | Handler needed? |
|---|---|---|---|
| Empty search | `python app.py ask 'designer ballgown size XXS under $5'` | "No listings matched. Try raising the price limit, dropping the size filter, or using fewer or different keywords." | No. The empty-search branch in `agent.py::run_agent` already sets this message and stops before `suggest_outfit`; `app.py::_ask_one` prints it. |
| Empty wardrobe | `python app.py ask 'vintage graphic tee under $30' --empty-wardrobe` | General styling advice for the Y2K Baby Tee (low-rise cargo pants and chunky platform sneakers, or a tiered midi skirt with a beaded shoulder bag and strappy sandals), with no wardrobe pieces named. No crash, no empty string. | No. `tools.py::suggest_outfit` already handles an empty `wardrobe["items"]`. |
| Model unavailable | Changed one character of `GEMINI_API_KEY` in `.env`, then ran a query I hadn't asked before: `python app.py ask 'black leather jacket under $60'` | "The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com." No stack trace and no hang. | No. `generate.py` raises `ModelUnavailable` with that message, and `agent.py::run_agent` catches it and puts it in `session["error"]`. |

All three already produced a message I'd show a user, so I didn't add a new handler. The only error-handling change in this unit is the one from the MCP move: the search step now catches `MCPError`, the failure that can actually happen there.

**On the MCP move:**

*What changed in the code.* `search_listings` is now registered as an MCP tool in `mcp_server.py`, using FastMCP. Its description is written for an agent that can't see my code. It says what the tool searches, how `size` matching works ("M" matches "M/L" and "S/M" but not "XL"), that `max_price` is in US dollars and inclusive, which fields each returned listing has, and that it returns an empty list `[]` rather than an error when nothing matches. The input types (`description: str`, `size: str | None`, `max_price: float | None`) are the same as in my Tool Inventory. `python mcp_client.py` lists the tool with all three inputs, `size` and `max_price` marked optional.

In `agent.py::run_agent`, the direct call `search_listings(description, size=size, max_price=max_price)` is now `call_tool("search_listings", {"description": ..., "size": ..., "max_price": ...})` from `mcp_client.py`. I also changed the `except` around that call from `ModelUnavailable` to `MCPError`. `search_listings` never calls the model, so `ModelUnavailable` could never be raised at that step. The failure that can actually happen there now is the MCP server not starting or refusing the call, and that shows up as `MCPError`. The other tools (`suggest_outfit`, `create_fit_card`, `compare_price`) are still called directly.

*What behaved differently.* The results didn't change. After the move, `python agent.py` found the same Mesh Long-Sleeve Top — Black, $15 on Depop, as the Sample Run above (recorded before the move), and the ballgown query still stopped with `fit_card` as `None`. `python app.py ask 'vintage graphic tee under $30'` returned the Y2K Baby Tee — Butterfly Print, $18 on Depop, the same as before the move. The only visible difference is speed: each run is slightly slower, because `call_tool` starts the server, makes the call, and shuts the server down every time.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One thing, in the parse step of `agent.py::run_agent`. Both the size match and the price match are found on the original query. The old code cut the size phrase out first and then cut the price phrase using its original positions, which were wrong by then. The new code cuts the two phrases **in reverse order of position, the later one first**. Removing text near the end of a string doesn't shift anything before it, so the earlier match's positions are still correct when it's cut. The change is five lines (commit `458b1ec`, "Milestone 5: fix parser…"). Nothing else in the agent, the tools or the scenarios changed between the two runs.

```python
# before
description = query
if size_match:
    description = description[: size_match.start()] + description[size_match.end():]
if price_match:
    description = description[: price_match.start()] + description[price_match.end():]

# after
description = query
matches = [m for m in (size_match, price_match) if m]
for match in sorted(matches, key=lambda m: m.start(), reverse=True):
    description = description[: match.start()] + description[match.end():]
```

**Which failure it was meant to fix:** The one in my diagnosis. For "denim jacket size M under $50" the word "under" leaked into the description, matched the Mesh Long-Sleeve Top's "layering under a graphic tee", and made a top the best match for a denim jacket query in 5 of 5 runs. No criterion caught it (see Verdicts and Diagnoses), so I measured it directly: the item selected for that query, in the same "item 3 of 5" scenario, before and after.

### Run Log — After

Produced by `python run_eval.py --label after` (`run_eval.py::main`), with the same scenarios, the same counting rule, caching off and temperature 0.9. Full output: `results/run_2026-10-11_2221_after.md`.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item stays the same across tool calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item's price and platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The agent respects the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Items for criteria 3–5 after the fix: `lst_002`, `lst_013`, **`lst_038`** (was `lst_017`), `lst_011`, `lst_001`. Item 3's price ceiling still holds: `prices [27.0, 33.0, 45.0]`, all ≤ 50.

**Before and after, side by side**

| | Before | After |
|---|---|---|
| Criteria met | 5 of 5 (all at 5/5) | 5 of 5 (all at 5/5) |
| "denim jacket size M under $50": description sent to search | `'denim jacket under'` | `'denim jacket'` |
| "denim jacket size M under $50": item selected | Mesh Long-Sleeve Top, `lst_017` (tops), 5 of 5 runs | Denim Vest — Medium Wash, Studded, `lst_038` (outerwear), 5 of 5 runs |
| "designer ballgown size XXS under $5": description sent to search | `'designer ballgown under $5'` | `'designer ballgown'` |
| Model calls in the run | 59 (one 500 INTERNAL error from the model service) | 60 (no errors) |

The after-run trace for item 3, Try 1:

```
[1] parse_query
      in:  'denim jacket size M under $50'
      out: {'description': 'denim jacket', 'size': 'M', 'max_price': 50.0}
[2] search_listings (via MCP)
      in:  {'description': 'denim jacket', 'size': 'M', 'max_price': 50.0}
      out: 3 listings, prices [27.0, 33.0, 45.0]: Denim Vest — Medium Wash, Studded, Shacket — Olive Canvas, 90s Track Ja…
[3] select_item
      in:  first of search_results
      out: {'id': 'lst_038', 'title': 'Denim Vest — Medium Wash, Studded'}
```

**Did it help, and how do I know:** Yes, for the failure it targeted, and it broke nothing. In the before-run, the denim jacket query picked a mesh top in 5 of 5 runs. In the after-run, it picked a denim vest in 5 of 5 runs, and the trace shows the description now arrives at the search tool without "under". All five criteria stayed at 5/5, so the fix didn't cause a regression anywhere they measure. What the criterion table does **not** show is the improvement itself: every row reads 5/5 in both runs. That's the same weakness I diagnosed, since none of my criteria checks whether the item matches what was asked for. I had to measure the fix with the before/after comparison above instead of with a criterion.

It's also only a partial fix. The data has no denim *jacket* in size M under $50, so a denim vest is a reasonable closest match. But it ranks first only because "denim" matches and it's the cheapest. The search tool still can't tell a jacket from a vest. (See What's Still Broken.)


---

## Stretch Results

Two more full runs, with the same five criteria, the same counting rule, caching off and temperature 0.9, plus two diagnostic scenarios added to `scenarios.py` for the stretch features:

- **Run #3**, `results/run_2026-10-11_2250_stretch-before.md`: after stretches 1 and 2, **before** stretch 3.
- **Run #4**, `results/run_2026-10-11_2309_stretch-after.md`: after stretch 3. Nothing else changed between #3 and #4.

### Stretch 1: `compare_price` moved onto MCP

**What changed:** `compare_price` is registered in `mcp_server.py` next to `search_listings`, with its own description (what it compares, the `item` input and which fields it uses, the one-sentence return, and the "nothing to compare" case) and a typed input `item: dict`. In `agent.py::run_agent`, step 6 now calls `call_tool("compare_price", {"item": session["selected_item"]})` instead of calling the function directly. An `MCPError` there is recorded in `session["price_comparison"]` rather than ending the run, so a failed price comparison doesn't throw away an outfit and fit card that were already made. `suggest_outfit` and `create_fit_card` are still called directly.

**The server offers both tools** (`python mcp_client.py`):

```
  search_listings
    Searches 40 secondhand clothing listings for items matching a free-text
    keyword description, such as "vintage graphic tee". Common filler words
    ("for", "looking", "a", "under", ...) are ignored, and keywords match
    whole words only.
    ...
    - description: string
    - size: string  (optional)
    - max_price: number  (optional)

  compare_price
    Compares one listing's price with the average price of the OTHER listings
    in the same category (e.g. "tops", "bottoms", "outerwear").
    ...
    - item: object
```

**A run going through the MCP path** (run #4, "matching query completes", Try 1):

```
[2] search_listings (via MCP)
      in:  {'description': 'vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 listings, prices [18.0, 19.0, 24.0, 15.0, 26.0, 12.0, 14.0, 16.0, 18.0, 20.0]: Y2K Baby Tee — Butterfly Pri…
...
[6] compare_price (via MCP)
      in:  {'item': 'Y2K Baby Tee — Butterfly Print'}
      out: At $18.00, this is 18% below the average price for tops ($22.00).
```

**Did anything behave differently?** No. The comparison sentences are the same as when `compare_price` was called directly (e.g. "At $18.00, this is 18% below the average price for tops ($22.00)." in both the after-run and run #4). It just takes a little longer, because each call starts the server.

### Stretch 2: Retry with looser constraints

**What changed:** In `agent.py::run_agent`, when `search_listings` returns nothing *and* the query had a size, the agent searches once more with the same description and price but `size: None`. Only the size is dropped, never the price, and it retries at most once. If the retry finds something, `session["relaxed"]` records it and `app.py` shows the user `Note: No listings in size XXS, so these are other sizes.` above the result. If the retry also finds nothing, the error says so: "No listings matched, even after dropping the size filter (size XXS)…".

**The run log showing the retry and the dropped constraint** (run #3, diagnostic scenario "denim jacket size XXS under $50", Try 1; the same in all 10 runs of #3 and #4):

```
[1] parse_query
      in:  'denim jacket size XXS under $50'
      out: {'description': 'denim jacket', 'size': 'XXS', 'max_price': 50.0}
[2] search_listings (via MCP)
      in:  {'description': 'denim jacket', 'size': 'XXS', 'max_price': 50.0}
      out: 0 listings, prices []:
[3] search_listings RETRY, dropped size filter 'XXS' (via MCP)
      in:  {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
      out: 7 listings, prices [42.0, 24.0, 27.0, 30.0, 33.0, 38.0, 45.0]: Denim Jacket — Light Wash, Cropped, High-Waiste…
[4] select_item
      in:  first of search_results
      out: {'id': 'lst_007', 'title': 'Denim Jacket — Light Wash, Cropped'}
```

The retry kept the $50 ceiling (every price ≤ 50) and found an actual denim jacket ($42, Poshmark). That also answers something from my diagnosis: the data *does* have a denim jacket under $50, just not in size M.

**When the retry finds nothing too** (run #3, "impossible query stops early", every try):

```
- stopped early: yes — No listings matched, even after dropping the size filter (size XXS). Try raising the price limit or using fewer or different keywords.

[3] search_listings RETRY, dropped size filter 'XXS' (via MCP)
      in:  {'description': 'designer ballgown', 'size': None, 'max_price': 5.0}
      out: 0 listings, prices []:
```

Criterion 2 still passes: there's an extra search step, but still no `suggest_outfit` step.

### Stretch 3: A second measured improvement

**What I changed:** One thing, in `tools.py::search_listings`. Keywords now skip a list of filler words (`_STOPWORDS`: "for", "looking", "a", "the", "under", "size", …), and a keyword only counts when it matches a **whole word** in the listing's title, description or style tags. Before, it was a substring test, so "tee" matched "streetwear". I added one sentence saying so to the `search_listings` description in `mcp_server.py`, because the published contract changed.

**Which failure it was meant to fix:** "What's Still Broken" #1. Filler words in a query score points against listings that happen to contain them. The agent's own example query, "looking for a vintage graphic tee under $30", is the test case.

**Run #3 (before this change)** and **Run #4 (after)**, the five criteria:

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| **Run #3** | | | | | | | |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item stays the same across tool calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item's price and platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The agent respects the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| **Run #4** | | | | | | | |
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The selected item stays the same across tool calls | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card names the item's price and platform | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. The agent respects the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Same counting rule as before. In both runs the five items were `lst_002`, `lst_013`, `lst_038`, `lst_011`, `lst_001`. Every fit card named its price and platform ($18 Depop, $30 Depop, $27.00 Depop, $27 Poshmark, $38 Depop in run #4's counted tries), and every price was under its ceiling.

**The diagnostic it was meant to fix**, "looking for a vintage graphic tee under $30":

| | Run #3 (before) | Run #4 (after) |
|---|---|---|
| Item selected, all 5 runs | Mesh Long-Sleeve Top — Black, `lst_017` ($15) | Y2K Baby Tee — Butterfly Print, `lst_002` ($18) |
| Prices returned (top first) | `[15.0, 18.0, 19.0, 24.0, …]` | `[18.0, 19.0, 24.0, 15.0, …]` |

Run #3:
```
[2] search_listings (via MCP)
      in:  {'description': 'looking for a vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 listings, prices [15.0, 18.0, 19.0, 24.0, 18.0, 20.0, 22.0, 25.0, 26.0, 27.0]: Mesh Long-Sleeve Top — Black…
```
Run #4:
```
[2] search_listings (via MCP)
      in:  {'description': 'looking for a vintage graphic tee', 'size': None, 'max_price': 30.0}
      out: 10 listings, prices [18.0, 19.0, 24.0, 15.0, 26.0, 12.0, 14.0, 16.0, 18.0, 20.0]: Y2K Baby Tee — Butterfly Pri…
```

With the filler words, "looking for a vintage graphic tee" now gives exactly the same top result as "vintage graphic tee". In run #3, "for" matched the Mesh Long-Sleeve Top's "Great **for** layering", gave it the same score as the Y2K Baby Tee, and the cheapest-first tie-break put it first. In run #4 "for" and "looking" don't count, so the Y2K Baby Tee scores higher and the mesh top drops to fourth.

**Other changes the run showed** (also from this change, since nothing else changed between #3 and #4):

- "silk slip dress under $40" returned 2 listings instead of 4. The Leather Belt — Brown ($12) and one other unrelated item dropped out; the slip dress and a Silk Button-Down remain. That's the whole-word rule removing partial-word matches.
- "501 jeans under $45" returned 3 listings instead of 4. High-Waisted Denim Shorts dropped out, and the second result is now Straight Leg Black Jeans. The top item (the 501s) didn't change.

**Did it help, and how do I know:** Yes. The diagnostic query that picked a mesh top in 5 of 5 runs of #3 picked the Y2K Baby Tee in 5 of 5 runs of #4, and other queries lost unrelated results (a belt for a slip dress, shorts for jeans) without losing the item they were looking for. All five criteria stayed MET at 5/5, so it didn't break anything they measure. As with my first improvement, the criteria table can't show the gain: it reads 5/5 in both runs, because none of my criteria checks whether the item is what was asked for. I measured it with the diagnostic scenario instead.

One honest caveat: while checking the change by hand, I first ran my quick test against the *old* `tools.py`, because I hadn't saved the new file yet. Seeing the mesh top still first, I briefly concluded the fix didn't work, and that the mesh top would tie anyway because its description contains "graphic tee". After saving, the run showed that conclusion was wrong. The tie came from the filler word "for", which is what I first diagnosed.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is still missed: all five were met in both runs. That's partly because my targets were too low, as I said in my diagnoses. Here is what's still broken, and what I'd do about each:

**1. (Fixed afterwards as stretch 3 — see Stretch Results.) The search tool still treats filler words as matches.** My fix stops the parser from leaking "under", but `tools.py::search_listings` would still score any filler word the user types. It has no list of words to ignore, and it matches with a substring test (`kw in haystack`), so "for" matches "perfect for", "under" matches "underneath", and "tee" matches "streetwear". "looking for a vintage graphic tee under $30" (the query in `agent.py`'s own example) still sends `'looking for a vintage graphic tee'` to the search. In my unit 3 Sample Run, that picked the Mesh Long-Sleeve Top because its description says "Great **for** layering". *What I'd do:* drop common filler words before scoring, and match whole words instead of substrings. *Why I stopped:* the unit allows one improvement, and the parser bug was the direct cause of the failure the run showed. This is the second cause, and it would be my next change, measured the same way.

**2. Ties are broken by price, not by how well an item fits.** The Denim Vest beats the Shacket and the 90s Track Jacket for "denim jacket" because it's the cheapest. All three score on a single word. A user asking for a jacket would probably rather see a jacket. *What I'd do:* weight matches in the title higher than matches in the description, so the item type the user named counts for more. *Why I stopped:* same reason. One change per unit, and this one needs its own measurement.

**3. Criterion 1 is too easy to pass.** It only checks that the loop finished with a fit card, so it passed even when the agent returned a mesh top for a denim jacket. *What I'd do:* add the tighter criterion from my diagnoses (the selected item's title or category is the kind of item the query named, in at least 4 of 5 tries) and run it before and after a search fix. *Why I stopped:* the rules say a criterion is only revised when it couldn't be measured. Criterion 1 measured what it said; it just said too little. So I'm naming the tighter version here instead of changing `criteria.md`.

**4. Criterion 4 is ambiguous about what counts as "the price".** In the after-run, item 2, run 3 (not a counted try), the fit card said the dress was on Depop for "thirty bucks" instead of "$30". I'd count that as mentioning the price, but a stricter reader might not, so the criterion as written doesn't settle it. *What I'd do:* reword it to say what counts, e.g. "contains the price as a dollar amount (like $30 or $30.00)", and, since `create_fit_card` already asks the model to mention the price, tell it to write it as `$30.00` exactly. *Why I stopped:* it didn't change any counted verdict, and it's a wording problem in the criterion rather than a failure of the agent.

**5. Model errors are handled, not retried.** In the before-run, one call failed with `500 INTERNAL` from the model service. The agent stopped with a clear message, which is the behavior I wanted from the failure-mode work. But for a user, one retry on a server-side error would probably have just worked. *What I'd do:* retry once on a 5xx error inside `generate.py` before raising `ModelUnavailable`. *Why I stopped:* it happened once in 35 runs and didn't affect a counted try, and `generate.py` is the course's shared adapter, not my agent.


<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
