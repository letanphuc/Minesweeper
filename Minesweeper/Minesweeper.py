import pygame
import random
import os
from loguru import logger
from enum import Enum
from dataclasses import dataclass


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
        RESIZE = 4,
        HIGHSCORES = 5

    t: EventType
    data: any


class MinesweeperGame:
    bg_color = (192, 192, 192)

    text_font = r'Calibri'
    font_size_large = 30
    font_size_small = 20

    grid_size = 32
    border = 16
    top_border = 100
    bottom_border = border + 2*font_size_small

    FPS = 20

    time_start = time_current = 0
    return_argument = None

    def __init__(self, game_width=10, game_height=10, num_mine=9, highscores=None):
        self.highscores = highscores
        logger.info(f"Init game with {game_width=}, {game_height=}, {num_mine=}")
        self.game_width = game_width
        self.game_height = game_height
        self.num_mine = num_mine

        pygame.init()
        self.timer = pygame.time.Clock()
        pygame.display.set_caption("Minesweeper")

        self.display_width = self.grid_size * game_width + self.border * 2
        self.display_height = self.grid_size * game_height + self.bottom_border + self.top_border
        self.display = pygame.display.set_mode((self.display_width, self.display_height))

        self.mine_left = self.mines = self.game_state = self.grid = None

        src_dir = os.path.dirname(os.path.realpath(__file__))
        # source: https://www.cleanpng.com/png-minesweeper-pro-classic-mine-sweeper-minesweeper-p-662259/
        pygame.display.set_icon(pygame.image.load(f"{src_dir}/Sprites/minesweeper_256.png"))  # change game icon

        self.spr_flag = pygame.image.load(f"{src_dir}/Sprites/flag.png")
        self.spr_grid = pygame.image.load(f"{src_dir}/Sprites/Grid.png")
        self.spr_mine = pygame.image.load(f"{src_dir}/Sprites/mine.png")
        self.spr_mine_clicked = pygame.image.load(f"{src_dir}/Sprites/mineClicked.png")
        self.spr_mine_false = pygame.image.load(f"{src_dir}/Sprites/mineFalse.png")
        self.spr_game_won = pygame.image.load(f"{src_dir}/Sprites/gamewon.png")  # https://www.cleanpng.com/png-microsoft-minesweeper-video-game-quantum-minesweep-3302023/
        self.spr_game_lost = pygame.image.load(f"{src_dir}/Sprites/gamelost.png")  # https://www.cleanpng.com/png-computer-icons-minesweeper-3374745/
        self.spr_rank = pygame.image.load(f"{src_dir}/Sprites/rank.png")  # https://de.cleanpng.com/png-5ejl5o/
        self.spr_grids = (
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

        self.text_font_large = pygame.font.SysFont(self.text_font, self.font_size_large, True)
        self.text_font_small = pygame.font.SysFont(self.text_font, self.font_size_small, True)
        self.segment_font = pygame.font.Font(f"{src_dir}/Fonts/DSEG7Classic-Bold.ttf", 50)

    def start_game(self):
        self.game_state = "Playing"
        self.mine_left = self.num_mine

        self.mines = set()
        while len(self.mines) < self.num_mine:
            pos = random.randrange(0, self.game_width), random.randrange(0, self.game_height)
            self.mines.add(pos)

        self.grid = [
            [Grid(i, j, -1 if (i, j) in self.mines else 0, self) for i in range(self.game_width)]
            for j in range(self.game_height)
        ]

        empty_cells = []
        for row in self.grid:
            for g in row:
                g.update_value()
                if g.val == 0:
                    empty_cells.append(g)

        # reveal any empty cell
        random.choice(empty_cells).reveal()

    def get_event(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                yield GameEvent(GameEvent.EventType.EXIT, None)
            elif event.type == pygame.KEYDOWN:
                logger.info(f"{event=}")
                if event.key == pygame.K_r:
                    yield GameEvent(GameEvent.EventType.RESTART, None)
                elif event.key == pygame.K_h:
                    yield GameEvent(GameEvent.EventType.HIGHSCORES, None)
                elif event.key == pygame.K_q:
                    yield GameEvent(GameEvent.EventType.EXIT, None)
                elif event.unicode == '-':
                    yield GameEvent(GameEvent.EventType.RESIZE, -1)
                elif event.unicode == '+':
                    yield GameEvent(GameEvent.EventType.RESIZE, 1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, row in enumerate(self.grid):
                    for j, g in enumerate(row):
                        if g.rect.collidepoint(event.pos):
                            t = GameEvent.EventType.CLICK if event.button == 1 else GameEvent.EventType.RIGHT_CLICK
                            yield GameEvent(t, (i, j))
                            break

    def main_loop(self):
        self.time_start = self.time_current = pygame.time.get_ticks()
        while self.game_state not in ("Exit", "Resize", "Highscores"):
            for event in self.get_event():
                logger.info(f"{event=}")

                if event.t == GameEvent.EventType.EXIT:
                    self.game_state = "Exit"

                elif event.t == GameEvent.EventType.RESIZE:
                    self.game_state = "Resize"
                    self.return_argument = event.data

                elif event.t == GameEvent.EventType.RESTART:
                    self.start_game()
                    self.main_loop()

                elif event.t == GameEvent.EventType.HIGHSCORES:
                    self.game_state = "Highscores"

                if self.game_state == "Playing":
                    if event.t == GameEvent.EventType.CLICK:
                        g = self.grid[event.data[0]][event.data[1]]

                        if g.flag:  # left-click flag: unflag
                            self.mine_left += 1
                            g.flag = False
                        else:
                            g.reveal()
                            if g.val == -1:  # Mine exploded
                                self.game_state = "Game Over"
                                g.mine_clicked = True
                                for i in self.grid:  # reveal all false flags
                                    for j in i:
                                        if j.flag and j.val != -1:
                                            j.mine_false = True

                    elif event.t == GameEvent.EventType.RIGHT_CLICK:
                        g = self.grid[event.data[0]][event.data[1]]
                        if not g.clicked:  # toggle flag
                            self.mine_left += 1 if g.flag else -1
                            g.flag = not g.flag

            if self.game_state not in ("Exit", "Resize", "Highscores", "Win"):
                self.process_state()
                self.render()
                self.timer.tick()

            if self.game_state not in ("Game Over", "Win"):
                self.time_current = pygame.time.get_ticks()

        pygame.quit()
        return self.game_state, self.return_argument

    def process_state(self):

        won = True
        for i in self.grid:
            for j in i:
                if j.val != -1 and not j.clicked:
                    won = False
                    break

        if won and self.game_state != "Exit":
            self.game_state = "Win"
            # if entry is in highscore list, return index to highlight
            self.return_argument = self.highscores.add_entry(
                (self.game_width, self.game_height, self.num_mine),
                self.time_current - self.time_start)

    def render(self):

        self.display.fill(self.bg_color)

        for i in self.grid:
            for j in i:
                j.draw()

        s = str((self.time_current - self.time_start) // 1000)  # draw time
        time_rect = self.draw_segment(s, topleft=(self.border, self.border))

        s = str(self.mine_left)  # draw number of mines left
        mines_rect = self.draw_segment(s, topright=(self.display_width - self.border, self.border))

        x = (mines_rect.left + time_rect.right) // 2
        if self.game_state == "Game Over":
            rect = self.spr_game_lost.get_rect(midtop=(x, time_rect.top))
            self.display.blit(self.spr_game_lost, rect)
        elif self.game_state == "Win":
            if self.return_argument is not None:
                rect = self.spr_rank.get_rect(midtop=(x, time_rect.top))
                self.display.blit(self.spr_rank, rect)
                text_surface = self.text_font_large.render(str(self.return_argument + 1), True, "gold2")
                text_rect = text_surface.get_rect(center=rect.center)
                self.display.blit(text_surface, text_rect)
            else:
                rect = self.spr_game_won.get_rect(midtop=(x, time_rect.top))
                self.display.blit(self.spr_game_won, rect)

        # bottom key hints
        texts = ["R Restart, H Highscores",
                 "-/+ Resize, Q Quit"]
        x = self.border + self.grid_size * self.game_width / 2
        y_off = self.top_border + self.grid_size * self.game_height + self.border/2
        for txt in texts:
            text_surface = self.text_font_small.render(txt, True, (0, 0, 0))
            rect = text_surface.get_rect(midtop=(x, y_off))
            self.display.blit(text_surface, rect)
            y_off += rect.height

        pygame.display.update()

    def draw_segment(self, txt, **pos):
        text_surface = self.segment_font.render(txt, True, (255, 0, 0))
        text_rect = text_surface.get_rect(**pos)
        bg_rect = text_rect.inflate(0, 8)
        self.display.fill((0, 0, 0), bg_rect)
        self.display.blit(text_surface, text_rect)
        return bg_rect
