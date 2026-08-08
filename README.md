# ✦ Luminary — Scryfall Image Downloader

A single-file, browser-based tool for fetching Magic: The Gathering card images from the [Scryfall API](https://scryfall.com/docs/api) and turning them into downloadable assets: individual images, a visual decklist, or a print-ready proxy PDF.

No installation, no build step, no API key. Open `index.html` and go.

---

## Features at a Glance

- Paste card names or upload a `.txt` deck list
- Parses virtually every common deck export format, including main/sideboard sections and quantities
- Six image resolution options (Small through PNG)
- **Paper Only** — exclude digital-only prints (MTGO, Arena)
- **First Print** — fetch the oldest printing of each card
- **Three output modes:**
  - **Individual Cards** — preview grid + ZIP download
  - **Visual Decklist** — a single stacked-layout PNG, with optional transparent background
  - **Print for Proxy** — paginated A4/A3 PDF at true card dimensions
- Local card database for instant printing lookups (no per-card API calls)
- 7-day browser cache of card metadata, with a per-variant breakdown and clear button
- Cancel a fetch mid-flight without reloading the page
- Rate-limit-aware fetching with automatic backoff and retry

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

### Deduplication

Duplicate entries are ignored case-insensitively, scoped per section. The dedup key is name + set + collector number, so `Lightning Bolt (M10)` and `Lightning Bolt (LEA)` are both kept.

> Because dedup happens per line, splitting copies across multiple identical lines (`2 Lightning Bolt` then `2 Lightning Bolt`) keeps only the first line's quantity. Combine them into one line instead.

---

## Image Resolution

Choose the resolution before clicking **Summon Cards**. The selection applies to the whole batch and determines the ZIP file extension.

| Option | Dimensions | Format | Best For |
|---|---|---|---|
| Small | 146 × 204 px | JPEG | Thumbnails, quick previews |
| Normal | 488 × 680 px | JPEG | Standard use, most deck tools |
| Large | 672 × 936 px | JPEG | High quality printing |
| PNG | 745 × 1040 px | PNG | Lossless, highest quality (default) |
| Art Crop | Varies | JPEG | Art only, no card frame |
| Border Crop | Varies | JPEG | Full card, border removed |

For proxy printing, **PNG** or **Large** are recommended — the PDF places cards at 63 × 88 mm, so lower resolutions will look soft.

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

Requests run three at a time, spaced ~150 ms apart globally to stay inside [Scryfall's rate limit guidelines](https://scryfall.com/docs/api#rate-limits). A `429` response triggers a `Retry-After`-aware backoff; image CDN failures retry with exponential backoff (500 ms → 1 s → 2 s).

### Cancelling

While a fetch is running, the button becomes **Cancel Summoning**. Clicking it aborts all in-flight and queued requests immediately.

### Search Strategy (3-tier fallback)

For each card, in order:

1. **Exact name** — `GET /cards/named?exact=<name>` (plus `&set=` if a set code was given)
2. **Fuzzy name** — `GET /cards/named?fuzzy=<name>`, catching typos and alternate spellings
3. **Name-only fuzzy** — if a set code was given but not found, the set is dropped and the name searched alone. Flagged yellow in the log.

When both a set code and collector number are supplied (e.g. `M10 93`), the direct endpoint `GET /cards/:code/:number` is used instead and name search is skipped.

### Log Colours

| Colour | Meaning |
|---|---|
| 🔵 Blue | Card found exactly as requested |
| 🟡 Yellow | Fallback or alternate print was used |
| 🔴 Red | Card could not be found |

Successful entries may carry suffixes: `⚠ alt print used` for a substituted printing, and `💾` when the card came from the local cache instead of the API.

---

## Output Mode 1 — Individual Cards

The default view. Successfully fetched cards appear in a grid; failures appear only in the log.

- **Hover** a card for a frosted panel showing its full name and the set code of the exact printing fetched
- **Click** (or middle-click) a card to open that printing on Scryfall in a new tab
- **Download ZIP** packages every fetched image into one archive

### File Naming

```
Lightning_Bolt_m10.jpg
Black_Lotus_lea.png
Jace_the_Mind_Sculptor_wwk.jpg
```

The extension follows the selected resolution (`.png` for PNG, `.jpg` for everything else). The archive is named `scryfall-<resolution>.zip`.

---

## Output Mode 2 — Visual Decklist

Renders the whole deck as a single image using the classic stacked/fanned layout.

- **Main deck** — 5 columns, up to 4 cards per overlapping stack
- **Sideboard** — a separate right-hand column, up to 15 cards per stack, with a rotated `SIDEBOARD` label
- Cards are sorted by type (Creature → Instant → Sorcery → Enchantment → Artifact → Planeswalker → Land), then mana value, then name
- Quantities are respected — a playset appears as four overlapping copies

### Options

- **Export Resolution** — Full, Large (75%), or Medium (50%)
- **Transparent Background** — drops the purple gradient backdrop, giving a PNG with alpha for compositing elsewhere

**Download Image** saves a PNG named `visual-decklist-<timestamp>.png`.

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

A live preview renders every page before you commit. When the job spans multiple pages, use the **‹ ›** arrows to page through them. The summary line above the preview reports the layout, total card count, page count, and spacing.

**Generate PDF** saves `proxy-<size>-<timestamp>.pdf`, with a progress bar during assembly.

PNG cards are re-encoded to high-quality JPEG when building the PDF. At 63 x 88 mm a
745 x 1040 image is already around 300 DPI, so nothing is downscaled — but PNG is stored
essentially uncompressed inside a PDF, which made large proxy sets run to hundreds of
megabytes and risk failing during assembly. The re-encode cuts that by roughly 5-10x with
no visible difference at print size. Images fetched at the JPEG resolutions are passed
through untouched rather than re-encoded.

---

## Card Database

**Paper Only** and **First Print** need to know every printing of a card. Doing that per-card through the API means one paginated search per card, which triggers rate limiting fast — and Scryfall's `/cards/search` endpoint blocks cross-origin requests from some hosting origins, GitHub Pages included.

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

### Why there is no in-browser download

Earlier versions fell back to downloading Scryfall's bulk file directly in the browser when no local index was present. That path has been removed. Scryfall completed its migration to gzipped JSONL bulk files on **2026-07-20**: the `/bulk-data` manifest no longer exposes `download_uri` (it is now `jsonl_download_uri`, with `compressed_size` replacing `size`), and the payload is gzip-compressed newline-delimited JSON rather than a single JSON array.

Rebuilding the index in a tab would mean streaming roughly 460 MB of decompressed data to reproduce a file that `update_bulk_data.py` already generates offline in seconds. When the local file is missing, the app now says so plainly and falls back to per-card API lookups, where rate limits apply.

> **If you are upgrading:** a copy of `update_bulk_data.py` written before July 2026 will break against the new manifest. It needs to read `jsonl_download_uri` instead of `download_uri`, and to gunzip and parse the download line by line rather than as one JSON array.

---

## Metadata Cache

Resolved card data is cached in `localStorage` for **7 days** so repeat fetches skip the API entirely. Cached hits are marked with `💾` in the log.

Each option combination is cached separately — Standard, Paper Only, First Print, and Paper + First are distinct entries for the same card, so toggling options never returns a stale result.

Open the info modal to see a live breakdown by variant and a total count. **Clear All Cache** wipes every entry. When storage fills up, the oldest 30% of entries are evicted automatically.

Images are **not** cached; only metadata is.

---

## Interface Notes

- **ⓘ** (top right) opens the info modal: quick instructions, supported formats, changelog, cache management, and database status. It fades out as you scroll.
- The progress area shows a phase label, a per-phase counter, and a scrolling log.
- There is one undocumented option, unlocked by a keyboard sequence, that swaps cards for their showcase, borderless, Universes Beyond, and Secret Lair printings where available. It relies on Scryfall's `/cards/search` endpoint and so may not work on all hosting origins.

---

## API & Attribution

This tool uses the [Scryfall REST API](https://scryfall.com/docs/api). Card data and images are © Wizards of the Coast and their respective artists. Scryfall provides card data under the [DMCA safe harbour](https://scryfall.com/docs/api#usage).

Proxies generated with this tool are for personal playtesting only. Do not sell them, and do not use them in sanctioned play.

Created by **ianos** · [GitHub](https://github.com/ianos93/scryfall-image-downloader/) · Powered by [Scryfall](https://scryfall.com)
