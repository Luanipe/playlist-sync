# AUTH

Principle: the user should do as little as possible, and secrets never touch disk in plain text.

> **Before implementing, verify against current documentation:** Spotify Web API access rules for
> apps in development mode (user limits, allowlist, redirect URI requirements — loopback must use
> `127.0.0.1`, not `localhost`), the PKCE flow, and `ytmusicapi`'s currently supported auth methods.
> These change over time. If reality differs from this document, stop and ask.

## 1. Interface (`services/auth/base.py`)

```python
class AuthProvider(ABC):
    @abstractmethod
    def login(self) -> None: ...            # interactive, user-driven
    @abstractmethod
    def is_logged_in(self) -> bool: ...
    @abstractmethod
    def get_credentials(self) -> Any: ...   # opaque to core; consumed only by the adapter
    @abstractmethod
    def logout(self) -> None: ...           # deletes local credentials only
```

Adapters receive an `AuthProvider` (Strategy). Core never sees credentials.
On 401/403 the adapter raises `AuthExpiredError`; UI/CLI then shows "Reconnect <service>".

## 2. Token store (`services/auth/token_store.py`)

- Backed by `keyring` (service name `playlist-sync`, key per provider).
- Interface: `get(key)`, `set(key, value)`, `delete(key)`.
- If no keyring backend is available, fail with a clear message explaining how to proceed;
  do **not** fall back to plain-text files silently. (Optional later: explicit opt-in encrypted file.)
- Never log values.

## 3. Spotify — OAuth 2.0 Authorization Code with PKCE

- **Bring-your-own Client ID**: each user registers their own app in the Spotify developer dashboard.
  No Client Secret is used. The Client ID is stored in `config.toml` (it is not a secret).
- Redirect URI: `http://127.0.0.1:<port>/callback`. Default port configurable (e.g. 8765).
  The setup wizard shows the exact URI ready to copy.
- Flow: generate `code_verifier`/`code_challenge` (S256) → open browser to authorize →
  temporary local HTTP server receives the callback → exchange code for tokens →
  store access+refresh tokens in keyring → auto-refresh before expiry.
- Required scopes (minimum): `playlist-read-private`, `playlist-read-collaborative`,
  `playlist-modify-private`, `playlist-modify-public`, `user-library-read`, `user-library-modify`.
  Do not request more.
- Validate `state` on callback. Server binds to loopback only and shuts down right after the callback.
- `spotipy` may be used if it supports PKCE cleanly with a custom cache handler backed by the token store;
  otherwise implement the small PKCE flow directly with `httpx`/`requests`. Record the choice in `DECISIONS.md`.

## 4. YouTube Music — Playwright browser login (default)

Provider: `ytmusic_browser.py`. Requires the optional extra `playlist-sync[ytmusic-login]`.

1. On first connect, if Playwright browsers are missing, run `playwright install chromium`
   with visible progress (CLI: rich progress; UI: progress bar).
2. Launch a **visible** (never headless) persistent context:
   `launch_persistent_context(user_data_dir=<app dir>/browser-profile, headless=False)`
   pointing to `https://music.youtube.com`.
3. The user logs in normally (2FA, passkeys…). The program never sees the password.
4. Detect login completion: required auth cookies present (e.g. `SAPISID`/`__Secure-3PAPISID`)
   and the page shows a signed-in state. Timeout (default 5 min) → `AuthTimeoutError`.
5. Capture cookies for `music.youtube.com`/`.youtube.com`, build the header set expected by
   `ytmusicapi` (including `Authorization: SAPISIDHASH …` computed from `SAPISID` + origin + timestamp),
   store in keyring, close the browser.
6. If Google blocks the Playwright Chromium ("browser not secure"), retry with `channel="chrome"`
   (system Chrome). If that also fails, show instructions for the headers fallback (§5).

Session reuse: on later runs, use stored credentials; on `AuthExpiredError` prompt for reconnect
(re-launch persistent profile, which usually re-authenticates quickly).

Security notes (must also be in README): cookies grant account access; stored only in keyring;
automated login may break or be restricted by Google at any time; use at your own risk.

## 5. YouTube Music — paste headers (lightweight fallback)

Provider: `ytmusic_headers.py`. The user pastes request headers copied from the browser dev tools
once, following a guide in the UI/CLI (`ytmusicapi`'s documented browser auth). Stored in keyring.
Same `AuthProvider` interface.

## 6. First-run setup wizard (UI, phase 7; CLI equivalent earlier)

1. Explain in 3 steps how to create a Spotify app; show the redirect URI to copy; link to the dashboard.
2. User pastes the Client ID → saved to config.
3. Buttons: **Connect Spotify**, **Connect YouTube Music**.
4. Status badges: connected / expired / not connected.

## 7. Tests

- PKCE: verifier/challenge generation (known vectors), `state` validation, callback handling with a fake server.
- Token store: in-memory fake keyring backend; never touch the real keyring in tests.
- SAPISIDHASH computation: unit-tested with a fixed timestamp and cookie.
- Playwright login: not exercised in CI; isolate behind a small interface so the rest is testable,
  and provide a manual test checklist in `docs/MANUAL_TESTS.md`.
