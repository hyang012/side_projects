#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Nov 12 12:41:16 2018

@author: Derek
"""
import curses
import numpy as np
from random import randrange, choice
from itertools import chain

class GameField(object):
    """The field on which users play the 2048 game."""
    
    def __init__(self, size):
        self.size = size
        self.cells = None
        self.reset()
        
    def reset(self):
        self.cells = [[0 for _ in range(self.size)] for _ in range(self.size)]
        self.spawn()
        self.spawn()
        
    def _generate_game_field(self):
        """Generate a game field"""
        res = np.zeros((self.height, self.width))
        return res
    
    def spawn(self):
        """Randomly spawn a 4 or a 2 on the game field."""
        new_element = 4 if randrange(100) > 89 else 2
        
        # Randomly choose a zero cell to spawn the new element.
        (i, j) = choice([(i, j) for i in range(self.size) for j in range(self.size) if self.cells[i][j] == 0])
        self.cells[i][j] = new_element
    
    
    def transpose(self):
        self.cells = [list(row) for row in zip(*self.cells)]
    
    def invert(self):
        self.cells = [row[::-1] for row in self.cells]
    
    @staticmethod
    def move_row_left(row):
        def tighten(row):
            # move all non-zero elements together
            new_row = [i for i in row if i != 0]  
            new_row += [0] * (len(row) - len(new_row))
            return new_row
        
        def merge(row):
            # merge neighbor elements
            pair = False
            new_row = []
            for i in range(len(row)):
                if pair:
                    new_row.append(2 * row[i])
                    pair = False
                else:
                    if i + 1 < len(row) and row[i] == row[i + 1]:
                        pair = True
                        new_row.append(0)
                    else:
                        new_row.append(row[i])
            assert len(new_row) == len(row)
            return new_row
        
        # Move all non-zero elements together first, then merge paired elemnts,
        # finally move the non-zero elements in the new row together again.
        return tighten(merge(tighten(row)))
    
    def move_left(self):
        self.cells = [self.move_row_left(row) for row in self.cells]
    
    def move_right(self):
        self.invert()
        self.move_left()
        self.invert()
    
    def move_up(self):
        self.transpose()
        self.move_left()
        self.transpose()
    
    def move_down(self):
        self.transpose()
        self.move_right()
        self.transpose()
    
    @staticmethod
    def row_is_left_movable(row):
        def change(i):
            if row[i] == 0 and row[i+1] != 0:  # Can be moved
                return True
            if row[i] != 0 and row[i+1] == row[i]: # Can be moved
                return True
            return False
        return any(change(i) for i in range(len(row) - 1))
    
    def can_move_left(self):
        return any(self.row_is_left_movable(row) for row in self.cells)
    
    def can_move_right(self):
        self.invert()
        can = self.can_move_left()
        self.invert()
        return can
    
    def can_move_up(self):
        self.transpose()
        can = self.can_move_left()
        self.transpose()
        return can
    
    def can_move_down(self):
        self.transpose()
        can = self.can_move_right()
        self.transpose()
        return can
    

class Screen(object):
    help_string1 = '(W)Up (S)Down (A)Left (D)Right'
    help_string2 = '      (R)Restart  (Q)Exit'
    gameover_string = '             GAME OVER'
    win_string = 'Congratulation, YOU WIN!'

    def __init__(self, screen=None, grid=None, score=0, best_score=0, over=False, win=False):
        self.grid = grid
        self.score = score
        self.over = over
        self.win = win
        self.screen = screen
        self.counter = 0
    
    def cast(self, string):
        self.screen.addstr(string + '\n')
    
    def draw_row(self, row):
        self.cast(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in row) + '|' )
    
    def draw(self):
        self.screen.clear()
        self.cast('SCORE: ' + str(self.score))
        for row in self.grid.cells:
            self.cast('+------' * self.grid.size + '+')
            self.draw_row(row)
        self.cast('+------' * self.grid.size + '+')
        
        if self.win:
            self.cast(self.win_string)
        else:
            if self.over:
                self.cast(self.over_string)
            else:
                self.cast(self.help_string1)
        self.cast(self.help_string2)
          

class Action(object):
    """User actions."""
    UP = 'up'
    LEFT = 'left'
    DOWN = 'down'
    RIGHT = 'right'
    RESTART = 'restart'
    EXIT = 'exit'

    letter_codes = [ord(ch) for ch in 'WASDRQwasdrq']
    actions = [UP, LEFT, DOWN, RIGHT, RESTART, EXIT]
    actions_dict = dict(zip(letter_codes, actions*2))
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
    
    def get(self):
        char = 'N'
        while char not in self.actions_dict:
            char = self.stdscr.getch()
        return self.actions_dict[char]


class Admin(object):
    """Administrator that controls the process of the game."""
    
    def __init__(self, size=4, win_num=2048):
        self.size = size
        self.win_num = win_num
        self.reset()
    
    def reset(self):
        self.state = 'init'
        self.win = False
        self.over = False
        self.score = 0
        self.grid = GameField(self.size)
        self.grid.reset()
    
    @property
    def screen(self):
        return Screen(screen=self.stdscr, score=self.score, grid=self.grid, win=self.win, over=self.over)
    
    def move(self, direction):
        if self.can_move(direction):
            getattr(self.grid, 'move_' + direction)()
            self.grid.spawn()
            return True
        else:
            return False
    
    @property
    def is_win(self):
        self.win = max(chain(*self.grid.cells)) >= self.win_num
        return self.win
    
    @property
    def is_over(self):
        self.over = not any(self.can_move(move) for move in self.action.actions)
    
    def can_move(self, direction):
        return getattr(self.grid, 'can_move_' + direction)()
    
    def state_init(self):
        self.reset()
        return 'game'
    
    def state_game(self):
        self.screen.draw()
        action = self.action.get()
        
        if action == Action.RESTART:
            return 'init'
        if action == Action.EXIT:
            return 'exit'
        if self.move(action):
            if self.is_win:
                return 'win'
            if self.is_over:
                return 'over'
        return 'game'
    
    def _restart_or_exit(self):
        self.screen.draw()
        return 'init' if self.action.get() == Action.RESTART else 'exit'
    
    def state_win(self):
        return self._restart_or_exit()
    
    def state_over(self):
        return self._restart_or_exit()
    
    def __call__(self, stdscr):
        curses.use_default_colors()
        self.stdscr = stdscr
        self.action = Action(stdscr)
        while self.state != 'exit':
            self.state = getattr(self, 'state_' + self.state)()
        
if __name__ == '__main__':
    curses.wrapper(Admin())
    
    