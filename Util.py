import enum
import random


class Movement(enum.Enum):
    Up = (0, -1)
    Down = (0, 1)
    Right = (1, 0)
    Left = (-1, 0)
    Nothing = None

    def coordinate_move(self, coordinate):
        if self.value:
            return (coordinate[0] + self.value[0],  coordinate[1] +
                    self.value[1])
        return coordinate

    def get_opposite_move(self):
        return lookup[self]


movement_sign_small = ["↑", "↓", "←", "→", " "]
movement_sign_big = ["↑↑", "↓↓", "←←", "→→", "  "]

movements = [Movement.Up, Movement.Down, Movement.Left, Movement.Right]
movements_num = {Movement.Up: 0, Movement.Down: 1, Movement.Left: 2,
                 Movement.Right: 3, Movement.Nothing: 4}
lookup = {Movement.Up: Movement.Down, Movement.Down: Movement.Up,
          Movement.Left: Movement.Right, Movement.Right: Movement.Left,
          Movement.Nothing: Movement.Nothing}


class ScentType(enum.Enum):
    IM_WALKIN_HERE = 0
    FOOD_THIS_WAY = 1


class Seasons(enum.Enum):
    SUMMER = 1
    WINTER = 2
    SPRING = 3
    FALL = 4


class FoodDistOpts(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class AlgoTypes(enum.Enum):
    RANDOM = "Random"
    SMART = "Scent Trail"
    GENETIC = "Genetic"
    Q_LEARNING = "Q-Learning"
    INDEPENDENT = "Independent Q-Learning"
    SIMULTANEOUS = "Simultaneous Q-Learning"


class SpeedTypes(enum.Enum):
    SLOW = "Slow"
    NORMAL = "Normal"
    FAST = "Fast"


class OutputSizes(enum.Enum):
    LOW = "Low"
    HIGH = "High"


class ScreenSizes(enum.Enum):
    LARGE = "Aquarium"
    SMALL = "Laptop"


speed_vals = {SpeedTypes.SLOW.value: 0.7, SpeedTypes.NORMAL.value: 0.4, SpeedTypes.FAST.value: 0.1}

food_change_vals = {FoodDistOpts.LOW.value: 0.2, FoodDistOpts.MEDIUM.value: 0.5,
                    FoodDistOpts.HIGH.value: 0.8}

queen_actions = [0, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]


def flip_coin(p):
    r = random.random()
    return r < p


class Counter(dict):
    """
    A counter keeps track of counts for a set of keys.

    The counter class is an extension of the standard python
    dictionary type.  It is specialized to have number values
    (integers or floats), and includes a handful of additional
    functions to ease the task of counting data.  In particular,
    all keys are defaulted to have value 0.  Using a dictionary:

    a = {}
    # print(a['test'])

    would give an error, while the Counter class analogue:

    >>> a = Counter()
    >>> # print(a['test'])
    0

    returns the default 0 value. Note that to reference a key
    that you know is contained in the counter,
    you can still use the dictionary syntax:

    >>> a = Counter()
    >>> a['test'] = 2
    >>> # print(a['test'])
    2

    This is very useful for counting things without initializing their counts,
    see for example:

    >>> a['blah'] += 1
    >>> # print(a['blah'])
    1

    The counter also includes additional functionality useful in implementing
    the classifiers for this assignment.  Two counters can be added,
    subtracted or multiplied together.  See below for details.  They can
    also be normalized and their total count and arg max can be extracted.
    """

    def __getitem__(self, idx):
        self.setdefault(idx, 0)
        return dict.__getitem__(self, idx)

    def incrementAll(self, keys, count):
        """
        Increments all elements of keys by the same count.

        >>> a = Counter()
        >>> a.incrementAll(['one','two', 'three'], 1)
        >>> a['one']
        1
        >>> a['two']
        1
        """
        for key in keys:
            self[key] += count

    def argMax(self):
        """
        Returns the key with the highest value.
        """
        if len(self.keys()) == 0: return None
        all = list(self.items())
        values = [x[1] for x in all]
        maxIndex = values.index(max(values))
        return all[maxIndex][0]

    def sortedKeys(self):
        """
        Returns a list of keys sorted by their values.  Keys
        with the highest values will appear first.

        >>> a = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> a['third'] = 1
        >>> a.sortedKeys()
        ['second', 'third', 'first']
        """
        sortedItems = list(self.items())
        sortedItems.sort(key=lambda item: -item[1])
        return [x[0] for x in sortedItems]

    def totalCount(self):
        """
        Returns the sum of counts for all keys.
        """
        return sum(self.values())

    def normalize(self):
        """
        Edits the counter such that the total count of all
        keys sums to 1.  The ratio of counts for all keys
        will remain the same. Note that normalizing an empty
        Counter will result in an error.
        """
        total = float(self.totalCount())
        if total == 0: return
        for key in self.keys():
            self[key] = self[key] / total

    def divideAll(self, divisor):
        """
        Divides all counts by divisor
        """
        divisor = float(divisor)
        for key in self:
            self[key] /= divisor

    def copy(self):
        """
        Returns a copy of the counter
        """
        return Counter(dict.copy(self))

    def __mul__(self, y):
        """
        Multiplying two counters gives the dot product of their vectors where
        each unique label is a vector element.

        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['second'] = 5
        >>> a['third'] = 1.5
        >>> a['fourth'] = 2.5
        >>> a * b
        14
        """
        sum = 0
        x = self
        if len(x) > len(y):
            x, y = y, x
        for key in x:
            if key not in y:
                continue
            sum += x[key] * y[key]
        return sum

    def __radd__(self, y):
        """
        Adding another counter to a counter increments the current counter
        by the values stored in the second counter.

        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> a += b
        >>> a['first']
        1
        """
        for key, value in y.items():
            self[key] += value

    def __add__(self, y):
        """
        Adding two counters gives a counter with the union of all keys and
        counts of the second added to counts of the first.

        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> (a + b)['first']
        1
        """
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] + y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = y[key]
        return addend

    def __sub__(self, y):
        """
        Subtracting a counter from another gives a counter with the union of all keys and
        counts of the second subtracted from counts of the first.

        >>> a = Counter()
        >>> b = Counter()
        >>> a['first'] = -2
        >>> a['second'] = 4
        >>> b['first'] = 3
        >>> b['third'] = 1
        >>> (a - b)['first']
        -5
        """
        addend = Counter()
        for key in self:
            if key in y:
                addend[key] = self[key] - y[key]
            else:
                addend[key] = self[key]
        for key in y:
            if key in self:
                continue
            addend[key] = -1 * y[key]
        return addend
