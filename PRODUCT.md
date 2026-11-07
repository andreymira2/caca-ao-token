# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Python + pywebview desktop window (WebView2 on Windows), one self-contained `ui/index.html` with inline CSS/JS, packaged as a single `.exe` by GitHub Actions. Must work offline except for Epic, fortnite-api.com and the raw `data/evento.json`; no hosted fonts or CDNs.

## Users

Andrey (owner, a designer) and his Fortnite squad friends, on Windows PCs, during the Treasure Hunters mini season (1 Nov – 5 Dec 2026). They open the app **between matches** (Alt+Tab in the lobby), check what they need in a few seconds and go back to the game. Portuguese (Brazil), Brasília time.

## Product Purpose

Track the hunt for the Pirate Shop Access token: how many chests you have opened, whether this week's prizes already dropped, when the next Treasure Hour is, and your odds of having pulled the token by now. Success = the user trusts the chest number and gets their answer at a glance.

## Positioning

Reads the player's own Epic profile, so counts and drops fill in by themselves, and knows the event schedule in Brasília time. No other tracker combines the live chest count with the weekly prize pool and the token odds.

## Operating Context

- Glance between matches: next Treasure Hour, this week's prizes still missing, chest count, today's count and rate, token odds. All of that on the main screen without clicks.
- The game itself shows the event chest total in Quests → Treasure Hunt. That number is the ground truth the app must match.
- Any Battle Royale chest (regular, rare, Sprite; opened or broken) can roll the token. Vault keys appear not to. Token odds are unconfirmed (1 in 2,000 dataminer estimate; 1 in 700k community figure).
- Weekly prize pool rotates on Saturdays 14:00 UTC; list comes from `data/evento.json` in the repo.

## Capabilities and Constraints

- Counter names in the Epic profile are unknown until a real account is read; the app must find the chest counter and let the user confirm it against the in-game number. Account stats (level, season) must never count as chests.
- Login token stored locally only; the app only reads.
- Not affiliated with Epic.

## Brand Commitments

Name: "Caça ao Token". Portuguese UI, short and direct. User feedback (7 Nov 2026): the first version felt confusing, text-heavy, with few icons; the agenda read as a wall of times and names; the chest total felt untrustworthy.

## Evidence on Hand

Real event facts in `data/evento.json` (dates, week 2 prizes, Treasure Hours, Captain's Days). No real profile data yet; nothing about chest counter names may be invented as fact.

## Product Principles

1. Trust before numbers: a count is shown as confirmed only when it matches the game.
2. Glance, then go: the main screen answers the five between-match questions in seconds.
3. Show, don't write: icons, time bars and states over sentences.
4. Never guess silently: unconfirmed odds and approximate times are labeled.
