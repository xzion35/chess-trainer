import sys
import chess
import time
import chess.pgn
import random

# GUI
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog
from PySide6.QtGui import QAction, QIcon
from chess_widgets import BoardWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Game state
        self.variations = []
        self.expected_move = None
        self.opening = None       
        self.board = chess.Board()
        self.move_number = 1
        self.streak = 0
        
        # Layout
        self.setWindowTitle("Chess Trainer")
        self.setWindowIcon(QIcon("Logos/logo1_white.png"))
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
            with open(file_path) as pgn:
                self.opening = chess.pgn.read_game(pgn)
            self.extract_variations()
            self.choose_variation()
            self.expected_move = self.variation[self.move_number - 1]
            self.reset_board()

    def extract_variations(self):
        stack = [(self.opening, [])]
        while stack:
            current_node, moves = stack.pop()
            # Is the variation finished ?
            if current_node.is_end():
                self.variations.append(moves)

            for variation in current_node.variations:
                move = variation.move
                stack.append((variation, moves + [move]))
        print(f"{len(self.variations)} variations loaded")

    def choose_variation(self):
        random_id = random.randrange(len(self.variations))
        self.variation = self.variations.pop(random_id)
        print(f'Variation selected : {self.variation}')

    def engine_turn(self):
        try:
            expected_move = self.variation[self.move_number - 1]
            self.board_widget.play_move(expected_move)
            self.move_number += 1
            if self.move_number >= len(self.variation) and len(self.variation) !=0:
                self.statusBar().showMessage("🎉 Line completed!", 3000)
                self.reset_board()
        except IndexError:
            self.reset_board()

    def reset_board(self):
        self.move_number = 1
        self.board_widget.set_board(chess.Board())


    def on_move_played(self, move: chess.Move, move_info: dict):
        if not move_info.get("interactive"):
            return
        try:
            self.expected_move = self.variation[self.move_number - 1]
        except IndexError:
            pass
        
        print("Expected Move:", self.expected_move)
        print("User played:", move)
        if self.move_number%2 != 0:
            # print(f'self.move_number = {self.move_number} taille = {len(self.expected_moves)}')
            if self.move_number >= len(self.variation) and len(self.variation) !=0:
                self.streak += 1
                self.statusBar().showMessage("🎉 Line completed!", 3000)
                time(5000)
                self.reset_board()
            else:
                # print(f'Expected_move : {self.expected_move}')
                if move == self.expected_move:
                    self.statusBar().showMessage("✅ Correct move!", 2000)
                    self.move_number += 1
                    self.engine_turn()
                elif len(self.variation) == 0:
                    self.reset_board()
                else:
                    self.statusBar().showMessage("❌ Wrong move!", 2000)
                    # Undo move visually
                    self.board_widget.undo_move()
        
    def show_move(self):
        try:
            self.engine_turn()
            time(3000)
            self.engine_turn()
        except IndexError:
            pass



# Main
if __name__ == "__main__":  
    # App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(650, 650)
    window.show()
    sys.exit(app.exec())