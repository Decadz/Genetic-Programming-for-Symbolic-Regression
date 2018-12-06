__author__ = "Christian Raymond"
__date__ = "06 December 2018"

"""
A classic implementation of Genetic Programming for Symbolic Regression.
This program aims to map the input data to the output data through the use
of a symbolic representation (expression trees) and evolutionary techniques.
"""

import algorithms.config as config
import numpy as np
import operator
import time

from utility.operators import division
from utility.evaluate import evaluate_population

from deap import base
from deap import creator
from deap import tools
from deap import gp


def execute_algorithm():

    """
    Executes the genetic program, evolving candidate solutions using
    the parameters specified in the config.py file.

    :return statistics: List of Statistics
    :return population: Final Population
    :return halloffame: Best Individuals
    """

    population = toolbox.population(n=config.size_population)
    halloffame = tools.HallOfFame(1)
    statistics = []

    # Begin the evolution process.
    for generation in range(config.num_generations):

        print("Generation: " + str(generation + 1) + "/" + str(config.num_generations))
        start_time = time.clock()  # Records the time at the start of the generation.

        # Evaluate the populations fitness.
        for individual, fitness in zip(population, list(map(toolbox.evaluate, population))):
            individual.fitness.values = fitness

        # Update the hall of fame.
        halloffame.update(population)

        # Gather all the fitnesses and size information about the population.
        fits = [individual.fitness.values[0] for individual in population]
        size = [len(individual) for individual in population]

        # Select the next generation of individuals and clone.
        next_gen = toolbox.select(population, config.size_population)
        next_gen = list(map(toolbox.clone, next_gen))

        # Apply crossover genetic operators.
        for i in range(1, config.size_population, 2):
            if np.random.random() < config.prob_crossover:
                next_gen[i - 1], next_gen[i] = toolbox.mate(next_gen[i - 1], next_gen[i])
                del next_gen[i - 1].fitness.values
                del next_gen[i].fitness.values

        # Apply mutation genetic operators.
        for mutant in next_gen:
            if np.random.random() < config.prob_mutation:
                toolbox.mutate(mutant)
                del mutant.fitness.values

        # The population is entirely replaced by the offspring
        population[:] = next_gen

        end_time = time.clock()  # Records the time at the end of the generation.

        # Evaluates the population and returns statistics.
        statistics.append(evaluate_population(generation, end_time - start_time, fits, size, halloffame[0],
                                              toolbox.compile(expr=halloffame[0])))

    return statistics, population, halloffame


"""
===============================================================================================================

    - Fitness Functions

===============================================================================================================
"""


def fitness_function_ae(individual, data, toolbox):

    """
    Calculates the fitness of a candidate solution/individual by using the absolute
    value of the errors (AE).

    :param individual: Candidate Solution
    :param data: Evaluation Data
    :param toolbox: Evolutionary Operators
    :return: Fitness Value
    """

    # Converts the expression tree into a callable function.
    func = toolbox.compile(expr=individual)
    total_error = 0

    for rows in range(data.shape[0]):

        # Uses splat operator to convert array into positional arg.
        pred = func(*(data.values[rows][0:data.shape[1]-1]))
        real = data.values[rows][data.shape[1]-1]

        error = abs(real - pred)
        total_error += error

    # Must return the value as a list object.
    return [total_error]


def fitness_function_sse(individual, data, toolbox):

    """
    Calculates the fitness of a candidate solution/individual by using the sum of
    the squared errors (SSE).

    :param individual: Candidate Solution
    :param data: Evaluation Data
    :param toolbox: Evolutionary Operators
    :return: Fitness Value
    """

    # Converts the expression tree into a callable function.
    func = toolbox.compile(expr=individual)
    total_error = 0

    for rows in range(data.shape[0]):

        # Uses splat operator to convert array into positional arg.
        pred = func(*(data.values[rows][0:data.shape[1]-1]))
        real = data.values[rows][data.shape[1]-1]

        error = (real - pred)**2
        total_error += error

    # Must return the value as a list object.
    return [total_error]


def fitness_function_mse(individual, data, toolbox):

    """
    Calculates the fitness of a candidate solution/individual by using the mean
    of the squared errors (MSE).

    :param individual: Candidate Solution
    :param data: Evaluation Data
    :param toolbox: Evolutionary Operators
    :return: Fitness Value
    """

    # Converts the expression tree into a callable function.
    func = toolbox.compile(expr=individual)
    total_error = 0

    for rows in range(data.shape[0]):

        # Uses splat operator to convert array into positional arg.
        pred = func(*(data.values[rows][0:data.shape[1]-1]))
        real = data.values[rows][data.shape[1]-1]

        error = (real - pred)**2
        total_error += error

    # Must return the value as a list object.
    return [total_error/data.shape[0]]


"""
===============================================================================================================

    - Algorithm Configuration (this portion of code must remain in global scope as per DEAP requirements).

===============================================================================================================
"""

# Creating a new primitive node set.
pset = gp.PrimitiveSet("main", config.training_data.shape[1] - 1)

# Adding operators to the primitive set.
pset.addPrimitive(np.add, 2)
pset.addPrimitive(np.subtract, 2)
pset.addPrimitive(np.multiply, 2)
pset.addPrimitive(division, 2)

# Adding some random terminals between a set range with a set #dp.
pset.addEphemeralConstant("randomTerm", lambda: round(np.random.uniform(config.random_lower, config.random_upper), 4))

# Tell the algorithm that we are trying to minimise the fitness function.
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", gp.PrimitiveTree, fitness=creator.FitnessMin, pset=pset)

# Creating a toolbox of evolutionary operators.
toolbox = base.Toolbox()

toolbox.register("expr", gp.genHalfAndHalf, pset=pset, min_=1, max_=2)
toolbox.register("individual", tools.initIterate, creator.Individual, toolbox.expr)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("compile", gp.compile, pset=pset)

toolbox.register("select", tools.selTournament, tournsize=3)
toolbox.register("evaluate", fitness_function_mse, data=config.training_data, toolbox=toolbox)
toolbox.register("mate", gp.cxOnePoint)
toolbox.register("expr_mut", gp.genFull, min_=0, max_=2)
toolbox.register('mutate', gp.mutUniform, expr=toolbox.expr_mut, pset=pset)

# Restricting size of expression tree to avoid bloat.
toolbox.decorate("mate", gp.staticLimit(key=operator.attrgetter('height'), max_value=config.max_height))
toolbox.decorate("mutate", gp.staticLimit(key=operator.attrgetter('height'), max_value=config.max_height))