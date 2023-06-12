from Minesweeper.Minesweeper import MinesweeperGame


if __name__ == '__main__':
    g = MinesweeperGame(20, 20, 20)
    g.start_game()
    g.main_loop()
