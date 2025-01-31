import pygame
import random
import os
from loguru import logger
from enum import Enum
from dataclasses import dataclass

pygame.init()


class Grid:
    def __init__(self, x_grid, y_grid, grid_type, game):
        self.x = x_grid
        self.y = y_grid
        self.clicked = False
        self.mine_clicked = False
        self.mine_false = False
        self.flag = False

        self.rect = pygame.Rect(
            game.border + self.x * game.grid_size,
            game.top_border + self.y * game.grid_size,
            game.grid_size,
            game.grid_size,
        )
        self.val = grid_type
        self.game = game

    def draw(self):

        if self.mine_false:
            self.game.display.blit(self.game.spr_mine_false, self.rect)
        elif self.clicked:
            if self.val == -1:
                if self.mine_clicked:
                    self.game.display.blit(self.game.spr_mine_clicked, self.rect)
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

    def reveal(self):
        self.clicked = True

        if self.val == 0:
            for x in range(-1, 2):
                if 0 <= self.x + x < self.game.game_width:
                    for y in range(-1, 2):
                        if 0 <= self.y + y < self.game.game_height:
                            if not self.game.grid[self.y + y][self.x + x].clicked:
                                self.game.grid[self.y + y][self.x + x].reveal()
        elif self.val == -1:

            for m in self.game.mines:
                if not self.game.grid[m[1]][m[0]].clicked:
                    self.game.grid[m[1]][m[0]].reveal()

    def update_value(self):

        if self.val != -1:
            for x in range(-1, 2):
                if 0 <= self.x + x < self.game.game_width:
                    for y in range(-1, 2):
                        if 0 <= self.y + y < self.game.game_height:
                            if self.game.grid[self.y + y][self.x + x].val == -1:
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

    grid_size = 32
    border = 16
    top_border = 100

    timer = pygame.time.Clock()
    pygame.display.set_caption("Minesweeper")

    spr_flag = pygame.image.load(f"{src_dir}/Sprites/flag.png")
    spr_grid = pygame.image.load(f"{src_dir}/Sprites/Grid.png")
    text_font = r'Calibri'

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
    spr_mine_clicked = pygame.image.load(f"{src_dir}/Sprites/mineClicked.png")
    spr_mine_false = pygame.image.load(f"{src_dir}/Sprites/mineFalse.png")

    def __init__(self, game_width=10, game_height=10, num_mine=9):
        logger.info(f"Init game with {game_width=}, {game_height=}, {num_mine=}")
        self.game_width = game_width
        self.game_height = game_height
        self.num_mine = num_mine
        self.display_width = self.grid_size * game_width + self.border * 2
        self.display_height = self.grid_size * game_height + self.border + self.top_border
        self.display = pygame.display.set_mode((self.display_width, self.display_height))

        self.running_time = self.mine_left = self.mines = self.game_state = self.grid = None

    def draw_text(self, txt, s, y_off=0):
        screen_text = pygame.font.SysFont(self.text_font, s, True).render(txt, True, (0, 0, 0))
        rect = screen_text.get_rect()
        rect.center = (
            self.game_width * self.grid_size / 2 + self.border,
            self.game_height * self.grid_size / 2 + self.top_border + y_off,
        )
        self.display.blit(screen_text, rect)

    def start_game(self):
        self.game_state = "Playing"
        self.mine_left = self.num_mine
        self.running_time = 0

        self.mines = set()
        while len(self.mines) < self.num_mine:
            pos = random.randrange(0, self.game_width), random.randrange(0, self.game_height)
            self.mines.add(pos)

        self.grid = [
            [Grid(i, j, -1 if (i, j) in self.mines else 0, self) for i in range(self.game_width)]
            for j in range(self.game_height)
        ]

        for row in self.grid:
            for g in row:
                g.update_value()

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
                            t = GameEvent.EventType.CLICK if event.button == 1 else GameEvent.EventType.RIGHT_CLICK
                            yield GameEvent(t, (i, j))
                            break

    def main_loop(self):
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

                    g.reveal()

                    if g.flag:
                        self.mine_left += 1
                        g.flag = False

                    if g.val == -1:
                        self.game_state = "Game Over"
                        g.mine_clicked = True
                else:

                    g = self.grid[event.data[0]][event.data[1]]
                    if not g.clicked:
                        self.mine_left += 1 if g.flag else -1
                        g.flag = not g.flag

            self.process_state()
            self.render()
        pygame.quit()

    def process_state(self):

        won = True
        for i in self.grid:
            for j in i:
                if j.val != -1 and not j.clicked:
                    won = False
                    break

        if won and self.game_state != "Exit":
            self.game_state = "Win"

    def render(self):

        self.display.fill(self.bg_color)

        for i in self.grid:
            for j in i:
                j.draw()

        if self.game_state != "Game Over" and self.game_state != "Win":
            self.running_time += 1
        elif self.game_state == "Game Over":
            self.draw_text("Game Over!", 50)
            self.draw_text("R to restart", 35, 50)
            for i in self.grid:
                for j in i:
                    if j.flag and j.val != -1:
                        j.mine_false = True
        else:
            self.draw_text("You WON!", 50)
            self.draw_text("R to restart", 35, 50)

        s = str(self.running_time // 15)
        screen_text = pygame.font.SysFont(self.text_font, 50).render(s, True, (0, 0, 0))
        self.display.blit(screen_text, (self.border, self.border))

        screen_text = pygame.font.SysFont(self.text_font, 50).render(self.mine_left.__str__(), True, (0, 0, 0))
        self.display.blit(screen_text, (self.display_width - self.border - 50, self.border))

        pygame.display.update()

        self.timer.tick(15)
