import qlearningAgents
from New_Anthill import *
from Util import *
import math
from defaults import *


class MovementState:
    def __init__(self, ant: Ant, day_info, grid: Grid):
        self.ant = ant
        self.day_info = day_info
        self.grid = grid

    def getLegalActions(self):
        return_val = []
        for move in movements:
            if self.is_move_legal(move):
                return_val.append(move)
        return return_val

    def is_move_legal(self, move: Movement):
        x, y = move.coordinate_move(self.ant.location)
        if x < 0 or y < 0 or x >= self.grid.grid_size or y >= \
                self.grid.grid_size:
            return False
        return True


SCALE_FACTOR = 10000.0


class MovementFeatExtractor:
    def __init__(self):
        pass

    def getFeatures(self, state: MovementState, action: Movement):
        """
        A function we will probably want to change as our features change.
        :param state: a State object holding all the info given the the
        movement func.
        :param action: does nothing as of now.
        :return: a list of features in the current state.
        """
        features = Counter()
        scents = state.grid.get_scent_values_for_direction(
            state.ant.location, action)

        features['scent food'] = scents[ScentType.FOOD_THIS_WAY.value] * 5
        if features['scent food'] < 1:
            features['is out'] = int(self.is_out(state.ant.location, action, state.grid))

            if features['is out']:
                features['scent walked here'] = (1 - scents[ScentType.IM_WALKIN_HERE.value])

        features.divideAll(SCALE_FACTOR)
        return features

    def is_out(self, coordinate, movement: Movement, grid: Grid):
        hill_x, hill_y = grid.anthill
        x, y = coordinate
        if movement == Movement.Up:
            return y < hill_y
        elif movement == Movement.Down:
            return y > hill_y
        elif movement == Movement.Left:
            return x < hill_x
        elif movement == Movement.Right:
            return x > hill_x
        # print("Error! movement nothing!")
        return False

    def get_dist_from_anthill(self, state: MovementState):
        dist = abs(state.grid.anthill[0] - state.ant.location[0])
        dist += abs(state.grid.anthill[1] - state.ant.location[1])
        return dist


class MovementPolicy:

    def __init__(self, years_learning=10, years_running=1, days_in_year=DAYS_PER_YEAR,
                 steps_per_day=STEPS_PER_DAY, const_ant_num=DEFAULT_NUM_ANTS,
                 queen_policy=default_queen_policy,
                 food_dist=default_food_dist, food_change_prob=0.5):
        movement_feat_extractor = MovementFeatExtractor()
        self.agent = qlearningAgents.ApproximateQAgent(extractor=movement_feat_extractor,
                                                       numTraining=years_learning)
        self.game = GameRunner(days_in_year=days_in_year,
                               steps_per_day=steps_per_day,
                               movement_policy=self.get_movement_policy(),
                               init_ants_num=const_ant_num,
                               queen_policy=queen_policy,
                               food_dist=food_dist, food_change_prob=food_change_prob)
        self.food_training = []
        self.years_learning = years_learning
        self.years_running = years_running
        self.learning = True
        self.game_done = False

    def do_learning(self):
        self.learning = True
        return_val = 0
        for i in range(0, self.years_learning):
            return_val = self.game.do_year()
        # # print("weights are ", self.agent.weights)
        return return_val

    def do_running(self):
        self.learning = False
        self.game_done = False
        delta = self.game.do_years(self.years_running)
        # self.game.do_years(self.years_running)
        return delta

    def get_movement_policy(self):
        def movement_policy(ant, day_info, grid):
            state = MovementState(ant, day_info, grid)
            next_movement: Movement = self.agent.getAction(state)
            next_coordinate = next_movement.coordinate_move(ant.location)
            next_state = MovementState(ant, day_info, grid)
            reward = grid.food_at_location(next_coordinate)
            if self.learning:
                self.agent.update(state, next_movement, next_state, reward)

            return next_movement

        return movement_policy

    def get_queen_policy_for_movement(self, num: int):
        def queen_policy(food_gathered, food_delta, num_of_ants, day_info):
            return num

        return queen_policy


    def set_learning(self, value: bool):
        self.learning = value


class QueenState:
    def __init__(self, food_gathered, food_delta, num_of_ants, day_info):
        self.food_gathered = food_gathered
        self.food_delta = food_delta
        self.num_of_ants = num_of_ants
        self.day_info = day_info

    def __eq__(self, other):
        return self.num_of_ants == other.num_of_ants

    def __hash__(self):
        return self.num_of_ants

    def __repr__(self):
        return "ant num " + str(self.num_of_ants)

    def getLegalActions(self):
        if self.num_of_ants not in queen_actions:
            # print("Error! ", self.num_of_ants, " not in queen actions")
            return [0]
        i = int(self.num_of_ants / 100)
        return_val = []
        for i in range(max(0, i-2), min(len(queen_actions), i+3)):
            return_val.append(queen_actions[i])
        return return_val


class QueenFeatExtractor:
    def __init__(self, init_ant_num=100):
        self.init_ant_num = init_ant_num
        self.old_state = QueenState(0, 0, 0, DayInfo())

    def getFeatures(self, state: QueenState, action):
        """
        A function we will probably want to change as our features change.
        :param state: a State object holding all the info given the the
        movement func.
        :param action: does nothing as of now.
        :return: a list of features in the current state.
        """
        features = dict()
        features["delta_ants"] = state.num_of_ants - self.init_ant_num
        # features['food gathered'] = state.food_gathered
        # features['food delta'] = state.food_delta
        # features['num of ants'] = state.num_of_ants

        # features['food gathered'] = math.log10(state.food_gathered + 1)
        #
        # if(state.food_delta <= 0):
        #     food_delta_feat = -math.log10(-state.food_delta + 1)
        # else:
        #     food_delta_feat = math.log10(state.food_delta + 1)
        # features['food delta'] = food_delta_feat
        # features['num of ants'] = math.log10(state.num_of_ants + 1)
        # # # print(features)
        return features


class QueenPolicy:

    def __init__(self, years_learning=10, years_running=3, days_in_year=DAYS_PER_YEAR,
                 steps_per_day=STEPS_PER_DAY, start_ant_num=DEFAULT_NUM_ANTS):
        self.queen_extractor = QueenFeatExtractor()
        # self.agent = qlearningAgents.ApproximateQAgent(
        #     extractor=self.queen_extractor, numTraining=years_training)
        self.ant_num = start_ant_num
        self.food_training = []
        self.years_learning = years_learning
        self.years_running = years_running
        self.learning = True

        self.agent = qlearningAgents.QLearningAgent()
        self.game = GameRunner(days_in_year=days_in_year,
                               steps_per_day=steps_per_day,
                               queen_policy=self.get_queen_policy(),
                               init_ants_num=start_ant_num)
        self._to_print = False

    def do_learning(self):
        self.learning = True
        self.food_training = []
        for i in range(0, self.years_learning):
            self.food_training.append(self.game.do_year())
        # print("-----------------done learning!----------------------")
        # print(self.agent.get_q_values())

    def do_running(self):
        self.learning = False
        self.game.do_years(self.years_running)

    def get_queen_policy(self):
        # We keep the prev action and state, because we will only get their
        # reward in the next time we call the function. so that's where we
        # update their qvalue.
        state = QueenState(0, 0, 0, DayInfo())
        # action: PERCENTS = PERCENTS.NONE
        action = self.ant_num

        def queen_policy(food_gathered, food_delta, num_of_ants, day_info):
            nonlocal state, action
            next_state = QueenState(food_gathered, food_delta, num_of_ants,
                               day_info)
            # reward of the previous state and action, naturally.
            reward = next_state.food_delta
            # if self._to_print:
                # print("Num ants at start was ", num_of_ants)
                # print("reward was ", reward)
                # print("features are ", self.queen_extractor.getFeatures(state, action))
            # self.agent.final(state)
            if self.learning and state:
                self.agent.update(state, action, next_state, reward)
            state = next_state
            if self.learning:
                action = self.agent.getAction(state)
            else:
                action = self.agent.getPolicy(state)
            # if self._to_print:
                # print("policy from here ", action)
                # print("----------------------")

            return action

        return queen_policy

    def set_learning(self, value: bool):
        self.learning = value

    def set_printing(self, value: bool):
        self._to_print = value


class RunTogetherPolicy:

    def __init__(self, years_learning=10, years_running=1, days_in_year=DAYS_PER_YEAR,
                 steps_per_day=STEPS_PER_DAY, start_ant_num=100,
                 food_dist=default_food_dist, food_change_prob=0.5):
        self.ant_num = start_ant_num
        self.food_training = []
        self.years_learning = years_learning
        self.years_running = years_running
        self.learning = True

        self.queen_policy = QueenPolicy(years_learning, years_running,
                                        days_in_year, steps_per_day,
                                        start_ant_num)

        self.movement_policy = MovementPolicy(years_learning, years_running,
                                              days_in_year, steps_per_day)

        self.game = GameRunner(days_in_year=days_in_year,
                               steps_per_day=steps_per_day,
                               queen_policy=self.queen_policy.get_queen_policy(),
                               movement_policy=self.movement_policy.get_movement_policy(),
                               init_ants_num=start_ant_num,
                               food_dist=food_dist,
                               food_change_prob=food_change_prob)

    def do_learning(self):
        self.set_learnings(True)
        self.food_training = []
        delta = 0
        for i in range(0, self.years_learning):
            delta = self.food_training.append(self.game.do_year())
        # # print("-----------------done learning!----------------------")
        return delta

    def do_running(self):
        self.set_learnings(False)
        delta = self.game.do_years(self.years_running)
        return delta

    def set_learnings(self, value: bool):
        self.queen_policy.set_learning(value)
        self.movement_policy.set_learning(value)


class RunIndependentlyPolicy:

    def __init__(self, years_learning=10, years_running=1, days_in_year=DAYS_PER_YEAR,
                 steps_per_day=STEPS_PER_DAY, start_ant_num=100,
                 food_dist=default_food_dist, food_change_prob=0.5):
        self.ant_num = start_ant_num
        self.food_training = []
        self.years_learning = years_learning
        self.years_running = years_running
        self.learning = True

        self.queen_policy = QueenPolicy(years_learning, years_running,
                                        days_in_year, steps_per_day,
                                        start_ant_num)

        self.movement_policy = MovementPolicy(years_learning, years_running,
                                              days_in_year, steps_per_day)

        self.game = GameRunner(days_in_year=days_in_year,
                               steps_per_day=steps_per_day,
                               queen_policy=self.queen_policy.get_queen_policy(),
                               movement_policy=self.movement_policy.get_movement_policy(),
                               init_ants_num=start_ant_num,
                               food_dist=food_dist, food_change_prob=food_change_prob)

    def do_learning(self):
        learning_episodes = int((self.years_learning + 1) / 2)
        for i in range(0, learning_episodes):
            self.do_learning_episode()
        # print("-----------------done learning!----------------------")

    def do_learning_episode(self):
        self.set_opposite_learnings(True)
        delta_1 = self.game.do_year()
        self.set_opposite_learnings(False)
        delta_2 = self.game.do_year()
        return delta_1, delta_2

    def do_running(self):
        self.set_learnings(False)
        delta = self.game.do_years(self.years_running)
        return delta

    def set_learnings(self, value: bool):
        self.queen_policy.set_learning(value)
        self.movement_policy.set_learning(value)

    def set_opposite_learnings(self, value: bool):
        self.queen_policy.set_learning(value)
        self.movement_policy.set_learning(not value)

