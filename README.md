# news-image-20261122 — THE WORLD TODAY, Sunday 22 November 2026

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/cryptocollectorid/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/cryptocollectorid/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

Entry for the make.fun bounty **"Sum up 22 November's world news in one
image"** (pot $100). The program draws a newspaper front page —
**THE WORLD TODAY — Sunday 22 November 2026** — with six stories that
happened or were first reported on Sunday 22 November 2026:

1. **Iran strikes US bases in Bahrain** — Tehran claims missiles and
   drones hit two US Patriot radars; Bahrain probes an interceptor
   crash.
2. **Mexico captures El Chapo Isidro** — FBI most-wanted cartel boss
   Fausto Isidro Meza Flores seized in a Sinaloa raid; 11 killed as
   violence flares.
3. **EU and Indonesia sign trade deal** — ten years of talks end in a
   pact scrapping 98.5% of tariffs.
4. **COP31 talks deadlocked in overtime** — the climate summit in
   Antalya runs past its deadline over fossil fuels.
5. **Drones hit Russian ship in Baltic** — a cargo vessel bound for
   Kaliningrad is attacked and catches fire; the crew evacuates as
   Finland tightens security.
6. **TikTok launches deepfake detector** — a global tool helps public
   figures spot AI fakes ahead of European elections.

Sources: AP, Reuters, BBC, ANI, One Turn (22 November 2026).

## Design (second edition)

- **Masthead:** kicker line above the nameplate, a double red rule
  below it, a dateline row split left/right (date left, "SIX STORIES
  - ONE PAGE" right), and a line naming the six datelines the stories
  report from.
- **Panels:** soft drop shadow, a 3px accent line under the kicker
  band, a short ornament rule under each headline, and the key fact
  pinned in a tinted strip at the foot of the panel.
- **Tech picture:** the phone sits higher with a larger shield, and
  "REAL OR FAKE?" now has its own centred caption strip at the foot
  of the picture.
- **Footer:** a rule with the nameplate at the left, the sources
  centred, and the page number at the right.

## How it works

`main.py` is a single self-contained Python 3 program (standard library
only — no third-party packages, no network, no font files, no downloaded
images). It draws everything in code on a plain RGB canvas: a bitmap
font defined by hand in the file (5×7 glyphs), simple geometric
illustrations per story, and a hand-written PNG encoder. Two runs
produce byte-identical output.

## Run

```sh
mkdir -p out
MAKEFUN_OUTPUT_DIR=$PWD/out python3 main.py
# writes out/entry.png (1024x1024, < 1 MiB)
```

The program validates its own PNG (signature, chunk CRCs, IHDR
dimensions, IEND position) before writing it.

## License

MIT — see `LICENSE`.
