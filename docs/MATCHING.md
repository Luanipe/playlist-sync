# MATCHING

Goal: given a source `Track`, choose the right track in the destination, or decide there is none.
The matcher is **service-agnostic** and **symmetric**: it only sees `Track` objects.
Wrong-version errors (live instead of studio) are the main failure to avoid.

## 1. Normalization (`core/normalize.py`)

Applied to title, artists and album before comparing:
- Unicode NFKD, strip accents, lowercase, casefold
- Collapse whitespace, remove punctuation except meaningful characters
- Remove noise suffixes/brackets that don't change identity:
  `- Remastered 2011`, `(Remastered)`, `- Single Version`, `(Deluxe Edition)`, `- Radio Edit`
  *(Radio Edit is noise only if source has no such marker; see markers below)*
- Strip featuring credits from titles: `(feat. X)`, `[with X]`, `ft. X` and move artists into the artist set
- Artist comparison is set-based and order-insensitive; split on `,`, `&`, ` x `, `;`

## 2. Version markers

Markers: `live`, `remix`, `karaoke`, `instrumental`, `acoustic`, `cover`, `sped up`, `slowed`,
`reverb`, `8d`, `nightcore`, `demo`, `radio edit`, `extended`, `tribute`, `version` qualifiers.
Extract them from title (and album when relevant) in several languages where cheap
(e.g. `ao vivo`, `en vivo`, `en directo`).

**Veto rule:** a candidate is rejected if it has a marker the source does not have.
(The reverse — source has marker, candidate lacks it — is penalized, not vetoed.)

## 3. Strategies (Strategy pattern, `core/matching/strategies.py`)

Each strategy: `score(source: Track, candidate: Track) -> float` in `[0, 1]`.

| Strategy | Method |
|---|---|
| `TitleSimilarity` | `rapidfuzz` `token_set_ratio`/`WRatio` on normalized titles |
| `ArtistSimilarity` | Jaccard-ish overlap of artist sets + fuzzy per-name match |
| `DurationProximity` | 1.0 if diff ≤ 2s, linear decay to 0 at `max_duration_diff_seconds * 2`; neutral 0.5 if either is missing |
| `AlbumSimilarity` | fuzzy on normalized album; weak signal; neutral if missing |
| `IsrcMatch` | exact ISRC equality → hard accept signal, only when both have ISRC |

## 4. Scorer (`core/matching/scorer.py`)

```
score = 100 * (0.45*title + 0.35*artist + 0.15*duration + 0.05*album)
```

Weights live in config and are overridable. `IsrcMatch == True` sets score to 100
(still subject to vetoes except duration).

## 5. Vetoes (independent of score)

Reject candidate if any:
- Duration difference > `max_duration_diff_seconds` (default 10) when both durations known
  (skipped when ISRC matches)
- Candidate has a version marker absent in source
- Artist overlap is empty after normalization

## 6. Decision

Applied to the best candidates after vetoes:

| Condition | Result |
|---|---|
| best ≥ `threshold` (default 85) and unique winner | **match** → migrate |
| `review_floor` ≤ best < threshold | `low_confidence` → `unmatched`, store best candidate |
| best < `review_floor` or no candidates | `not_found` |
| two or more candidates ≥ threshold and tiebreakers don't decide | `ambiguous` |

**Tiebreakers, in order:** ISRC match → official album/audio over video/user upload
(YouTube Music: prefer `resultType == "song"` over `"video"`) → higher score →
explicit flag matches source → earliest in service ranking.

## 7. Search query building

- Spotify destination: if ISRC available use `isrc:<code>` first; fallback `track:<title> artist:<artist>`.
- YouTube Music destination: `"<title> <primary artist>"`, filter `songs` first, then `videos` as fallback
  (videos only if no song candidate passes).
- Always limit results (default 10) and cache search results per run.

## 8. Quality gate

Create `tests/fixtures/matching_cases.json`: a labeled set (≥ 100 cases, anonymized, no personal data)
covering: same song with remaster, live vs studio, remix, feat. credits, accents, non-Latin titles
(Japanese, Cyrillic, Portuguese), covers/karaoke traps, duplicates across single/album.
Each case: source track, candidate list, expected result (`match:<id>` | `not_found` | `ambiguous`).
CI runs the matcher on this set and enforces:
- 0 wrong-version auto-matches in the "traps" group
- ≥ 90% correct overall

Any change to weights/rules must keep this gate green.
