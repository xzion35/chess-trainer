import sys
import chess
import chess.pgn
import random

# Functions
## Randomly select one variation
def process_node(node):
    expected_variation = []
    try:
        while not node.is_end():
            # Get all possible next moves
            variations = node.variations
            if not variations:
                break  # no more moves
            node = random.choice(variations)
            expected_variation.append(node.move)
    except AttributeError:
        return expected_variation
    return expected_variation


# GUI
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog
from PySide6.QtGui import QAction
from chess_widgets import BoardWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.expected_moves = []
        self.expected_move = None
        self.opening = None
        
        # Layout
        self.setWindowTitle("Chess Trainer")
        self.create_menu()
        container = QWidget()
        layout = QVBoxLayout(container)

        self.board_widget = BoardWidget()
        self.statusbar = self.statusBar()
        self.hint_button = QPushButton("Show Move")

        layout.addWidget(self.board_widget)
        layout.addWidget(self.hint_button)

        self.setCentralWidget(container)
        self.hint_button.clicked.connect(self.show_move)

        # Game state
        self.board = chess.Board()
        self.move_number = 1

        # Connect signal
        self.board_widget.move_played.connect(self.on_move_played)

        # Style
        self.statusBar().setStyleSheet("""
                                     font-size: 24px;
                                     """)
    def create_menu(self):
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")

        # Open PGN action
        open_action = QAction("Open PGN", self)
        open_action.triggered.connect(self.open_pgn)
        file_menu.addAction(open_action)

        # Reset Board action
        reset_action = QAction("Reset Board", self)
        reset_action.triggered.connect(self.reset_board)
        file_menu.addAction(reset_action)
    
    def engine_turn(self):
        try:
            expected_move = self.expected_moves[self.move_number - 1]
            self.board_widget.play_move(expected_move)
            self.move_number += 1
            if self.move_number >= len(self.expected_moves) and len(self.expected_moves) !=0:
                self.statusBar().showMessage("🎉 Line completed!", 3000)
                self.reset_board()
        except IndexError:
            self.reset_board()

    def open_pgn(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PGN File", "", "PGN Files (*.pgn);;All Files (*)")
        if file_path:
            print("Loaded PGN:", file_path)
            with open(file_path) as pgn:
                self.opening = chess.pgn.read_game(pgn)
            self.expected_moves = process_node(self.opening)
            self.reset_board()

    def reset_board(self):
        self.move_number = 1
        self.board_widget.set_board(chess.Board())
        self.expected_moves = process_node(self.opening)

    def on_move_played(self, move: chess.Move, move_info: dict):
        if not move_info.get("interactive"):
            return
        try:
            self.expected_move = self.expected_moves[self.move_number - 1]
        except IndexError:
            pass
        print("User played:", move)
        print("Expected Move:", self.expected_move)
        if self.move_number%2 != 0:
            print(f'self.move_number = {self.move_number} taille = {len(self.expected_moves)}')
            if self.move_number >= len(self.expected_moves) and len(self.expected_moves) !=0:
                self.statusBar().showMessage("🎉 Line completed!", 3000)
                self.reset_board()
            else:
                # print(f'Expected_move : {self.expected_move}')
                if move == self.expected_move:
                    self.statusBar().showMessage("✅ Correct move!", 2000)
                    self.move_number += 1
                    self.engine_turn()
                elif len(self.expected_moves) == 0:
                    self.reset_board()
                else:
                    self.statusBar().showMessage("❌ Wrong move!", 2000)
                    # Undo move visually
                    self.board_widget.undo_move()
        

    def show_move(self):
        try:
            self.engine_turn()
            self.engine_turn()
        except IndexError:
            pass


# Main
if __name__ == "__main__":
    # App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())