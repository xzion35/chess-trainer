import sys
import chess
import chess.pgn
import random

# Functions
## Randomly select one variation
def process_node(node):
    expected_variation = []
    while not node.is_end():
        # Get all possible next moves
        variations = node.variations
        if not variations:
            break  # no more moves
        node = random.choice(variations)
        expected_variation.append(node.move)
    return expected_variation

def engine_turn(self):
    print(f'engine : {expected_moves[self.move_number - 1]}')
    try:
        self.board_widget.play_move(expected_moves[self.move_number - 1])
        self.move_number += 1
    except:
        self.move_number = 1
        self.board_widget.set_board(chess.Board())
        self.statusbar.showMessage("🔄 New variation loaded!", 2000)


# GUI
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog
from PySide6.QtGui import QAction
from chess_widgets import BoardWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Trainer")

        # Layout
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
    
    def open_pgn(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PGN File", "", "PGN Files (*.pgn);;All Files (*)")
        if file_path:
            print("Loaded PGN:", file_path)
            # TODO: load your game here

    def reset_board(self):
        print("Board reset")
        # TODO: reset your chessboard state


    def on_move_played(self, move: chess.Move, move_info: dict):
        if not move_info.get("interactive"):
            return
        print("User played:", move)
        try:
            expected_move = expected_moves[self.move_number - 1]
            print(f'Expected_move : {expected_move}')
            print(f'move_number : {self.move_number}')
        except IndexError:
            self.move_number = 1
            self.board_widget.set_board(chess.Board())
            
        if self.move_number%2 != 0:
            if move == expected_move:
                self.statusBar().showMessage("✅ Correct move!", 2000)
                self.move_number += 1
                engine_turn(self)
            else:
                self.statusBar().showMessage("❌ Wrong move!", 2000)
                # Undo move visually
                self.board_widget.undo_move()

    def show_move(self):
        try:
            print(self.move_number)
            expected_move = expected_moves[self.move_number - 1]
            print(self.move_number,expected_move)
            engine_turn(self)
            engine_turn(self)
        except IndexError:
            self.move_number = 1
            self.board_widget.set_board(chess.Board())

# Main
if __name__ == "__main__":
    # Set up
    global expected_moves

    board = chess.Board()
    pgn = open("PGN/Vienna Gambit.pgn")
    opening = chess.pgn.read_game(pgn)

    expected_moves = process_node(opening)

    # App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())