# Agentic Chess Coach

A Python chess coaching application that combines:

- **Full chess simulation** (human or AI on either side)
- **Move tracking in SAN/algebraic notation** and **PGN export**
- **Stockfish-powered evaluation and best move analysis** (using `python-chess`)
- **Agentic coaching system** powered by the **OpenAI Agents SDK**, with specialist tools for opening, tactics, endgames, and external reference search.

## Core Design Goals

1. Model a complete chess game with legal move generation, SAN notation, move history, and PGN export.
2. Allow either side to be controlled by:
   - Human
   - Stockfish engine
   - Human-like coaching player (`gm-agent`)
3. Keep Stockfish analysis available for objective evaluation, while coaching recommendations remain human-principled (non-engine line following).
4. Use a modular multi-agent coaching architecture:
   - Opening theory agent
   - Tactical pattern agent
   - Endgame planning agent
   - Research agent for titled-player references

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

## Agent tools implemented

The following functions are implemented as OpenAI Agents SDK tools in `chess_coach/tools.py`:

- `identify_opening_tool`
- `tactical_scan_tool`
- `endgame_plan_tool`
- `candidate_human_moves_tool`
- `titled_advice_search_tool`

## Testing

```bash
pytest -q
```
