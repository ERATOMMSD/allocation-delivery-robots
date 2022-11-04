import logging as log
from abc import ABC, abstractmethod

import pandas as pd
from jmetal.core.problem import IntegerProblem
from jmetal.core.solution import FloatSolution

from simulator import Simulator
from typing import Tuple, List
from deliverysearch.objectives import DeliveryObjective, MaximizeDeliveryRate, MinimizeRisks, MaximizeUtilization


class DeliveryProblem(IntegerProblem, ABC):

    def __init__(self, sim: Simulator):
        super().__init__()
        self.sim = sim
        self.records = []
        self.generation = 0

    def update_generation(self, generation: int):
        self.generation = generation

    def get_individuals_data_frame(self):
        return pd.DataFrame(self.records)

    @abstractmethod
    def fill_missing_data(self):
        pass


class RobotQuantityProblem(DeliveryProblem):
    """ Problem RobotQuantityProblem. Continuous archive having a flat Pareto front
    .. note:: Unconstrained archive. The problem has 2 integer variables and 3 float objectives.
    """

    def __init__(self, sim: Simulator,
                 speed_bounds: Tuple[int, int],
                 robot_bounds: Tuple[int, int],
                 speed_factor: int,
                 objectives: Tuple[DeliveryObjective] = (
                 MaximizeDeliveryRate(), MaximizeUtilization(), MinimizeRisks())):
        """ :param number_of_variables: number of decision variables of the archive.
        """
        super(RobotQuantityProblem, self).__init__(sim=sim)

        self.number_of_variables = 2
        self.number_of_objectives = len(objectives)
        self.number_of_constraints = 0

        self.obj_directions = [obj.direction for obj in objectives]
        self.obj_labels = [obj.label for obj in objectives]

        # the speed factor changes the granularity of the speed (10 kmh * 10 factor --> 100 values)
        self.speed_factor = speed_factor
        self.lower_bound = [robot_bounds[0], speed_bounds[0] * speed_factor]
        self.upper_bound = [robot_bounds[1], speed_bounds[1] * speed_factor]

    def evaluate(self, solution: FloatSolution) -> FloatSolution:

        speed = solution.variables[1]
        speed_kmh = speed/self.speed_factor
        robots = solution.variables[0]

        log.getLogger().info(f"Evaluating individual with {robots} robots and {speed_kmh} speed...")
        response = self.sim.run(num_robots=robots, robot_speed_kmh=speed_kmh)

        solution.objectives = [response[obj_label] for obj_label in self.obj_labels]
        log.getLogger().info(f"Objectives: {' - '.join([f'{k}:{v}' for k, v in response.items()])}")

        data_record = {'num_robots': robots, 'robot_speed': speed, 'robot_speed_kmh': speed_kmh,
                       'simulation_duration': self.sim.simulation_duration,
                       'generation': self.generation}
        data_record.update(response)
        self.records.append(data_record)

        return solution

    def get_individuals_data_frame(self):
        return pd.DataFrame(self.records)

    def fill_missing_data(self):
        records = self.records
        self.records = []

        # Re-evaluating all the solutions (on the current number of simulations)
        for record in records:
            solution = FloatSolution(lower_bound=self.lower_bound,
                                     upper_bound=self.upper_bound,
                                     number_of_objectives=self.number_of_objectives)

            solution.variables = [record['num_robots'], record['robot_speed']]

            # The evaluation of a solution is using the memoization of the simulator
            self.evaluate(solution)

            # Overriding the generation
            self.records[-1]['generation'] = record['generation']

    def get_name(self):
        return 'RobotQuantityProblem'

class RobotScheduleAssignmentProblemVariableRobots(DeliveryProblem):
    """ Problem RobotScheduleAssignmentProblemVariableRobots. Continuous archive having a flat Pareto front
    .. note:: Unconstrained archive. The problem has 1 + n integer variables and 3 float objectives,
             where n is the number of robots.
    """

    def __init__(self, sim: Simulator,
                 max_number_of_robots: int,
                 speed_bounds: Tuple[int, int],
                 speed_factor: int,
                 business_hours: Tuple[int, int],
                 objectives: Tuple[DeliveryObjective] = (
                 MaximizeDeliveryRate(), MaximizeUtilization(), MinimizeRisks())):
        """ :param number_of_variables: number of decision variables of the archive.
        """
        super(RobotScheduleAssignmentProblemVariableRobots, self).__init__(sim=sim)

        self.max_number_of_robots = max_number_of_robots

        self.number_of_variables = max_number_of_robots * 2 + 1
        self.number_of_objectives = len(objectives)
        self.number_of_constraints = 0

        self.obj_directions = [obj.direction for obj in objectives]
        self.obj_labels = [obj.label for obj in objectives]

        min_working_hours = 0 #in this way we also allow to not select this robot
        max_working_hours = business_hours[1] - business_hours[0]

        self.end_of_business = business_hours[1]

        self.speed_factor = speed_factor
        self.lower_bound = [business_hours[0], min_working_hours] * max_number_of_robots + [speed_bounds[0] * speed_factor]
        self.upper_bound = [business_hours[1] - 1, max_working_hours] * max_number_of_robots + [speed_bounds[1] * speed_factor]

    def evaluate(self, solution: FloatSolution) -> FloatSolution:
        utilization_time_period = []
        selected_num_of_robots = 0
        for i in range(len(solution.variables) // 2):
            start_time = solution.variables[i * 2]
            working_hours = solution.variables[i * 2 + 1]
            end_time = min(start_time + working_hours, self.end_of_business)
            if start_time < end_time:
                selected_num_of_robots = selected_num_of_robots + 1
                utilization_time_period.append((start_time, end_time))

        speed = solution.variables[-1]
        speed_kmh = speed / self.speed_factor

        log.getLogger().info(f"Evaluating individual with {speed_kmh} speed and"
                             f" utilization periods {' - '.join([f'({s},{e})' for s, e in utilization_time_period])}...")

        if selected_num_of_robots > 0:
            response = self.sim.run(num_robots=selected_num_of_robots,
                                    robot_speed_kmh=speed_kmh,
                                    utilization_time_period=utilization_time_period)
        else:
            response = self.sim.run_no_robots(robot_speed_kmh=speed_kmh)

        solution.objectives = [response[obj_label] for obj_label in self.obj_labels]
        log.getLogger().info(f"Objectives: {' - '.join([f'{k}:{v}' for k, v in response.items()])}")

        data_record = {'robot_speed': speed, 'robot_speed_kmh': speed_kmh,
                       'simulation_duration': self.sim.simulation_duration,
                       'generation': self.generation}

        for i, (start, end) in enumerate(utilization_time_period):
            data_record[f'robot_{i}_start'] = start
            data_record[f'robot_{i}_end'] = end
        if selected_num_of_robots < self.max_number_of_robots:
            for i in range(selected_num_of_robots, self.max_number_of_robots):
                data_record[f'robot_{i}_start'] = 0
                data_record[f'robot_{i}_end'] = 0
        data_record.update(response)
        self.records.append(data_record)

        return solution

    def fill_missing_data(self):
        log.getLogger().info(f"\n\nFill missing data\n")

        records = self.records
        self.records = []

        # Re-evaluating all the solutions (on the current number of simulations)
        for record in records:
            solution = FloatSolution(lower_bound=self.lower_bound,
                                     upper_bound=self.upper_bound,
                                     number_of_objectives=self.number_of_objectives)

            solution.variables = []
            for i in range(0, self.max_number_of_robots):
                working_hours = record[f'robot_{i}_end'] - record[f'robot_{i}_start']
                solution.variables = solution.variables + [record[f'robot_{i}_start'], working_hours]
            solution.variables = solution.variables + [record['robot_speed']]

            # The evaluation of a solution is using the memoization of the simulator
            self.evaluate(solution)

            # Overriding the generation
            self.records[-1]['generation'] = record['generation']

    def get_name(self):
        return 'RobotScheduleAssignmentProblemVariableRobots'
