import random

import New_Anthill
import Util
from defaults import *

MUTATION_CHANCE = 0.3

class Policy:
    def value_of_action(self, val_list, action):
        pass
       # # print("Shouldn't get here!!!1")


    def get_legal_actions(self):
        pass
        ## print("Shouldn't get here!!!1")

    def crossover(self, other: "Policy"):
        pass
        # print("Shouldn't get here!!!1")

    def mutate(self):
        pass
        ## print("Shouldn't get here!!!1")


class QueenPolicy(Policy):
    def __init__(self, ant_num):
        self.ant_num = ant_num
        self.actions = {ant_num}

    def __str__(self):
        return "ANT NUMBER IS"+str(self.actions)

    def value_of_action(self, val_list, action):
        return action

    def get_legal_actions(self):
        return self.actions

    def crossover(self, other: 'QueenPolicy'):
        good_num=max(self.ant_num,other.ant_num)
        policy=QueenPolicy(good_num)
        return policy

    def mutate(self):
        if (random.randint(0, 1) / 100) < 0.002:
          rand_anr_num= random.randint(10,100)
          new_ant_num=int((self.ant_num+rand_anr_num)/2)

        else:
            new_ant_num=self.ant_num
        return QueenPolicy(new_ant_num)


class MovementPolicy(Policy):
    def __init__(self, dir_weight, scent_weight, walked_weight):

        self.dir_weight = dir_weight
        self.scent_weight = scent_weight
        self.walked_weight = walked_weight
        self.actions = Util.movements #should not just one action for the one indisvual util.movement change to movement

    def __str__(self):
        return "SCENT IS:"+str(self.scent_weight)+"THE DIRECTION IS"+str(self.dir_weight)

    def is_move_legal(self, move: Util.Movement,ant:New_Anthill.Ant,grid:New_Anthill.Grid):
        x, y = move.coordinate_move(ant.location)
        if x < 0 or y < 0 or x >= grid.grid_size or y >= grid.grid_size:
            return False
        return True

    def value_of_action(self, val_list, action: Util.Movement):
        """
        :param val_list: {ant, day_info, grid}
        :param action:
        """

        ant = val_list[0]
        grid = val_list[2]
        new_location = action.coordinate_move(ant.location)
        if not self.is_move_legal(action, ant, grid):
            return -1

        scents = grid.get_scent_values_for_direction(
            new_location, action)

        val_scent = scents[Util.ScentType.FOOD_THIS_WAY.value]
        val_dir = 1 if (self.is_out(new_location, action, grid) and val_scent < 0.1) else 0
        val_walked = scents[Util.ScentType.IM_WALKIN_HERE.value]
        return_val = \
            self.dir_weight*val_dir + self.scent_weight*val_scent + self.walked_weight*val_walked

        return return_val

    def get_legal_actions(self):
        return self.actions

    def get_dir_weight(self):
        return self.dir_weight

    def get_scent_weight(self):
        return self.scent_weight

    def set_scent_weight(self, scent_w):
        self.scent_weight = scent_w

    def set_dir_weight(self, dir_w):
        self.dir_weight = dir_w

    def crossover(self, other: 'MovementPolicy'):
        # # print(self.dir_weight,other.dir_weight)
        scent_w = (self.scent_weight+other.scent_weight)/2
        dir_w = (self.dir_weight+other.dir_weight)/2
        walk_w = (self.walked_weight+other.walked_weight)/2

        return MovementPolicy(dir_w, scent_w, walk_w)

    def mutate(self):
        if random.randint(0, 1) == 0:
            self.dir_weight = self._mutate_val(self.dir_weight)
        else:
            self.scent_weight = self._mutate_val(self.scent_weight)

    def _mutate_val(self, val):
        ran = random.random() / 5
        if random.randint(0, 1) == 0:
            val -= ran * val
        else:
            val += (1 - val) * ran
        return val

    def is_out(self, coordinate, movement: Util.Movement, grid: New_Anthill.Grid):
        hill_x, hill_y = grid.anthill
        x, y = coordinate
        if movement == Util.Movement.Up:
            return y < hill_y
        elif movement == Util.Movement.Down:
            return y > hill_y
        elif movement == Util.Movement.Left:
            return x < hill_x
        elif movement == Util.Movement.Right:
            return x > hill_x
        # print("Error! movement nothing!")
        return False


class Individual:
    def __init__(self, policy: Policy):
        self.policy = policy

    def __repr__(self):
        return str(self.policy)

    def max_action(self, val_list):
        max_actions = None
        max_value = 0
        for action in self.policy.get_legal_actions():
            cur_value = self.policy.value_of_action(val_list, action)
            if not max_actions or max_value < cur_value:
                max_actions = [action]
                max_value = cur_value
            elif max_value == cur_value:
                max_actions.append(action)
        i = random.randint(0, len(max_actions)-1)
        return max_actions[i]

    def crossover(self, other: 'Individual'):
        new_policy = self.policy.crossover(other.policy)
        new_individual = Individual(new_policy)
        return new_individual

    def mutate(self):
        self.policy.mutate()


class MovementGenetic:
    def __init__(self, days_in_year=DAYS_PER_YEAR, steps_per_day=STEPS_PER_DAY,
                 const_ant_num=DEFAULT_NUM_ANTS, individuals_num=5, food_change_prob=0.5):
        self.game = New_Anthill.GameRunner(days_in_year=days_in_year,
                                           steps_per_day=steps_per_day,
                                           movement_policy=self.get_movement_policy(),
                                           food_change_prob=food_change_prob)
        self.individuals_num = individuals_num
        self.individual_reward = [0] * individuals_num
        self.raw_individual_reward = [0] * individuals_num
        self.individual_list = self.make_individuals(self.individuals_num)
        self.cur_individual: Individual = None

    def make_individuals(self, individuals_num):
        individual_list = []
        for i in range(0,individuals_num):
            individual_list.append(self.make_individual())
        return individual_list

    def make_individual(self):#random for weigth 0,1create policy
        dir_w = random.uniform(-1, 1)
        scent_w = random.uniform(-1, 1)
        walk_w = random.uniform(-1, 1)

        policy = MovementPolicy(dir_w, scent_w, walk_w)
        return Individual(policy)

    # def best_fit(self):
    #     maxFit = 0
    #     max_Index = 0
    #
    #     for i in range(len(self.individual_reward)):
    #         if maxFit <= self.individual_reward[i]:
    #             maxFit = self.individual_reward[i]
    #             max_Index = i
    #     return self.individual_list[max_Index],self.individual_reward[max_Index]
    #
    # def second_best_fit(self):
    #     max_id1 = 0
    #     max_id2 = 0
    #     if self.individual_reward[0]>=self.individual_reward[1]:
    #         max_id1=0
    #         max_id2=1
    #     else:
    #         max_id1=1
    #         max_id2=0
    #
    #     for i in range(2,len(self.individual_reward)):
    #         if self.individual_reward[i] > self.individual_reward[max_id1]  :
    #             max_id2 = max_id1
    #             max_id1 = i
    #         elif self.individual_reward[i] > self.individual_reward[max_id2]\
    #             and self.individual_reward[i]!=self.individual_reward[max_id1]:
    #             max_id2 = i
    #         elif self.individual_reward[max_id1] == self.individual_reward[max_id2] \
    #                 and self.individual_reward[i] != self.individual_reward[max_id2]:
    #             max_id2=i
    #
    #     return self.individual_list[max_id2], self.individual_reward[max_id2]
    #
    # def move_fitness(self,ant ,day_info,grid):
    #     sum = 0
    #     for i in range(len(self.individual_list)):
    #         reward = MovementPolicy.value_of_action(val_list=[ant, day_info, grid], action=self.individual_list[i])
    #         self.individual_reward.append(reward)
    #         sum += reward

    def do_episode(self):
        size = len(self.individual_list)
        self.individual_reward = [0] * size
        self.raw_individual_reward = [0] * size
        for i in range(0, size):
            self.cur_individual = self.individual_list[i]
            self.raw_individual_reward[i] = self.game.do_years(1)
            self.individual_reward[i] = max(0, self.raw_individual_reward[i])

    def do_genetic(self):
        if max(self.individual_reward) <= 0:
            self.individual_list = self.make_individuals(self.individuals_num)
            # print("All bad results. starting from scratch.")
            return
        size = len(self.individual_list)
        new_individuals = [0] * size
        min_reward = min(self.individual_reward)
        individual_weights = [reward - min_reward for reward in
                              self.individual_reward]

        for i in range(0, size):
            choise1 = random.choices(range(0, len(self.individual_list)),
                                     weights=individual_weights)
            choise2 = random.choices(range(0, len(self.individual_list)),
                                     weights=individual_weights)
            # # print(self.individual_reward)
            # # print(self.individual_list)
            new_individuals[i] = self.individual_list[choise1[0]].crossover(
                self.individual_list[choise2[0]] )
            if Util.flip_coin(1 - MUTATION_CHANCE):
                new_individuals[i].mutate()

        self.individual_list = new_individuals

        # # print("after changeeeeeeeeeeeeeee")
        # # print(self.individual_list)

        #return self.individual_reward

    def do_episodes(self, num_of_episodes, last_one=False):
        for i in range(0, num_of_episodes):
            self.do_episode()# for the new list after genetic algotitm
            if not last_one:
                self.do_genetic()
            # # print("Episode: ", i, "Results: ", self.raw_individual_reward)
        return max(self.raw_individual_reward)

    def for_year(self ,day_in_year,num_day):
        for i in range(day_in_year):
            # print("for day")
            sum=self.do_episodes(num_day)
            # print(max(sum))

    def get_movement_policy(self):
        def movement_policy(ant, day_info, grid):
            action = self.cur_individual.max_action([ant, day_info, grid])
            return action
        return movement_policy




class QueentGenetic:
    def __init__(self, years_learning=10, years_running=1, days_in_year=DAYS_PER_YEAR,
                 steps_per_day=STEPS_PER_DAY, const_ant_num=300, individuals_num=5):
        self.game = New_Anthill.GameRunner(days_in_year=days_in_year,
                                           steps_per_day=steps_per_day,
                                           queen_policy=self.get_queen_policy())
        self.individuals_num=individuals_num
        self.individual_reward = []
        self.individual_list = self.make_individuals(self.individuals_num)
        self.cur_individual: Individual = None
        self.const_ant_num=const_ant_num
        self.individual_reward = []

    def make_individuals(self, individuals_num):
        individual_list = []
        for i in range(0, individuals_num):
            individual_list.append(self.make_individual())
        return individual_list

    def make_individual(self):
        ant_num=random.randint(10,100)
        policy= QueenPolicy(ant_num)
        return Individual(policy)
    def ret_ant_num(self):
        return  300

    def get_queen_policy(self):
        a=self.ret_ant_num()
        def queen_policy(foodgatherd,food_delta,a,day_info):
            action = self.cur_individual.max_action([foodgatherd,food_delta,a,day_info])
            return action
        return queen_policy

    def queen_fitness(self ):
        sum = 0
        for i in range(len(self.individual_list)):
            reward=self.individual_list[i].value(self.const_ant_num,QueenPolicy.actions)
            self.individual_reward.append(reward)
            sum += reward
            #check the vl_lst
        return sum
    def best_fit(self):
        maxFit = 0
        max_Index = 0

        for i in range(len(self.individual_reward)):
            if maxFit <= self.individual_reward[i]:
                maxFit = self.individual_reward[i]
                max_Index = i

        return self.individual_list[max_Index],self.individual_reward[max_Index]

    def second_best_fit(self):
        max_id1 = 0
        max_id2 = 0
        if self.individual_reward[0]>=self.individual_reward[1]:
            max_id1=0
            max_id2=1
        else:
            max_id1=1
            max_id2=0

        for i in range(2,len(self.individual_reward)):
            if self.individual_reward[i] > self.individual_reward[max_id1]:
                max_id2 = max_id1
                max_id1 = i
            elif self.individual_reward[i] > self.individual_reward[max_id2]\
                and self.individual_reward[i]!=self.individual_reward[max_id1]:
                max_id2 = i
            elif self.individual_reward[max_id1] == self.individual_reward[max_id2] \
                    and self.individual_reward[i] != self.individual_reward[max_id2]:
                max_id2=i

        return self.individual_list[max_id2], self.individual_reward[max_id2]

    def run_episode(self):
        size = len(self.individual_list)
        self.individual_reward = [0] * size
        for i in range(0, size):
            self.cur_individual = self.individual_list[i]
            self.individual_reward[i] = self.game.do_day(False, 1)
        while max(self.individual_reward) < 0:
            self.individual_list = self.make_individuals(self.individuals_num)
            self.run_episode()

    def do_genetic(self):  # problem infinite loop
        inds=[]

        if max(self.individual_reward)<0:
            self.individual_list=self.make_individuals(self.individuals_num)
            return

        a = []
        # # print("befoore changeeeeeeeeeeeeeeeee")
        # # print(self.individual_list)
        for i in range(len(self.individual_reward)):

            if self.individual_reward[i] < 0:
                a.append(-1 * self.individual_reward[i])
            else:
                a.append(self.individual_reward[i])

        for i in range(len(self.individual_reward)):
            choise1=random.choices(range(0,len(self.individual_list)),weights=a)
            choise2=random.choices(range(0,len(self.individual_list)),weights=a)
            policy=self.individual_list[choise1[0]].policy.crossover(self.individual_list[choise2[0]].policy)
            self.individual_list[choise1[0]].policy = policy
            new_policy = self.individual_list[choise1[0]].policy.mutaion()
            inds.append(Individual(new_policy))
        self.individual_list = inds

    def do_episodes(self, num_of_episodes):
        self.run_episode()
        # # print(self.individual_reward)
        sum = [0] * len(self.individual_reward)

        for i in range(0, num_of_episodes):

            self.do_genetic()
            self.run_episode()  # for the new list after genetic algotitm
            for i in range(len(self.individual_reward)):
                sum[i] = sum[i] + self.individual_reward[i]

        # # print(sum)
        return sum
        # # print("hi")


