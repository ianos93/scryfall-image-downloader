# ✦ Luminary — Scryfall Image Downloader

A single-file, browser-based tool for fetching Magic: The Gathering card images from the [Scryfall API](https://scryfall.com/docs/api) and turning them into downloadable assets: individual images, a visual decklist, or a print-ready proxy PDF.

No installation, no build step, no API key. Open `index.html` and go.

**Version 4.2**

---

## Features at a Glance

- Paste card names or upload a `.txt` deck list
- Parses virtually every common deck export format, including main/sideboard sections and quantities
- Six image resolution options (Small through PNG), using Scryfall's WebP images
- **Paper Only** — exclude digital-only prints (MTGO, Arena)
- **First Print** — fetch the oldest printing of each card
- **Three output modes:**
  - **Individual Cards** — preview grid + ZIP download
  - **Visual Decklist** — the whole deck as one image, in stacks or a grid with quantities, as PNG or PDF
  - **Print for Proxy** — paginated A4/A3 PDF at true card dimensions
- **Recent Lists** — your last 20 fetched lists, saved in the browser and reloadable in one click
- Local card database for instant printing lookups (no per-card API calls)
- 7-day browser cache of card metadata, with a per-variant breakdown and clear button
- Cancel a fetch mid-flight without reloading the page
- Batched card lookups (75 per request) inside Scryfall's rate limits, with a 30-second pause on a 429

---

## Getting Started

Open `index.html` in any modern browser.

For GitHub Pages, push `index.html` (and optionally `favicon.png` and the `data/` folder) to the root of your repository, then enable Pages under **Settings → Pages → Branch: main**.

### Project Structure

```
index.html                  The entire application
favicon.png                 Site icon
data/
  prints_index.json         Local card database (generated)
  bulk_manifest.json        Database age/size metadata (generated)
update_bulk_data.py         Builds the two files above from Scryfall bulk data
update_bulk_data.bat        Windows launcher - double-click to run the script
```

The `data/` folder is optional. Without it the app still works, but **Paper Only** and **First Print** fall back to live API calls (see [Card Database](#card-database)).

---

## Entering Card Names

### Typing or Pasting

Type or paste card names into the **Card Names** text area, one per line.

### Uploading a File

Drag and drop a `.txt` file onto the **Import Decklist** panel, or click it to browse. The file contents replace whatever is in the text area. Exports from Moxfield, Archidekt, MTGTop8, EDHREC, and MTG Arena all work.

### Limits

- Above **100 cards** you'll be asked to confirm before the fetch starts
- **500 cards** is a hard cap per run

---

## Supported Input Formats

Quantities, set codes, collector numbers, and special syntax are all stripped automatically — only the name (and optionally set/number) is used for lookup.

### Quantities

```
4 Lightning Bolt
4x Lightning Bolt
4X Lightning Bolt
4× Lightning Bolt
```

Quantities are remembered and used by the Visual Decklist and Proxy PDF.

### Set Codes and Collector Numbers

Set codes can appear in any bracket style, with or without a collector number, in any order:

```
Lightning Bolt
Lightning Bolt M10
Lightning Bolt (M10)
Lightning Bolt [M10]
Lightning Bolt <M10>
Lightning Bolt (M10) 93
Lightning Bolt 93 (M10)
Lightning Bolt #93 (M10)
```

> **Note:** Bare (unbracketed) set codes must be ALL-CAPS (e.g. `M10`, `BRO`, `MH3`) to avoid ambiguity with card name words. Bracketed set codes like `(m10)` are accepted in any case.

### Double-Faced Cards

Only the front face name is needed. Everything after `//` is stripped:

```
Fire // Ice
```

### Leading Punctuation

Lines may begin with `/`, `#`, `*`, `-`, or whitespace — these are stripped before parsing. Lines starting with `#` are treated as comments and skipped entirely.

### Main Deck vs Sideboard

The parser tracks which section each card belongs to. A card enters the sideboard when any of the following is seen:

- An explicit header: `Sideboard`, `Side board`, `Side`, `SB`, `S.B.`
- A bracket header: `[Sideboard]`
- The **first blank line** after at least one main-deck card — but only if the file contains no bracket headers

Headers such as `Deck`, `Main Deck`, `Commander`, and `Companion` switch back to the main deck. Category headers (`Lands`, `Creatures`, `Spells`, `Artifacts`, `About`, `Maybeboard`, …) are filtered out and never treated as card names.

### Repeated Lines

Lines requesting the same card **and** the same printing are combined, and their quantities added. `2 Lightning Bolt` followed later by `2 Lightning Bolt` gives you four copies, so decklists that split a playset across categories come out right.

The match is on name + set code + collector number, case-insensitively, so asking for genuinely different printings keeps them apart:

```
2 Lightning Bolt (M10)      -> 2 copies of the M10 printing
2 Lightning Bolt (LEA)      -> 2 copies of the LEA printing
```

A bare name and a set-qualified name count as different requests, since the app cannot know at parse time whether they resolve to the same printing. Main deck and sideboard are totalled independently.

---

## Image Resolution

Choose the resolution before clicking **Summon Cards**. The selection applies to the whole batch and determines the ZIP file extension.

| Option | Scryfall key | Dimensions | Format | Best For |
|---|---|---|---|---|
| Small | `thumb` | 146 × 204 px | WebP | Thumbnails, quick previews |
| Normal | `grid` | 488 × 680 px | WebP | Standard use, most deck tools |
| Large | `display` | 672 × 936 px | WebP | High quality printing (default) |
| PNG | `png` | 744 × 1040 px | PNG | Lossless, highest quality — see below |
| Art Crop | `art` | 626 × 457 px | WebP | Art only, no card frame |
| Border Crop | `crop` | 480 × 680 px | WebP | Full card, border removed |

For proxy printing, **Large** or **PNG** are recommended — the PDF places cards at 63 × 88 mm, so lower resolutions will look soft. Large is about 270 DPI at that size.

### Scryfall's WebP migration

On [14 October 2026](https://scryfall.com/blog/new-webp-images-jpeg-deprecations-237) Scryfall started serving WebP versions of every card image, under new keys. **After 1 January 2027** the `small`, `large`, `border_crop` and `art_crop` JPEGs are no longer served, `normal` is renamed to `jpeg`, and PNGs can no longer be hotlinked. Luminary uses the WebP keys throughout, so it is unaffected by the JPEG removal.

PNG is still offered, but once Scryfall refuses it the app switches the rest of the session to **Large** WebP and marks those cards **⚠ WebP, PNG unavailable** in the log, rather than failing them. Saved lists that used the old size names load with their WebP equivalent.

---

## Fetch Options

### Paper Only

Checks the `games` field on every fetched card. If a card exists only digitally (MTGO, Arena), the closest paper printing is substituted.

- If a paper printing is found it is used instead and flagged **⚠ alt print used** in the log
- If no paper printing exists at all, the card is reported as an error

### First Print

Resolves each card to its oldest non-promo, non-digital printing — useful for original artwork and early set symbols.

- If the card is already the oldest printing it is kept as-is, with no warning
- If an older printing is found it is swapped in and flagged **⚠ alt print used**
- If the lookup fails, the originally fetched card is kept as a silent fallback
- The search is **skipped** when you explicitly specified a set code for that card, so you can always pin an exact printing

**Ties on the earliest date resolve to the base printing.** Alternate treatments — retro frame, showcase, borderless, extended art — release on the same day, in the same set, as the base card, and are not marked as promos, so release date and set code cannot tell them apart. Collector number can: Wizards numbers the base set first and places variants above it, so the lowest collector number among tied printings is taken. This affects roughly 17% of cards.

This requires a **format 3** database. If `data/prints_index.json` was generated before this change, the info panel will warn you and First Print will fall back to an arbitrary but stable choice among tied printings — re-run `update_bulk_data.py` to fix it.

### Combining Both

Paper Only and First Print can be active together, in which case the app resolves the **oldest paper printing** — for example the original Alpha/Beta/Revised print of a classic card, excluding digital-only reprints.

---

## The Fetch Process

Clicking **Summon Cards** runs up to three phases, tracked by the badges and progress bar:

1. **Card Data** — resolve every line to a Scryfall card object
2. **Options** — apply Paper Only / First Print (only shown when one is enabled)
3. **Images** — download the image for each resolved card

Requests follow [Scryfall's rate limits](https://scryfall.com/docs/api/rate-limits): `/cards/collection`, `/cards/named` and `/cards/search` are spaced 550 ms apart (the limit is 2 per second), every other API call 110 ms apart (limit 10 per second). A `429` locks a client out for 30 seconds, so one pauses all API requests for that long, with a note in the log, instead of retrying into the lockout. Image downloads come from `cards.scryfall.io`, which has no rate limit; failures there retry with exponential backoff (500 ms → 1 s → 2 s).

### Cancelling

While a fetch is running, the button becomes **Cancel Summoning**. Clicking it aborts all in-flight and queued requests immediately.

### Search Strategy

Every line that is not already cached goes to `POST /cards/collection`, **75 lines per request** — a 500-card list takes 7 requests. Each line is sent as set + collector number, name + set, or name alone, depending on what it gives. The collection endpoint matches names exactly but ignores case and accents, and accepts a double-faced card's front name on its own.

Lines it cannot resolve fall back to individual lookups, in order:

1. **Set + collector number** — `GET /cards/:code/:number`, used only if the card there has the name you asked for
2. **Name within the set** — `GET /cards/named?exact=<name>&set=<code>`, then `fuzzy`
3. **Fuzzy name alone** — `GET /cards/named?fuzzy=<name>`, catching typos. If a set or number was given but dropped, the line is flagged yellow.

A set + collector number names a slot, not a card, so it is checked against the name: `Island (UNF) 240` is a Plains. When they disagree the card is found by name and set instead, and the log says **⚠ UNF #240 is Plains, matched by name**.

### Log Colours

| Colour | Meaning |
|---|---|
| 🔵 Blue | Card resolved as requested |
| 🟡 Yellow | The request could not be honoured exactly |
| 🔴 Red | Card could not be found |

Successful entries may carry suffixes:

| Suffix | Meaning |
|---|---|
| `✦ first print` | First Print swapped in an earlier printing |
| `✦ paper print` | Paper Only swapped in a paper printing |
| `⚠ alt print used` | The set code or collector number you gave was not found, so the card was matched by name |
| `⚠ M10 #93 is …, matched by name` | That set + number holds a different card, so the card was found by name and set |
| `⚠ WebP, PNG unavailable` | Scryfall refused the PNG, so the Large WebP was used |
| `✦ cached` | Served from the local cache instead of the API |

Only `⚠ alt print used` colours the line yellow. A swap caused by an option you switched on is the feature working, so it stays blue.

---

## Output Mode 1 — Individual Cards

The default view. Successfully fetched cards appear in a grid; failures appear only in the log.

- **Hover** a card for a frosted panel showing its full name and the set code of the exact printing fetched
- **Click** (or middle-click) a card to open that printing on Scryfall in a new tab
- **Download ZIP** packages every fetched image into one archive

### File Naming

```
Lightning Bolt_m10_146.webp
Black Lotus_lea_232.png
Island_unf_236.webp
Island_unf_241.webp
```

Names are `<card>_<set>_<collector number>`, so two printings from the same set get separate files. The extension follows the selected resolution (`.png` for PNG, `.webp` for everything else). The same printing listed in both main deck and sideboard is stored once. The archive is named `scryfall-<resolution>.zip`.

---

## Output Mode 2 — Visual Decklist

Renders the whole deck as a single image, in one of two layouts. Either way, cards are sorted by type (Creature → Instant → Sorcery → Enchantment → Artifact → Planeswalker → Land), then mana value, then name.

**Stacks** — the classic stacked/fanned layout:
- **Main deck** — 5 columns, up to 4 cards per overlapping stack
- **Sideboard** — a separate right-hand column, up to 15 cards per stack, with a rotated `SIDEBOARD` label
- Quantities are respected — a playset appears as four overlapping copies

**Grid** — one card per printing:
- **Main deck** and **Sideboard** each get a heading with their card count (`Main deck 60`), then up to 7 cards per row
- The quantity is written under each card (`×4`); single copies are left unlabelled so the counts that matter stand out
- Lines that resolved to the same printing share one card, with their copies added together

### Options

The controls sit in a bar above the preview that stays in view while you scroll: view settings (Layout, Transparent Background) on the left, export settings and the downloads on the right. Each output tab uses the same arrangement. On a phone the export controls move to a bar pinned to the bottom of the screen instead.

- **Layout** — Stacks or Grid
- **Export Size** — 100%, 75% or 50% of the rendered image, with the resulting pixel size shown next to it
- **Transparent Background** — drops the purple gradient backdrop, giving a PNG with alpha for compositing elsewhere. The grid's headings and counts are light-coloured, so they need a dark background behind them

**Download Image** saves a PNG named `visual-decklist-<timestamp>.png`.

**Download PDF** saves `visual-decklist-<timestamp>.pdf`: a single page sized to the decklist, with every card at its true 63 × 88 mm, so it prints at real size or scales to any paper with "fit to page". Export Resolution changes the image detail, not the page size. The image is stored as JPEG, or PNG when Transparent Background is on, which makes that PDF several times larger.

---

## Output Mode 3 — Print for Proxy

Builds a print-ready PDF with cards at true physical size (63 × 88 mm).

### Settings

| Setting | Options |
|---|---|
| Page Size | A4 (210 × 297 mm, 3 × 3 = 9 per page) · A3 (297 × 420 mm, 4 × 4 = 16 per page) |
| Card Spacing | No spacing · 2 mm gap · 5 mm gap |
| Repeat by Quantity | Print each card as many times as the decklist specifies |
| Ignore Basic Lands | Skip Plains, Island, Swamp, Mountain, Forest, Wastes, and their snow-covered versions |

The grid is centred on the page, so trimming with a guillotine or corner punch is straightforward. **No spacing** gives edge-to-edge cards with shared cut lines; the gap options give each card its own margin.

### Preview

A live preview shows each page before you commit, drawn when you turn to it so large jobs stay light on memory. When the job spans multiple pages, use the **‹ ›** arrows to page through them. The summary line above the preview reports the layout, total card count, page count, and spacing.

**Generate PDF** saves `proxy-<size>-<timestamp>.pdf`, with a progress bar during assembly.

PNG and WebP cards are re-encoded to high-quality JPEG when building the PDF. At 63 x 88 mm a
744 x 1040 image is already around 300 DPI, so nothing is downscaled — but PNG is stored
essentially uncompressed inside a PDF, which made large proxy sets run to hundreds of
megabytes and risk failing during assembly. The re-encode cuts that by roughly 5-10x with
no visible difference at print size. WebP is re-encoded because JPEG is the image format
every PDF reader handles natively. Images that are already JPEG are passed through
untouched rather than re-encoded.

---

## Card Database

**Paper Only** and **First Print** need to know every printing of a card. Doing that per-card through the API means one paginated search per card, which triggers rate limiting fast: `/cards/search` allows only 2 requests per second. (Its rate-limit responses can arrive without CORS headers, so in the browser this used to look like a CORS block.)

Luminary solves this with a local index.

### Generating It

Run `update_bulk_data.py` once. It downloads Scryfall's `default_cards` bulk file and writes two files into `data/`:

- **`prints_index.json`** — a compact map of `oracle_id` → printings, pre-sorted oldest-first. Each printing is stored as `[id, set, YYYYMMDD, gamesBits, flagsBits, collectorNumber]`, keeping the file small enough to load in the browser.
- **`bulk_manifest.json`** — timestamps and record counts, used to display database age.

Image URLs are reconstructed from card IDs rather than stored, which keeps the index roughly an order of magnitude smaller than the raw bulk data.

### Status and Refresh

The **Card Database** section of the info modal (**ⓘ**, top right) shows a status dot:

| Dot | Meaning |
|---|---|
| 🟢 Green | Local database loaded, updated within the last 14 days |
| 🟡 Amber | Loaded but stale, or the file could not be parsed |
| 🟠 Orange | No local database found |

**Refresh Database** drops the in-memory index and re-reads `data/prints_index.json`, so a database you have just regenerated is picked up without a hard reload. It does not contact Scryfall.

To actually update the data, re-run `update_bulk_data.py` and then hit Refresh. Do this after each new set release, roughly every three months.

On Windows, double-click **`update_bulk_data.bat`** instead of using a terminal. It finds your Python install, runs the script in its own folder, and keeps the window open at the end so you can read the result. It needs Python 3.7+ on the system and tells you where to get it if none is found.

The script identifies itself to Scryfall as `Luminary-BulkUpdater/<version>`. Scryfall refuses scripted downloads that send a generic User-Agent (`Python-urllib`, `curl` and the like), so keep that line if you adapt the script, and bump its version alongside the app's.

### Why there is no in-browser download

Earlier versions fell back to downloading Scryfall's bulk file directly in the browser when no local index was present. That path has been removed. Scryfall completed its migration to gzipped JSONL bulk files on **2026-07-20**: the `/bulk-data` manifest no longer exposes `download_uri` (it is now `jsonl_download_uri`, with `compressed_size` replacing `size`), and the payload is gzip-compressed newline-delimited JSON rather than a single JSON array.

Rebuilding the index in a tab would mean streaming roughly 460 MB of decompressed data to reproduce a file that `update_bulk_data.py` already generates offline in seconds. When the local file is missing, the app now says so plainly and falls back to per-card API lookups, where rate limits apply.

> **If you are upgrading:** a copy of `update_bulk_data.py` written before July 2026 will break against the new manifest. It needs to read `jsonl_download_uri` instead of `download_uri`, and to gunzip and parse the download line by line rather than as one JSON array.

---

## Recent Lists

Every fetch that returns at least one card is saved, so a list you used last week is one click away. Nothing is saved for a run that found nothing, and typing alone never saves.

The panel sits above **Image Resolution**, collapsed until you open it, and stays hidden entirely until you have something in it.

| Action | What it does |
|---|---|
| **Load** | Puts the list back in the card names field and restores the resolution and options it was fetched with. It does not re-fetch — edit first if you want to. |
| **✎** | Rename the list. Appears on hover, next to the name. Press Enter to save, Escape to cancel, or clear the field to go back to the automatic name. |
| **↓** | Download the list as a `.txt` file, named after the list and the date it was saved. |
| **×** | Remove that entry. |

Lists are named automatically from their contents — `Lightning Bolt +23 more` — until you rename one. A custom name survives re-running the list, and the automatic name keeps tracking the contents underneath, reachable as the row's tooltip.

Re-fetching a list you already have moves it to the top rather than adding a duplicate. Matching ignores casing, blank lines and trailing spaces, so a lightly edited list counts as the same list. The 20 most recent are kept.

**Clear List History** in the info panel removes them all at once. History is stored under its own key, so clearing the card cache never touches it — and the reverse is true too.

> Storage is per browser and per site. Lists saved while testing locally won't appear on your hosted copy, and clearing site data removes them. There are no accounts and nothing is uploaded.

---

## Metadata Cache

Resolved card data is cached in `localStorage` for **7 days** so repeat fetches skip the API entirely. Cached hits are marked with `✦ cached` in the log. Only the fields Luminary reads are kept, about 1.8 KB per entry, so the browser's storage holds a few thousand cards.

Each option combination is cached separately — Standard, Paper Only, First Print, and Paper + First are distinct entries for the same printing, so toggling options never returns a stale result.

Open the info modal to see a live breakdown by variant and a total count. **Clear All Cache** wipes every entry. When storage fills up, the oldest 30% of entries are evicted automatically.

Images are **not** cached; only metadata is.

---

## Interface Notes

- **ⓘ** (top right) opens the info modal: quick instructions, supported formats, changelog, cache and saved lists, and database status. It fades out as you scroll.
- **Recent Lists** sits above Image Resolution and appears once you have fetched something.
- The progress area shows a phase label, a per-phase counter, and a scrolling log.
- There is one undocumented option, unlocked by a keyboard sequence, that swaps cards for their showcase, borderless, Universes Beyond, and Secret Lair printings where available. It relies on Scryfall's `/cards/search` endpoint, one request per card at 2 per second, so it is slow on long lists.

---

## What's New in 4.2

**New**
- Visual Decklist **Grid** layout: one card per printing, quantity underneath, with Main deck and Sideboard headings and counts
- Visual decklists download as **PDF** too, one page with cards at true size

**Changed**
- All three output tabs share one layout: a bar with a summary and the main action at the top, kept in view while scrolling, then settings, then the preview. Download ZIP, Download Image/PDF and Generate PDF no longer sit below long previews or card grids. On phones the actions move to a bar pinned to the bottom of the screen
- Individual Cards opens with a summary, for example "9 images · Large WebP", plus a failure count when a card was not found
- Visual Decklist export sizes read 100% / 75% / 50% with the exact pixel size, instead of Full / Large / Medium, which clashed with the Large image size
- Generate PDF uses the same button style as the other downloads instead of copying Summon Cards

**Fixed**
- Opening or closing the info panel shifted the whole page sideways by the scrollbar's width; so did a short page first becoming scrollable
- The stacked decklist image reserved a full four-card row and a fifteen-card sideboard stack whatever the deck held, leaving a third or more of the image empty. The rotated SIDEBOARD label is now centred on the sideboard column

---

## What's New in 4.1

**Changed**
- Images use Scryfall's WebP versions (`thumb`, `grid`, `display`, `art`, `crop`), ahead of the JPEG retirement on 1 January 2027. **Large** is the new default; PNG falls back to Large when Scryfall stops serving it to the browser
- Card lookups go through `/cards/collection`, 75 lines per request, and the request pacing follows Scryfall's published per-endpoint limits. The old pacing sent about 6.7 requests per second to endpoints limited to 2
- A `429` pauses all API requests for Scryfall's 30-second lockout instead of retrying after 2 seconds
- jsPDF updated from 2.5.1 to 4.2.1, which fixes several published image-parsing vulnerabilities
- The cache stores about a third as much per card, and old entries are invalidated

**Fixed**
- Two printings from one set (`Island (UNF) 236` and `241`) overwrote each other in the ZIP, showed as one tile, and with Paper Only or First Print on, shared one cached result
- A set + collector number pointing at a different card than the one named was used silently; it is now caught and the card found by name
- A line typed in capitals (`LIGHTNING BOLT`) read its last word as a set code, and a name starting with a number (`1996 World Champion`) lost it as a quantity
- The proxy preview drew every page up front, which could use over a gigabyte for a large deck, and a settings change mid-draw could mix pages from two layouts
- A failed PDF build left the Generate button stuck on "Generating…"
- `update_bulk_data.py` and `update_bulk_data.bat` are back in the repository

---

## What's New in 4.0

**New**
- Recent Lists: save, reload, rename and export your recent card lists
- Repeated lines add their quantities together instead of the later line being dropped

**Fixed**
- First Print resolved to whichever same-day printing happened to be listed first, so cards from sets with alternate treatments (MH2, WAR, and about 17% of all cards) could return a showcase, borderless or retro-frame version. It now takes the lowest collector number, which is always the base printing.
- The card database updater was broken by Scryfall's move to gzipped JSONL bulk files on 2026-07-20
- Log entries now say *why* a printing changed rather than flagging every substitution as a warning
- Swapped printings no longer link to the printing you did not receive
- A failed database load no longer poisons the rest of the session

**Changed**
- Index format 3 adds collector numbers — **re-run `update_bulk_data.py` after upgrading**
- The in-browser bulk download fallback was removed; it could not work after the JSONL migration
- Proxy PDFs re-encode PNG cards to JPEG, cutting file size 5-10x with no visible difference at print size
- Decoded card images are capped by memory budget, and oversized visual decklists scale down instead of rendering blank
- Subresource Integrity on the CDN libraries, and `connect-src` narrowed from any HTTPS host to Scryfall only
- Squarer corners throughout, and specs and counts moved to a sans face for legibility

---

## API & Attribution

This tool uses the [Scryfall REST API](https://scryfall.com/docs/api). Card data and images are © Wizards of the Coast and their respective artists. Scryfall provides card data under the [DMCA safe harbour](https://scryfall.com/docs/api#usage).

Proxies generated with this tool are for personal playtesting only. Do not sell them, and do not use them in sanctioned play.

Created by **ianos** · [GitHub](https://github.com/ianos93/scryfall-image-downloader/) · Powered by [Scryfall](https://scryfall.com)
