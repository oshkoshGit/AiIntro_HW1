from framework.graph_search import *
from framework.ways import *
from .deliveries_problem_input import DeliveriesProblemInput

from typing import Set, FrozenSet, Iterator, Tuple, Union


class RelaxedDeliveriesState(GraphProblemState):
    """
    An instance of this class represents a state of the relaxed
     deliveries problem.
    Notice that our state has "real number" field, which makes our
     states space infinite.
    """

    def __init__(self, current_location: Junction,
                 dropped_so_far: Union[Set[Junction], FrozenSet[Junction]],
                 fuel: float):
        self.current_location: Junction = current_location
        self.dropped_so_far: FrozenSet[Junction] = frozenset(dropped_so_far)
        self.fuel: float = fuel
        assert fuel > 0

    @property
    def fuel_as_int(self):
        """
        Sometimes we have to compare 2 given states. However, our state
         has a float field (fuel).
        As we know, floats comparison is an unreliable operation.
        Hence, we would like to "cluster" states within some fuel range,
         so that 2 states in the same fuel range would be counted as equal.
        """
        return int(self.fuel * 1000000)

    def __eq__(self, other):
        """
        This method is used to determine whether two given state objects represents the same state.
        Notice: Never compare floats using `==` operator! Use `fuel_as_int` instead of `fuel`.
        """
        assert isinstance(other, RelaxedDeliveriesState)
        location_equal = (self.current_location == other.current_location)
        drop_off_equal = (self.dropped_so_far == other.dropped_so_far)
        fuel_equal = self.fuel_as_int == other.fuel_as_int
        return location_equal and drop_off_equal and fuel_equal


    def __hash__(self):
        """
        This method is used to create a hash of a state.
        It is critical that two objects representing the same state would have the same hash!
        A common implementation might be something in the format of:
        >>> return hash((self.some_field1, self.some_field2, self.some_field3))
        Notice: Do NOT give float fields to `hash(...)`.
                Otherwise the upper requirement would not met.
                In our case, use `fuel_as_int`.
        """
        return hash((self.current_location, self.dropped_so_far, self.fuel_as_int))

    def __str__(self):
        """
        Used by the printing mechanism of `SearchResult`.
        """
        return str(self.current_location.index)


class RelaxedDeliveriesProblem(GraphProblem):
    """
    An instance of this class represents a relaxed deliveries problem.
    """

    name = 'RelaxedDeliveries'

    def __init__(self, problem_input: DeliveriesProblemInput):
        self.name += '({})'.format(problem_input.input_name)
        assert problem_input.start_point not in problem_input.drop_points
        initial_state = RelaxedDeliveriesState(
            problem_input.start_point, frozenset(), problem_input.gas_tank_init_fuel)
        super(RelaxedDeliveriesProblem, self).__init__(initial_state)
        self.start_point = problem_input.start_point
        self.drop_points = frozenset(problem_input.drop_points)
        self.gas_stations = frozenset(problem_input.gas_stations)
        self.gas_tank_capacity = problem_input.gas_tank_capacity
        self.possible_stop_points = self.drop_points | self.gas_stations

    def expand_state_with_costs(self, state_to_expand: GraphProblemState) -> Iterator[Tuple[GraphProblemState, float]]:
        """
        This method represents the `Succ: S -> P(S)` function of the relaxed deliveries problem.
        The `Succ` function is defined by the problem operators as shown in class.
        The relaxed problem operators are defined in the assignment instructions.
        It receives a state and iterates over the successor states.
        Notice that this is an *Iterator*. Hence it should be implemented using the `yield` keyword.
        For each successor, a pair of the successor state and the operator cost is yielded.
        """
        assert isinstance(state_to_expand, RelaxedDeliveriesState)

        for successor_state_junction in self.possible_stop_points:
            if successor_state_junction==state_to_expand.current_location:
                # Don't expand your current location
                continue

            if successor_state_junction in state_to_expand.dropped_so_far:
                # By definition, operators are not defined to drop points we already visited
                continue

            distance = state_to_expand.current_location.calc_air_distance_from(successor_state_junction)
            successor_state_fuel = state_to_expand.fuel - distance

            if successor_state_fuel < 0.0:
                # There is not enough fuel to reach the successor state - do nothing
                continue

            # Check the kind of state
            if successor_state_junction in self.drop_points:
                successor_state_dropped_points = state_to_expand.dropped_so_far.union(set([successor_state_junction]))

            else:
                # Junction is a gas station
                successor_state_fuel = self.gas_tank_capacity
                successor_state_dropped_points = state_to_expand.dropped_so_far

            successor_state = RelaxedDeliveriesState(successor_state_junction, successor_state_dropped_points,
                                                    successor_state_fuel)
            yield successor_state, distance


    def is_goal(self, state: GraphProblemState) -> bool:
        """
        This method receives a state and returns whether this state is a goal.
        """
        assert isinstance(state, RelaxedDeliveriesState)
        # Have all the ordered been delivered?
        return state.dropped_so_far == self.drop_points

    def solution_additional_str(self, result: 'SearchResult') -> str:
        """This method is used to enhance the printing method of a found solution."""
        return 'gas-stations: [' + (', '.join(
            str(state) for state in result.make_path() if state.current_location in self.gas_stations)) + ']'
