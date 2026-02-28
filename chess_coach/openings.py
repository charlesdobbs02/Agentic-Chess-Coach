"""Small opening knowledge base for coach guidance."""

OPENING_PLANS = {
    "Sicilian Defense": {
        "moves": ["e4", "c5"],
        "ideas": [
            "Fight for d4 and central dark squares.",
            "Develop with ...Nc6/...d6 and prepare kingside safety.",
            "Look for minority pressure on queenside in many structures.",
        ],
    },
    "Ruy Lopez": {
        "moves": ["e4", "e5", "Nf3", "Nc6", "Bb5"],
        "ideas": [
            "Pressure e5 and support d4 central expansion.",
            "Keep flexible pawn structure before committing c3/d4.",
            "Use bishop pair trade decisions based on center tension.",
        ],
    },
    "Queen's Gambit": {
        "moves": ["d4", "d5", "c4"],
        "ideas": [
            "Challenge Black's d5 pawn and aim for central space edge.",
            "Develop light-squared bishop actively before e3 if possible.",
            "Watch for minority attack themes with b4-b5 in some lines.",
        ],
    },
}


def detect_opening_name(move_san_history: list[str]) -> str | None:
    for name, payload in OPENING_PLANS.items():
        seq = payload["moves"]
        if len(move_san_history) >= len(seq) and move_san_history[: len(seq)] == seq:
            return name
    return None
