---
name: Caça ao Token
description: A between-matches Fortnite companion that reads like the game's own lobby.
colors:
  lobby-navy: "#071447"
  lobby-deep: "#0B1E66"
  lobby-royal: "#1840C0"
  lobby-sky: "#2F6BFF"
  panel-glass: "rgba(4, 12, 52, .62)"
  panel-hi: "rgba(255, 255, 255, .07)"
  hairline: "rgba(255, 255, 255, .14)"
  text-white: "#FFFFFF"
  text-soft: "#C3D0FF"
  text-dim: "#8EA0E6"
  lobby-yellow: "#FFE14D"
  lobby-yellow-hover: "#FFEA7A"
  yellow-ink: "#2A2100"
  confirm-green: "#63E06B"
  alert-red: "#FF6A5C"
  rarity-common-hi: "#A2A7B0"
  rarity-common-lo: "#5B6069"
  rarity-uncommon-hi: "#7FD32C"
  rarity-uncommon-lo: "#2B7A0B"
  rarity-rare-hi: "#4FC8FF"
  rarity-rare-lo: "#1660B2"
  rarity-epic-hi: "#CE6BFF"
  rarity-epic-lo: "#6418AE"
  rarity-legendary-hi: "#FFB24A"
  rarity-legendary-lo: "#C14F14"
  rarity-mythic-hi: "#FFE36A"
  rarity-mythic-lo: "#C2860E"
  rarity-icon-hi: "#3BE0E6"
  rarity-icon-lo: "#0D6E82"
typography:
  display:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "128px"
    fontWeight: 400
    lineHeight: 0.9
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "76px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.01em"
  numeral:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "34px"
    fontWeight: 400
    lineHeight: 1
  title:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.03em"
  button:
    fontFamily: "Anton, Arial Narrow, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.03em"
  body:
    fontFamily: "Barlow Semi Condensed, Segoe UI, sans-serif"
    fontSize: "15px"
    fontWeight: 500
    lineHeight: 1.4
  label:
    fontFamily: "Barlow Semi Condensed, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.04em"
rounded:
  bar: "2px"
  sm: "3px"
  md: "4px"
  tile: "5px"
  panel: "6px"
  card: "8px"
  track: "10px"
spacing:
  xs: "6px"
  sm: "10px"
  md: "16px"
  lg: "22px"
  xl: "28px"
components:
  button-primary:
    backgroundColor: "{colors.lobby-yellow}"
    textColor: "{colors.yellow-ink}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
  button-primary-hover:
    backgroundColor: "{colors.lobby-yellow-hover}"
  button-secondary:
    backgroundColor: "rgba(255, 255, 255, .12)"
    textColor: "{colors.text-white}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
  button-secondary-hover:
    backgroundColor: "rgba(255, 255, 255, .2)"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.text-white}"
    typography: "{typography.button}"
    rounded: "{rounded.sm}"
    padding: "10px 18px"
  tab:
    backgroundColor: "transparent"
    textColor: "{colors.text-soft}"
    rounded: "{rounded.sm}"
    padding: "9px 18px"
  tab-hover:
    backgroundColor: "{colors.panel-hi}"
    textColor: "{colors.text-white}"
  tab-active:
    backgroundColor: "{colors.lobby-yellow}"
    textColor: "{colors.yellow-ink}"
  chip:
    backgroundColor: "rgba(255, 255, 255, .12)"
    textColor: "{colors.text-white}"
    typography: "{typography.label}"
    rounded: "{rounded.sm}"
    padding: "5px 10px"
  chip-confirmed:
    backgroundColor: "rgba(99, 224, 107, .18)"
    textColor: "{colors.confirm-green}"
  chip-live:
    backgroundColor: "{colors.lobby-yellow}"
    textColor: "{colors.yellow-ink}"
  panel:
    backgroundColor: "{colors.panel-glass}"
    textColor: "{colors.text-white}"
    rounded: "{rounded.panel}"
    padding: "18px 20px"
  item-tile:
    backgroundColor: "{colors.rarity-rare-lo}"
    textColor: "{colors.text-white}"
    rounded: "{rounded.tile}"
  input-game:
    backgroundColor: "rgba(0, 0, 30, .45)"
    textColor: "{colors.text-white}"
    rounded: "{rounded.sm}"
    padding: "10px 12px"
    width: "140px"
---

# Design System: Caça ao Token

## Overview

**Creative North Star: "The Lobby Between Matches"**

The app is a room the player already knows: the saturated blue Fortnite lobby, its heavy condensed caps leaning forward, its item shop of rarity-framed tiles with a refresh timer. A player who Alt+Tabs in mid-session should find the chest count, the next Treasure Hour, the missing prizes and the token odds without reading, because every element sits where the game taught them to look. The world is loud in colour and type but sparse in words: big numerals, short Portuguese labels, drawn line icons, bars instead of sentences.

Density is "one glance": the main view fits a short desktop window without scrolling, and secondary views (Prêmios, Agenda, Conta) only extend what the lobby already shows. Depth comes from a glowing radial field with diagonal light streaks behind translucent navy glass panels; colour is reserved. Yellow means "act" or "live". Rarity gradients belong only to item tiles. Everything else is blue, white and soft periwinkle.

It rejects the grey, dark-card admin dashboard of the first version: no neutral greys as surfaces, no small centred text blocks, no walls of times and names.

**Key Characteristics:**
- Lobby-blue radial field with faint 115° light streaks, fixed behind everything.
- Anton caps, skewed forward (about -7° to -8°), for every number, title, tab and button.
- Parallelogram controls: tabs, buttons, the mark badge and step numbers are skewed boxes with upright contents.
- One yellow, used for the primary action, the active tab, focus and anything live.
- Rarity gradients on item tiles only; the prize row is the signature.
- One-stroke drawn line icons (2px stroke, round caps) beside nearly every heading and label.

## Colors

A saturated lobby blue family carries every surface, white and periwinkle carry the text, and one hot yellow carries action; rarity colours live in item tiles and nowhere else.

### Primary
- **Lobby Yellow** (lobby-yellow): primary buttons (Atualizar, Conectar), the active tab, the mark badge, the "now" agenda event, step numbers, owned stamps on tiles, the today bar, odds fills, the focus ring and text selection. Hover lightens to Lobby Yellow Hover. Always paired with Yellow Ink text, never white.
- **Yellow Ink** (yellow-ink): the near-black olive used for text and icons on yellow, and inverted as a fill inside the live Treasure Hour panel.

### Secondary
- **Rarity gradients** (rarity-*-hi to rarity-*-lo, 160°): common, uncommon, rare, epic, legendary, mythic and icon series, each a light-to-dark diagonal. They fill item tiles, so a prize reads at its in-game rarity before its name is read. Mythic doubles as the token medallion and the token-found card. Icon-series cyan (rarity-icon-hi) also marks Captain's Day in the agenda; legendary marks the event finale.

### Tertiary
- **Confirm Green** (confirm-green): only the "confere com o jogo" state, as text on an 18% green wash. It is the trust signal for the chest count and is not used decoratively.
- **Alert Red** (alert-red): error banners, as a 16% wash with a 50% border.

### Neutral
- **Lobby Navy / Deep / Royal / Sky** (lobby-navy, lobby-deep, lobby-royal, lobby-sky): the four stops of the background radial, brightest at top left, sinking to navy at the edges.
- **Panel Glass** (panel-glass): 62% navy fill for every panel and agenda day; the field glows through it.
- **Panel Highlight** (panel-hi): 7% white for tab hover and inner event rows.
- **Hairline** (hairline): 14% white for panel borders, the header rule, section dividers and table rows.
- **Text White** (text-white): numerals, titles, item names.
- **Text Soft** (text-soft): panel headings, inactive tabs, secondary copy.
- **Text Dim** (text-dim): small print and table headers only.

### Named Rules
**The One Yellow Rule.** Yellow means "press this" or "this is happening now". A screen has one yellow button; any other yellow must be a live state, the active tab or an owned stamp.

**The Rarity Belongs to Items Rule.** Rarity gradients fill item tiles, the token medallion and event-type icons only. Panels, buttons and backgrounds never take a rarity colour.

**The No Grey Rule.** There are no neutral grey surfaces. Every dark surface is a translucent navy over the blue field.

## Typography

**Display Font:** Anton (with Arial Narrow, sans-serif), bundled locally as woff2
**Body Font:** Barlow Semi Condensed, 500/600/700 (with Segoe UI, sans-serif), bundled locally

**Character:** Anton is the lobby's shouted header: tall, condensed, all caps, leaning forward. Barlow Semi Condensed is the quiet narrow sans that carries labels and the few sentences, close enough in width to sit beside Anton without looking soft.

### Hierarchy
- **Display** (Anton 400, 128px, line-height 0.9): the chest count only. Drops to 84px in short windows.
- **Headline** (Anton 400, 76px, 1): the Treasure Hour countdown; 64px for the odds percentage, 54px for the agenda's next event. Drops to 52px / 44px in short windows.
- **Numeral** (Anton 400, 34px, 1): secondary stats (today, per hour); 21–26px for agenda times and day names.
- **Title** (Anton 400, 18px, 0.03em, uppercase): panel headings in Text Soft, led by a yellow line icon.
- **Button** (Anton 400, 16–17px, 0.03em, uppercase): buttons and tabs.
- **Body** (Barlow SC 500, 15px, 1.4): sentences, event labels, list rows. Keep runs short; this UI does not set paragraphs.
- **Label** (Barlow SC 700, 11–13px, 0.04–0.06em, uppercase): chips, stat captions, item types, owned stamps, table heads.

All numbers use tabular figures.

### Named Rules
**The Leaning Caps Rule.** Every Anton element that reads as a header or number is skewed forward (skewX -7°, origin bottom left). Anton has no italic; the skew is the italic. Body text never leans.

**The Numbers Shout Rule.** The answer is the biggest thing in its panel. A count, countdown or percentage is set in Anton at numeral size or larger, with its label in small Barlow caps underneath or beside it.

## Layout

A full-height app shell: a header bar (mark, four icon tabs, timestamp, refresh button at the far right) above a scrolling main area with a 28px side gutter (22px top). The main view is a 12-column grid with 16px gaps: chest panel 7 + Treasure Hour 5 on the first row, prize row 8 + odds 4 on the second. Secondary views use full-width panels or an auto-fill grid of 200px agenda day cards; the full prize shop auto-fills 140px tiles.

Spacing works in a tight 6 / 10 / 16 / 22 / 28px rhythm; panels pad 18px 20px. Under 1100px wide the header tightens and drops the account name; under 900px every column spans 12 and the header wraps. Under 760px tall the whole Painel compresses (smaller numerals, 150px tiles, 12px gaps) so all four answers stay in view without scrolling, which is the operating promise.

## Elevation & Depth

Depth is atmospheric: a glowing radial field behind translucent glass panels, with soft ambient shadows lifting the panels off the field. There is no stacked elevation scale; panels sit on one plane, and only the toast and the token-found overlay float above it.

### Shadow Vocabulary
- **Panel lift** (`box-shadow: 0 10px 30px rgba(0,0,20,.25)`): every panel at rest.
- **Floating** (`box-shadow: 0 10px 30px rgba(0,0,0,.4)`): toast.
- **Modal** (`box-shadow: 0 20px 60px rgba(0,0,0,.5)`): token-found card over an 80% navy scrim.
- **Tile rim** (`box-shadow: inset 0 0 0 2px rgba(255,255,255,.25)`): the bright inner frame on item tiles.
- **Art drop** (`filter: drop-shadow(0 6px 8px rgba(0,0,0,.35))`): item art cut-outs over their gradient, under a radial white glow at 35% from the top.

### Named Rules
**The Glow Behind Rule.** Light comes from the field, not from the panels. Panels stay translucent so the radial and its streaks read through them; never make a panel opaque.

## Shapes

Small, hard-edged corners and forward-leaning parallelograms. Controls are skewed boxes (skewX -8°) with 3px corners whose contents are counter-skewed upright; the mark badge and numbered steps follow the same shape at 4px. Panels and day cards are plain rectangles at 6px, item tiles 5px at a 3:4 portrait ratio, the overlay card 8px. Only progress tracks are fully rounded (10px), and only the token medallion is a circle.

## Components

### Buttons
Forward-leaning, loud, few.
- **Shape:** skewed parallelogram, 3px corners, contents counter-skewed.
- **Primary:** Lobby Yellow with Yellow Ink, Anton caps, icon + verb, 10px 18px.
- **Hover / Focus:** primary lightens to Lobby Yellow Hover; secondary goes from 12% to 20% white. Focus is a 3px yellow outline at 2px offset everywhere. Background transitions in 0.15s. While refreshing, the icon spins.
- **Secondary:** 12% white fill, white text. **Ghost:** transparent with a 2px 30% white inset ring (used for "Conferir de novo"). Disabled drops to 50% opacity.

### Tabs
Parallelogram buttons in the header, each an icon plus Anton caps label. Inactive in Text Soft, hover fills Panel Highlight, the active tab is solid yellow with Yellow Ink.

### Chips
- **Style:** 3px corners, Barlow 700 caps at 13px, optional 15px icon, 5px 10px, 12% white by default. Chips do not skew.
- **State:** confirmed is green text on a green wash; "falta conferir", warnings and live states are solid yellow with Yellow Ink. Chips sit right-aligned in panel headings.

### Panels
- **Corner Style:** 6px.
- **Background:** Panel Glass over the field; turns into a yellow gradient (#FFE96E to #FFC21F) with Yellow Ink text when the Treasure Hour is live.
- **Shadow Strategy:** panel lift (see Elevation & Depth).
- **Border:** 1px hairline.
- **Internal Padding:** 18px 20px; headings use the Title role with a yellow line icon and a trailing chip.

### Inputs / Fields
- **Style:** dark navy well (45% navy) with a 2px 25% white border, 3px corners; the in-game count field uses Anton at 22px so the typed number matches the display numerals.
- **Focus:** border turns Lobby Yellow, no outline.

### Prize Row (signature)
The weekly prize pool shown as an item-shop row: equal 3:4 tiles filled with their rarity gradient, art centred in the top 74% over a soft white glow, and a dark bottom band with the item name in leaning Anton caps and its type in small Barlow caps. Owned items carry a yellow "Na conta" stamp top right and dim their art to 55%; auto-detected drops show the chest number top left. The panel heading carries the "saem em" refresh countdown as a chip, like the shop's timer. Tiles rise 2px on hover.

### Odds Bars
A mythic-gold token medallion beside the main percentage in Headline Anton, then three scenario rows: label, a 10px rounded track at 12% white with a yellow fill, and the percentage right-aligned in Anton.

### Agenda Events
Rows on a 7% white fill with a 40px square icon well coloured by event type (yellow Treasure Hour, cyan Captain's Day, white-wash prize reset, legendary finale), the time in leaning Anton and the label in Barlow. The current event turns solid yellow with its icon inverted; past days and events fade to 45%.

## Do's and Don'ts

### Do:
- **Do** set every number that answers a question in Anton, skewed -7°, at 34px or larger, with tabular figures.
- **Do** pair each heading, tab, chip and stat label with a one-stroke line icon (24px grid, 2px stroke, round caps and joins).
- **Do** keep yellow for the single primary action, the active tab, focus, owned stamps and live states, always with Yellow Ink text.
- **Do** show prizes as rarity-gradient 3:4 tiles with art, a dark name band and an owned stamp.
- **Do** keep panels translucent navy (62%) with a 1px 14% white hairline so the lobby field glows through.
- **Do** make every control a skewed parallelogram (-8°) with upright contents and 3px corners.
- **Do** keep the Painel's four answers visible without scrolling down to a 760px-tall window.

### Don't:
- **Don't** use neutral grey surfaces or opaque dark cards; that is the v0.1 dashboard this world replaced.
- **Don't** put rarity gradients on panels, buttons or backgrounds.
- **Don't** set white text on yellow, or add a second yellow button to a view.
- **Don't** skew body text or chips; only Anton headers, numerals and controls lean.
- **Don't** explain in sentences what a bar, icon or state can show.
- **Don't** load fonts or icons from a CDN; fonts ship as local woff2 and icons as inline SVG symbols.
