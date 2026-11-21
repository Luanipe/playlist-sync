# ARCHITECTURE

## 1. Layers and dependency rule

```
interfaces (cli.py, ui/)          ← composition root: wires registry + DI
        │
        ▼
core/ (MigrationService, DiffEngine, matching, plan/commands)
        │
        ▼
domain/ (Track, Playlist, Album)   services/base.py (StreamingService, ABC)
        ▲                                  ▲
        │                                  │
storage/ (Repository, SQLite)      services/<name>/ (adapters, vendor SDKs)
reporting/
```

Rules:
- Arrows point to what a layer may import. `domain/` imports nothing from the project.
- `core/` depends only on `domain/`, `services/base.py`, `storage/` interfaces.
- Vendor SDKs (`spotipy`, `ytmusicapi`, `playwright`) are imported only inside `services/<name>/`.
- `core/` is **direction-agnostic**: it never knows which service is source or destination.

## 2. Folder layout

```
playlist-sync/
├── AGENTS.md  opencode.json  pyproject.toml  README.md  LICENSE
├── docs/
├── .opencode/{agent,command}/
├── src/playlist_sync/
│   ├── errors.py
│   ├── config.py                 # pydantic settings + config.toml
│   ├── domain/models.py          # Track, Playlist, Album, TrackRef
│   ├── services/
│   │   ├── base.py               # StreamingService ABC + Capabilities
│   │   ├── registry.py           # ServiceRegistry (+ entry-point discovery)
│   │   ├── decorators.py         # with_retry, rate_limited
│   │   ├── auth/{base,spotify_pkce,ytmusic_browser,ytmusic_headers,token_store}.py
│   │   ├── spotify/{adapter,mapper}.py
│   │   └── ytmusic/{adapter,mapper}.py
│   ├── core/
│   │   ├── singleton.py          # SingletonMeta
│   │   ├── normalize.py          # text normalization
│   │   ├── matching/{strategies,scorer,matcher}.py
│   │   ├── diff.py               # DiffEngine
│   │   ├── plan.py               # MigrationPlan + Action commands
│   │   ├── linker.py             # PlaylistLinker
│   │   └── migration.py          # MigrationService (plan/apply orchestration)
│   ├── storage/{repository,sqlite_repo,schema.sql}.py
│   ├── reporting/{summary,export}.py
│   ├── cli.py
│   └── ui/                       # phase 7
└── tests/
    ├── fakes/fake_service.py
    ├── contract/test_streaming_service_contract.py   # reusable for any adapter
    ├── fixtures/                 # anonymized recorded API responses
    └── unit/ integration/
```

## 3. Domain models (`domain/models.py`)

Frozen `dataclass(slots=True)`:

```python
@dataclass(frozen=True, slots=True)
class Track:
    service: str               # "spotify", "ytmusic"
    id: str                    # service-native id
    title: str
    artists: tuple[str, ...]
    album: str | None = None
    duration_ms: int | None = None
    isrc: str | None = None
    explicit: bool | None = None
    set_video_id: str | None = None   # ytmusic playlist-item id, if needed; adapters only

@dataclass(frozen=True, slots=True)
class Playlist:
    service: str
    id: str
    name: str
    description: str = ""
    track_count: int | None = None
    kind: Literal["playlist", "liked", "saved_albums"] = "playlist"

@dataclass(frozen=True, slots=True)
class Album:
    service: str
    id: str
    title: str
    artists: tuple[str, ...]
    year: int | None = None
    track_count: int | None = None
```

## 4. Adapter interface (`services/base.py`)

```python
class StreamingService(ABC):
    name: ClassVar[str]

    @abstractmethod
    def capabilities(self) -> Capabilities: ...          # e.g. supports_isrc_search

    # auth
    @abstractmethod
    def authenticate(self) -> None: ...                  # raises AuthExpiredError if needs relogin
    @abstractmethod
    def is_authenticated(self) -> bool: ...

    # read
    @abstractmethod
    def get_playlists(self) -> list[Playlist]: ...
    @abstractmethod
    def get_playlist_tracks(self, playlist_id: str) -> list[Track]: ...
    @abstractmethod
    def get_liked_tracks(self) -> list[Track]: ...
    @abstractmethod
    def get_saved_albums(self) -> list[Album]: ...
    @abstractmethod
    def search_track(self, query: Track, limit: int = 10) -> list[Track]: ...

    # write (ADDITIVE ONLY)
    @abstractmethod
    def create_playlist(self, name: str, description: str = "") -> Playlist: ...
    @abstractmethod
    def add_tracks(self, playlist_id: str, track_ids: Sequence[str]) -> None: ...
    @abstractmethod
    def like_tracks(self, track_ids: Sequence[str]) -> None: ...
    @abstractmethod
    def save_albums(self, album_ids: Sequence[str]) -> None: ...
```

**There are no remove/delete methods. Do not add any.**
Adapters must: paginate fully, batch writes within vendor limits, translate vendor errors
into `playlist_sync.errors`, and map vendor payloads to domain models in `mapper.py`
(pure functions, unit-tested with fixtures).

Album saving across services needs album matching: search the album by title+artists,
or resolve via tracks. Document the chosen approach in `DECISIONS.md` when you reach it.

## 5. Singleton + Registry

```python
class SingletonMeta(type):
    _instances: dict[type, object] = {}
    _lock = threading.Lock()
    def __call__(cls, *a, **kw):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*a, **kw)
        return cls._instances[cls]
    @classmethod
    def reset(mcs) -> None: ...        # tests only
```

Each real adapter (`SpotifyService`, `YTMusicService`) uses `metaclass=SingletonMeta`
(combine with `ABC`'s metaclass via a small derived metaclass).

`ServiceRegistry`:
- `register(name, factory)`, `get(name)` → the singleton instance, `available()` → names
- Discovers third-party adapters from entry-point group **`playlist_sync.services`**
  via `importlib.metadata.entry_points`
- `reset()` for tests

Testability: core receives services as arguments. Tests use `FakeService` (not a singleton).

## 6. Resilience (`services/decorators.py`)

- `@with_retry`: exponential backoff + jitter (`tenacity`) on `RateLimitError` and
  `ServiceUnavailableError`; honor `Retry-After` when present. Never retry on `AuthExpiredError`.
- `@rate_limited(calls_per_second=...)`: token bucket per adapter, configurable.
- Apply to adapter methods that hit the network.

## 7. Plan and actions (Command pattern) — `core/plan.py`

```python
class Action(Protocol):
    mutates: ClassVar[bool]
    def describe(self) -> str: ...
    def execute(self, ctx: ExecContext) -> ActionResult: ...
```

| Action | mutates | Notes |
|---|---|---|
| `CreatePlaylist` | yes | destination playlist missing |
| `AddTracks` | yes | batches of resolved destination track ids |
| `LikeTracks` | yes | liked tracks → library |
| `SaveAlbums` | yes | saved albums → library |
| `NotFound` | no | persists to `unmatched` |
| `LowConfidence` / `Ambiguous` | no | persists to `unmatched` with best candidate |
| `ExtraInDestination` | no | informational only, hidden unless `--show-extras` |

`MigrationPlan` = ordered list of actions + summary stats. It is serializable to JSON so a
plan can be saved, inspected and resumed. `plan()` builds it without any write.
`apply(plan)` executes only `mutates=True` actions, records progress in `runs`, and is idempotent.

## 8. Diff algorithm (three layers)

For each source track in a source playlist, find whether it already exists in the linked
destination playlist:

1. **Equivalence map** (`track_matches`): known mapping source→destination id. If the
   destination id is already in the destination playlist → skip. If known but not in
   playlist → `AddTracks`.
2. **Normalized comparison** against the current destination playlist contents
   (fuzzy title+artist+duration via `core/matching`). Catches tracks the user added manually.
   Save the discovered mapping to `track_matches`.
3. **Search** in the destination (`search_track`) + full matching. Only for what remains.
   Respect `unmatched` retry policy (see below).

Handle: duplicates within a playlist (dedupe by resolved destination id), tracks
unavailable in the destination (permanent `NotFound` until retry window), ignored tracks.

Playlist order: preserved only at creation; later runs append at the end.

### Unmatched retry policy
- `not_found`: retry after `retry_not_found_days` (default 30) or with `--retry-unmatched`
- `low_confidence` / `ambiguous`: not retried automatically; resolved via `sync unmatched`
  (user picks candidate, pastes link/id, or marks "ignore forever")
- `error`: retried on next run
- `ignored = 1`: never retried, never reported

## 9. PlaylistLinker

Decides which source playlist ↔ which destination playlist:
1. `playlist_links` table
2. Exact normalized name match in destination
3. Otherwise create a new destination playlist (`CreatePlaylist`) and save the link
Never prompts during `apply`. If several destination playlists match, pick the oldest-linked
or first exact match deterministically and record it; surface in the report.

## 10. Storage (SQLite via Repository)

Access only through `storage/repository.py` (ABC) with `SqliteRepository` implementation.
Location: `platformdirs.user_data_dir("playlist-sync")`. Use migrations by `PRAGMA user_version`.
Directions are always stored explicitly (source service → target service).

```sql
CREATE TABLE track_matches (
  id INTEGER PRIMARY KEY,
  source_service TEXT NOT NULL, source_track_id TEXT NOT NULL,
  target_service TEXT NOT NULL, target_track_id TEXT NOT NULL,
  score REAL NOT NULL, manual INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  UNIQUE (source_service, source_track_id, target_service)
);
CREATE TABLE playlist_links (
  id INTEGER PRIMARY KEY,
  source_service TEXT NOT NULL, source_playlist_id TEXT NOT NULL,
  target_service TEXT NOT NULL, target_playlist_id TEXT NOT NULL,
  created_at TEXT NOT NULL,
  UNIQUE (source_service, source_playlist_id, target_service)
);
CREATE TABLE unmatched (
  id INTEGER PRIMARY KEY,
  source_service TEXT NOT NULL, source_track_id TEXT NOT NULL,
  target_service TEXT NOT NULL,
  playlist_source_id TEXT,
  track_json TEXT NOT NULL,
  reason TEXT NOT NULL CHECK (reason IN ('not_found','low_confidence','ambiguous','error')),
  best_candidate_json TEXT, best_score REAL,
  attempts INTEGER NOT NULL DEFAULT 1,
  first_attempt_at TEXT NOT NULL, last_attempt_at TEXT NOT NULL,
  ignored INTEGER NOT NULL DEFAULT 0,
  UNIQUE (source_service, source_track_id, target_service)
);
CREATE TABLE runs (
  id INTEGER PRIMARY KEY,
  started_at TEXT NOT NULL, finished_at TEXT,
  source_service TEXT NOT NULL, target_service TEXT NOT NULL,
  stats_json TEXT
);
```

## 11. Reporting

End-of-run summary (terminal via `rich`, plus CSV/JSON in the reports dir):

1. **Migrated**: playlists created, tracks added/liked, albums saved
2. **Not migrated**: grouped by playlist then reason, with best candidate + score if any
3. **Informational differences**: `ExtraInDestination`, only with `--show-extras`

## 12. Configuration (`config.toml`, pydantic)

```toml
[matching]
threshold = 85
review_floor = 60
max_duration_diff_seconds = 10
retry_not_found_days = 30

[rate_limit]
spotify_calls_per_second = 5
ytmusic_calls_per_second = 2

[paths]
# optional overrides; defaults come from platformdirs
```

CLI flags override config (`--threshold 90`). Secrets are never in config.

## 13. CLI (`typer`)

```
playlist-sync auth spotify|ytmusic
playlist-sync plan  --from spotify --to ytmusic [--playlist NAME ...] [--liked] [--albums] [--threshold N] [--save plan.json]
playlist-sync apply [--plan plan.json | --from ... --to ...] [--show-extras]
playlist-sync unmatched [list|resolve|ignore] [--export csv|json]
playlist-sync fix  ...                      # change a wrong automatic match (phase 6)
playlist-sync ui                            # phase 7
```

## 14. Testing strategy

- Unit: normalization, strategies, scorer, mappers, diff, plan serialization
- Contract tests (`tests/contract`): parametrized over adapters; `FakeService` always included.
  Any new adapter must pass them. Real adapters run contract tests against recorded fixtures only.
- Integration: `MigrationService` with two `FakeService`s (both directions, idempotency,
  resume, unmatched report)
- Property-like cases for normalization (accents, `feat.`, `- Remastered`, brackets)
- Coverage target: ≥ 85% for `core/` and `domain/`
