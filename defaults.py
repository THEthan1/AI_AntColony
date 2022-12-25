import random
from New_Anthill import *
from Util import *

DEFAULT_NUM_ANTS = 300
STEPS_PER_DAY = 500
DAYS_PER_YEAR = 10
ANT_REPRESENTATION_RATIO = 100
NEW_ANT_COST = 10
ANT_FOOD_PER_DAY = 2
SCENT_HALFLIFE_STEPS = 20
ANT_SCENT_VALUE = 1
ANT_MAX_AGE_DAYS = 100
GRID_SIZE = 151


def default_food_dist():
    # note that there are ~10,000 indexes
    # for testing queen policy
    # return_val = random.choices([0, 1, 1000, 10000], weights=(22400, 100,0,0))
    return_val = random.choices([0, 1, 5, 20], weights=(6300, 10, 100, 50))
    return return_val[0]


# part of Elisheva's tests. please don't change.
def elisheva_food_dist():
    return_val = random.choices([0, 1, 5, 20], weights=(6300, 10, 100, 50))
    return return_val[0]


# part of Elisheva's tests. please don't change.
def default_food_change(food, prob, coordinate, day_info: 'DayInfo'):
    if flip_coin(prob):
        return_val = random.choices([0, 1, 10, 100], weights=(6300, 10, 100, 50))
        return food + return_val[0]

    return food


def default_queen_policy(food_gathered, food_delta, num_of_ants, day_info):
    # return 1
    # new_ants_num = (food_gathered - food_delta)/(2 * ANT_COST)
    # return int(max(0, new_ants_num))
    return DEFAULT_NUM_ANTS


# part of Elisheva's tests. please don't change.
# noinspection PyUnusedLocal
def default_movement_policy(ant, day_info, grid):
    coordinate = ant.location
    cur_direction = ant.cur_direction

    return get_random_move(coordinate, grid)


# part of Elisheva's tests. please don't change.
def scent_movement_policy(ant, day_info, grid):
    coordinate = ant.location
    cur_direction = ant.cur_direction

    if coordinate == grid.get_anthill_location() and cur_direction != Movement.Nothing:
        return cur_direction.get_opposite_move()

    walking_value = grid.get_scent_value_for_type(coordinate, ScentType.IM_WALKIN_HERE)
    food_value = grid.get_scent_value_for_type(coordinate, ScentType.FOOD_THIS_WAY)

    if food_value > 0.2:
        return grid.get_scent_direction_for_type(coordinate, ScentType.FOOD_THIS_WAY)
    if walking_value < 0.1:
        return grid.get_scent_direction_for_type(coordinate, ScentType.IM_WALKIN_HERE)

    return get_random_move(coordinate, grid)


def get_random_move(coordinate, grid: 'Grid'):
    movement: Movement = random.choice([movement for movement in movements])
    x, y = movement.coordinate_move(coordinate)
    while x < 0 or y < 0 or x >= grid.grid_size or y >= grid.grid_size:
        movement = random.choice(
            [movement for movement in movements])
        x, y = movement.coordinate_move(coordinate)
    return movement


def default_death_func(ant, coordinate):
    return random.randint(1, 10000) == 1
