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
    def __init__(self):
        super().__init__()
        # Game state
        self.variation = [] # List of the selected variation
        self.variations = [] # List of all possible variations
        self.expected_move = None
        self.opening = None
        self.board = chess.Board()
        self.user_color = "white" # default value
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

        # Sound
        self.move_sound = QSoundEffect()
        self.move_sound.setSource(QUrl.fromLocalFile("Sound/Move.wav"))
        self.capture_sound = QSoundEffect()
        self.capture_sound.setSource(QUrl.fromLocalFile("Sound/Capture.wav"))
        # Volume
        self.move_sound.setVolume(0.5)
        self.capture_sound.setVolume(0.5)
        
        # Connect signal
        self.board_widget.move_played.connect(self.on_move_played)

        # Style
        self.statusBar().setStyleSheet("""
                                     font-size: 24px;
                                     """)
    # Menu on top of the App
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

    def play_move_sound(self, move: chess.Move):
        # Condition to play the correct sound
        if self.board.is_capture(move):
            self.capture_sound.play()
        else:
            self.move_sound.play()

    def open_pgn(self):
        # Open openging file in PGN format
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PGN File", "", "PGN Files (*.pgn);;All Files (*)")
        if file_path:
            print("Loaded PGN:", file_path)
            with open(file_path) as pgn:
                self.opening = chess.pgn.read_game(pgn)

            # Read board side
            orientation_tag = self.opening.headers.get("Orientation", "white").lower()
            self.user_color = orientation_tag if orientation_tag in ["white", "black"] else "white"
            print(f'User color : {self.user_color}')

            # Initialisation
            self.variations = []  # reset variations
            self.extract_variations()
            self.choose_variation()
            self.expected_move = self.variation[self.move_number - 1]
            self.reset_board()

    def extract_variations(self):
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

    # Randomly choose a variation and remove it from the list to not play it twice
    def choose_variation(self):
        random_id = random.randrange(len(self.variations))
        self.variation = self.variations.pop(random_id)
        print("Variation selected")
        
    def engine_turn(self):
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
        self.move_number = 1
        self.board = chess.Board()
        self.board_widget.set_board(self.board)
        
        if self.user_color == "white":
            self.board_widget.set_flipped(False)  # False = White
        else:
            self.board_widget.set_flipped(True)   # True = Black
        
        if self.user_color == "black" and self.variation:
            self.engine_turn()
        print("Board Reset")


    def on_move_played(self, move: chess.Move, move_info: dict):
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
        if not self.variation:
            self.statusBar().showMessage("⚠️ Load a PGN first!", 3000)
            return
        # Disable button and Re-enable button after 1 second
        self.hint_button.setEnabled(False)
        def safe_unlock():
            # Enable buton only if it's not the end of the variation
            if self.move_number < len(self.variation) and self.hint_button.isEnabled() == False:
                self.hint_button.setEnabled(True)
                print(f'move_n : {self.move_number}, taille {len(self.variation)}')
        QTimer.singleShot(1000, safe_unlock)
        try:
            self.engine_turn()
            # If there are still moves left, schedule the next move after animation
            if self.move_number <= len(self.variation):
                QTimer.singleShot(500, self.engine_turn) # add small delay to let the animation
        except IndexError:
            pass

    def check_for_completion(self):
        if self.move_number >= len(self.variation):
            self.streak += 1
            if not self.variations:
                self.statusBar().showMessage("🎉 Training completed!", 3000)
                # Disable button and Re-enable button after 5 seconds
                self.hint_button.setEnabled(False)
                QTimer.singleShot(5000, lambda: self.hint_button.setEnabled(True))
                QTimer.singleShot(5000, self.reset_board)
                # Force user to load an other PGN
                self.variation = None
            else:
                self.choose_variation()
                self.statusBar().showMessage("🎉 Line completed!", 3000)
                # Disable button and Re-enable button after 5 seconds
                self.hint_button.setEnabled(False)
                QTimer.singleShot(5000, lambda: self.hint_button.setEnabled(True))
                QTimer.singleShot(5000, self.reset_board)
            

# Main
if __name__ == "__main__":  
    # App
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(650, 650)
    window.show()
    sys.exit(app.exec())