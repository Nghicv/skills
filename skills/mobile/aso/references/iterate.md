# Planning the next metadata version

Input: vN is live and has at least two measurements. Output:
`reports/<date>-vN+1-proposal.md`, then `metadata/vN+1.yml`.

## 1. Character budget audit

The keyword field is 100 characters and zero-sum. Every version must account for all 100.

`validate_metadata.py` reports per locale:
- characters used / wasted on words already in Title or Subtitle
- **dead keywords** — never reached top 200 across two versions
- CORE keywords missing from metadata entirely

Dead keywords are the budget you spend on new ones.

## 2. Classify every tracked keyword into one action

| State | Action |
|---|---|
| CORE, holding rank | Leave alone |
| #4–30 and climbing | Leave alone, it is working |
| #4–30, flat for 2 measurements | Push: move to Subtitle, or to the front of the field |
| Newly entered top 200 | Hold one more cycle before judging |
| Outside top 200 after 2 versions | **Retire** — reclaim the characters |
| App has the feature but does not rank | **Coverage gap** — add it |
| Ranks well, conversion poor | Not a keyword problem — fix the page |

## 3. Hunt coverage gaps

Cross-check two ways:

- **Feature ↔ keyword**: list what the app does, check you rank for each.
- **Locale ↔ locale**: the same feature ranking in one market and absent in another means
  that locale's field is missing the term.

> Example: an app ranked **#2** for the local-language term for "receipt scanning" in one
> market, yet did not appear in the top 200 for `receipt scanner` in English. Same feature,
> one market monetising it, one invisible. That asymmetry is the signal to open the English
> keyword field and check.

## 4. Prefer headroom over rescue

Moving #12 → #5 is worth more, and is far more likely, than moving #170 → #40.

## 5. Write the proposal

For each locale state: what is being **removed** (and the evidence it is dead), what is
being **added** (and the expected term), and what is **untouched**. A version that cannot
name what it removed has not done the audit.

## 6. Record the outcome, including failure

After the next measurement, append to `CHANGELOG.md`:

```markdown
## v3.0 — 2026-08-12 (app 1.5.1)
Change: restored the "receipts" keyword group in the de field + reverted the de subtitle.
Why: de "receipt scanner" fell from #33 to unranked after v2.0.
Result (measured +25d): FAILED — still unranked.
  Re-diagnosis: the phrase was in the Title in all three versions, so the rollback added
  no new signal. The real blocker was the token "scanner" (see reports/...).
What did work: restoring "OCR" to the subtitle moved de "ocr" from #6 to #4.
```

The failed attempt and its explanation are the most valuable lines in the file. Without
them somebody repeats the experiment next quarter.
