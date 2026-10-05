## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
`search_listings` scores by keyword overlap with the title, description, and
style tags, so a query phrased differently from how a listing is written
(e.g. "comfy jeans" vs. a listing tagged "relaxed fit") can score zero and
return nothing, even when a human would call it a match. 4 of 5 allows for
that kind of phrasing mismatch without accepting a search that fails often.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path is a single structural check — did the list come back empty — with
no model call and no keyword scoring involved, so nothing about it is
probabilistic. It should work every time or something is actually broken.

---

## 3. The selected item stays the same across tool calls

For 5 different matching queries, the `id` of the item in
`session["selected_item"]` matches the `id` of the item that `suggest_outfit`
is actually called with, in all 5 tries.

**Why this target:**
Reading a value back out of a dict either works or it doesn't — there's no
reason this would succeed sometimes and fail other times, so the target is
5 of 5, not a rate.

---

## 4. The fit card names the item's price and platform

For 5 different items, the generated fit card mentions the item's price and
its platform (e.g. "depop", "poshmark") at least once each, in at least 4 of
5 tries.

**Why this target:**
The caption's exact wording changes because it comes from the model, but
price and platform are fixed facts handed to the prompt, not something the
model invents. 4 of 5 allows for the model occasionally dropping one detail
in favor of a shorter sentence, without accepting it dropping both regularly.

---

## 5. The agent respects the price ceiling

For 5 queries that each include an explicit "under $X" phrase, every item
returned by `search_listings` has `price <= X`, in 5 of 5 tries.

**Why this target:**
This is a plain numeric comparison on data the tool already has — `price`
against `max_price` — not something that depends on the model or on
ambiguous keyword matching, so there's no scenario where it should fail
even once.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
