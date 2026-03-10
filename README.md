# ✦ Scryfall Image Downloader

A browser-based tool for downloading Magic: The Gathering card images via the [Scryfall API](https://scryfall.com/docs/api). No installation required — open the page, paste your card list, and download a ZIP of high-quality card images.

---

## Features at a Glance

- Paste card names or upload a `.txt` deck list file
- Supports all major deck list export formats
- Six image resolution options (Small through PNG)
- **Paper Only** — exclude digital-only prints (MTGO, Arena)
- **First Print** — automatically fetch the oldest printing of each card
- Visual card preview grid with hover details
- Click or middle-click any card to open its Scryfall page
- Download all fetched images as a single ZIP file

---

## Getting Started

Open `index.html` in any modern browser. No server, build step, or API key is needed.

If hosting on GitHub Pages, push `index.html` (and optionally `favicon.png`) to the root of your repository and enable Pages under **Settings → Pages → Branch: main**.

---

## Entering Card Names

### Typing or Pasting

Type or paste card names into the **Card Names** text area, one card per line. The input field accepts a wide range of formats — see [Supported Input Formats](#supported-input-formats) below.

### Uploading a File

Drag and drop a `.txt` file onto the **Upload List** panel, or click the panel to browse for a file. The file's contents are loaded directly into the card name field. Standard deck export files from tools like Moxfield, Archidekt, EDHREC, and MTG Arena are all supported.

---

## Supported Input Formats

The parser handles virtually every common deck list export format. Quantities, set codes, collector numbers, and special syntax are all stripped automatically — only the card name is used for the lookup.

### Quantities

```
4 Lightning Bolt
4x Lightning Bolt
4X Lightning Bolt
4× Lightning Bolt
```

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

> **Note:** Bare (unbracketed) set codes must be written in ALL-CAPS (e.g. `M10`, `BRO`, `MH3`) to avoid ambiguity with card name words. Bracketed set codes like `(m10)` are accepted in any case.

### Double-Faced Cards

Only the front face name is needed. The `//` separator is stripped automatically:

```
Fire // Ice
```

### Deck Section Headers

Lines matching common export headers are automatically filtered out and not treated as card names:

```
Deck
Sideboard
Commander
Companion
Maybeboard
About
```

### Deduplication

Duplicate entries (case-insensitive) are silently ignored. Each unique card is fetched once.

---

## Image Resolution

Choose the resolution before clicking **Summon Cards**. The selection applies to all cards in the batch.

| Option | Dimensions | Format | Best For |
|---|---|---|---|
| Small | 146 × 204 px | JPEG | Thumbnails, quick previews |
| Normal | 488 × 680 px | JPEG | Standard use, most deck tools |
| Large | 672 × 936 px | JPEG | High quality printing |
| PNG | 745 × 1040 px | PNG | Lossless, highest quality |
| Art Crop | Varies | JPEG | Art only, no card frame |
| Border Crop | Varies | JPEG | Full card, border removed |

---

## Fetch Options

### Paper Only

When enabled, the downloader checks the `games` field on every fetched card. If a card is only available digitally (MTGO, Arena), it automatically searches for the closest paper-printed version using the Scryfall search API with `game:paper`.

- If a paper printing is found, it is used instead and flagged with **⚠ alt print used** in the log
- If no paper printing exists at all, the card is marked as an error

### First Print

When enabled, the downloader searches for the oldest known printing of each card by querying Scryfall sorted by `released` ascending. This is useful for getting original artwork and the earliest set symbol.

- If the card you specified is already the oldest printing, it is kept as-is with no warning
- If a different (older) printing is found, it is swapped in and flagged with **⚠ alt print used** in the log
- If the first print search fails, the originally fetched card is kept as a silent fallback

### Combining Both Options

Paper Only and First Print can be active simultaneously. When both are on, the downloader searches for the **oldest paper printing** — useful for getting the original Alpha/Beta/Revised printing of classic cards while excluding any digital-only reprints.

---

## The Fetch Process

Once you click **Summon Cards**, the downloader processes each card in sequence with a short delay between requests to comply with [Scryfall's rate limit guidelines](https://scryfall.com/docs/api#rate-limits).

### Search Strategy (3-tier fallback)

For each card, the following attempts are made in order:

1. **Exact name search** — `GET /cards/named?exact=<name>` (optionally with `&set=` if a set code was provided). Precise matching, will not match tokens or variants.
2. **Fuzzy name search** — `GET /cards/named?fuzzy=<name>`. Catches minor typos and alternate spellings.
3. **Name-only fuzzy fallback** — If a set code was specified but not found, drops the set and searches by name only. This result is flagged with a yellow warning in the log.

For set + collector number inputs (e.g. `M10 93`), the direct endpoint `GET /cards/:code/:number` is used instead, bypassing name search entirely.

### Log Colours

| Colour | Meaning |
|---|---|
| 🔵 Blue | Card found exactly as requested |
| 🟡 Yellow | Fallback or alternate print was used |
| 🔴 Red | Card could not be found |

---

## Card Preview Grid

Successfully fetched cards appear as a visual grid below the progress bar. Cards that fail are not shown in the grid — errors appear only in the log.

### Hovering

Hover over any card to see a frosted info panel slide up from the bottom of the tile, showing:
- The card's full name
- The set code of the specific printing fetched

### Opening on Scryfall

Click any card (left-click or middle/scroll-wheel click) to open that exact printing on Scryfall in a new tab.

---

## Downloading Images

Once at least one card has been fetched successfully, the **Download ZIP** button becomes active. Clicking it packages all fetched images into a single `.zip` file and downloads it.

### File Naming

Each image file inside the ZIP is named using the card name and set code:

```
Lightning_Bolt_m10.jpg
Black_Lotus_lea.png
Jace_the_Mind_Sculptor_wwk.jpg
```

The file extension matches the selected resolution (`.jpg` for all sizes except PNG, which uses `.png`).

---

## API & Attribution

This tool uses the [Scryfall REST API](https://scryfall.com/docs/api). Card data and images are © Wizards of the Coast and their respective artists. Scryfall provides card data under the [DMCA safe harbour](https://scryfall.com/docs/api#usage).

Per Scryfall's guidelines, requests are spaced 120ms apart and include a descriptive `User-Agent` header.
