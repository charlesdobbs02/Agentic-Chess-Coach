from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import chess
import chess.engine
import chess.pgn

from players import Player


@dataclass
class ChessGame:
    white: Player
    black: Player
    board: chess.Board = field(default_factory=chess.Board)
    san_moves: list[str] = field(default_factory=list)

    def play_one_move(self) -> chess.Move:
        player = self.white if self.board.turn == chess.WHITE else self.black
        move = player.choose_move(self.board)
        san = self.board.san(move)
        self.board.push(move)
        self.san_moves.append(san)
        return move

    def play_to_completion(self, max_plies: int = 300) -> str:
        plies = 0
        while not self.board.is_game_over() and plies < max_plies:
            self.play_one_move()
            plies += 1
        if self.board.is_game_over():
            return self.board.result()
        return "*"

    def export_pgn(self, out_path: str | Path, white_name: str = "White", black_name: str = "Black") -> None:
        game = chess.pgn.Game()
        game.headers["Event"] = "Agentic Chess Coach Game"
        game.headers["White"] = white_name
        game.headers["Black"] = black_name
        game.headers["Result"] = self.board.result(claim_draw=True) if self.board.is_game_over() else "*"

        node = game
        board = chess.Board()
        for move in self.board.move_stack:
            node = node.add_variation(move)
            board.push(move)

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            print(game, file=f)


@dataclass
class StockfishAnalyzer:
    engine: chess.engine.SimpleEngine

    def evaluate(self, board: chess.Board, think_time: float = 0.1) -> dict:
        info = self.engine.analyse(board, chess.engine.Limit(time=think_time))
        score = info.get("score")
        pv = info.get("pv", [])
        return {
            "score": str(score) if score else "n/a",
            "best_line": [board.san(m) for m in pv[:5]] if pv else [],
            "best_move": pv[0].uci() if pv else None,
        }
