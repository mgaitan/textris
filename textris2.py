# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "textual",
# ]
# ///

from textual.app import App, ComposeResult
from textual.widgets import Static, Label
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.style import Style
import random

# Tetris piece definitions (standard Tetrominos)
PIECES = {
    'I': {
        'color': 'cyan',
        'shapes': [
            [[1, 1, 1, 1]],
            [[1], [1], [1], [1]]
        ]
    },
    'O': {
        'color': 'yellow',
        'shapes': [
            [[1, 1], [1, 1]]
        ]
    },
    'T': {
        'color': 'magenta',
        'shapes': [
            [[0, 1, 0], [1, 1, 1]],
            [[1, 0], [1, 1], [1, 0]],
            [[1, 1, 1], [0, 1, 0]],
            [[0, 1], [1, 1], [0, 1]]
        ]
    },
    'S': {
        'color': 'green',
        'shapes': [
            [[0, 1, 1], [1, 1, 0]],
            [[1, 0], [1, 1], [0, 1]]
        ]
    },
    'Z': {
        'color': 'red',
        'shapes': [
            [[1, 1, 0], [0, 1, 1]],
            [[0, 1], [1, 1], [1, 0]]
        ]
    },
    'J': {
        'color': 'blue',
        'shapes': [
            [[1, 0, 0], [1, 1, 1]],
            [[1, 1], [1, 0], [1, 0]],
            [[1, 1, 1], [0, 0, 1]],
            [[0, 1], [0, 1], [1, 1]]
        ]
    },
    'L': {
        'color': 'bright_yellow',
        'shapes': [
            [[0, 0, 1], [1, 1, 1]],
            [[1, 0], [1, 0], [1, 1]],
            [[1, 1, 1], [1, 0, 0]],
            [[1, 1], [0, 1], [0, 1]]
        ]
    }
}

class TetrisPiece:
    def __init__(self, piece_type=None):
        if piece_type is None:
            piece_type = random.choice(list(PIECES.keys()))

        self.type = piece_type
        self.color = PIECES[piece_type]['color']
        self.shapes = PIECES[piece_type]['shapes']
        self.rotation = 0
        self.x = 4  # Start at center of board
        self.y = 0

    @property
    def shape(self):
        return self.shapes[self.rotation % len(self.shapes)]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.shapes)

class TetrisBoard(Static):
    """The main game board widget"""

    def __init__(self, width=10, height=20, **kwargs):
        super().__init__(**kwargs)
        self.board_width = width
        self.board_height = height
        self.board = [[0 for _ in range(width)] for _ in range(height)]
        self.current_piece = TetrisPiece()

    def compose(self) -> ComposeResult:
        yield Static(self.render_board(), id="board-display")

    def on_mount(self):
        """Called when the widget is mounted"""
        self.update_display()

    def render_board(self) -> Text:
        """Render the current state of the board"""
        text = Text()

        # Create a copy of the board to render the current piece
        display_board = [row[:] for row in self.board]

        # Add current piece to display board
        if self.current_piece:
            piece_shape = self.current_piece.shape
            for py, row in enumerate(piece_shape):
                for px, cell in enumerate(row):
                    if cell:  # Only render non-zero cells
                        board_x = self.current_piece.x + px
                        board_y = self.current_piece.y + py
                        if (0 <= board_x < self.board_width and
                            0 <= board_y < self.board_height):
                            display_board[board_y][board_x] = self.current_piece.color

        # Add top border
        text.append("┌" + "─" * (self.board_width * 2) + "┐\n", style="bold white")

        # Render each row
        for row in display_board:
            text.append("│", style="bold white")
            for cell in row:
                if cell == 0:
                    text.append("  ")
                else:
                    text.append("██", style=f"bold {cell}")
            text.append("│\n", style="bold white")

        # Add bottom border
        text.append("└" + "─" * (self.board_width * 2) + "┘", style="bold white")

        return text

    def update_display(self):
        """Update the board display"""
        try:
            board_display = self.query_one("#board-display", Static)
            board_display.update(self.render_board())
        except:
            pass  # Widget not ready yet

    def move_piece(self, dx, dy):
        """Move the current piece"""
        old_x, old_y = self.current_piece.x, self.current_piece.y
        self.current_piece.x += dx
        self.current_piece.y += dy

        # Check collision with boundaries and existing pieces
        if self.check_collision():
            # Revert move
            self.current_piece.x, self.current_piece.y = old_x, old_y
            return False

        self.update_display()
        return True

    def check_collision(self):
        """Check if current piece collides with boundaries or other pieces"""
        piece_shape = self.current_piece.shape

        for py, row in enumerate(piece_shape):
            for px, cell in enumerate(row):
                if cell:  # Only check non-zero cells
                    board_x = self.current_piece.x + px
                    board_y = self.current_piece.y + py

                    # Check boundaries
                    if (board_x < 0 or board_x >= self.board_width or
                        board_y >= self.board_height):
                        return True

                    # Check collision with existing pieces (if board_y >= 0)
                    if board_y >= 0 and self.board[board_y][board_x] != 0:
                        return True

        return False

    def rotate_piece(self):
        """Rotate the current piece"""
        old_rotation = self.current_piece.rotation
        self.current_piece.rotate()

        # Check if rotation causes collision
        if self.check_collision():
            # Revert rotation
            self.current_piece.rotation = old_rotation
            return False

        self.update_display()
        return True

class NextPieceWidget(Static):
    """Widget to show the next piece"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next_piece = TetrisPiece()

    def compose(self) -> ComposeResult:
        yield Label("NEXT", classes="section-title")
        yield Static(self.render_next_piece(), id="next-piece-display")

    def render_next_piece(self) -> Text:
        shape = self.next_piece.shape
        color = self.next_piece.color
        shape_h = len(shape)
        shape_w = max(len(r) for r in shape)
        dim     = max(shape_h, shape_w, 4)

        text = Text()
        # top border
        text.append("┌" + "─" * (dim*2) + "┐\n", style="dim white")

        # how many blank rows above/below
        top_pad    = (dim - shape_h) // 2
        bottom_pad = dim - shape_h - top_pad

        # helper for an empty row
        empty = "│" + "  " * dim + "│\n"
        for _ in range(top_pad):
            text.append(empty)

        # each shape row, centered horizontally
        for row in shape:
            # left padding
            left   = (dim - len(row)) // 2
            right  = dim - len(row) - left
            text.append("│" + "  " * left)
            for cell in row:
                if cell:
                    text.append("██", style=f"bold {color}")
                else:
                    text.append("  ")
            text.append("  " * right + "│\n", style="dim white")

        for _ in range(bottom_pad):
            text.append(empty)

        # bottom border
        text.append("└" + "─" * (dim*2) + "┘", style="dim white")
        return text


    def update_piece(self, piece):
        """Update the next piece"""
        self.next_piece = piece
        next_display = self.query_one("#next-piece-display", Static)
        next_display.update(self.render_next_piece())

class ScoreWidget(Static):
    """Widget to display score and level"""

    score = reactive(0)
    level = reactive(1)
    lines = reactive(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        yield Label("SCORE", classes="section-title")
        yield Label(str(self.score), id="score-value", classes="score-number")
        yield Label("LEVEL", classes="section-title")
        yield Label(str(self.level), id="level-value", classes="score-number")
        yield Label("LINES", classes="section-title")
        yield Label(str(self.lines), id="lines-value", classes="score-number")

    def watch_score(self, score: int):
        try:
            self.query_one("#score-value", Label).update(str(score))
        except:
            pass  # Widget not ready yet

    def watch_level(self, level: int):
        try:
            self.query_one("#level-value", Label).update(str(level))
        except:
            pass  # Widget not ready yet

    def watch_lines(self, lines: int):
        try:
            self.query_one("#lines-value", Label).update(str(lines))
        except:
            pass  # Widget not ready yet

class TetrisApp(App):
    """Main Tetris application"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_timer = None
        self.drop_interval = 1.0  # Seconds between automatic drops

    CSS = """
    Screen {
        background: $background;
    }

    #game-container {
        width: 100%;
        height: 100%;
        background: $surface;
        border: heavy $primary;
        padding: 1;
    }

    #board-container {
        width: 24;
        height: 24;
        margin: 1;
        padding: 1;
        background: $panel;
        border: solid $accent;
    }

    #board-display {
        margin: 1;
    }

    #sidebar {
        width: 20;
        margin-left: 2;
        padding: 1;
    }

    #next-piece-container {
        margin-bottom: 2;
        padding: 1;
        background: $panel;
        border: solid $accent;
    }

    #score-container {
        height: 12;
        padding: 1;
        background: $panel;
        border: solid $accent;
    }

    .section-title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }

    .score-number {
        text-align: center;
        text-style: bold;
        color: $warning;
        margin-bottom: 1;
        content-align: center middle;
    }

    #controls {
        margin-top: 2;
        padding: 1;
        background: $panel;
        border: solid $accent;
        height: 8;
    }

    #title {
        text-align: center;
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("left,a", "move_left", "Move Left"),
        ("right,d", "move_right", "Move Right"),
        ("down,s", "move_down", "Move Down"),
        ("up,w,space", "rotate", "Rotate"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="game-container"):
            yield Label("🎮 TETRIS 🎮", id="title")
            with Horizontal():
                with Container(id="board-container"):
                    yield TetrisBoard(id="board")
                with Vertical(id="sidebar"):
                    with Container(id="next-piece-container"):
                        yield NextPieceWidget(id="next-piece")
                    with Container(id="score-container"):
                        yield ScoreWidget(id="score-widget")
                    with Container(id="controls"):
                        yield Label("CONTROLS", classes="section-title")
                        yield Label("↑/W/Space: Rotate")
                        yield Label("←/A: Move Left")
                        yield Label("→/D: Move Right")
                        yield Label("↓/S: Move Down")
                        yield Label("Q: Quit")

    def on_mount(self):
        """Initialize the game"""
        self.board = self.query_one("#board", TetrisBoard)
        self.next_piece_widget = self.query_one("#next-piece", NextPieceWidget)
        self.score_widget = self.query_one("#score-widget", ScoreWidget)

        # Give widgets time to mount, then update displays
        self.call_after_refresh(self._update_all_displays)

        # Start the game timer for automatic piece dropping
        self.start_game_timer()

    def _update_all_displays(self):
        """Update all game displays after widgets are mounted"""
        self.board.update_display()
        self.next_piece_widget.update_piece(TetrisPiece())

    def start_game_timer(self):
        """Start the automatic piece dropping timer"""
        self.game_timer = self.set_interval(self.drop_interval, self.auto_drop)

    def auto_drop(self):
        """Automatically drop the current piece"""
        if not self.board.move_piece(0, 1):
            # Piece can't move down anymore - this is where we'd lock it and spawn new piece
            # For now, just reset to top
            self.board.current_piece.x = 4
            self.board.current_piece.y = 0
            self.board.current_piece = TetrisPiece()
            self.board.update_display()

    def action_move_left(self):
        """Move piece left"""
        self.board.move_piece(-1, 0)

    def action_move_right(self):
        """Move piece right"""
        self.board.move_piece(1, 0)

    def action_move_down(self):
        """Move piece down"""
        self.board.move_piece(0, 1)

    def action_rotate(self):
        """Rotate piece"""
        self.board.rotate_piece()

if __name__ == "__main__":
    app = TetrisApp()
    app.run()
