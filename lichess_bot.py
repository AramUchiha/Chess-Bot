"""
Minimal Lichess bot: accept incoming challenges and play via Board API.

Requires a Lichess **bot** account token:
  export LICHESS_BOT_TOKEN='lip_...'

Optional:
  export LICHESS_MAX_DEPTH=5
  export LICHESS_ACCEPT_RATED=1   # set to 0 to decline rated games

Docs: https://lichess.org/api#tag/Board
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from functools import partial
from typing import Any, Callable

import chess
import requests
from requests.adapters import HTTPAdapter

from engine import SearchLimits, choose_move

LICHESS = "https://lichess.org"
LOG = logging.getLogger("lichess_bot")

# Connect timeout (seconds), read timeout between stream chunks (None = no limit).
# A finite read timeout drops the stream during long quiet periods and the bot
# stops accepting challenges until restarted.
_STREAM_TIMEOUT = (30, None)


def _retry_after_seconds(response: requests.Response | None) -> float:
    """Seconds to wait after a 429 (honor Retry-After when present)."""
    if response is None:
        return 60.0
    raw = response.headers.get("Retry-After")
    if not raw:
        return 60.0
    try:
        return min(max(float(raw), 5.0), 300.0)
    except (TypeError, ValueError):
        return 60.0


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def lichess_session(token: str) -> requests.Session:
    """New session with auth. Use one session per stream/thread — Session is not thread-safe."""
    s = requests.Session()
    s.headers.update(_headers(token))
    # Small pool: Lichess asks to avoid parallel connections on one token.
    adapter = HTTPAdapter(pool_connections=1, pool_maxsize=1, max_retries=0)
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def _challenge_challenger_name(ch: dict[str, Any]) -> str:
    who = ch.get("challenger") or {}
    return str(who.get("name") or who.get("id") or who.get("username") or "")


def _ndjson_lines(resp: requests.Response):
    for raw in resp.iter_lines(decode_unicode=True):
        if not raw:
            continue
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")
        if raw.startswith(":"):
            continue
        try:
            yield json.loads(raw)
        except json.JSONDecodeError:
            LOG.warning("skip bad json: %s", raw[:200])


def fetch_username(session: requests.Session) -> str:
    r = session.get(f"{LICHESS}/api/account", timeout=30)
    r.raise_for_status()
    data = r.json()
    return str(data["username"])


def accept_challenge(session: requests.Session, challenge_id: str) -> bool:
    url = f"{LICHESS}/api/challenge/{challenge_id}/accept"
    for attempt in range(3):
        r = session.post(url, timeout=30)
        if r.status_code == 429:
            wait = _retry_after_seconds(r)
            LOG.warning(
                "accept 429 challenge=%s attempt %s/3; sleeping %.0fs",
                challenge_id,
                attempt + 1,
                wait,
            )
            time.sleep(wait)
            continue
        if r.status_code >= 400:
            LOG.error(
                "accept failed challenge=%s status=%s body=%s",
                challenge_id,
                r.status_code,
                r.text[:500],
            )
            return False
        LOG.info("accepted challenge %s", challenge_id)
        return True
    LOG.error("accept gave up after 429s challenge=%s", challenge_id)
    return False


def decline_challenge(session: requests.Session, challenge_id: str) -> None:
    session.post(f"{LICHESS}/api/challenge/{challenge_id}/decline", timeout=30)


def play_move(session: requests.Session, game_id: str, move: chess.Move) -> None:
    uci = move.uci()
    url = f"{LICHESS}/api/bot/game/{game_id}/move/{uci}"
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            r = session.post(url, timeout=30)
            if r.status_code >= 400:
                LOG.error("move post failed %s %s", r.status_code, r.text[:500])
            return
        except requests.RequestException as exc:
            last_err = exc
            LOG.warning(
                "move post attempt %s/3 failed (%s); retrying",
                attempt + 1,
                exc,
            )
            time.sleep(0.4 * (attempt + 1))
    LOG.error("move post gave up after 3 tries: %s", last_err)


def board_from_uci_moves(moves_uci: str) -> chess.Board:
    b = chess.Board()
    if not moves_uci:
        return b
    for uci in moves_uci.split():
        b.push_uci(uci)
    return b


def pick_time_budget_sec(
    *,
    is_white: bool,
    wtime: float,
    btime: float,
    winc: float,
    binc: float,
) -> float | None:
    """Return seconds for engine search; None = depth only."""
    my = wtime if is_white else btime
    inc = winc if is_white else binc
    if my <= 0:
        return None
    # Spend a small fraction of remaining clock plus a slice of increment.
    sec = (my / 1000.0) * 0.05 + (inc / 1000.0) * 0.5
    return max(0.15, min(sec, 8.0))


class GameRunner:
    def __init__(
        self,
        session: requests.Session,
        username: str,
        game_id: str,
        is_white: bool,
        base_depth: int,
        on_closed: Callable[[], None] | None = None,
    ) -> None:
        self.session = session
        self.username = username
        self.game_id = game_id
        self.is_white = is_white
        self.base_depth = base_depth
        self._on_closed = on_closed
        self._boards: dict[str, chess.Board] = {}
        self._stop = threading.Event()
        self._last_decided_fen: str | None = None

    def board(self) -> chess.Board:
        return self._boards.setdefault(self.game_id, chess.Board())

    def handle_game_stream(self) -> None:
        url = f"{LICHESS}/api/bot/game/stream/{self.game_id}"
        try:
            with self.session.get(url, stream=True, timeout=_STREAM_TIMEOUT) as resp:
                resp.raise_for_status()
                for event in _ndjson_lines(resp):
                    if self._stop.is_set():
                        break
                    self._on_game_event(event)
        except requests.RequestException as exc:
            resp = getattr(exc, "response", None)
            if resp is not None and resp.status_code == 429:
                LOG.warning(
                    "game stream 429 for %s (rate limit — use one bot process and one stream per game)",
                    self.game_id,
                )
            else:
                LOG.warning("game stream closed for %s: %s", self.game_id, exc)
        finally:
            if self._on_closed:
                self._on_closed()

    def stop(self) -> None:
        self._stop.set()

    def _on_game_event(self, event: dict[str, Any]) -> None:
        t = event.get("type")
        if t == "gameFull":
            white_name = (event.get("white") or {}).get("name", "")
            black_name = (event.get("black") or {}).get("name", "")
            my_color = (
                chess.WHITE
                if white_name.lower() == self.username.lower()
                else chess.BLACK
            )
            self.is_white = my_color == chess.WHITE
            st = event.get("state") or {}
            moves = st.get("moves", "")
            self._boards[self.game_id] = board_from_uci_moves(moves)
            LOG.info(
                "gameFull %s as %s vs %s / %s",
                self.game_id,
                "white" if self.is_white else "black",
                white_name,
                black_name,
            )
            self._maybe_play(self.board(), st)

        elif t == "gameState":
            moves = event.get("moves", "")
            self._boards[self.game_id] = board_from_uci_moves(moves)
            self._maybe_play(self.board(), event)

        elif t == "chatLine":
            pass
        elif t == "gameFinish":
            LOG.info("gameFinish %s", self.game_id)
            self.stop()

    def _maybe_play(self, board: chess.Board, state: dict[str, Any]) -> None:
        my_turn = (board.turn == chess.WHITE) == self.is_white
        if not my_turn or board.is_game_over():
            return

        fen = board.fen()
        if fen == self._last_decided_fen:
            return

        wtime = float(state.get("wtime", 600_000))
        btime = float(state.get("btime", 600_000))
        winc = float(state.get("winc", 0))
        binc = float(state.get("binc", 0))

        budget = pick_time_budget_sec(
            is_white=self.is_white,
            wtime=wtime,
            btime=btime,
            winc=winc,
            binc=binc,
        )
        limits = SearchLimits(depth=self.base_depth, time_sec=budget)
        move = choose_move(board, limits)
        LOG.info("play %s in %s", move.uci(), self.game_id)
        play_move(self.session, self.game_id, move)
        self._last_decided_fen = fen


def run_bot() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    token = os.environ.get("LICHESS_BOT_TOKEN", "").strip()
    if not token:
        LOG.error("Set LICHESS_BOT_TOKEN to your bot API token.")
        sys.exit(1)

    base_depth = int(os.environ.get("LICHESS_MAX_DEPTH", "4"))
    accept_rated = os.environ.get("LICHESS_ACCEPT_RATED", "1") != "0"

    session = lichess_session(token)

    username = fetch_username(session)
    LOG.info("logged in as %s (pid %s)", username, os.getpid())
    LOG.info(
        "Use exactly one running bot and one token; a second terminal/Cursor run causes 429s."
    )

    threads: list[threading.Thread] = []
    games_lock = threading.Lock()
    active_game_ids: set[str] = set()

    def release_game_id(gid: str) -> None:
        with games_lock:
            active_game_ids.discard(gid)

    backoff = 5.0
    consecutive_429 = 0
    while True:
        try:
            with session.get(
                f"{LICHESS}/api/stream/event",
                stream=True,
                timeout=_STREAM_TIMEOUT,
            ) as resp:
                resp.raise_for_status()
                consecutive_429 = 0
                backoff = 5.0
                for event in _ndjson_lines(resp):
                    et = event.get("type")
                    if et == "challenge":
                        ch = event.get("challenge") or {}
                        ch_id = ch.get("id")
                        challenger = _challenge_challenger_name(ch)
                        ch_status = ch.get("status")
                        if ch_status in ("canceled", "declined"):
                            LOG.info(
                                "challenge %s status=%s; ignoring",
                                ch_id,
                                ch_status,
                            )
                            continue
                        if (
                            ch_id
                            and challenger
                            and challenger.lower() == username.lower()
                        ):
                            # Outgoing challenge we created; opponent accepts on their side.
                            continue
                        rated = bool(ch.get("rated"))
                        if not ch_id:
                            LOG.warning("challenge event without id: %s", event)
                            continue
                        if rated and not accept_rated:
                            decline_challenge(session, ch_id)
                            LOG.info("declined rated challenge %s", ch_id)
                            continue
                        LOG.info(
                            "incoming challenge %s from %s rated=%s status=%s",
                            ch_id,
                            challenger or "?",
                            rated,
                            ch_status,
                        )
                        accept_challenge(session, ch_id)

                    elif et == "gameStart":
                        game = event.get("game") or {}
                        gid = game.get("gameId") or game.get("id")
                        color = game.get("color")
                        if not gid or color not in ("white", "black"):
                            LOG.warning("gameStart missing id/color: %s", event)
                            continue
                        gid_s = str(gid)
                        with games_lock:
                            if gid_s in active_game_ids:
                                LOG.info(
                                    "skip duplicate gameStart %s (already have a stream)",
                                    gid_s,
                                )
                                continue
                            active_game_ids.add(gid_s)
                        is_white = color == "white"
                        runner = GameRunner(
                            session=lichess_session(token),
                            username=username,
                            game_id=gid_s,
                            is_white=is_white,
                            base_depth=base_depth,
                            on_closed=partial(release_game_id, gid_s),
                        )
                        th = threading.Thread(
                            target=runner.handle_game_stream,
                            name=f"game-{gid_s}",
                            daemon=True,
                        )
                        th.start()
                        threads.append(th)
                        LOG.info("gameStart %s as %s", gid_s, color)

                    elif et == "gameFinish":
                        fin = event.get("game") or {}
                        gid_done = fin.get("gameId") or fin.get("id")
                        if gid_done:
                            release_game_id(str(gid_done))
                        LOG.info("gameFinish %s", event.get("game", {}))

                    elif et == "challengeCanceled":
                        LOG.info("challengeCanceled %s", event.get("challenge", {}))

        except requests.RequestException as exc:
            resp = getattr(exc, "response", None)
            if resp is not None and resp.status_code == 429:
                consecutive_429 += 1
                base = _retry_after_seconds(resp)
                # Escalate when Lichess keeps returning 429 (often: multiple bot processes).
                wait = min(base * (1.4 ** (consecutive_429 - 1)), 300.0)
                LOG.warning(
                    "event stream 429 (#%s); waiting %.0fs then reconnect "
                    "(challenges sent while offline are not replayed — avoid 429s)",
                    consecutive_429,
                    wait,
                )
                time.sleep(wait)
                backoff = 5.0
                continue
            consecutive_429 = 0
            LOG.warning("event stream disconnected (%s); reconnecting in %.0fs", exc, backoff)
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 120.0)


if __name__ == "__main__":
    run_bot()
