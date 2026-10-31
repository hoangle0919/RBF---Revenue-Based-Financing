"""FX adapter — mocked throughout. No test here depends on today's live rate.

One test (`test_live_smoke`) touches the network and is skipped unless
RBF_FX_LIVE=1. It demonstrates connectivity only. It is never a correctness
oracle: a provider outage must not turn this suite red.
"""
import http.client
import json
from decimal import Decimal
import threading
import time
import urllib.error
from datetime import date, datetime, timedelta, timezone

import pytest

import fx


_UNSET = object()


def _doc(rate=25807, ref=_UNSET, base="USD", quote="VND"):
    # NOT `ref or today`: that collapses "" (a malformed date we must reject)
    # into a valid one, which silently defeated the malformed-date test.
    return [{"date": fx._utc_today().isoformat() if ref is _UNSET else ref,
             "base": base, "quote": quote, "rate": rate}]


class _Resp:
    def __init__(self, payload): self._b = json.dumps(payload).encode()
    def read(self, n=-1): return self._b[:n] if n and n > 0 else self._b
    def __enter__(self): return self
    def __exit__(self, *a): return False


@pytest.fixture(autouse=True)
def _clean():
    fx._reset_for_tests()
    yield
    fx._reset_for_tests()


def _patch(monkeypatch, payload=None, exc=None):
    def fake(req, timeout=None, context=None):
        if exc is not None:
            raise exc
        return _Resp(payload)
    monkeypatch.setattr(fx.urllib.request, "urlopen", fake)


# ── orientation and arithmetic ───────────────────────────────────────────────

def test_orientation_is_vnd_per_usd():
    # 1 USD = 25,000 VND  =>  250,000,000 VND is 10,000 USD, not 6.25e12
    assert fx.approximate_usd(250_000_000, "25000") == "10000.00"


def test_rounds_to_cents_half_up_at_presentation_only():
    assert fx.approximate_usd(1, "8") == "0.13"          # 0.125 -> 0.13
    assert fx.approximate_usd(0, "25000") == "0.00"


def test_zero_and_large_amounts():
    assert fx.approximate_usd(0, "25807") == "0.00"
    assert fx.approximate_usd(10**13, "25000").endswith(".00")


@pytest.mark.parametrize("bad", ["0", "-5", "abc", "NaN", "Infinity", ""])
def test_unusable_rate_yields_none_not_a_guess(bad):
    assert fx.approximate_usd(1_000_000, bad) is None


# ── validation ───────────────────────────────────────────────────────────────

def test_wrong_pair_rejected(monkeypatch):
    _patch(monkeypatch, _doc(base="EUR"))
    assert fx.get_quote()["error"] == fx.ERR_BAD_RATE


def test_missing_vnd_quote_rejected(monkeypatch):
    _patch(monkeypatch, _doc(quote="THB"))
    assert fx.get_quote()["error"] == fx.ERR_BAD_RATE


def test_inverted_orientation_is_rejected_not_silently_inverted(monkeypatch):
    # 1/25807 would "work" arithmetically and be wrong by 9 orders of magnitude
    _patch(monkeypatch, _doc(rate=0.0000387))
    q = fx.get_quote()
    assert q["status"] == fx.STATUS_UNAVAILABLE
    assert q["error"] == fx.ERR_BAD_RATE


@pytest.mark.parametrize("bad", [0, -1, "nope", None, True])
def test_malformed_rate_rejected(monkeypatch, bad):
    _patch(monkeypatch, _doc(rate=bad))
    assert fx.get_quote()["status"] == fx.STATUS_UNAVAILABLE


def test_future_reference_date_rejected(monkeypatch):
    future = (fx._utc_today() + timedelta(days=2)).isoformat()
    _patch(monkeypatch, _doc(ref=future))
    assert fx.get_quote()["error"] == fx.ERR_BAD_DATE


@pytest.mark.parametrize("bad", ["2026-13-01", "not-a-date", "", 20261024])
def test_malformed_date_rejected(monkeypatch, bad):
    _patch(monkeypatch, _doc(ref=bad))
    assert fx.get_quote()["error"] == fx.ERR_BAD_DATE


def test_oversized_response_rejected(monkeypatch):
    class Big:
        def read(self, n=-1): return b"x" * (fx.MAX_BYTES + 1)
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(fx.urllib.request, "urlopen", lambda r, timeout=None, context=None: Big())
    assert fx.get_quote()["error"] == fx.ERR_BAD_RESPONSE


def test_multi_record_response_rejected(monkeypatch):
    _patch(monkeypatch, _doc() + _doc())
    assert fx.get_quote()["error"] == fx.ERR_BAD_RESPONSE


# ── freshness bands ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("age,expected", [
    (0, fx.STATUS_OK), (3, fx.STATUS_OK),          # inside the weekend-gap band
    (4, fx.STATUS_STALE), (7, fx.STATUS_STALE),    # shown, but warned
    (8, fx.STATUS_UNAVAILABLE),                    # suppressed
])
def test_reference_age_boundaries(monkeypatch, age, expected):
    ref = (fx._utc_today() - timedelta(days=age)).isoformat()
    _patch(monkeypatch, _doc(ref=ref))
    q = fx.get_quote()
    assert q["status"] == expected
    if expected == fx.STATUS_UNAVAILABLE:
        assert q["vnd_per_usd"] is None
    else:
        assert q["reference_age_days"] == age
        assert q["reference_date"] == ref


# ── transport failures ───────────────────────────────────────────────────────

@pytest.mark.parametrize("exc", [
    urllib.error.URLError("down"),
    urllib.error.HTTPError("u", 429, "rate limited", {}, None),
    urllib.error.HTTPError("u", 503, "unavailable", {}, None),
    TimeoutError("slow"),
    OSError("socket"),
])
def test_transport_failure_is_a_safe_code_not_an_exception(monkeypatch, exc):
    _patch(monkeypatch, exc=exc)
    q = fx.get_quote()
    assert q["status"] == fx.STATUS_UNAVAILABLE
    assert q["error"] == fx.ERR_UNREACHABLE
    # no upstream status code or internal text leaks to the browser
    assert "503" not in json.dumps(q) and "429" not in json.dumps(q)


def test_no_fallback_constant_is_ever_synthesized(monkeypatch):
    _patch(monkeypatch, exc=urllib.error.URLError("down"))
    assert fx.get_quote()["vnd_per_usd"] is None


# ── cache, failed refresh, recovery ──────────────────────────────────────────

def test_cache_avoids_a_second_fetch(monkeypatch):
    calls = []
    monkeypatch.setattr(fx.urllib.request, "urlopen",
                        lambda r, timeout=None, context=None: (calls.append(1), _Resp(_doc()))[1])
    fx.get_quote(); fx.get_quote(); fx.get_quote()
    assert len(calls) == 1


def test_expired_cache_refetches(monkeypatch):
    calls = []
    monkeypatch.setattr(fx.urllib.request, "urlopen",
                        lambda r, timeout=None, context=None: (calls.append(1), _Resp(_doc()))[1])
    fx.get_quote()
    fx._cache_fetched_at -= (fx.CACHE_TTL_S + 1)
    fx.get_quote()
    assert len(calls) == 2


def test_failed_refresh_serves_cache_and_says_so_without_rewriting_fetched_at(monkeypatch):
    _patch(monkeypatch, _doc())
    first = fx.get_quote()
    assert first["refresh_failed"] is False

    # Age the cache past its TTL so the next call attempts a real refresh.
    fx._cache_fetched_at -= (fx.CACHE_TTL_S + 1)
    aged_at = datetime.fromtimestamp(fx._cache_fetched_at, timezone.utc) \
                      .isoformat(timespec="seconds")

    _patch(monkeypatch, exc=urllib.error.URLError("down"))
    second = fx.get_quote()

    assert second["status"] in (fx.STATUS_OK, fx.STATUS_STALE)
    assert second["refresh_failed"] is True
    assert second["error"] == fx.ERR_UNREACHABLE
    assert second["vnd_per_usd"] == first["vnd_per_usd"]
    # A refetch of an old observation is NOT a newly dated rate: the failed
    # refresh must report the ORIGINAL fetch time, not "now".
    assert second["fetched_at"] == aged_at
    now_iso = datetime.now(timezone.utc).isoformat(timespec="seconds")
    assert second["fetched_at"] < now_iso


def test_a_failure_opens_a_backoff_window_that_suppresses_refetching(monkeypatch):
    """Negative caching. Without it, every request during an upstream outage
    pays the full timeout before failing."""
    calls = []
    monkeypatch.setattr(fx.urllib.request, "urlopen",
                        lambda r, timeout=None, context=None: (_ for _ in ()).throw(
                            urllib.error.URLError("down")) if calls.append(1) is None else None)
    assert fx.get_quote()["status"] == fx.STATUS_UNAVAILABLE
    assert len(calls) == 1
    for _ in range(5):
        assert fx.get_quote()["status"] == fx.STATUS_UNAVAILABLE
    assert len(calls) == 1, "backoff window must suppress further fetches"
    assert fx._failed_until > time.time()


def test_backoff_grows_but_is_bounded(monkeypatch):
    _patch(monkeypatch, exc=urllib.error.URLError("down"))
    waits = []
    for _ in range(10):
        fx._failed_until = 0.0            # allow the next attempt
        fx.get_quote()
        waits.append(fx._failed_until - time.time())
    assert waits[1] > waits[0], "backoff should grow"
    assert max(waits) <= fx.BACKOFF_MAX_S + 1, "backoff must be bounded"


def test_an_explicit_refresh_bypasses_the_backoff_window(monkeypatch):
    _patch(monkeypatch, exc=urllib.error.URLError("down"))
    assert fx.get_quote()["status"] == fx.STATUS_UNAVAILABLE
    _patch(monkeypatch, _doc())
    assert fx.get_quote()["status"] == fx.STATUS_UNAVAILABLE   # still backed off
    good = fx.get_quote(force=True)
    assert good["status"] == fx.STATUS_OK and good["refresh_failed"] is False
    assert fx._failed_until == 0.0 and fx._fail_streak == 0


def test_service_recovery_once_the_window_expires(monkeypatch):
    _patch(monkeypatch, exc=urllib.error.URLError("down"))
    assert fx.get_quote()["status"] == fx.STATUS_UNAVAILABLE
    fx._failed_until = 0.0                # simulate the window elapsing
    _patch(monkeypatch, _doc())
    good = fx.get_quote()
    assert good["status"] == fx.STATUS_OK and good["refresh_failed"] is False


@pytest.mark.parametrize("exc", [
    RuntimeError("unexpected"),
    http.client.IncompleteRead(b""),
    http.client.BadStatusLine("garbage"),
    MemoryError(),
])
def test_an_unexpected_exception_does_not_wedge_the_adapter(monkeypatch, exc):
    """The single-flight flag must be released no matter how the fetch ends.

    If it is not, every later caller sees a refresh "in progress" that will
    never finish, and the rate can never recover for the life of the process --
    a worse outage than the one single-flight was added to prevent.
    """
    _patch(monkeypatch, exc=exc)
    q = fx.get_quote()
    assert q["status"] == fx.STATUS_UNAVAILABLE
    assert q["error"] == fx.ERR_UNREACHABLE
    assert fx._fetching is False, "single-flight flag left set; adapter is wedged"

    # ...and the adapter must still be able to recover.
    _patch(monkeypatch, _doc())
    good = fx.get_quote(force=True)
    assert good["status"] == fx.STATUS_OK


def test_httpexception_is_converted_by_fetch_not_leaked(monkeypatch):
    """HTTPException is not an OSError, so it needs naming explicitly or a
    malformed upstream response escapes the conversion in _fetch."""
    _patch(monkeypatch, exc=http.client.BadStatusLine("nonsense"))
    assert fx.get_quote()["error"] == fx.ERR_UNREACHABLE
    assert fx._fetching is False


def test_release_and_publish_happen_in_one_lock_transition(monkeypatch):
    """F3. Ownership of the single flight and publication of its result must be
    one transition.

    When they were two, a caller entering the gap started a second fetch whose
    newer result was then overwritten by the first caller's older one. The lock
    wrapper below schedules a thread into exactly that boundary.
    """
    paused, resume = threading.Event(), threading.Event()

    class BoundaryLock:
        def __init__(self):
            self.lock = threading.Lock()
            self.exits = 0

        def __enter__(self):
            self.lock.acquire()
            return self

        def __exit__(self, *a):
            first = threading.current_thread().name == "first"
            if first:
                self.exits += 1
            boundary = first and self.exits == 2
            self.lock.release()
            if boundary:
                paused.set()
                if not resume.wait(3):
                    raise RuntimeError("test synchronization timeout")

    real_lock = fx._lock
    fx._lock = BoundaryLock()
    fetches = []

    def fake_fetch():
        rate = Decimal("25000" if threading.current_thread().name == "first" else "26000")
        fetches.append(str(rate))
        return {"rate": rate, "reference_date": fx._utc_today().isoformat()}

    monkeypatch.setattr(fx, "_fetch", fake_fetch)
    results = {}
    t = threading.Thread(name="first", target=lambda: results.update(first=fx.get_quote()))
    t.start()
    try:
        if not paused.wait(3):
            # The boundary never occurred: there is no two-transition gap left.
            t.join(3)
            assert fetches == ["25000"]
            return
        results["second"] = fx.get_quote()
        resume.set()
        t.join(3)
        assert not t.is_alive()
        # The second caller must NOT have started a competing fetch...
        assert fetches == ["25000"], f"a second fetch started in the gap: {fetches}"
        # ...and the published cache must be the value that was actually fetched.
        assert str(fx._cache["rate"]) == "25000"
    finally:
        resume.set()
        fx._lock = real_lock


@pytest.mark.parametrize("message", [
    "audit-sentinel PRIVATE_RESPONSE_DETAIL",
    "/Users/someone/secret/path.json",
    "connection to 10.0.0.5:5432 refused",
])
def test_unexpected_valueerror_text_never_reaches_the_public_error(monkeypatch, message):
    """F4. A ValueError raised anywhere inside _fetch -- including from a
    library it calls -- had its message copied verbatim into the public `error`
    field. Only codes from the fixed taxonomy may appear."""
    monkeypatch.setattr(fx, "_fetch", lambda: (_ for _ in ()).throw(ValueError(message)))
    q = fx.get_quote()
    blob = json.dumps(q)
    assert message not in blob, "exception text leaked into the response"
    assert q["error"] in fx._PUBLIC_ERRORS
    assert q["error"] == fx.ERR_UNREACHABLE


def test_known_codes_still_pass_through_the_taxonomy(monkeypatch):
    """The allowlist must not flatten the real codes into one."""
    for code in (fx.ERR_BAD_RATE, fx.ERR_BAD_DATE, fx.ERR_BAD_RESPONSE):
        fx._reset_for_tests()
        monkeypatch.setattr(fx, "_fetch", lambda c=code: (_ for _ in ()).throw(ValueError(c)))
        assert fx.get_quote()["error"] == code


def test_the_module_lock_is_not_held_across_network_io(monkeypatch):
    """The finding this guards: a stalled upstream must cost one thread, not
    the worker pool. FastAPI runs sync endpoints in a bounded threadpool, so a
    lock held across a slow fetch would starve the whole application."""
    started, release = threading.Event(), threading.Event()

    def stalled(req, timeout=None, context=None):
        started.set()
        release.wait(5)                   # hold the "network" open
        return _Resp(_doc())

    monkeypatch.setattr(fx.urllib.request, "urlopen", stalled)
    slow = threading.Thread(target=fx.get_quote)
    slow.start()
    assert started.wait(2), "fetch did not begin"

    # While that fetch is stalled, another caller must return promptly.
    done = threading.Event()
    def other():
        fx.get_quote()
        done.set()
    threading.Thread(target=other).start()
    assert done.wait(1.5), "a second caller blocked behind the in-flight fetch"

    release.set()
    slow.join(5)


def test_concurrent_refreshes_are_deduplicated(monkeypatch):
    calls = []
    def slow(req, timeout=None, context=None):
        calls.append(1)
        import time as _t; _t.sleep(0.05)
        return _Resp(_doc())
    monkeypatch.setattr(fx.urllib.request, "urlopen", slow)
    ts = [threading.Thread(target=fx.get_quote) for _ in range(8)]
    [t.start() for t in ts]; [t.join() for t in ts]
    assert len(calls) == 1


def test_reference_date_and_fetch_time_are_distinct_fields(monkeypatch):
    ref = (fx._utc_today() - timedelta(days=2)).isoformat()
    _patch(monkeypatch, _doc(ref=ref))
    q = fx.get_quote()
    assert q["reference_date"] == ref
    assert q["fetched_at"].startswith(datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    assert q["reference_date"] != q["fetched_at"][:10]


# ── the boundary that matters most ───────────────────────────────────────────

def test_fx_is_not_imported_by_calculation_modules():
    """A network value must not be reachable from a settlement path.

    Checked by source inspection rather than sys.modules, because an import
    added inside a function would not show up in a fresh-import check.
    """
    import os, re
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    repo = os.path.dirname(here)
    targets = [os.path.join(here, "money.py"),
               os.path.join(here, "financing_engine.py"),
               os.path.join(here, "lab.py")]
    for rel in ("generator.py", "contracts.py", "engine.py", "metrics.py", "settlement.py"):
        targets.append(os.path.join(repo, "research", "rbf_sim", rel))
    pat = re.compile(r"^\s*(import\s+fx\b|from\s+fx\s+import|from\s+\.\s*fx\s+import)", re.M)
    for t in targets:
        if os.path.exists(t):
            assert not pat.search(open(t, encoding="utf-8").read()), \
                f"{os.path.relpath(t, repo)} imports fx — a rate must never reach contract arithmetic"


@pytest.mark.skipif(not __import__("os").environ.get("RBF_FX_LIVE"),
                    reason="live provider smoke test; set RBF_FX_LIVE=1 to run")
def test_live_smoke():
    """Connectivity demonstration only. Never an oracle for correctness."""
    q = fx.get_quote(force=True)
    assert q["status"] in (fx.STATUS_OK, fx.STATUS_STALE, fx.STATUS_UNAVAILABLE)


@pytest.mark.parametrize("vnd,rate,expected", [
    (25125, "25000", "1.01"),      # exact tie -> half-up
    (1, "8", "0.13"),              # 0.125 -> half-up
    (0, "25000", "0.00"),
    (185_000_000, "25807", "7168.60"),
    (222_000_000, "25765", "8616.34"),
])
def test_browser_and_backend_agree_on_cents(vnd, rate, expected):
    """F5. The browser previously used binary float Math.round while claiming
    agreement with this function, and disagreed on exact ties. These fixtures
    are pinned identically in tools/check_i18n_fx_state.cjs; if either side
    changes its rounding, one of the two suites fails."""
    assert fx.approximate_usd(vnd, rate) == expected
