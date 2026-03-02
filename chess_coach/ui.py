from __future__ import annotations

from dataclasses import dataclass, field

import chess
import pygame

from .coach import CoachOrchestrator

LIGHT = (240, 217, 181)
DARK = (181, 136, 99)
HIGHLIGHT = (120, 180, 120)
BG = (28, 28, 32)
TEXT = (230, 230, 230)

PIECE_TO_UNICODE = {
    "P": "♙",
    "N": "♘",
    "B": "♗",
    "R": "♖",
    "Q": "♕",
    "K": "♔",
    "p": "♟",
    "n": "♞",
    "b": "♝",
    "r": "♜",
    "q": "♛",
    "k": "♚",
}


@dataclass
class PygameChessUI:
    coach: CoachOrchestrator
    board: chess.Board = field(default_factory=chess.Board)
    san_moves: list[str] = field(default_factory=list)
    selected_square: int | None = None
    coach_feedback: str = "Press C to request coach feedback."

    square_size: int = 80
    board_origin: tuple[int, int] = (20, 20)
    sidebar_width: int = 420

    def run(self) -> None:
        pygame.init()
        window_size = (self.square_size * 8 + self.sidebar_width + 40, self.square_size * 8 + 40)
        screen = pygame.display.set_mode(window_size)
        pygame.display.set_caption("Agentic Chess Coach - Pygame UI")

        piece_font = pygame.font.SysFont("dejavusans", 44)
        text_font = pygame.font.SysFont("dejavusans", 22)
        small_font = pygame.font.SysFont("dejavusans", 18)

        clock = pygame.time.Clock()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
                    if event.key == pygame.K_c:
                        report = self.coach.coach(self.board, self.san_moves)
                        self.coach_feedback = str(report.get("synthesis", report))
                    if event.key == pygame.K_r:
                        self.board.reset()
                        self.san_moves.clear()
                        self.selected_square = None
                        self.coach_feedback = "Board reset. Press C for coach feedback."
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos)

            screen.fill(BG)
            self._draw_board(screen)
            self._draw_pieces(screen, piece_font)
            self._draw_sidebar(screen, text_font, small_font)
            pygame.display.flip()
            clock.tick(60)

    def _handle_click(self, pos: tuple[int, int]) -> None:
        square = self._pixel_to_square(pos)
        if square is None:
            self.selected_square = None
            return

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
            return

        move = chess.Move(self.selected_square, square)
        legal = self._find_legal_variant(move)
        if legal is not None:
            san = self.board.san(legal)
            self.board.push(legal)
            self.san_moves.append(san)
            self.coach_feedback = f"Played {san}. Press C for updated coaching."

        self.selected_square = None

    def _find_legal_variant(self, move: chess.Move) -> chess.Move | None:
        if move in self.board.legal_moves:
            return move

        from_rank = chess.square_rank(move.from_square)
        to_rank = chess.square_rank(move.to_square)
        piece = self.board.piece_at(move.from_square)
        if piece and piece.piece_type == chess.PAWN and (to_rank == 0 or to_rank == 7) and abs(from_rank - to_rank) == 1:
            promo = chess.Move(move.from_square, move.to_square, promotion=chess.QUEEN)
            if promo in self.board.legal_moves:
                return promo
        return None

    def _draw_board(self, screen: pygame.Surface) -> None:
        ox, oy = self.board_origin
        for rank in range(8):
            for file in range(8):
                x = ox + file * self.square_size
                y = oy + rank * self.square_size
                color = LIGHT if (rank + file) % 2 == 0 else DARK
                square = chess.square(file, 7 - rank)
                if self.selected_square == square:
                    color = HIGHLIGHT
                pygame.draw.rect(screen, color, (x, y, self.square_size, self.square_size))

    def _draw_pieces(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        ox, oy = self.board_origin
        for square, piece in self.board.piece_map().items():
            file = chess.square_file(square)
            rank = 7 - chess.square_rank(square)
            x = ox + file * self.square_size + self.square_size // 2
            y = oy + rank * self.square_size + self.square_size // 2
            glyph = PIECE_TO_UNICODE[piece.symbol()]
            text = font.render(glyph, True, TEXT)
            rect = text.get_rect(center=(x, y))
            screen.blit(text, rect)

    def _draw_sidebar(self, screen: pygame.Surface, text_font: pygame.font.Font, small_font: pygame.font.Font) -> None:
        x0 = self.board_origin[0] + self.square_size * 8 + 20
        y = self.board_origin[1]

        title = text_font.render("Moves played", True, TEXT)
        screen.blit(title, (x0, y))
        y += 36

        move_lines = self._format_moves(self.san_moves)
        for line in move_lines[-16:]:
            line_text = small_font.render(line, True, TEXT)
            screen.blit(line_text, (x0, y))
            y += 22

        y += 10
        subtitle = text_font.render("Coach feedback", True, TEXT)
        screen.blit(subtitle, (x0, y))
        y += 34

        for line in self._wrap(self.coach_feedback, 44):
            line_text = small_font.render(line, True, TEXT)
            screen.blit(line_text, (x0, y))
            y += 22

        y += 8
        instructions = ["Mouse: select source and destination", "C: run coach", "R: reset board", "Esc: quit"]
        for line in instructions:
            line_text = small_font.render(line, True, (190, 190, 200))
            screen.blit(line_text, (x0, y))
            y += 20

    def _pixel_to_square(self, pos: tuple[int, int]) -> int | None:
        ox, oy = self.board_origin
        px, py = pos
        if not (ox <= px < ox + self.square_size * 8 and oy <= py < oy + self.square_size * 8):
            return None
        file = (px - ox) // self.square_size
        rank_from_top = (py - oy) // self.square_size
        rank = 7 - rank_from_top
        return chess.square(file, rank)

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        words = text.split()
        if not words:
            return [""]
        lines: list[str] = []
        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if len(candidate) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
        return lines

    @staticmethod
    def _format_moves(san_moves: list[str]) -> list[str]:
        lines: list[str] = []
        for i in range(0, len(san_moves), 2):
            move_no = i // 2 + 1
            white = san_moves[i]
            black = san_moves[i + 1] if i + 1 < len(san_moves) else ""
            lines.append(f"{move_no}. {white} {black}".strip())
        return lines


def run_pygame_ui(coach_model: str = "gpt-4.1-mini", disable_openai_agents: bool = False) -> None:
    coach = CoachOrchestrator(model=coach_model, use_openai_agents=not disable_openai_agents)
    app = PygameChessUI(coach=coach)
    app.run()


if __name__ == "__main__":
    run_pygame_ui()
