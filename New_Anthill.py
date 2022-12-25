"""
This Page Includes All the different Ant Constructs
"""
import enum
import random
import threading
import time

import numpy
from Util import *
import math
import tkinter as tk
from defaults import *


class Ant:
    """
    An ant object represents 100 ants - this is done for efficiency purposes,
    as ant colonies can have well over 100,000 ants in them,
    though they will amost always be in large groups (never travel alone).
    """
    def __init__(self, location, age=0):
        self.location = location
        self.age = age
        self.food = 0
        self.is_dead = False
        self.cur_scent = ScentType.IM_WALKIN_HERE
        self.cur_direction = Movement.Nothing


class DayInfo:
    """
    a data structure to hold all information on day for various funcs.
    """
    def __init__(self, day=0, days_in_year=100, steps_per_day=100):
        self.day = day
        self.days_in_year = days_in_year
        self. steps_per_day = steps_per_day

    def new_day(self):
        self.day += 1

    def do_step(self):
        return self.day

# --------------------- big classes ------------------------------------


class Grid:
    def __init__(self, food_dist_func, day_info: DayInfo,
                 grid_size=GRID_SIZE, scent_multiplier=0.95,
                 food_change_func=None, food_change_prob=0.5):
        self.grid_size = grid_size
        self.food_dist_func = food_dist_func
        self.food_change_func = food_change_func
        self.food_change_prob = food_change_prob
        self.food_land = numpy.zeros([self.grid_size, self.grid_size])
        self.food_collected = 0
        self.anthill = (int(self.grid_size / 2), int(self.grid_size / 2))
        # for each direction hold scent value
        self.scent_value = numpy.zeros([self.grid_size, self.grid_size, len(ScentType)])
        self.scent_direction = ([[[Movement.Nothing for i in range(len(ScentType))]
                                for j in range(self.grid_size)] for k in range(self.grid_size)])
        self.output_ant_grid = numpy.zeros([self.grid_size, self.grid_size])
        self.scent_multiplier = scent_multiplier
        self.day_info = day_info
        self.scent_trail_update_counter = 0

    def create_land(self):
        for i in range(0, self.grid_size):
            for j in range(0, self.grid_size):
                self.food_land[i, j] = self.food_dist_func()

    def get_anthill_location(self):
        return self.anthill

    def food_at_location(self, coordinate):
        x, y = coordinate
        if self.is_in_bounds(coordinate):
            return self.food_land[x][y]
        return 0

    def is_in_bounds(self, coordinate):
        is_smaller = coordinate[0] < self.grid_size and coordinate[1] < self.grid_size
        return is_smaller and coordinate[0] >= 0 and coordinate[1] >= 0

    def food_pickup(self, coordinate, amount=1):
        x, y = coordinate
        if self.food_land[x][y] >= amount:
            self.food_land[x][y] -= amount
            return amount
        else:
            remainder = self.food_land[x][y]
            self.food_land[x][y] = 0
            return remainder

    """returns scent array for a specific coordinate"""
    def get_scent_values(self, coordinate):
        return self.scent_value[coordinate[0]][coordinate[1]]

    def get_scent_value_for_type(self, coordinate, scent_type: ScentType):
        return_val = self.scent_value[coordinate[0]][coordinate[1]][scent_type.value]
        return return_val

    def get_scent_values_for_direction(self, coordinate, movement: Movement):
        return_val = [0, 0]
        for scent in ScentType:
            if self.get_scent_direction_for_type(coordinate, scent) == movement:
                return_val[scent.value] = \
                    self.get_scent_value_for_type(coordinate, scent)
        return return_val

    def get_scent_directions(self, coordinate):
        return self.scent_direction[coordinate[0]][coordinate[1]]

    def get_scent_direction_for_type(self, coordinate, scent_type: ScentType):
        return self.scent_direction[coordinate[0]][coordinate[1]][scent_type.value]

    def add_scent(self, ant):
        self.scent_value[ant.location[0]][ant.location[1]][ant.cur_scent.value] = ANT_SCENT_VALUE
        direction = ant.cur_direction
        if ant.cur_scent == ScentType.FOOD_THIS_WAY:
            direction = direction.get_opposite_move()
        self.scent_direction[ant.location[0]][ant.location[1]][ant.cur_scent.value] = direction

    def update_scent_trails(self):
        if self.scent_trail_update_counter < SCENT_HALFLIFE_STEPS:
            self.scent_trail_update_counter += 1
            return

        self.scent_trail_update_counter = 0
        self.scent_value *= 0.5

    def end_day(self):
        """
        changes the grid to represent end of day.
        so far
        - changes the food landscape based on food_change_func
        - adjust smell trail
        :return: None
        """
        for i in range(0, self.grid_size):
            for j in range(0, self.grid_size):
                self.food_land[i, j] = self.food_change_func(self.food_land[i, j], self.food_change_prob, (i, j),
                                                             self.day_info)
        self.scent_value *= 0


class Ants:
    def __init__(self, grid: Grid, day_params: DayInfo, death_func,
                 movement_policy, ants_num=DEFAULT_NUM_ANTS, ant_capacity=1):
        self.season = Seasons.SPRING
        self.day_info = day_params
        # Each ant will include (location, food_amount, steps_list)
        self.grid = grid
        self.ants = numpy.array([], dtype=object)
        self.add_active_workers(ants_num)
        self.death_func = death_func
        self.movement_policy = movement_policy
        self.ant_capacity = ant_capacity
        self.food_collected = 0

    def add_active_workers(self, ant_num):
        for i in range(0, ant_num):
            ant = Ant(self.grid.get_anthill_location())
            self.ants = numpy.append(self.ants, ant)

    def end_of_day(self, new_ant_num):
        """
        does end of day ant stuff
        :param new_ant_num: new ants to add
        :return: food gathered today, food intake today.
        """
        self.end_of_day_deaths()
        self.return_ants_to_anthill()
        self.add_active_workers(new_ant_num)
        # # print(f"food collected today: ", self.food_collected)
        self.food_collected = 0

        return self.ants

    def food_info_today(self):
        """
        :return: food gathered today, food eaten today
        """
        return self.food_collected,  len(self.ants) * ANT_FOOD_PER_DAY

    def return_ants_to_anthill(self):
        for ant in self.ants:
            self.collect_food(ant)
            ant.location = self.grid.get_anthill_location()
            ant.cur_direction = Movement.Nothing

    def end_of_day_deaths(self):
        dead_ants = list()
        for index in range(self.ants.size):
            ant = self.ants[index]
            ant.age += 1

            if ant.is_dead or ant.age > ANT_MAX_AGE_DAYS:
                dead_ants.append(index)
        numpy.delete(self.ants, dead_ants)

    def should_die(self, ant: Ant):
        return self.death_func(ant, self.day_info)

    """
    Note that it is up to the POLICY to prevent ant from going out of bound.
    This means it must prevent the ant from going more than 75 spaces from the anthill (grid center)
    """
    def explore(self, ant: Ant):
        ant.cur_direction = self.movement_policy(ant, self.day_info, self.grid)
        new_location = ant.cur_direction.coordinate_move(ant.location)

        ant.location = new_location

    def do_step(self):
        for ant in self.ants:
            # if self.movement_policy(ant, self.grid):
            did_ex = False
            if ant.is_dead:
                continue

            if self.should_die(ant):
                ant.is_dead = True
                continue

            if ant.food == 0:
                did_ex = True
                self.explore(ant)
                if self.grid.food_at_location(ant.location):
                    ant.food = self.grid.food_pickup(ant.location, self.ant_capacity)
                    ant.cur_scent = ScentType.FOOD_THIS_WAY
            else:
                ant.cur_direction = self.send_home(ant)
                ant.location = ant.cur_direction.coordinate_move(ant.location)

                if ant.location == self.grid.get_anthill_location():
                    self.collect_food(ant)

            self.grid.add_scent(ant)

        self.grid.update_scent_trails()

    def send_home(self, ant: Ant):
        location = ant.location
        home = self.grid.anthill

        if location[1] > home[1]:
            return Movement.Up
        if location[1] < home[1]:
            return Movement.Down
        if location[0] > home[0]:
            return Movement.Left
        if location[0] < home[0]:
            return Movement.Right

        return Movement.Nothing

    def collect_food(self, ant):
        self.food_collected += ant.food
        ant.food = 0
        ant.cur_scent = ScentType.IM_WALKIN_HERE

    def get_ants_num(self):
        return self.ants.size


class GameRunner:
    def __init__(self, days_in_year=DAYS_PER_YEAR, steps_per_day=STEPS_PER_DAY,
                 queen_policy=default_queen_policy,
                 movement_policy=default_movement_policy,
                 food_dist=default_food_dist, grid_size=GRID_SIZE,
                 scent_thingy=0.95, food_change_func=default_food_change,
                 death_func=default_death_func, init_ants_num=DEFAULT_NUM_ANTS, ant_capacity=1,
                 gui_updater=None, food_change_prob=0.5):
        self.queen_policy = queen_policy
        self.movement_policy = movement_policy
        self.food_dist = food_dist
        self.grid_size = grid_size
        self.scent_thingy = scent_thingy
        self.death_func = death_func
        self.init_ants_num = init_ants_num
        self.ant_capacity = ant_capacity
        self.food_change_func = food_change_func

        self.day_info = DayInfo(days_in_year=days_in_year, steps_per_day=steps_per_day)
        self.grid = Grid(food_dist, self.day_info, grid_size, scent_thingy, food_change_func, food_change_prob)
        self.ants = Ants(self.grid, self.day_info, death_func,
                         movement_policy, self.init_ants_num,
                         self.ant_capacity)
        self.death_func = death_func
        self.movement_policy = movement_policy
        self.food_gathered = 0
        self.food_delta = 0
        self.food_gathered_today = 0
        self.prev_ant_num = 0
        self.gui_updater = gui_updater

    def do_day(self, end_of_year, day_num=0):
        total_ant_num = self.queen_policy(self.food_gathered, self.food_delta,
                                          self.prev_ant_num,
                                          self.day_info)
        # new_ants_num = max(total_ant_num - self.ants.get_ants_num(), 0)
        # self.food_gathered -= new_ants_num * NEW_ANT_COST
        self.ants = Ants(self.grid, self.day_info, self.death_func,
                         self.movement_policy, total_ant_num,
                         self.ant_capacity)
        # for updating num ants
        if self.gui_updater:
            self.gui_updater(self.grid, self.ants, False, 0)

        for i in range(0, self.day_info.steps_per_day):
            self.ants.do_step()
            self.day_info.do_step()

            # this code controls when we see output of grid
            if self.gui_updater and end_of_year:
                self.gui_updater(self.grid, self.ants, end_of_year)

        # for updating progress bar
        if self.gui_updater:
            self.gui_updater(self.grid, self.ants)

        # end day:
        self.grid.end_day()
        food_collected, food_consumed = self.ants.food_info_today()
        self.food_delta = food_collected - food_consumed
        self.food_gathered += self.food_delta
        self.prev_ant_num = self.ants.get_ants_num()
        self.day_info.new_day()
        # # print("Day: ", day_num, "Food: ", food_collected, "Delta: ",
        #       self.food_delta)
        return self.food_delta

    def do_year(self, year=1):
        self.grid.create_land()  # every year we start with fresh grid (all new food - no build up)
        food = 0
        self.delta_each_day = [0] * self.day_info.days_in_year
        for i in range(0, self.day_info.days_in_year-1):
            # food +=
            self.delta_each_day[i] = self.do_day(False, i)

        self.delta_each_day[-1] = self.do_day(True)
        # food += self.do_day(True)
        # # print("Food gathered in year ", year, ": ", food)
        return self.delta_each_day

    def do_years(self, num_of_years):
        self.food_gathered = 0
        for i in range(0, num_of_years):
            self.do_year(i+1)
        # print("Food gathered over ", num_of_years, "years: Total = ", self.food_gathered,
        #       ", Average = ", int(self.food_gathered / num_of_years))

        return self.food_gathered


