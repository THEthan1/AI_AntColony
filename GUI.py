import tkinter as tk
from tkinter import ttk
import enum
from New_Anthill import *
from AnthillGeneticPolicy import MovementGenetic
from defaults import *
from Util import *
import threading
import Policy


class Thread(threading.Thread):
    def __init__(self, _id, _name, run_function):
        threading.Thread.__init__(self)
        self.id = _id
        self.name = _name
        self.run_function = run_function

    def run(self):
        self.run_function()


def get_small_output(grid: Grid, ants: Ants, screen_size: ScreenSizes):
    ants_list = ants.ants
    scent_value_grid = grid.scent_value
    scent_dir_grid = grid.scent_direction

    first = int(grid.grid_size / 2)

    for ant in ants_list:
        coord = ant.location
        grid.output_ant_grid[coord[0]][coord[1]] = 1

        if coord[0] < first:
            first = coord[0]

    third = int(grid.grid_size / 3)
    start, end = 15, 134
    frame = "-" * int(4.7*third) + "\n"

    if screen_size == ScreenSizes.SMALL.value:
        start, end = 29, 121
        frame = "-" * int(2*(end - start)-1) + "\n"

    out_text = frame

    for row in range(third, 2 * third):
        out_text += "|"
        for col in range(start, end):
            char = " "
            if (row, col) == grid.anthill:
                char = "@"
            elif grid.output_ant_grid[col][row] == 1:
                char = "X"
            elif grid.food_at_location((col, row)) > 0:
                food = grid.food_at_location((col, row))
                if food < 100:
                    char = str(int(food / 10))
                elif food < 1000:
                    char = "C"
                else:
                    char = "K"
            elif scent_value_grid[col][row][ScentType.FOOD_THIS_WAY.value] > 0.1:
                movement = scent_dir_grid[col][row][ScentType.FOOD_THIS_WAY.value]
                char = movement_sign_small[movements_num[movement]]  # + "F"
            # elif scent_value_grid[col][row][ScentType.IM_WALKIN_HERE.value] > 0.1:
            #     movement = scent_dir_grid[col][row][ScentType.IM_WALKIN_HERE.value]
            #     char = movement_sign[movements_num[movement]] + "W"

            out_text += char + "|"
        out_text += "\n " + frame

    grid.output_ant_grid *= 0

    return out_text


def get_large_output(grid: Grid, ants: Ants, screen_size: ScreenSizes):
    ants_list = ants.ants
    scent_value_grid = grid.scent_value
    scent_dir_grid = grid.scent_direction

    first = int(grid.grid_size / 2)

    for ant in ants_list:
        coord = ant.location
        grid.output_ant_grid[coord[0]][coord[1]] = 1

        if coord[0] < first:
            first = coord[0]

    third = int(grid.grid_size / 3)
    start, end = 36, 114
    frame = "-" * int(3*(end-start)) + "\n"

    if screen_size == ScreenSizes.SMALL.value:
        start, end = 45, 105
        frame = "-" * int(3*(end-start)) + "\n"

    out_text = frame

    for row in range(third, 2 * third):
        out_text += "|"
        for col in range(start, end):
            char = "  "
            if (row, col) == grid.anthill:
                char = "/\\"
            elif grid.output_ant_grid[col][row] == 1:
                char = "XX"
            elif grid.food_at_location((col, row)) > 0:
                food = grid.food_at_location((col, row))
                if food < 100:
                    char = str(int(food))
                elif food < 1000:
                    char = str(int(food / 100)) + "C"
                else:
                    char = str(int(food / 1000)) + "K"

                if len(char) == 1:
                    char = " " + char
            elif scent_value_grid[col][row][ScentType.FOOD_THIS_WAY.value] > 0.1:
                movement = scent_dir_grid[col][row][ScentType.FOOD_THIS_WAY.value]
                char = movement_sign_big[movements_num[movement]]  # + "F"
            # elif scent_value_grid[col][row][ScentType.IM_WALKIN_HERE.value] > 0.1:
            #     movement = scent_dir_grid[col][row][ScentType.IM_WALKIN_HERE.value]
            #     char = movement_sign[movements_num[movement]] + "W"

            out_text += char + "|"
        out_text += "\n " + frame

    grid.output_ant_grid *= 0

    return out_text


class GUI:
    def __init__(self):
        self.window = tk.Tk()
        self.run_btn = None
        self.output_box = None
        self.progress_bar = None
        self.food_value = tk.StringVar("")
        self.num_ants_value = tk.StringVar("")
        self.food_dist_var = tk.StringVar(self.window)
        self.daily_added_food_var = tk.StringVar(self.window)
        self.algo_type_var = tk.StringVar(self.window)
        self.speed_var = tk.StringVar(self.window)
        self.size_var = tk.StringVar(self.window)
        self.screen_size_var = tk.StringVar(self.window)
        self.status_text = tk.StringVar("")
        self.training = False
        self.game = None

        self.set_up_window()

    def run(self):
        run_function = None
        algo = self.algo_type_var.get()
        if algo == AlgoTypes.RANDOM.value:
            run_function = self.run_with_random
        elif algo == AlgoTypes.SMART.value:
            run_function = self.run_with_scent
        elif algo == AlgoTypes.GENETIC.value:
            run_function = self.run_with_genetic
        elif algo == AlgoTypes.Q_LEARNING.value:
            run_function = self.run_with_qlearning_basic
        elif algo == AlgoTypes.INDEPENDENT.value:
            run_function = self.run_with_qlearning_independent
        elif algo == AlgoTypes.SIMULTANEOUS.value:
            run_function = self.run_with_qlearning_simultaneous

        thread = Thread(1, algo, run_function)
        thread.start()

    def run_with_random(self):
        self.run_with_policy(default_movement_policy)

    def run_with_scent(self):
        self.run_with_policy(scent_movement_policy)

    def run_with_policy(self, policy):
        self.training = False
        self.status_text.set("Running!")
        self.progress_bar['maximum'] = DAYS_PER_YEAR-1
        self.game = GameRunner(movement_policy=policy,
                                           gui_updater=self.get_update_function(),
                                           food_change_prob=food_change_vals[self.food_dist_var.get()])
        self.game.do_years(1)
        self.status_text.set("Done")
        self.run_btn['state'] = tk.NORMAL

    def run_with_genetic(self):
        num_individuals = 5
        num_episodes = 5
        policy = MovementGenetic(individuals_num=num_individuals)
        self.game = policy.game
        self.game.grid.food_change_prob = food_change_vals[self.food_dist_var.get()]
        self.game.gui_updater = self.get_update_function()
        self.status_text.set("Gestating....")
        self.progress_bar['maximum'] = DAYS_PER_YEAR * num_episodes * num_individuals
        self.run_btn['state'] = tk.NORMAL
        self.training = True
        policy.do_episodes(num_episodes)
        self.training = False
        self.progress_bar['maximum'] = DAYS_PER_YEAR * num_individuals
        self.progress_bar['value'] = 0
        policy.do_episodes(1)
        self.status_text.set("Done")
        self.run_btn['state'] = tk.NORMAL

    def run_with_qlearning(self, policy, years_learning):
        self.game = policy.game
        self.game.grid.food_change_prob = food_change_vals[self.food_dist_var.get()]
        self.game.gui_updater = self.get_update_function()
        self.status_text.set("Training....")
        self.training = True
        self.progress_bar['maximum'] = DAYS_PER_YEAR * years_learning
        policy.do_learning()

        self.status_text.set("Running!")
        self.training = False
        self.progress_bar['maximum'] = DAYS_PER_YEAR - 1
        self.progress_bar['value'] = 0
        policy.do_running()

        self.status_text.set("Done")
        self.run_btn['state'] = tk.NORMAL

    def run_with_qlearning_basic(self):
        years_learning = 3
        policy = Policy.MovementPolicy(years_learning=years_learning)
        self.run_with_qlearning(policy, years_learning)

    def run_with_qlearning_independent(self):
        years_learning = 10
        policy = Policy.RunIndependentlyPolicy(years_learning=years_learning)
        self.run_with_qlearning(policy, years_learning)

    def run_with_qlearning_simultaneous(self):
        years_learning = 5
        policy = Policy.RunTogetherPolicy(years_learning=years_learning)
        self.run_with_qlearning(policy, years_learning)

    def get_update_function(self):
        get_output_func = get_large_output

        if self.size_var.get() == OutputSizes.HIGH.value:
            get_output_func = get_small_output

        speed = self.speed_var.get()
        size = self.screen_size_var.get()

        def update_function(grid: Grid, ants: Ants, is_final_day=False, increment=1):
            if is_final_day and not self.training:
                self.set_output(get_output_func(grid, ants, size))
                self.output_box.see(grid.grid_size/2)
                time.sleep(speed_vals[speed])
            if not is_final_day:
                self.progress_bar['value'] += increment
                self.num_ants_value.set(str(len(ants.ants)))
                self.food_value.set(str(int(self.game.food_gathered)))

        return update_function

    def run_btn_tapped(self):
        self.run_btn['state'] = tk.DISABLED
        self.output_box.delete(1.0, tk.END)
        self.progress_bar['value'] = 0
        self.num_ants_value.set(str(DEFAULT_NUM_ANTS))
        self.food_value.set(str(0))
        self.run()

    def set_output(self, text):
        self.output_box.delete(1.0, tk.END)
        self.output_box.insert(tk.END, text)

    def set_up_window(self):
        """ WINDOW SETTINGS ----------------------------------------"""
        self.window.title("A.I. Ant Colony")
        self.window.attributes('-fullscreen', True)
        # self.window.resizable(False, False)

        """ ROW 1 ----------------------------------------"""
        row_1 = tk.Frame(master=self.window, borderwidth=1)
        row_1.pack(fill=tk.X, side=tk.TOP)

        algo_type_label = tk.Label(master=row_1, text="Algorithm:")
        algo_type_opts = [opt.value for opt in AlgoTypes]
        self.algo_type_var.set(AlgoTypes.Q_LEARNING.value)
        algo_types_menu = tk.OptionMenu(row_1, self.algo_type_var, *algo_type_opts)

        algo_type_label.pack(fill=tk.Y, side=tk.LEFT)
        algo_types_menu.pack(fill=tk.Y, side=tk.LEFT)

        food_dist_label = tk.Label(master=row_1, text="Food Probability:")
        food_dist_opts = [opt.value for opt in FoodDistOpts]
        self.food_dist_var.set(FoodDistOpts.MEDIUM.value)
        food_dist_menu = tk.OptionMenu(row_1, self.food_dist_var, *food_dist_opts)

        food_dist_label.pack(fill=tk.Y, side=tk.LEFT)
        food_dist_menu.pack(fill=tk.Y, side=tk.LEFT)

        output_label = tk.Label(master=row_1, text="Output Density:")
        output_opts = [opt.value for opt in OutputSizes]
        self.size_var.set(OutputSizes.LOW.value)
        size_menu = tk.OptionMenu(row_1, self.size_var, *output_opts)

        output_label.pack(fill=tk.Y, side=tk.LEFT)
        size_menu.pack(fill=tk.Y, side=tk.LEFT)

        screen_label = tk.Label(master=row_1, text="Screen:")
        screen_opts = [opt.value for opt in ScreenSizes]
        self.screen_size_var.set(ScreenSizes.LARGE.value)
        screen_menu = tk.OptionMenu(row_1, self.screen_size_var, *screen_opts)

        screen_label.pack(fill=tk.Y, side=tk.LEFT)
        screen_menu.pack(fill=tk.Y, side=tk.LEFT)

        speed_label = tk.Label(master=row_1, text="Playback:")
        speed_opts = [opt.value for opt in SpeedTypes]
        self.speed_var.set(SpeedTypes.NORMAL.value)
        speed_menu = tk.OptionMenu(row_1, self.speed_var, *speed_opts)

        speed_label.pack(fill=tk.Y, side=tk.LEFT)
        speed_menu.pack(fill=tk.Y, side=tk.LEFT)

        num_ants_title = tk.Label(master=row_1, text="Num Ants:")
        num_ants_label = tk.Label(master=row_1, textvariable=self.num_ants_value)
        num_ants_title.pack(fill=tk.Y, side=tk.LEFT)
        num_ants_label.pack(fill=tk.Y, side=tk.LEFT)

        food_title = tk.Label(master=row_1, text="Food Delta:")
        food_label = tk.Label(master=row_1, textvariable=self.food_value)
        food_title.pack(fill=tk.Y, side=tk.LEFT)
        food_label.pack(fill=tk.Y, side=tk.LEFT)

        """ ROW 2 ----------------------------------------"""
        row_2 = tk.Frame(master=self.window, borderwidth=1)
        row_2.pack(fill=tk.X, side=tk.TOP)

        tenth = int(self.window.winfo_screenwidth()/10)
        self.run_btn = tk.Button(master=row_2, text="Run", command=self.run_btn_tapped, width=int(tenth/10), fg='green')
        self.run_btn.pack(side=tk.LEFT)

        self.progress_bar = ttk.Progressbar(master=row_2, orient='horizontal', mode='determinate',
                                            length=8*tenth)
        self.progress_bar.pack(side=tk.LEFT)

        status_label = tk.Label(master=row_2, textvariable=self.status_text, fg="green", width=tenth)
        status_label.pack(side=tk.LEFT)

        self.num_ants_value.set(str(DEFAULT_NUM_ANTS))
        self.food_value.set("0")

        """ OUTPUT WINDOW ----------------------------------------"""
        self.output_box = tk.Text(master=self.window)
        self.output_box.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
        self.window.mainloop()



