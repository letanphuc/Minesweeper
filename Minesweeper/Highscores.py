import bz2
import datetime
import os
import pickle
from datetime import datetime
from tkinter import *
from dataclasses import dataclass


@dataclass(order=True)
class Score:
    msec: int
    timestamp: datetime
    username: str


class Highscores:
    MAX_ENTRIES = 15

    def __init__(self, loadfiles, savefile=None):
        """
        :param loadfiles: list of score files to load
        :type loadfiles: list[str]
        :param savefile: score file to save, default loadfiles[0]
        :type savefile: str
        """
        self.highscores = {}  # dict {level: list[Score]}, level: (width: int, height: int, number_of_mines: int)
        self.loadfiles = loadfiles
        if savefile:
            self.savefile = savefile
        else:
            self.savefile = loadfiles[0]
        self.load()

    def load(self):
        self.highscores = {}
        self.oldstate = None
        try:
            for filename in self.loadfiles:
                with open(filename, 'rb') as f:
                    self.oldstate = f.read()
                myscores = pickle.loads(bz2.decompress(self.oldstate))
                if self.highscores:  # further files: add to level scores
                    for level in myscores:
                        if level not in self.highscores:
                            self.highscores[level] = []
                        self.highscores[level].append(myscores[level])
                    self.oldstate = None  # multiple files: save even if new state is any imported state
                else:  # first file: use data loaded
                    self.highscores = myscores
        except:
            pass  # use empty dict or partially loaded data
        self.sort_and_limit()

    def save(self):
        """save game state if changed"""
        newstate = bz2.compress(pickle.dumps(self.highscores))
        if self.oldstate != newstate:
            with open(self.savefile, 'wb') as f:
                f.write(newstate)
            self.oldstate = newstate

    def sort_and_limit(self):
        """sort and limit entries per level"""
        for level in self.highscores:
            self.highscores[level] = sorted(self.highscores[level])[0:self.MAX_ENTRIES]

    def add_entry(self, level, score):
        """add score to highscore list

        :param level: game level: (width, height, number_of_mines)
        :type level: tuple[int]
        :param score: game time in milliseconds
        :type score: int
        :return index: int  index of added entry, if still in list
        """
        level = tuple(level)
        time = datetime.now().replace(microsecond=0)
        if level not in self.highscores:
            self.highscores[level] = []
        self.highscores[level].append(Score(int(score),
                                            time,
                                            os.getlogin()))
        self.sort_and_limit()
        myindex = None
        for i, entry in enumerate(self.highscores[level]):
            if entry.timestamp == time:
                myindex = i
                self.save()
                break
        return myindex  # return index of added entry, if still in list

    def show(self, level, index=None):
        """Show a window with highscores of given level.
        Highlight entry with index.
        Close by pressing any key.

        :param level: game level: (width, height, number_of_mines)
        :type level: tuple[int]
        :param index: index of entry to highlight
        :type index: int
        """
        level = tuple(level)
        if level in self.highscores:
            win = Tk()
            win.title("Minesweeper")

            src_dir = os.path.dirname(os.path.realpath(__file__))
            # icon source: https://www.cleanpng.com/png-minesweeper-pro-classic-mine-sweeper-minesweeper-p-662259/
            icon = PhotoImage(file=f"{src_dir}/Sprites/minesweeper_256.png")
            win.iconphoto(True, icon)

            Label(text=f"Scores {level[0]}x{level[1]}, {level[2]} Mines", height=2).grid(row=0, columnspan=4)
            Label(text="Rank", width=6, relief=SUNKEN).grid(row=1, column=0)
            Label(text="Time", width=14, relief=SUNKEN).grid(row=1, column=1)
            Label(text="Date", width=20, relief=SUNKEN).grid(row=1, column=2)
            Label(text="Player", width=25, relief=SUNKEN).grid(row=1, column=3)

            for i, entry in enumerate(self.highscores[level]):
                highlight = {"fg": "blue"} if index == i else {}
                minutes, msec = divmod(entry.msec, 60000)
                min_str = f"{minutes} m " if minutes else ""
                Label(text=str(i + 1),
                      width=6, relief=SUNKEN, **highlight).grid(row=i + 2, column=0)
                Label(text=f"{min_str}{msec / 1000:06.3f} s",
                      width=14, relief=SUNKEN, **highlight).grid(row=i + 2, column=1)
                Label(text=entry.timestamp.strftime("%d.%m.%Y, %H:%M:%S"),
                      width=20, relief=SUNKEN, **highlight).grid(row=i + 2, column=2)
                Label(text=entry.username,
                      width=25, relief=SUNKEN, **highlight).grid(row=i + 2, column=3)

            Label(text="Press any key to close", height=2).grid(row=len(self.highscores[level]) + 2, columnspan=4)
            win.bind_all('<Key>', lambda e: win.destroy())
            mainloop()
