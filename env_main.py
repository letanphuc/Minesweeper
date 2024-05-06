#!/usr/bin/env python3

import argparse
import os

from Minesweeper.Minesweeper import MinesweeperGame
from Minesweeper.Highscores import Highscores

SCOREFILE = str(os.path.expanduser("~")) + "/.minesweeper"

levels = (  # width, height, number of mines
    (8, 8, 10),
    (16, 16, 40),
    (30, 16, 99)
)


def get_arguments():
    """get and process command line arguments"""
    parser = argparse.ArgumentParser(
        description="Minesweeper"
    )
    parser.add_argument(
        "--scores",
        metavar="file(s)",
        help=f"Comma separated list of score files to import (default: {SCOREFILE})",
        default=SCOREFILE
    )
    parser.add_argument(
        "--savescores",
        metavar="file",
        help=f"Score file to save (default: {SCOREFILE})",
        default=SCOREFILE
    )
    parser.add_argument(
        "--level",
        metavar="number",
        help=f"Level (difficulty 0..2) (default: 1)",
        default=0
    )
    args = parser.parse_args()

    # process arguments
    args.scores = args.scores.split(",")  # split to list of score files to import

    return args


if __name__ == '__main__':
    args = get_arguments()  # get and process command line arguments
    level = args.level
    highscores = Highscores(loadfiles=args.scores, savefile=args.savescores)
    return_value = ""
    while return_value != "Exit":
        g = MinesweeperGame(*levels[level], highscores)
        g.start_game()
        return_value, return_argument = g.main_loop()
        if return_value == "Resize":
            level = (level + return_argument) % len(levels)
        elif return_value == "Highscores":
            highscores.show(levels[level], return_argument)
    highscores.save()
