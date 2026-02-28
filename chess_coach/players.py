from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import chess
import chess.engine


class Player(Protocol):
    name: str

    def choose_move(self, board: chess.Board) -> chess.Move:
        ...


@dataclass
class HumanPlayer:
    name: str = "human"

    def choose_move(self, board: chess.Board) -> chess.Move:
        print(board)
        print(f"Turn: {'White' if board.turn else 'Black'}")
        move_text = input("Enter move in SAN or UCI: ").strip()
        try:
            return board.parse_san(move_text)
        except ValueError:
            move = chess.Move.from_uci(move_text)
            if move in board.legal_moves:
                return move
            raise ValueError("Invalid move input.")


@dataclass
class StockfishPlayer:
    engine: chess.engine.SimpleEngine
    name: str = "stockfish"
    think_time: float = 0.1

    def choose_move(self, board: chess.Board) -> chess.Move:
        result = self.engine.play(board, chess.engine.Limit(time=self.think_time))
        return result.move


PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0,
}


@dataclass
class GMAgentPlayer:
    """Human-like policy bot: opening principles + tactical safety + simple search."""

    name: str = "gm-agent"
    search_depth: int = 2

    def choose_move(self, board: chess.Board) -> chess.Move:
        best_move = None
        best_score = float("-inf")
        for move in board.legal_moves:
            board.push(move)
            score = -self._negamax(board, self.search_depth - 1)
            score += self._human_style_bonus(board)
            board.pop()
            if score > best_score:
                best_score = score
                best_move = move
        return best_move if best_move else next(iter(board.legal_moves))

    def _negamax(self, board: chess.Board, depth: int) -> float:
        if depth == 0 or board.is_game_over():
            return self._evaluate(board)
        best = float("-inf")
        for move in board.legal_moves:
            board.push(move)
            score = -self._negamax(board, depth - 1)
            board.pop()
            best = max(best, score)
        return best

    def _evaluate(self, board: chess.Board) -> float:
        if board.is_checkmate():
            return -10_000 if board.turn else 10_000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        material = 0
        for p, v in PIECE_VALUES.items():
            material += len(board.pieces(p, chess.WHITE)) * v
            material -= len(board.pieces(p, chess.BLACK)) * v

        mobility = len(list(board.legal_moves)) * (1 if board.turn else -1)
        return material + 0.2 * mobility

    def _human_style_bonus(self, board: chess.Board) -> float:
        bonus = 0.0
        # Encourage center control.
        for sq in [chess.D4, chess.E4, chess.D5, chess.E5]:
            piece = board.piece_at(sq)
            if piece:
                bonus += 10 if piece.color == chess.WHITE else -10

        # Encourage king safety via castling rights usage.
        if board.fullmove_number < 15:
            if board.has_kingside_castling_rights(chess.WHITE):
                bonus -= 4
            if board.has_kingside_castling_rights(chess.BLACK):
                bonus += 4
        return bonus
