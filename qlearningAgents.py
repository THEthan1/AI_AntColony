# qlearningAgents.py
# ------------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html


from learningAgents import ReinforcementAgent

import random,Util,math


class QLearningAgent(ReinforcementAgent):
  """
    Q-Learning Agent

    Functions you should fill in:
      - getQValue
      - getAction
      - getValue
      - getPolicy
      - update

    Instance variables you have access to
      - self.epsilon (exploration prob)
      - self.alpha (learning rate)
      - self.discount (discount rate)

    Functions you should use
      - self.getLegalActions(state)
        which returns legal actions
        for a state
  """
  def __init__(self, unexplored_val=10000, **args):
    "You can initialize Q-values here..."
    ReinforcementAgent.__init__(self, **args)
    self.policy = {}
    self.unexplored_val = unexplored_val

    # (state, action) -> Q-value
    self.q_values = {}

  def get_q_values(self):
    return self.q_values

  def getQValue(self, state, action):
    """
      Returns Q(state,action)
      Should return 0.0 if we never seen
      a state or (state,action) tuple
    """
    return self.q_values.get((state, action), self.unexplored_val)

  def getValue(self, state):
    """
      Returns max_action Q(state,action)
      where the max is over legal actions.  Note that if
      there are no legal actions, which is the case at the
      terminal state, you should return a value of 0.0.
    """
    return self.getMaxActionValuePair(state)[1]

  def getPolicy(self, state):
    """
      Compute the best action to take in a state.  Note that if there
      are no legal actions, which is the case at the terminal state,
      you should return None.
    """

    return self.getMaxActionValuePair(state)[0]

  def getMaxActionValuePair(self, state):
    legal_actions = self.getLegalActions(state)

    max_value = 0.0
    max_actions = None

    for action in legal_actions:
      q_value = self.getQValue(state, action)
      if max_actions is None or q_value > max_value:
        max_value = q_value
        max_actions = [action]
      elif q_value == max_value:
        max_actions.append(action)

    return random.choice(max_actions), max_value

  def getAction(self, state):
    """
      Compute the action to take in the current state.  With
      probability self.epsilon, we should take a random action and
      take the best policy action otherwise.  Note that if there are
      no legal actions, which is the case at the terminal state, you
      should choose None as the action.

      HINT: You might want to use util.flipCoin(prob)
      HINT: To pick randomly from a list, use random.choice(list)
    """
    # Pick Action
    legal_actions = self.getLegalActions(state)

    if len(legal_actions) == 0:
      return None

    if Util.flip_coin(self.epsilon):
      return random.choice(legal_actions)

    return self.getPolicy(state)

  def update(self, state, action, nextState, reward):
    """
      The parent class calls this to observe a
      state = action => nextState and reward transition.
      You should do your Q-Value update here

      NOTE: You should never call this function,
      it will be called on your behalf

      self.rewards = {}
      self.values = {}
      self.policy = {}
    """
    q_value = self.getQValue(state, action)
    # self.q_values[(state, action)] = \
    #           q_value + self.alpha * (reward + self.discount * self.getValue(nextState) - q_value)

    self.q_values[(state, action)] = \
              q_value + self.alpha * (reward - q_value)


class ApproximateQAgent(QLearningAgent):
  def __init__(self, extractor, **args):
    self.featExtractor = extractor
    self.index = 0
    QLearningAgent.__init__(self, **args)

    self.weights = Util.Counter()

  def getAction(self, state):
    action = QLearningAgent.getAction(self, state)
    self.doAction(state, action)
    return action

  def getQValue(self, state, action):
    q_value = 0.0
    features = self.featExtractor.getFeatures(state, action)
    for feature in features:
      q_value += self.weights[feature] * features[feature]

    return q_value

  def update(self, state, action, nextState, reward):
    q_value = self.getQValue(state, action)
    value = self.getValue(nextState)
    correction = reward + self.discount * value - q_value
    features = self.featExtractor.getFeatures(state, action)
    for feature in features:
      self.weights[feature] += self.alpha * correction * features[feature]


  def final(self, state):
    if self.episodesSoFar == self.numTraining:
      pass
      # print(self.weights)
    # print("weights are ", self.weights)
