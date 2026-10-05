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

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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
