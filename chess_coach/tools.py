from __future__ import annotations

from typing import Any

import chess
import requests
from bs4 import BeautifulSoup

from .openings import OPENING_PLANS, detect_opening_name

try:
    from agents import function_tool
except Exception:  # pragma: no cover - import shim for environments without SDK
    def function_tool(func):
        return func


def _to_board(fen: str) -> chess.Board:
    return chess.Board(fen) if fen else chess.Board()


@function_tool
def identify_opening_tool(san_history_csv: str) -> dict[str, Any]:
    """Identify opening and provide key strategic plans based on SAN move history.

    Args:
        san_history_csv: Comma-separated SAN moves from the game start.
    """
    san_history = [m.strip() for m in san_history_csv.split(",") if m.strip()]
    opening_name = detect_opening_name(san_history)
    if not opening_name:
        return {
            "opening": None,
            "plan": ["Develop quickly", "Control center", "Castle early"],
        }
    return {
        "opening": opening_name,
        "plan": OPENING_PLANS[opening_name]["ideas"],
    }


@function_tool
def tactical_scan_tool(fen: str) -> dict[str, Any]:
    """Scan the position for forcing tactical candidates.

    Args:
        fen: Board position in FEN format.
    """
    board = _to_board(fen)
    forcing: list[str] = []
    for move in board.legal_moves:
        if board.is_capture(move) or board.gives_check(move):
            forcing.append(board.san(move))
    return {
        "in_check": board.is_check(),
        "forcing_candidates": forcing[:10],
    }


@function_tool
def endgame_plan_tool(fen: str) -> dict[str, str]:
    """Provide endgame planning guidance from board features.

    Args:
        fen: Board position in FEN format.
    """
    board = _to_board(fen)
    pieces = len(board.piece_map())
    if pieces > 12:
        return {"phase": "middlegame", "advice": "Improve worst-placed piece and simplify only when favorable."}
    return {
        "phase": "endgame",
        "advice": "Activate king, create passed pawns, and use opposition/zugzwang motifs carefully.",
    }


@function_tool
def titled_advice_search_tool(topic: str, max_results: int = 3) -> list[str]:
    """Search public web snippets for titled-player advice.

    Args:
        topic: Opening/tactic/endgame topic to search.
        max_results: Maximum references to return.
    """
    query = f"site:chess.com OR site:chessbase.com grandmaster advice {topic}"
    try:
        response = requests.get("https://duckduckgo.com/html/", params={"q": query}, timeout=6)
        response.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[str] = []
    for tag in soup.select("a.result__a"):
        title = tag.get_text(" ", strip=True)
        href = tag.get("href", "")
        if title and href:
            results.append(f"{title} ({href})")
        if len(results) >= max_results:
            break
    return results


@function_tool
def candidate_human_moves_tool(fen: str, max_moves: int = 3) -> list[str]:
    """Return principled move candidates without engine best-move usage.

    Args:
        fen: Board position in FEN format.
        max_moves: Number of move candidates to return.
    """
    board = _to_board(fen)
    scored: list[tuple[int, chess.Move]] = []
    for move in board.legal_moves:
        score = 0
        if board.is_capture(move):
            score += 2
        if board.gives_check(move):
            score += 2
        board.push(move)
        if board.is_attacked_by(board.turn, move.to_square):
            score -= 1
        board.pop()
        scored.append((score, move))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [board.san(move) for _, move in scored[:max_moves]]


@function_tool
def legal_moves_tool(fen: str) -> list[str]:
    """Return all legal moves in SAN notation for a given FEN."""
    board = _to_board(fen)
    return [board.san(move) for move in board.legal_moves]


@function_tool
def lichess_opening_explorer_tool(fen: str, top_n: int = 6) -> dict[str, Any]:
    """Fetch opening explorer move frequencies from Lichess public API."""
    try:
        response = requests.get(
            "https://explorer.lichess.ovh/lichess",
            params={"fen": fen, "moves": top_n, "variant": "standard"},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return {"source": "lichess", "moves": [], "total_games": 0}

    moves: list[dict[str, Any]] = []
    for move in payload.get("moves", [])[:top_n]:
        total = move.get("white", 0) + move.get("draws", 0) + move.get("black", 0)
        moves.append(
            {
                "san": move.get("san"),
                "white": move.get("white", 0),
                "draws": move.get("draws", 0),
                "black": move.get("black", 0),
                "total": total,
            }
        )
    return {"source": "lichess", "moves": moves, "total_games": payload.get("white", 0) + payload.get("draws", 0) + payload.get("black", 0)}
