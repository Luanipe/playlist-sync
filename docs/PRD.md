# PRD — playlist-sync

## Problem

People who use more than one streaming service (or want to switch) have no free, private,
open-source way to move playlists, liked tracks and saved albums between them.
Hosted tools (e.g. TuneMyMusic) require sending account access to a third party.

## Product

A local application, run on demand, that connects to two accounts (source and destination),
computes what is missing in the destination and adds it. It runs on the user's computer;
nothing leaves the machine except calls to the streaming services.

Initial services: **Spotify** and **YouTube Music**, **both directions from day one**.
Architecture must make adding other services (Deezer, Tidal, Apple Music...) a matter of
writing one adapter.

## Core behavior

- **On demand.** The user runs a migration whenever they want. No background sync.
- **Additive only.** Never deletes anything, on either side. Tracks that exist only in the
  destination are reported as informational "extras" and left untouched.
- **Goal: migrate as much as possible.** Running A→B then B→A converges to the union.
- **Two-step flow:** `plan` (read-only preview) → `apply` (executes).
- **Automatic matching.** No prompts during `apply`. Matches with score ≥ threshold (default 85)
  are migrated; everything else is stored as pending in `unmatched`.
- **Unmigrated tracks report.** At the end of each run, show tracks that could not be
  migrated, grouped by playlist and reason. Also export CSV/JSON.
- **Resumable & idempotent.** Re-running never duplicates tracks. Interrupted runs can resume.

## Scope

Migrate: user playlists, liked tracks, saved albums.
Liked tracks and saved albums are modeled as "special playlists" whose destination is the library.

## User experience

1. **CLI first** (phases 1–6), same core used later by the UI.
2. **Local web UI** (phase 7): first-run wizard, "Connect Spotify" / "Connect YouTube Music"
   buttons, direction picker, playlist selection, **Plan** button, **Apply** with progress bar,
   final report.
3. Credentials: user registers their own Spotify app once (BYO Client ID, PKCE, no secret).
   YouTube Music login through a Playwright browser window. See `docs/AUTH.md`.

## Non-goals

- Hosting a public web service or multi-user backend
- Deleting or mirroring (exact sync); reordering existing playlists
- Downloading audio, playback, recommendations
- Migrating podcasts, followed artists, playlist cover images (maybe later)
- Telemetry of any kind
- Bypassing service rate limits or terms

## Success criteria

- Migrating a 500-track playlist completes unattended and is resumable.
- ≥ 90% of tracks in a typical mainstream playlist auto-match with no wrong-version errors
  (measured on a labeled fixture set, see `docs/MATCHING.md`).
- Re-running the same migration performs zero writes.
- A contributor can add a new service by implementing one adapter and passing the contract tests.

## Legal / disclaimer (to put in README)

`ytmusicapi` is unofficial and its use may conflict with YouTube's terms. Not affiliated
with Spotify or Google. Use at your own risk. Cookies grant account access and are stored
only in the OS keyring.
