# Chess Bot

A Python chess engine you can play in the terminal or deploy as a [Lichess bot](https://lichess.org/@/lichess-bot). It uses classical search and hand-tuned evaluation — no neural networks — so the full decision pipeline is readable and testable.

## What it does

- **Play locally** — CLI game where you play White and the engine plays Black (`main.py`).
- **Play on Lichess** — Accepts incoming challenges and plays via the Lichess Board API (`lichess_bot.py`).
- **Search for the best move** — Negamax with alpha-beta pruning, move ordering, quiescence search, and a transposition table.
- **Evaluate positions** — Material, piece-square tables, pawn structure, king safety, and bishop-pair bonuses, blended across middlegame/endgame phase.

## How it works

```
Position (python-chess Board)
        │
        ▼
   engine.choose_move()
        │
        ├── iterative deepening (optional time budget)
        │
        └── negamax search
                ├── alpha-beta pruning
                ├── transposition table (exact / lower / upper bounds)
                ├── move ordering (captures, promotions, TT hash move)
                └── quiescence search at leaf nodes
                        │
                        ▼
                evaluation.evaluate_white()
                        ├── material + PST (MG/EG blend by phase)
                        ├── pawn structure (doubled, isolated, passed)
                        ├── king shield
                        └── bishop pair
```

**Search** (`search.py`, `engine.py`): The engine searches from depth 1 up to a configured maximum. When a time limit is set (Lichess games), it uses iterative deepening and keeps the result from the last fully completed depth. Terminal scores (checkmate, stalemate) use mate-distance scoring so shorter mates are preferred.

**Evaluation** (`evaluation.py`): Static scores are in centipawns from White's perspective. Piece-square tables differ for middlegame and endgame; phase is derived from remaining material. Structural heuristics penalize weak pawns and reward passed pawns and king protection.

**Lichess integration** (`lichess_bot.py`): Listens on the event stream for challenges, accepts them, and runs one thread per active game. Clock time is converted into a per-move search budget so the bot does not burn its entire clock on early moves.

## Tech stack

| Area | Choice |
|------|--------|
| Language | Python 3.10+ |
| Board / rules | [python-chess](https://python-chess.readthedocs.io/) |
| Lichess API | `requests` (Board API, NDJSON streams) |
| Tests | `unittest` |

## Getting started

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Play in the terminal

```bash
python main.py
```

Enter moves in [UCI notation](https://www.chessprogramming.org/UCI) (e.g. `e2e4`, `g1f3`). Default search depth is 4 plies; adjust in `main.py` via `SearchLimits(depth=4)`.

### Run on Lichess

1. Create a [Lichess bot account](https://lichess.org/account/oauth/token/create?scopes[]=bot:play) and copy the API token.
2. Set environment variables and start the bot:

```bash
export LICHESS_BOT_TOKEN='lip_...'
export LICHESS_MAX_DEPTH=4          # optional, default 4
export LICHESS_ACCEPT_RATED=1         # optional, set 0 to decline rated games
python lichess_bot.py
```

Run **one** bot process per token; a second instance will hit Lichess rate limits (429).

### Tests

```bash
python -m unittest discover -s tests -v
```

## Project layout

| File | Role |
|------|------|
| `engine.py` | Move selection, iterative deepening, time limits |
| `search.py` | Negamax, alpha-beta, TT, quiescence, move ordering |
| `evaluation.py` | Static evaluation and terminal scoring |
| `main.py` | Human vs engine CLI |
| `lichess_bot.py` | Lichess challenge handler and game loops |
| `display.py` | ASCII board rendering |
| `tests/` | Search and engine behavior tests |

## Skills demonstrated

- Game-tree search (negamax, alpha-beta, quiescence, transposition table)
- Heuristic evaluation and phase-aware tuning
- Time management for real-time play
- REST/streaming API integration with concurrency and rate-limit handling
- Unit tests for tactical correctness (e.g. mate-in-one)
