import random
import math
from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from black import out

import names

from simulation import SIMULATION_OUTCOMES, SimulationResult


class User(metaclass=ABCMeta):
    """The abstract baseclass for a user, please don't use this directly.

    Create your own subclass(es) with a '_get_simulation_outcome' private method.

    DummyUser is an example of how to do this.
    """

    
    # Added parameters success, miss and fail, which represent the
    # probability of each of the three possible outcomes of a simulation. 
    # Each user type has their own initial values for these parameters.
    # Each parameter has accuracy of 3 decimals and their sum is always 1.
    def __init__(self, success: float, miss: float, fail: float, type: str = "Base") -> None:
        """Init the object."""
        self.id: str = uuid4().hex
        self.type: str = type
        self.name: str = names.get_first_name()
        self.history: List[Optional[SimulationResult]] = []
        self.success: float = success
        self.miss: float = miss
        self.fail: float = fail
        

    @abstractmethod
    def _get_simulation_outcome() -> str:
        """Implement this method in your own subclass.

        It should always return one of the possible SIMULATION_OUTCOMES
        """
        pass

    # Most User classes determine the outcome the same way, i.e. 
    # randomly, with each outcome having a probability given by
    # the parameter of the same name. _get_simulation_outcome()
    # uses this function to determine the outcome, then acts
    # according to the logic of the class based on the outcome
    def _outcome_helper(self) -> str:
        c = round(random.uniform(0, 1), 3)
        if c < self.success:
            return "SUCCESS"
        elif c < self.success + self.fail:
            return "FAIL"
        else:
            return "MISS"

    def complete_simulation(self, timestamp: datetime) -> None:
        """Complete a simulation and store it in the user's history."""
        outcome = self._get_simulation_outcome()
        assert (
            outcome in SIMULATION_OUTCOMES
        ), "The outcome from your logic is not a valid simulation outcome."

        self.history.append(
            SimulationResult(
                timestamp=datetime.strftime(timestamp, "%Y-%m-%d %H:%M:%S"),
                user_id=self.id,
                type=self.type,
                name=self.name,
                outcome=outcome,
            )
        )

    @property
    def simulations_completed(self) -> int:
        """Return amount of simulations user has completed."""
        return len(self.history)

    def __repr__(self) -> str:
        """Update the representation of a class object."""
        return (
            f"User(id={self.id}, name={self.name}, type={self.type}, "
            f"success={self.success}, miss={self.miss}, fail={self.fail}, "
            f"simulations_completed={self.simulations_completed})"
        )

# Represents an user, who is disinterested and does not want to learn,
# because they deem it useless. As such, the outcome of a simulation
# will almost always be a miss with a small  chance of failing and initial
# success probability of 0. Failing will momentarily increase the users
# interest and success rate. Fail rate remains constant
class UnmotivatedUser(User):

    def __init__(self) -> None:
        # Random initial fail rate between 5-15% from uniform distribution
        init_fail = round(random.uniform(0.05, 0.15), 3)
        init_miss = round(1 - init_fail, 3)
        super(UnmotivatedUser, self).__init__(success = 0, miss = init_miss, fail = init_fail, type = "Unmotivated")

    def _get_simulation_outcome(self) -> str:
        outcome = self._outcome_helper()
        # If outcome is fail, success rate rises to ~0.2 * miss rate
        if outcome == "FAIL":
            self.success = round(self.miss * 0.2, 3)
            self.miss = round(1 - self.success - self.fail, 3)
        # Success rate decays fast linearly with each success
        elif outcome == "SUCCESS":
            self.success = max(self.success - 0.04, 0)
            self.miss = round(1 - self.success - self.fail, 3)
        return outcome

# Inactive user that e.g. is no longer with the organization, but
# has not been removed from the database for some reason. Miss
# rate of 100%. (Just some simulated noise to the data)
class InactiveUser(User):

    def __init__(self) -> None:
        super(InactiveUser, self).__init__(success = 0, miss = 1, fail = 0, type = "Inactive")

    def _get_simulation_outcome(self) -> str:
        # Outcome is always a miss
        return "MISS"

# Represents the average user who is willing to improve and learn.
# Starts with some somewhat randomized numbers for fail, miss and success.
# User will "learn" from each miss and fail, which decreases the probability
# of both, with the latter having a stronger effect than the former. Effect of
# learning slows down as the success rate grows larger.
class LearningUser(User):

    def __init__(self) -> None:
        # Amount of learning done by the user
        self.knowledge = 0

        init_miss = 2
        # Determine initial miss rate with the help of a normal
        # distribution, with expected value 0.6, standard deviation 0.15
        while init_miss > 0.8 or init_miss < 0.1:
            init_miss = round(random.gauss(0.6, 0.15), 3)
        
        # Initial fail rate between 5-20%
        init_fail = round(random.uniform(0.05, 0.20), 3)
        # Rest are successes
        init_success = round(1 - init_miss - init_fail, 3)
        super(LearningUser, self).__init__(success = init_success, miss = init_miss, fail = init_fail, type = "Learning")

    def _get_simulation_outcome(self) -> str:
        # Possible amount of learning depends on the amount of learning
        # so far
        outcome = self._outcome_helper()
        # If outcome is fail or miss, learning happens
        if outcome == "FAIL" or outcome == "MISS":
            # If outcome is miss, less learning
            multiplier = 1 if outcome == "FAIL" else 0.6
            # Learning slows down as knowledge is accumulated
            learning = multiplier * (0.01 - min(self.knowledge * 0.00001, 0.009)) 
            # The effect of learning is stronger on missing
            self.miss = round(max(self.miss - 2 * learning, 0), 3)
            self.fail = round(max(self.fail - learning, 0), 3)
            self.success = round(1 - self.miss - self.fail, 3)
            # Knowledge increases with each learning experience
            self.knowledge += 1

        return outcome

# Tech-savvy user, with very low fail rate and an initial miss rate
# between 5-30%, to account for more and less interested tech-savvy
# users. Failing will increase the success rate momentarily.
class SavvyUser(User):

    def __init__(self) -> None:
        init_miss = round(random.uniform(0.05, 0.30), 3)
        # Fail rate between 0 and 1/6 of miss rate
        init_fail = round(random.uniform(0, init_miss / 6), 3)
        init_success = round(1 - init_fail - init_miss, 3)
        # Parameter to store normal rates
        self.init_success = init_success
        self.init_fail = init_fail
        self.init_miss = init_miss
        super(SavvyUser, self).__init__(success = init_success, miss = init_miss, fail = init_fail, type = "Savvy")

    def _get_simulation_outcome(self) -> str:
        outcome = self._outcome_helper()
        # If outcome is a fail, success rises, miss and fail rates decrease
        # momentarily
        if outcome == "FAIL":
            self.success += round((self.miss / 2 + self.fail / 2), 3)
            self.miss = round(self.miss / 2, 3)
            self.fail = round(1 - self.success - self.miss, 3)
        # Raised success rate decays back to normal linearly
        elif self.init_success < self.success:
            self.success = max(self.success - 0.02, self.init_success)
            # If success rate is back to normal, restore miss and fail rates
            if self.success == self.init_success:
                self.miss = self.init_miss
                self.fail = self.init_fail
            else:
                self.miss = round(self.miss + 0.01, 3)
                self.fail = round(1 - self.miss - self.success, 3)

        return outcome