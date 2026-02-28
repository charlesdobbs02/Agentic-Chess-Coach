import chess

from chess_coach.coach import CoachOrchestrator
from chess_coach.game import ChessGame
from chess_coach.players import GMAgentPlayer
from chess_coach.tools import candidate_human_moves_tool, identify_opening_tool


def test_gm_agent_generates_legal_move():
    board = chess.Board()
    player = GMAgentPlayer()
    move = player.choose_move(board)
    assert move in board.legal_moves


def test_game_tracks_san_moves():
    game = ChessGame(white=GMAgentPlayer(), black=GMAgentPlayer())
    game.play_one_move()
    assert len(game.san_moves) == 1
    assert isinstance(game.san_moves[0], str)


def test_opening_tool_detects_ruy_lopez():
    result = identify_opening_tool("e4,e5,Nf3,Nc6,Bb5")
    assert result["opening"] == "Ruy Lopez"


def test_human_move_tool_returns_san_list():
    moves = candidate_human_moves_tool(chess.Board().fen(), max_moves=3)
    assert isinstance(moves, list)
    assert len(moves) <= 3


def test_coach_report_shape_local_fallback():
    board = chess.Board()
    coach = CoachOrchestrator(use_openai_agents=False)
    report = coach.coach(board, [])
    assert report["mode"] == "local_tools_fallback"
    assert "opening" in report
    assert "tactics" in report
    assert "endgame" in report
    assert "human_recommendation" in report
    assert "external_references" in report
