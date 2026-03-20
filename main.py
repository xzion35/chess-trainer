import chess
import chess.pgn
import random

board = chess.Board()
pgn = open("PGN/Vienna Gambit.pgn")
opening = chess.pgn.read_game(pgn)
move_number = 1

node = opening

# Start at the root of the game
node = opening

while not node.is_end():
    result = 0
    # Get all possible next moves (variations)
    variations = node.variations
    if not variations:
        break  # no more moves
    # Randomly select one variation
    node = random.choice(variations)
    # Print the move in SAN (Standard Algebraic Notation)
    print(f'Move {move_number} : {node.move}')
    if move_number %2 != 0:
        while result == 0:
            print("Quel est le meilleur coup ?")
            attempt = input()
            if attempt == str(node.move):
                # Good awnser
                result = 1
            else:
                # Bad awnser
                print("Mauvaise réponse")

    move_number += 1