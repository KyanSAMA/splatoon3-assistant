# Splatoon3 Assistant - Technical Roadmap

## Token Auto-Refresh Mechanism

### Architecture Overview

The token auto-refresh mechanism automatically handles token expiration by detecting 401 errors and refreshing tokens transparently. This implementation references the `refresh_gtoken_and_bullettoken` method from splatoon3-nso.

**Core Flow:**
```
API Request → 401 Error → Auto Refresh Tokens → Save → Retry Request
```

**Key Components:**
- `SplatNet3API.request()`: Detects 401 and triggers refresh
- `_refresh_tokens()`: Locked refresh with Double-Checked Locking (DCL)
- Concurrency control: `asyncio.Lock` + DCL pattern
- Callback execution: Outside lock to prevent deadlock

### Detailed Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│               User calls API method                      │
│           (e.g., api.get_recent_battles())              │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│              SplatNet3API.request()                     │
│  - Build headers (with bullet_token)                    │
│  - Send GraphQL request                                 │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
         ┌────────┴────────┐
         │ Check HTTP status│
         └────────┬────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
    ┌──────┐           ┌──────┐
    │ 200  │           │ 401  │ Token expired
    └───┬──┘           └───┬──┘
        │                  │
        │                  ▼
        │      ┌─────────────────────────┐
        │      │  _can_auto_refresh()?   │
        │      │  - Check NSOAuth exists  │
        │      │  - Check session_token   │
        │      └─────────┬───────────────┘
        │                │
        │        ┌───────┴────────┐
        │        │ No             │ Yes
        │        ▼                ▼
        │    Return None   ┌──────────────────┐
        │                  │ _refresh_tokens()│
        │                  │  [Locked refresh] │
        │                  └────────┬─────────┘
        │                           │
        │          ┌────────────────┴────────────────┐
        │          │         asyncio.Lock             │
        │          │  1. Check _is_refreshing         │
        │          │  2. If true → wait & return      │
        │          │  3. If false → start refresh     │
        │          └────────┬────────────────────────┘
        │                   │
        │                   ▼
        │          ┌─────────────────────┐
        │          │ Refresh g_token      │
        │          │ ← NSOAuth.get_gtoken │
        │          └──────────┬───────────┘
        │                     │
        │                     ▼
        │          ┌─────────────────────┐
        │          │ Refresh bullet_token │
        │          │ ← NSOAuth.get_bullet │
        │          └──────────┬───────────┘
        │                     │
        │                     ▼
        │          ┌─────────────────────┐
        │          │ Update in-memory     │
        │          │ - self.g_token       │
        │          │ - self.bullet_token  │
        │          └──────────┬───────────┘
        │                     │
        │                     ▼
        │          ┌─────────────────────┐
        │          │ Return token_data    │
        │          └──────────┬───────────┘
        │                     │
        │          ┌──────────┴───────────┐
        │          │   [Release lock]      │
        │          └──────────┬───────────┘
        │                     │
        │                     ▼
        │          ┌─────────────────────┐
        │          │ Call callback to     │
        │          │ save tokens          │
        │          │ on_tokens_updated()  │
        │          └──────────┬───────────┘
        │                     │
        └─────────────────────┤
                              │
                              ▼
                   ┌─────────────────────┐
                   │  Retry request (max 1)│
                   │  - Use new tokens    │
                   └──────────┬───────────┘
                              │
                              ▼
                   ┌─────────────────────┐
                   │   Return API result  │
                   └─────────────────────┘
```

### Exception Handling Flow

```
_refresh_tokens() throws exception
        │
        ├── SessionExpiredError
        │   → session_token expired
        │   → Propagate to caller
        │   → User needs to re-login
        │
        ├── MembershipRequiredError
        │   → NSO membership expired
        │   → Propagate to caller
        │   → User needs to renew membership
        │
        ├── BulletTokenError
        │   → Bullet token acquisition failed
        │   → status_code: 401/403/204/499
        │   → Propagate to caller
        │   → User needs to update version or check ban
        │
        └── TokenRefreshError
            → Other refresh failure reasons
            → Propagate to caller
            → User needs to check network or retry
```

---

## Concurrent Control Implementation

### Problem: Refresh Storm

Multiple API requests receiving 401 simultaneously would trigger multiple token refresh operations, causing:
- Redundant API calls to NSO
- Potential rate limiting
- Wasted resources

### Solution: Double-Checked Locking (DCL)

**Implementation:**

```python
async def _refresh_tokens(self) -> tuple[bool, Optional[Dict[str, Any]]]:
    # First check (outside lock, fast-path)
    if not self._can_auto_refresh():
        raise TokenRefreshError("Cannot auto-refresh")

    # Acquire lock
    async with self._refresh_lock:
        # Second check (inside lock, avoid duplicate refresh)
        if self._is_refreshing:
            # Another coroutine is refreshing, reuse its result
            return (True, None)

        # Set refresh flag
        self._is_refreshing = True

        try:
            # Perform refresh...
            return (True, token_data)
        finally:
            # Clear refresh flag
            self._is_refreshing = False
```

**How it works:**

1. Concurrent requests A, B, C all receive 401
2. A acquires lock, starts refresh
3. B, C wait for lock
4. A completes refresh, releases lock
5. B acquires lock, sees `_is_refreshing=False`, returns `(True, None)` to reuse A's result
6. C acquires lock, sees `_is_refreshing=False`, returns `(True, None)` to reuse result

**Result:** Only 1 refresh operation for multiple concurrent 401s

---

## Callback Deadlock Prevention

### Problem: Deadlock Risk

If callback is executed inside the lock and the callback calls an API method, it would cause deadlock:

```python
async with self._refresh_lock:  # Holding lock
    # Refresh tokens...
    await callback(token_data)  # Call callback
    # ↑ If callback calls API → tries to acquire lock again → DEADLOCK
```

### Solution: Callback Outside Lock

**Implementation:**

```python
# Inside _refresh_tokens()
async with self._refresh_lock:
    # Refresh tokens...
    return (True, token_data)  # Return data

# Inside request() - outside lock
if self.on_tokens_updated and token_data:
    try:
        if asyncio.iscoroutinefunction(self.on_tokens_updated):
            await self.on_tokens_updated(token_data)
        else:
            self.on_tokens_updated(token_data)
    except Exception as e:
        print(f"Token callback failed: {e}")
        # Callback failure doesn't affect refresh flow
```

**Key points:**
- `_refresh_tokens()` returns `(success, token_data)` tuple
- Callback executed in `request()` after lock is released
- Callback failures logged but don't break refresh flow
- Supports both sync and async callbacks

---

## Exception Type System

### Design Philosophy

Clear, actionable exception types that guide users to correct resolution steps.

### Exception Hierarchy

```python
SplatoonError (base)
├── SessionExpiredError      # session_token expired → re-login
├── MembershipRequiredError  # NSO membership expired → renew
├── BulletTokenError         # bullet token error → update/check ban
├── TokenRefreshError        # refresh failed → check network
└── NetworkError             # network issues → retry
```

### Exception Details

| Exception | Trigger | User Action |
|-----------|---------|-------------|
| `SessionExpiredError` | session_token expired | Re-login (QR scan) |
| `MembershipRequiredError` | NSO membership expired | Renew NSO membership |
| `BulletTokenError` | Bullet token error (401/403/204/499) | Update version or check account status |
| `TokenRefreshError` | Other refresh failures | Check network or retry |

### Usage Example

```python
try:
    battles = await api.get_recent_battles()
except SessionExpiredError:
    # Guide user to re-login
    print("Please re-login")
except MembershipRequiredError:
    # Guide user to renew
    print("NSO membership expired, please renew")
except BulletTokenError as e:
    # Check specific error
    if e.status_code == 403:
        print("Application version outdated")
    elif e.status_code == 499:
        print("Account banned")
except TokenRefreshError as e:
    # Network or other errors
    print(f"Refresh failed: {e}")
```

---

## Token Persistence

### Atomic File Write Pattern

Ensures token data integrity even if process crashes during write.

**Implementation:**

```python
def save(self, data: Dict[str, Any]):
    """Atomic write: write to temp file, then rename"""
    # Add timestamp
    data["updated_at"] = datetime.now().isoformat()

    # Write to temporary file
    temp_file = self.file_path.with_suffix('.tmp')
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Atomic rename (OS-level atomic operation)
    temp_file.replace(self.file_path)
```

**Why atomic?**
- `os.replace()` is atomic on all major OSes
- If crash occurs during `json.dump()`, original file remains intact
- Only after successful write does rename occur
- No partial/corrupted token files

---

## Code Review Findings

### Round 1: Initial Implementation Issues

**Issue 1: Exception Propagation**
- **Problem:** All exceptions wrapped in `TokenRefreshError`, losing specific error types
- **Impact:** Users couldn't distinguish between session expiration, membership expiration, etc.
- **Fix:** Added explicit exception handling for `SessionExpiredError`, `MembershipRequiredError`, `BulletTokenError`

**Issue 2: Concurrent Refresh Control**
- **Problem:** Missing DCL implementation, potential refresh storm
- **Impact:** Multiple concurrent requests would all trigger refresh
- **Fix:** Implemented DCL pattern with `_is_refreshing` flag

**Issue 3: Callback Deadlock**
- **Problem:** Callback executed inside lock
- **Impact:** If callback calls API, would cause deadlock
- **Fix:** Moved callback execution outside lock

### Round 2: Return Value Inconsistency

**Issue:** Return type mismatch
- **Problem:**
  - Method signature: `-> bool`
  - Success path: `return (True, token_data)`
  - DCL path: `return True`
- **Impact:** Destructuring would fail in DCL path
- **Fix:**
  - Changed return type to `tuple[bool, Optional[Dict[str, Any]]]`
  - Made DCL path return `(True, None)`
  - Updated docstring

### Round 3: Documentation

**Issue:** Missing docstring updates
- **Problem:** Docstrings didn't reflect new return type
- **Fix:** Updated all relevant docstrings and comments

---

## Best Practices

### 1. Use TokenStore for Persistence

✅ **Recommended:**
```python
from src import TokenStore

store = TokenStore(".token_cache.json")
api = SplatNet3API(
    nso_auth=auth,
    session_token=token,
    on_tokens_updated=lambda t: store.save(t)
)
```

❌ **Not recommended:** Manual file management

### 2. Proper Exception Handling

✅ **Recommended:** Distinguish exception types
```python
try:
    result = await api.get_recent_battles()
except SessionExpiredError:
    # Guide to re-login
    pass
except MembershipRequiredError:
    # Guide to renew
    pass
```

❌ **Not recommended:** Catch all exceptions
```python
try:
    result = await api.get_recent_battles()
except Exception:
    pass  # Loses error information
```

### 3. Resource Management

✅ **Recommended:** Use context manager
```python
async with SplatNet3API(...) as api:
    battles = await api.get_recent_battles()
# Automatically calls api.close()
```

Or explicit cleanup:
```python
api = SplatNet3API(...)
try:
    battles = await api.get_recent_battles()
finally:
    await api.close()
```

### 4. Simple Callbacks

✅ **Recommended:** Keep callbacks simple
```python
api = SplatNet3API(
    on_tokens_updated=lambda t: store.save(t)
)
```

❌ **Not recommended:** Call API in callback (deadlock risk)
```python
api = SplatNet3API(
    on_tokens_updated=lambda t: await api.get_home()  # ❌ DEADLOCK!
)
```

### 5. Cold Start Support

The API supports initialization with only `session_token`:

```python
api = SplatNet3API(
    nso_auth=auth,
    session_token=token,
    # g_token and bullet_token are None
)

# First request will auto-refresh
battles = await api.get_recent_battles()
```

---

## Troubleshooting Guide

### Session Token Expired

**Symptoms:** `SessionExpiredError`

**Causes:**
- Password changed
- Long period of inactivity
- Token manually revoked

**Resolution:**
1. Clear token cache
2. Re-run authentication flow (QR scan)
3. Save new tokens

### NSO Membership Expired

**Symptoms:** `MembershipRequiredError`

**Causes:**
- NSO subscription expired

**Resolution:**
1. Visit Nintendo website
2. Renew NSO membership
3. Retry API calls

### Bullet Token Error

**Symptoms:** `BulletTokenError` with various status codes

**Causes and resolutions:**
- `403`: Application version outdated → Update `nso_auth.py` version strings
- `499`: Account banned → Check account status
- `401`: Invalid g_token → Should auto-refresh, if not check session_token
- `204`: Empty response → Check NSO service status

### Token Refresh Failures

**Symptoms:** `TokenRefreshError`

**Causes:**
- Network connectivity issues
- NSO API temporarily unavailable
- Rate limiting

**Resolution:**
1. Check network connection
2. Wait and retry
3. Check NSO service status

---

## Development Timeline

### 2024-12-13: Token Auto-Refresh Feature ⭐

**Implemented features:**
- [x] 401 error detection and auto-refresh
- [x] Concurrent refresh control (asyncio.Lock + DCL)
- [x] Clear exception type system
- [x] TokenStore persistence (atomic writes)
- [x] Callback mechanism (outside lock)
- [x] Complete error handling

**Code quality:**
- Passed 3 rounds of codex review
- Fixed return value type inconsistency
- Fixed callback deadlock issue
- Improved exception propagation

**Technical details:** See implementation sections above

### 2024-12-12: v4 API Encryption Support

**Completed:**
- [x] Upgraded to v4 API (`/v4/Account/Login` and `/v4/Game/GetWebServiceToken`)
- [x] Implemented nxapi encryption/decryption (`encrypt_token_request` and `f_decrypt_response`)
- [x] Removed msgpack dependency, use base64 for encrypted payloads
- [x] Enhanced error handling (status code validation, JSON parse errors, payload validation)
- [x] OAuth scope expansion: `ca:gf` → `ca:gf ca:er ca:dr`

### 2024-12-10: NSO API Integration Completed

**Completed:**
- [x] Full authentication flow (following splatoon3-nso)
- [x] Method names match reference project (`login_in`, `login_in_2`, `get_bullet`)
- [x] Global variable version caching
- [x] Complete GraphQL API wrapper
- [x] Functional test file
- [x] All 8 Python modules pass syntax check

---

## Future Improvements

### Potential Enhancements

1. **Token expiration prediction**: Calculate token TTL and refresh proactively
2. **Retry with exponential backoff**: For network errors
3. **Token validation**: Verify token format before using
4. **Metrics collection**: Track refresh frequency, failure rates
5. **Multi-account support**: Manage multiple NSO accounts

### Performance Optimizations

1. **Connection pooling**: Reuse HTTP connections
2. **Request batching**: Combine multiple GraphQL queries
3. **Caching layer**: Cache frequently accessed data
4. **Async improvements**: Better concurrent request handling

---

## References

- [splatoon3-nso](https://github.com/Cypas/splatoon3-nso) - Main reference project
- [nxapi](https://github.com/samuelthomas2774/nxapi) - NSO API support
- OAuth Client ID: `EJ5mqnRSwmWfOPmRDIRGwg` (project-specific)
