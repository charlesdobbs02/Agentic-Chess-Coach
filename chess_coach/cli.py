from __future__ import annotations

import argparse

import chess
import chess.engine

from .coach import CoachOrchestrator
from .game import ChessGame, StockfishAnalyzer
from .players import GMAgentPlayer, HumanPlayer, StockfishPlayer


def _build_player(kind: str, engine: chess.engine.SimpleEngine | None):
    if kind == "human":
        return HumanPlayer()
    if kind == "gm-agent":
        return GMAgentPlayer()
    if kind == "stockfish":
        if engine is None:
            raise ValueError("stockfish player requested but no --stockfish-path provided")
        return StockfishPlayer(engine=engine)
    raise ValueError(f"Unknown player type: {kind}")


def run_play(args: argparse.Namespace) -> None:
    engine = chess.engine.SimpleEngine.popen_uci(args.stockfish_path) if args.stockfish_path else None
    try:
        white = _build_player(args.white, engine)
        black = _build_player(args.black, engine)
        game = ChessGame(white=white, black=black)
        coach = CoachOrchestrator(model=args.coach_model, use_openai_agents=not args.disable_openai_agents)
        analyzer = StockfishAnalyzer(engine=engine) if engine else None

        while not game.board.is_game_over() and len(game.board.move_stack) < args.max_plies:
            game.play_one_move()
            if args.verbose_coach:
                report = coach.coach(game.board, game.san_moves)
                print("\n[Coach Report]")
                for k, v in report.items():
                    print(f"- {k}: {v}")
                if analyzer:
                    print("- stockfish_eval:", analyzer.evaluate(game.board))

        print("Result:", game.board.result(claim_draw=True) if game.board.is_game_over() else "*")
        if args.pgn_out:
            game.export_pgn(args.pgn_out, white_name=white.name, black_name=black.name)
            print("PGN written to", args.pgn_out)
    finally:
        if engine:
            engine.quit()


def run_coach(args: argparse.Namespace) -> None:
    board = chess.Board(args.fen) if args.fen else chess.Board()
    san_history = args.san_history.split(",") if args.san_history else []
    coach = CoachOrchestrator(model=args.coach_model, use_openai_agents=not args.disable_openai_agents)
    report = coach.coach(board, san_history)
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic Chess Coach CLI")
    sub = parser.add_subparsers(required=True)

    play = sub.add_parser("play", help="Play a game")
    play.add_argument("--white", choices=["human", "gm-agent", "stockfish"], default="human")
    play.add_argument("--black", choices=["human", "gm-agent", "stockfish"], default="gm-agent")
    play.add_argument("--stockfish-path", default=None)
    play.add_argument("--max-plies", type=int, default=300)
    play.add_argument("--pgn-out", default=None)
    play.add_argument("--verbose-coach", action="store_true")
    play.add_argument("--disable-openai-agents", action="store_true")
    play.add_argument("--coach-model", default="gpt-4.1-mini")
    play.set_defaults(func=run_play)

    coach = sub.add_parser("coach", help="Coach a position")
    coach.add_argument("--fen", default=None)
    coach.add_argument("--san-history", default="")
    coach.add_argument("--disable-openai-agents", action="store_true")
    coach.add_argument("--coach-model", default="gpt-4.1-mini")
    coach.set_defaults(func=run_coach)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
