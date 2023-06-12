import pygame
import random
import os
from loguru import logger
from enum import Enum
from dataclasses import dataclass

pygame.init()


class Grid:
    def __init__(self, xGrid, yGrid, type, game):
        self.xGrid = xGrid  # X pos of grid
        self.yGrid = yGrid  # Y pos of grid
        self.clicked = False  # Boolean var to check if the grid has been clicked
        self.mineClicked = False  # Bool var to check if the grid is clicked and its a mine
        self.mineFalse = False  # Bool var to check if the player flagged the wrong grid
        self.flag = False  # Bool var to check if player flagged the grid
        # Create rectObject to handle drawing and collisions
        self.rect = pygame.Rect(
            game.border + self.xGrid * game.grid_size,
            game.top_border + self.yGrid * game.grid_size,
            game.grid_size,
            game.grid_size,
        )
        self.val = type  # Value of the grid, -1 is mine
        self.game = game

    def drawGrid(self):
        # Draw the grid according to bool variables and value of grid
        if self.mineFalse:
            self.game.display.blit(self.game.spr_mineFalse, self.rect)
        else:
            if self.clicked:
                if self.val == -1:
                    if self.mineClicked:
                        self.game.display.blit(self.game.spr_mineClicked, self.rect)
                    else:
                        self.game.display.blit(self.game.spr_mine, self.rect)
                else:
                    assert 0 <= self.val <= 8, f"{self.val=}"
                    self.game.display.blit(self.game.spr_grids[self.val], self.rect)

            else:
                if self.flag:
                    self.game.display.blit(self.game.spr_flag, self.rect)
                else:
                    self.game.display.blit(self.game.spr_grid, self.rect)

    def revealGrid(self):
        self.clicked = True
        # Auto reveal if it's a 0
        if self.val == 0:
            for x in range(-1, 2):
                if self.xGrid + x >= 0 and self.xGrid + x < self.game.game_width:
                    for y in range(-1, 2):
                        if self.yGrid + y >= 0 and self.yGrid + y < self.game.game_height:
                            if not self.game.grid[self.yGrid + y][self.xGrid + x].clicked:
                                self.game.grid[self.yGrid + y][self.xGrid + x].revealGrid()
        elif self.val == -1:
            # Auto reveal all mines if it's a mine
            for m in self.game.mines:
                if not self.game.grid[m[1]][m[0]].clicked:
                    self.game.grid[m[1]][m[0]].revealGrid()

    def updateValue(self):
        # Update the value when all grid is generated
        if self.val != -1:
            for x in range(-1, 2):
                if self.xGrid + x >= 0 and self.xGrid + x < self.game.game_width:
                    for y in range(-1, 2):
                        if self.yGrid + y >= 0 and self.yGrid + y < self.game.game_height:
                            if self.game.grid[self.yGrid + y][self.xGrid + x].val == -1:
                                self.val += 1


@dataclass
class GameEvent:
    class EventType(Enum):
        EXIT = 0
        RESTART = 1
        CLICK = 2
        RIGHT_CLICK = 3

    t: EventType
    data: any


class MinesweeperGame:
    src_dir = os.path.dirname(os.path.realpath(__file__))
    bg_color = (192, 192, 192)
    grid_color = (128, 128, 128)

    # Size of grid (WARNING: make sure to change the images dimension as well)
    grid_size = 32
    border = 16  # Top border
    top_border = 100  # Left, Right, Bottom border

    timer = pygame.time.Clock()  # Create timer
    pygame.display.set_caption("Minesweeper")  # S Set the caption of window

    # Import files
    spr_flag = pygame.image.load(f"{src_dir}/Sprites/flag.png")
    spr_grid = pygame.image.load(f"{src_dir}/Sprites/Grid.png")

    spr_grids = (
        pygame.image.load(f"{src_dir}/Sprites/empty.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid1.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid2.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid3.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid4.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid5.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid6.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid7.png"),
        pygame.image.load(f"{src_dir}/Sprites/grid8.png"),
    )
    spr_mine = pygame.image.load(f"{src_dir}/Sprites/mine.png")
    spr_mineClicked = pygame.image.load(f"{src_dir}/Sprites/mineClicked.png")
    spr_mineFalse = pygame.image.load(f"{src_dir}/Sprites/mineFalse.png")

    def __init__(self, game_width=10, game_height=10, num_mine=9):
        logger.info(f"Init game with {game_width=}, {game_height=}, {num_mine=}")
        self.game_width = game_width
        self.game_height = game_height
        self.num_mine = num_mine
        self.display_width = self.grid_size * game_width + self.border * 2
        self.display_height = self.grid_size * game_height + self.border + self.top_border
        self.display = pygame.display.set_mode((self.display_width, self.display_height))

        self.grid = None
        self.mines = None
        self.game_state = "None"
        self.mine_left = self.num_mine

    def draw_text(self, txt, s, yOff=0):
        screen_text = pygame.font.SysFont("Calibri", s, True).render(txt, True, (0, 0, 0))
        rect = screen_text.get_rect()
        rect.center = (
            self.game_width * self.grid_size / 2 + self.border,
            self.game_height * self.grid_size / 2 + self.top_border + yOff,
        )
        self.display.blit(screen_text, rect)

    def start_game(self):
        self.game_state = "Playing"
        self.mine_left = self.num_mine

        # Generating mines
        self.mines = set()
        while len(self.mines) < self.num_mine:
            pos = random.randrange(0, self.game_width), random.randrange(0, self.game_height)
            self.mines.add(pos)

        self.grid = [
            [Grid(i, j, -1 if (i, j) in self.mines else 0, self) for i in range(self.game_width)]
            for j in range(self.game_height)
        ]

        # Update of the grid
        for row in self.grid:
            for g in row:
                g.updateValue()

    def get_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                yield GameEvent(GameEvent.EventType.EXIT, None)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                yield GameEvent(GameEvent.EventType.RESTART, None)
            elif event.type == pygame.MOUSEBUTTONUP:
                for i, row in enumerate(self.grid):
                    for j, g in enumerate(row):
                        if g.rect.collidepoint(event.pos):
                            yield GameEvent(
                                GameEvent.EventType.CLICK if event.button == 1 else GameEvent.EventType.RIGHT_CLICK,
                                (i, j),
                            )
                            break

    def main_loop(self):
        t = 0  # Set time to 0
        # Main Loop
        while self.game_state != "Exit":
            for event in self.get_event():
                logger.info(f"{event=}")

                if event.t == GameEvent.EventType.EXIT:
                    self.game_state = "Exit"

                elif event.t == GameEvent.EventType.RESTART:
                    self.start_game()
                    self.main_loop()

                elif event.t == GameEvent.EventType.CLICK:
                    g = self.grid[event.data[0]][event.data[1]]
                    # If player left clicked of the grid
                    g.revealGrid()
                    # Toggle flag off
                    if g.flag:
                        self.mine_left += 1
                        g.flag = False
                    # If it's a mine
                    if g.val == -1:
                        self.game_state = "Game Over"
                        g.mineClicked = True
                else:
                    j = self.grid[event.data[0]][event.data[1]]
                    if not j.clicked:
                        if j.flag:
                            j.flag = False
                            self.mine_left += 1
                        else:
                            j.flag = True
                            self.mine_left -= 1

            # Reset screen
            self.display.fill(self.bg_color)

            # Check if won
            w = True
            for i in self.grid:
                for j in i:
                    j.drawGrid()
                    if j.val != -1 and not j.clicked:
                        w = False
            if w and self.game_state != "Exit":
                self.game_state = "Win"

            # Draw Texts
            if self.game_state != "Game Over" and self.game_state != "Win":
                t += 1
            elif self.game_state == "Game Over":
                self.draw_text("Game Over!", 50)
                self.draw_text("R to restart", 35, 50)
                for i in self.grid:
                    for j in i:
                        if j.flag and j.val != -1:
                            j.mineFalse = True
            else:
                self.draw_text("You WON!", 50)
                self.draw_text("R to restart", 35, 50)
            # Draw time
            s = str(t // 15)
            screen_text = pygame.font.SysFont("Calibri", 50).render(s, True, (0, 0, 0))
            self.display.blit(screen_text, (self.border, self.border))
            # Draw mine left
            screen_text = pygame.font.SysFont("Calibri", 50).render(self.mine_left.__str__(), True, (0, 0, 0))
            self.display.blit(screen_text, (self.display_width - self.border - 50, self.border))

            pygame.display.update()  # Update screen

            self.timer.tick(15)  # Tick fps
        pygame.quit()
