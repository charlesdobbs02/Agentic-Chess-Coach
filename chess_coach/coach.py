from __future__ import annotations

import json
from dataclasses import dataclass

import chess

from .openings import detect_opening_name
from .tools import (
    candidate_human_moves_tool,
    endgame_plan_tool,
    identify_opening_tool,
    tactical_scan_tool,
    titled_advice_search_tool,
)

try:
    from agents import Agent, Runner
except Exception:  # pragma: no cover - SDK optional at runtime
    Agent = None
    Runner = None


@dataclass
class CoachOrchestrator:
    """Coordinates specialist coaching agents via OpenAI Agents SDK tools."""

    model: str = "gpt-4.1-mini"
    use_openai_agents: bool = True

    def coach(self, board: chess.Board, san_history: list[str]) -> dict:
        if self.use_openai_agents and Agent is not None and Runner is not None:
            try:
                return self._coach_with_agents_sdk(board, san_history)
            except Exception:
                # Safe fallback so local/offline runs still work.
                pass
        return self._coach_locally(board, san_history)

    def _coach_with_agents_sdk(self, board: chess.Board, san_history: list[str]) -> dict:
        fen = board.fen()
        san_csv = ",".join(san_history)

        opening_agent = Agent(
            name="Opening Coach Agent",
            instructions=(
                "You are a 2800+ human chess coach focused on opening understanding. "
                "Use identify_opening_tool and explain plans in practical, human language."
            ),
            model=self.model,
            tools=[identify_opening_tool],
        )
        tactics_agent = Agent(
            name="Tactics Coach Agent",
            instructions=(
                "You are a tactical coach. Use tactical_scan_tool and provide concrete tactical alerts "
                "with forcing priorities and blunder prevention."
            ),
            model=self.model,
            tools=[tactical_scan_tool],
        )
        endgame_agent = Agent(
            name="Endgame Coach Agent",
            instructions="You are an endgame coach. Use endgame_plan_tool and provide practical plans.",
            model=self.model,
            tools=[endgame_plan_tool],
        )
        recommendation_agent = Agent(
            name="Human Move Recommendation Agent",
            instructions=(
                "Recommend human-like candidate moves. Never use engine best moves. "
                "Use candidate_human_moves_tool and justify in plain language."
            ),
            model=self.model,
            tools=[candidate_human_moves_tool],
        )
        research_agent = Agent(
            name="Chess Research Agent",
            instructions="Find titled-player references for the current topic using titled_advice_search_tool.",
            model=self.model,
            tools=[titled_advice_search_tool],
        )

        opening_res = Runner.run_sync(
            opening_agent,
            f"SAN history CSV: {san_csv}\nReturn concise opening diagnosis and plan.",
        )
        tactics_res = Runner.run_sync(tactics_agent, f"FEN: {fen}\nReturn tactical priorities.")
        endgame_res = Runner.run_sync(endgame_agent, f"FEN: {fen}\nReturn endgame or simplification plan.")
        recommendation_res = Runner.run_sync(
            recommendation_agent,
            f"FEN: {fen}\nGive top human-style candidate moves and rationale.",
        )

        topic = detect_opening_name(san_history) or "middlegame planning"
        research_res = Runner.run_sync(
            research_agent,
            f"Topic: {topic}\nReturn up to 3 high-signal references.",
        )

        return {
            "opening": str(opening_res.final_output),
            "tactics": str(tactics_res.final_output),
            "endgame": str(endgame_res.final_output),
            "human_recommendation": str(recommendation_res.final_output),
            "external_references": str(research_res.final_output),
            "mode": "openai_agents_sdk",
        }

    def _coach_locally(self, board: chess.Board, san_history: list[str]) -> dict:
        fen = board.fen()
        opening = identify_opening_tool(",".join(san_history))
        tactics = tactical_scan_tool(fen)
        endgame = endgame_plan_tool(fen)
        candidates = candidate_human_moves_tool(fen)
        topic = opening.get("opening") or "middlegame planning"
        links = titled_advice_search_tool(topic)

        return {
            "opening": json.dumps(opening),
            "tactics": json.dumps(tactics),
            "endgame": json.dumps(endgame),
            "human_recommendation": f"Candidate moves: {', '.join(candidates) if candidates else 'None'}",
            "external_references": links,
            "mode": "local_tools_fallback",
        }
