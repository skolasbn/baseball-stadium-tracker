# MLB Ballpark Visit Tracker: handoff notes

This is a personal, static web page that shows which MLB ballparks the owner has visited, on an SVG map of North America, with the games seen and their results. It's hosted as a single HTML file on the owner's own domain. The next step is to put it in git and enhance it.

## Files

| File | What it is |
|---|---|
| `index.html` | The whole app: one self-contained page with inline CSS, inline JS, and inline SVG map paths. No build step to run it. Named `index.html` so GitHub Pages serves it at the site root. |
| `build_map.py` | One-off Python script that generated the SVG basemap paths from Natural Earth data. Only needed if the map itself changes. Its docstring has setup steps. |
| `ballpark-visits.csv` | The original 30-park template the owner used to start the Google Sheet. It's historical only, because the live data is in the sheet. |

## How the page works

1. **Data source.** On every page load, the page fetches a published Google Sheet as CSV. The URL is in `SHEET_CSV_URL` near the top of the script:
   `https://docs.google.com/spreadsheets/d/e/2PACX-1vSOTZw_QlKtwdXdoudGaWx5MvolRMQQgPsdm05qQRROUcbedzDsJ_z53hEkOCjUWUfi44rMPnSU0wwF/pub?output=csv`
   - Google refreshes published CSVs roughly every 5 minutes.
   - Google sends a 302 redirect to `*.googleusercontent.com`. A strict CSP on the host would need to allow both domains.
   - Sandboxed previews, such as a chat file preview, block this fetch and log `Google Sheet didn't load: Failed to fetch`. That's expected. It works on a real domain.
2. **Fallback.** If the fetch fails, or returns HTML instead of CSV, the page renders `VISITS_CSV`, a backup copy of the data embedded in the script. The fallback is silent and logs only a console warning. The owner asked that no message appear on the page. This copy has to be kept in sync by hand, and the owner wasn't sure it's worth keeping.
3. **Park list.** `PARKS` is a hardcoded array of the 30 current (2026) MLB parks: name, team, city, lat, lon. It uses current names: Rate Field, Daikin Park, American Family Field, Sutter Health Park (Athletics, West Sacramento, through 2027), and Tropicana Field (Rays returned in 2026). CSV rows are matched to parks by normalized name (lowercase, alphanumerics only).
4. **Rendering.** `render(csvText)` builds the tally line, map pins, the selected park's card, and the game log table. The oldest visit is selected by default. The game log table is still sorted newest-first.
5. **Map.** It uses an Albers equal-area conic projection with a 1000×580 viewBox. The JS `project()` must match `build_map.py` exactly.
6. **Pin layout.** `scalePins()` runs on resize through a ResizeObserver. It keeps pins about 20px on screen, pushes overlapping pins apart with a simple pairwise relaxation that has a weak spring back to each true position, and draws a leader line plus an anchor dot from each moved pin to its real location. It was tested at 1280px and 390px wide, and every pin's center hit-tests to itself.

## CSV schema

Headers are case-insensitive. Rows with an empty `date` or `ballpark` are skipped; these are parks not visited yet.

| Column | Required | Notes |
|---|---|---|
| `date` | yes | Accepts `2024-08-10`, `2024_08_10` (the owner's style), `2024/08/10`, or `8/10/2024` |
| `ballpark` | yes | Must match a `PARKS` name, unless `lat` and `lon` are given |
| `home_team` | yes | |
| `away_team` | no | If missing, the game shows as "<home> home game" |
| `away_score`, `home_score` | no | The winner is worked out from these and shown as "X won 8–5" |
| `city`, `lat`, `lon` | no | Only for parks not in `PARKS`, such as former parks or spring training |

The owner's sheet may also have a `winner` column. The page ignores it.

## Current data (8 games, all verified against box scores)

| Date | Park | Away | Home | Score |
|---|---|---|---|---|
| 2013-07-26 | Coors Field | Brewers | Rockies | 3–8 |
| 2014-06-18 | Fenway Park | Twins | Red Sox | 1–2 (10 inn.) |
| 2014-09-21 | Wrigley Field | Dodgers | Cubs | 8–5 |
| 2015-07-27 | Oracle Park | Brewers | Giants | 2–4 |
| 2016-05-06 | Rate Field | Twins | White Sox | 4–10 |
| 2018-08-10 | Comerica Park | Twins | Tigers | 3–5 |
| 2019-06-30 | American Family Field | Pirates | Brewers | 1–2 |
| 2025-06-07 | Great American Ball Park | Diamondbacks | Reds | 1–13 |

Two dates were corrected along the way: White Sox 5/16 → 5/6, and Brewers 7/7 → 6/30, since the Brewers were in Pittsburgh on 7/7. A November 2014 Target Field row was dropped. When adding games, check the date against a box score, such as Baseball-Reference `boxes/{TEAM}/{TEAM}{YYYYMMDD}0.shtml`.

## Design system (owner-approved; do not invent new UI)

The owner's standing preference is: **don't make up UI. Follow the design system, or ask if there isn't one.** There was no existing system, so the owner picked a "classic ballpark" direction, light mode only. New components should reuse these tokens and patterns. Ask the owner before introducing anything new.

- **Colors** (`:root`): paper `#F1E6CC`, land/card `#FBF5E6`, navy `#1A2B4C` for text, lines, and borders, stitch red `#B22234` for the accent, selection, and the card's top rule, muted `#586174`, rule `#CDBB93`, water `#D1CAB9`.
- **Type:** Alfa Slab One for display headings and Source Serif 4 for body text, both from Google Fonts.
- **Patterns:**
  - 2px navy borders, with no rounded corners and no shadows.
  - The park card has a 6px red top rule.
  - Pins: a baseball (white with red stitches) means visited; a navy home plate means not yet.
  - Hover/focus shows a navy tooltip. The selected pin gets a red ring.
  - Tables use hairline rules in the `--rule` color.
- **Layout:** the map (about 2/3 width) and the park card sit side by side at 900px and up, and stack on mobile. The full game log table is below.
- **Accessibility:** pins are focusable `role="button"` with `aria-pressed` and descriptive labels, Enter/Space selects, the card is `aria-live`, and reduced motion is respected.

## Known issues and enhancement ideas

- **Structure.** Everything lives in one file, and the SVG path data (~90 KB) is inline. For git, consider splitting it into `index.html`, `styles.css`, `app.js`, `map.svg` or `paths.json`, and `parks.js`, and keeping `build_map.py` with a requirements file. Keep the deploy a static file upload with no server needed.
- **Backup data drift.** `VISITS_CSV` drifts from the sheet. Options: remove it and show an empty state with a message, or generate it at build or deploy time.
- **`PARKS` is hardcoded.** Park renames and relocations (A's to Las Vegas in 2028, a possible Rays new stadium) mean manual edits.
- **Possible features** (ask the owner which they want before designing):
  - Filters by year or team
  - A per-team "seen play" tally
  - Photos per visit
  - Former parks
  - A "next park to visit" suggestion
  - Sorting the game log
- **No tests yet.** Worth adding: CSV parsing (quoted fields, date formats), park-name matching, winner logic, and the pin-overlap invariant (each pin's center hit-tests to itself at 390px and 1280px). Playwright is a natural fit.
