from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import chess

from .openings import detect_opening_name
from .tools import (
    candidate_human_moves_tool,
    endgame_plan_tool,
    identify_opening_tool,
    legal_moves_tool,
    lichess_opening_explorer_tool,
    tactical_scan_tool,
    titled_advice_search_tool,
)

try:
    from agents import Agent, Runner
except Exception:  # pragma: no cover - SDK optional at runtime
    Agent = None
    Runner = None


MAX_DYNAMIC_AGENTS = 6


@dataclass
class CoachOrchestrator:
    """Coordinates a dynamic agent workflow with planning, critique, and synthesis."""

    model: str = "gpt-4.1-mini"
    use_openai_agents: bool = True

    def coach(self, board: chess.Board, san_history: list[str]) -> dict[str, Any]:
        if self.use_openai_agents and Agent is not None and Runner is not None:
            try:
                return self._coach_with_agents_sdk(board, san_history)
            except Exception:
                # Safe fallback so local/offline runs still work.
                pass
        return self._coach_locally(board, san_history)

    def _coach_with_agents_sdk(self, board: chess.Board, san_history: list[str]) -> dict[str, Any]:
        fen = board.fen()
        legal_moves = legal_moves_tool(fen)
        topic = detect_opening_name(san_history) or "middlegame planning"

        planner_agent = Agent(
            name="Coach Workflow Planner",
            instructions=(
                "Plan a specialized coaching workflow for one chess position. "
                "Return strict JSON with key `agents`, where each item has: `name`, `role`, `goal`, "
                "`prompt`, and `tools` (tool names from this allowlist only: "
                "identify_opening_tool, lichess_opening_explorer_tool, tactical_scan_tool, "
                "candidate_human_moves_tool, endgame_plan_tool, titled_advice_search_tool, legal_moves_tool). "
                "Create at most 6 agents. Prefer opening+explorer+tactics in early game."
            ),
            model=self.model,
        )

        planner_input = (
            f"FEN: {fen}\n"
            f"Move count: {len(board.move_stack)}\n"
            f"Opening/topic hint: {topic}\n"
            f"Legal moves SAN: {', '.join(legal_moves)}\n"
            "Generate workflow JSON now."
        )
        plan_res = Runner.run_sync(planner_agent, planner_input)
        plan = self._parse_plan(str(plan_res.final_output))
        plan = plan[:MAX_DYNAMIC_AGENTS]

        tool_registry = {
            "identify_opening_tool": identify_opening_tool,
            "lichess_opening_explorer_tool": lichess_opening_explorer_tool,
            "tactical_scan_tool": tactical_scan_tool,
            "candidate_human_moves_tool": candidate_human_moves_tool,
            "endgame_plan_tool": endgame_plan_tool,
            "titled_advice_search_tool": titled_advice_search_tool,
            "legal_moves_tool": legal_moves_tool,
        }

        specialist_feedback: list[dict[str, str]] = []
        critic_feedback: list[dict[str, str]] = []

        for spec in plan:
            tool_names = [name for name in spec.get("tools", []) if name in tool_registry]
            if "legal_moves_tool" not in tool_names:
                tool_names.append("legal_moves_tool")
            tools = [tool_registry[name] for name in tool_names]

            specialist = Agent(
                name=spec.get("name", "Specialist Coach"),
                instructions=(
                    f"You are a chess specialist: {spec.get('role', 'general specialist')}. "
                    f"Goal: {spec.get('goal', 'provide practical guidance')}. "
                    "Never suggest illegal moves. Always cross-check with legal_moves_tool. "
                    "Mention concrete candidate SAN moves when appropriate."
                ),
                model=self.model,
                tools=tools,
            )
            specialist_input = (
                f"FEN: {fen}\n"
                f"SAN history: {', '.join(san_history) if san_history else 'None'}\n"
                f"Planner prompt: {spec.get('prompt', '')}\n"
                "Return concise coaching advice with move candidates."
            )
            specialist_res = Runner.run_sync(specialist, specialist_input)
            specialist_text = str(specialist_res.final_output)
            specialist_feedback.append({"agent": specialist.name, "response": specialist_text})

            critic = Agent(
                name=f"{specialist.name} Critic",
                instructions=(
                    "You are a strict chess specialist critic. Verify move legality and quality. "
                    "Use legal_moves_tool to reject illegal SAN suggestions. "
                    "Return concise JSON with keys: verdict, illegal_moves (list), revised_feedback."
                ),
                model=self.model,
                tools=[legal_moves_tool],
            )
            critic_input = (
                f"FEN: {fen}\n"
                f"Specialist response: {specialist_text}\n"
                "Critique and revise if needed."
            )
            critic_res = Runner.run_sync(critic, critic_input)
            critic_feedback.append({"agent": critic.name, "response": str(critic_res.final_output)})

        synthesis = Agent(
            name="Synthesis Agent",
            instructions=(
                "Synthesize specialist and critic outputs into one coherent coaching report. "
                "Highlight legal move shortlist, strategic plan, tactical warning, and one practical next step."
            ),
            model=self.model,
            tools=[legal_moves_tool],
        )
        synthesis_res = Runner.run_sync(
            synthesis,
            (
                f"FEN: {fen}\n"
                f"Specialist outputs: {json.dumps(specialist_feedback)}\n"
                f"Critic outputs: {json.dumps(critic_feedback)}\n"
                "Provide final concise synthesis."
            ),
        )

        return {
            "mode": "openai_agents_sdk_dynamic",
            "planned_agents": [spec.get("name", "Specialist Coach") for spec in plan],
            "agent_count": len(plan),
            "max_agents": MAX_DYNAMIC_AGENTS,
            "specialist_feedback": specialist_feedback,
            "critic_feedback": critic_feedback,
            "synthesis": str(synthesis_res.final_output),
            "legal_moves": legal_moves,
        }

    def _parse_plan(self, raw_output: str) -> list[dict[str, Any]]:
        try:
            payload = json.loads(raw_output)
            if isinstance(payload, dict) and isinstance(payload.get("agents"), list):
                agents = [item for item in payload["agents"] if isinstance(item, dict)]
                if agents:
                    return agents
        except Exception:
            pass

        # Fallback deterministic plan.
        return [
            {
                "name": "Opening Expert",
                "role": "opening specialist",
                "goal": "identify opening themes and practical setup",
                "prompt": "Assess opening ideas from move history and explorer frequencies.",
                "tools": ["identify_opening_tool", "lichess_opening_explorer_tool"],
            },
            {
                "name": "Tactics Expert",
                "role": "tactical specialist",
                "goal": "find forcing opportunities and blunder traps",
                "prompt": "Scan for checks, captures, and tactical motifs.",
                "tools": ["tactical_scan_tool", "candidate_human_moves_tool"],
            },
            {
                "name": "Endgame/Plan Expert",
                "role": "planning specialist",
                "goal": "set strategic plan for current phase",
                "prompt": "Evaluate phase and provide plan transitions.",
                "tools": ["endgame_plan_tool", "candidate_human_moves_tool"],
            },
            {
                "name": "Reference Expert",
                "role": "research specialist",
                "goal": "add trusted study references",
                "prompt": "Provide a few high-signal references for this position theme.",
                "tools": ["titled_advice_search_tool"],
            },
        ]

    def _coach_locally(self, board: chess.Board, san_history: list[str]) -> dict[str, Any]:
        fen = board.fen()
        opening = identify_opening_tool(",".join(san_history))
        opening_explorer = lichess_opening_explorer_tool(fen)
        tactics = tactical_scan_tool(fen)
        endgame = endgame_plan_tool(fen)
        candidates = candidate_human_moves_tool(fen)
        legal_moves = legal_moves_tool(fen)
        topic = opening.get("opening") or "middlegame planning"
        links = titled_advice_search_tool(topic)

        specialist_feedback = {
            "opening_expert": opening,
            "opening_explorer": opening_explorer,
            "tactics_expert": tactics,
            "endgame_expert": endgame,
            "candidate_moves_expert": candidates,
            "research_expert": links,
        }

        critic_feedback = {
            "illegal_candidates": [move for move in candidates if move not in legal_moves],
            "verified_legal_candidates": [move for move in candidates if move in legal_moves],
        }

        synthesis = (
            f"Opening/theme: {topic}. "
            f"Legal candidate moves: {', '.join(critic_feedback['verified_legal_candidates']) if critic_feedback['verified_legal_candidates'] else 'none identified'}. "
            f"Tactical forcing moves seen: {', '.join(tactics.get('forcing_candidates', [])) if tactics.get('forcing_candidates') else 'none'}. "
            f"Phase guidance: {endgame.get('advice', '')}"
        )

        return {
            "mode": "local_tools_fallback_dynamic",
            "planned_agents": ["Opening Expert", "Tactics Expert", "Endgame/Plan Expert", "Reference Expert"],
            "agent_count": 4,
            "max_agents": MAX_DYNAMIC_AGENTS,
            "specialist_feedback": specialist_feedback,
            "critic_feedback": critic_feedback,
            "synthesis": synthesis,
            "legal_moves": legal_moves,
        }
