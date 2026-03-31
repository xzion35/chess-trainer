# Import
import sys
import chess
import chess.pgn
import random

# GUI
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QFileDialog
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtMultimedia import QSoundEffect
from chess_widgets import BoardWidget

# MainWindow for GUI
class MainWindow(QMainWindow):
    """Main application window for the Chess Trainer."""

    def __init__(self):
        super().__init__()

        # --- Game state ---
        self.variation = []       # Currently selected variation (list of UCI moves)
        self.variations = []      # Remaining variations to practice
        self.expected_move = None # Next expected move from the user
        self.opening = None       # Loaded PGN game object
        self.user_color = "white" # Side the user is playing
        self.move_number = 1      # Current move index in the variation (1-based)
        self.streak = 0           # Number of variations completed in a row
        
        # --- Window setup ---
        self.setWindowTitle("Chess Trainer")
        self.setWindowIcon(QIcon("Logos/logo1_white.png"))
        self.create_menu()

        # --- Layout ---
        container = QWidget()
        layout = QVBoxLayout(container)
        self.board_widget = BoardWidget()
        self.statusbar = self.statusBar()
        self.hint_button = QPushButton("Show Move")
        layout.addWidget(self.board_widget)
        layout.addWidget(self.hint_button)
        self.setCentralWidget(container)
        self.hint_button.clicked.connect(self.show_move)

        # --- Sound effects ---
        self.move_sound = QSoundEffect()
        self.move_sound.setSource(QUrl.fromLocalFile("Sound/Move.wav"))
        self.capture_sound = QSoundEffect()
        self.capture_sound.setSource(QUrl.fromLocalFile("Sound/Capture.wav"))
        self.move_sound.setVolume(0.5)
        self.capture_sound.setVolume(0.5)
        
        # --- Signals ---
        self.board_widget.move_played.connect(self.on_move_played)

        # --- Styles ---
        self.statusBar().setStyleSheet("""
                                     font-size: 24px;
                                     """)
    # Menu on top of the App
    def create_menu(self):
        """Build the top menu bar with actions."""
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")

        # Open PGN action
        open_action = QAction("Open PGN", self)
        open_action.triggered.connect(self.open_pgn)
        file_menu.addAction(open_action)

        # Reset Board action
        reset_action = QAction("Reset Board", self)
        reset_action.triggered.connect(self.reset_board)
        file_menu.addAction(reset_action)

    def play_move_sound(self, move: chess.Move):
        """Play the appropriate sound depending on whether the move is a capture."""
        if self.board.is_capture(move):
            self.capture_sound.play()
        else:
            self.move_sound.play()

    def open_pgn(self):
        """Open a PGN file, parse its variations, and start the training session."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PGN File", "", "PGN Files (*.pgn);;All Files (*)")
        if file_path:
            print("Loaded PGN:", file_path)
            with open(file_path) as pgn:
                self.opening = chess.pgn.read_game(pgn)

            # Determine which side the user plays from the PGN headers
            orientation_tag = self.opening.headers.get("Orientation", "white").lower()
            self.user_color = orientation_tag if orientation_tag in ["white", "black"] else "white"
            print(f'User color : {self.user_color}')

            self.variations = []
            self.extract_variations()
            self.choose_variation()
            self.expected_move = self.variation[self.move_number - 1]
            self.reset_board()

    def extract_variations(self):
        """
        Traverse the PGN game tree and collect all leaf-to-root variations.
        Each variation is stored as a list of UCI move strings.
        """
        self.variations = []  # reset
        stack = [(self.opening, [])]
        while stack:
            current_node, moves = stack.pop()
            if current_node.is_end():
                self.variations.append(moves)
            for variation in current_node.variations:
                move = variation.move
                stack.append((variation, moves + [move.uci()]))  # store UCI string
        print(f"{len(self.variations)} variations loaded")

    def choose_variation(self):
        """Pick a random variation from the remaining list and remove it to avoid repetition."""
        random_id = random.randrange(len(self.variations))
        self.variation = self.variations.pop(random_id)
        print("Variation selected")
        
    def engine_turn(self):
        """Play the expected move from the current variation."""
        if not self.variation or not self.opening:
            return
        try:
            expected_uci = self.variation[self.move_number - 1]
            move = self.board.parse_uci(expected_uci)  # convert to Move
            print(f'Engine move : {move}')
            self.play_move_sound(move)
            self.board_widget.play_move(move)
            self.move_number += 1
            self.check_for_completion()
        except IndexError:
            self.reset_board()
            
    def reset_board(self):
        """Reset the board to its starting position and play the first engine move if needed."""
        self.move_number = 1
        self.board = chess.Board()
        self.board_widget.set_board(self.board)
        
        if self.user_color == "white":
            self.board_widget.set_flipped(False)
        else:
            self.board_widget.set_flipped(True)
        
        # If the user plays black, the engine opens with the first move
        if self.user_color == "black" and self.variation:
            self.engine_turn()
        print("Board Reset")


    def on_move_played(self, move: chess.Move, move_info: dict):
        """
        Handle a move played by the user on the board.
        Validate it against the expected variation move and respond accordingly.
        """
        if not move_info.get("interactive"):
            return
        if not self.variation:
            self.statusBar().showMessage("⚠️ Load a PGN first!", 3000)
            self.board_widget.undo_move()
            return
        try:
            expected_uci = self.variation[self.move_number - 1]
        except IndexError:
            return

        self.play_move_sound(move)
        print("Expected Move:", expected_uci)
        print("User played:", move)

        if move.uci() == expected_uci:
            print("Correct move pushed")
            self.statusBar().showMessage("✅ Correct move!", 2000)
            self.move_number += 1
            QTimer.singleShot(200, self.engine_turn)
        else:
            self.statusBar().showMessage("❌ Wrong move!", 2000)
            self.board_widget.undo_move()
            
    def show_move(self):
        """
        Reveal the correct move by playing it on the board.
        The hint button is temporarily disabled to prevent spamming.
        """
        if not self.variation:
            self.statusBar().showMessage("⚠️ Load a PGN first!", 3000)
            return
        # Disable button and Re-enable button after 1 second
        self.hint_button.setEnabled(False)
        def safe_unlock():
            # Re-enable the button only if the variation is not yet complete
            if self.move_number < len(self.variation) and self.hint_button.isEnabled() == False:
                self.hint_button.setEnabled(True)
                print(f'move_n : {self.move_number}, taille {len(self.variation)}')
        QTimer.singleShot(1000, safe_unlock)
        try:
            self.engine_turn()
            # If there are still moves left, schedule the next move after animation
            if self.move_number <= len(self.variation):
                QTimer.singleShot(500, self.engine_turn)
        except IndexError:
            pass

    def check_for_completion(self):
        """
        Check whether the current variation has been completed.
        If so, move to the next variation or end the session if all are done.
        """
        if self.move_number >= len(self.variation):
            self.streak += 1
            if not self.variations:
                self.statusBar().showMessage("🎉 Training completed!", 3000)
                # Disable button and Re-enable button after 5 seconds
                self.hint_button.setEnabled(False)
                QTimer.singleShot(5000, lambda: self.hint_button.setEnabled(True))
                QTimer.singleShot(5000, self.reset_board)
                self.variation = None # Prevent further interaction until a new PGN is loaded
            else:
                self.choose_variation()
                self.statusBar().showMessage("🎉 Line completed!", 3000)
                # Disable button and Re-enable button after 5 seconds
                self.hint_button.setEnabled(False)
                QTimer.singleShot(5000, lambda: self.hint_button.setEnabled(True))
                QTimer.singleShot(5000, self.reset_board)
            


if __name__ == "__main__":  
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(650, 650)
    window.show()
    sys.exit(app.exec())