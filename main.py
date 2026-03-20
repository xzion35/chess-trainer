import sys
import chess
import chess.pgn
import random

# Initialisation
board = chess.Board()
pgn = open("PGN/Vienna Gambit.pgn")
opening = chess.pgn.read_game(pgn)


# Functions
## Best move ?
def process_node(node):
    expected_variation = []
    while not node.is_end():
        # Get all possible next moves (variations)
        variations = node.variations
        if not variations:
            break  # no more moves
        # Randomly select one variation
        node = random.choice(variations)
        expected_variation.append(node.move)
    return expected_variation

# GUI
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from chess_widgets import BoardWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess Trainer")

        # Layout
        container = QWidget()
        layout = QVBoxLayout(container)

        self.board_widget = BoardWidget()
        self.label = QLabel("Play the correct move!")

        layout.addWidget(self.board_widget)
        layout.addWidget(self.label)

        self.setCentralWidget(container)

        # Game state
        self.board = chess.Board()
        self.move_number = 1

        # Connect signal
        self.board_widget.move_played.connect(self.on_move_played)

    def on_move_played(self, move: chess.Move, move_info: dict):
        print("User played:", move)
        expected_move = expected_moves[self.move_number - 1]
        print(self.move_number,expected_move)
        if self.move_number%2 != 0:
            if str(move) == str(expected_move):
                self.label.setText("✅ Correct move!")
                # Continue game logic here (set next expected move, etc.)
                self.move_number += 1
                self.board_widget.play_move(expected_moves[self.move_number - 1])
                self.move_number += 1
            else:
                self.label.setText("❌ Wrong move!")

                # Undo move visually
                self.board_widget.undo_move()





if __name__ == "__main__":
    expected_moves = process_node(opening)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())