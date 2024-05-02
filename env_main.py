from Minesweeper.Minesweeper import MinesweeperGame

levels = [  # width, height, number of mines
    [8, 8, 10],
    [16, 16, 40],
    [30, 16, 99]
]

if __name__ == '__main__':
    level = 1
    retval = "Resize"
    while retval == "Resize":
        g = MinesweeperGame(*levels[level])
        g.start_game()
        retval = g.main_loop()
        level = (level + 1) % len(levels)
