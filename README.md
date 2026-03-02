# Agentic Chess Coach

A Python chess coaching application that combines:

- **Full chess simulation** (human or AI on either side)
- **Move tracking in SAN/algebraic notation** and **PGN export**
- **Stockfish-powered evaluation and best move analysis** (using `python-chess`)
- **Dynamic agentic coaching** powered by the **OpenAI Agents SDK** with planner, specialists, critic loop, and synthesis.
- **Interactive pygame UI** with board rendering, move list, mouse-based moves, and coach feedback panel.

## Core Design Goals

1. Model a complete chess game with legal move generation, SAN notation, move history, and PGN export.
2. Allow either side to be controlled by:
   - Human
   - Stockfish engine
   - Human-like coaching player (`gm-agent`)
3. Keep Stockfish analysis available for objective evaluation, while coaching recommendations remain human-principled (non-engine line following).
4. Use a dynamic multi-agent coaching architecture:
   - **Planner agent** creates a per-position workflow (up to 6 specialists)
   - **Specialist agents** (opening/tactics/endgame/research, etc.) provide targeted feedback
   - **Specialist critic loop** validates each specialist response and checks legality
   - **Synthesis agent** merges all validated feedback into one final coaching summary

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

For OpenAI Agents SDK mode, set your API key:

```bash
export OPENAI_API_KEY="your-key"
```

If unavailable, the application automatically falls back to local tool execution.

### Stockfish setup

Install Stockfish and pass its binary path when launching:

```bash
python -m chess_coach.cli play --white human --black gm-agent --stockfish-path /usr/local/bin/stockfish
```

## Quick start

Play a game:

```bash
python -m chess_coach.cli play \
  --white human \
  --black gm-agent \
  --stockfish-path /usr/local/bin/stockfish \
  --pgn-out games/latest.pgn \
  --verbose-coach
```

Coach a FEN position with Agents SDK (default):

```bash
python -m chess_coach.cli coach --fen "r1bq1rk1/ppp2ppp/2n2n2/2bp4/4P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 0 1"
```

Coach with local fallback tools only:

```bash
python -m chess_coach.cli coach --disable-openai-agents
```

Launch pygame UI:

```bash
python -m chess_coach.cli ui
```

Controls:
- Mouse click source and destination squares to move pieces
- `C` for coach feedback
- `R` to reset board
- `Esc` to quit

## Agent tools implemented

The following functions are implemented as OpenAI Agents SDK tools in `chess_coach/tools.py`:

- `identify_opening_tool`
- `lichess_opening_explorer_tool`
- `tactical_scan_tool`
- `endgame_plan_tool`
- `candidate_human_moves_tool`
- `legal_moves_tool`
- `titled_advice_search_tool`

## Testing

```bash
pytest -q
```
