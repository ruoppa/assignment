from collections import Counter
from datetime import datetime, timedelta
from typing import List
from matplotlib import use

import pandas as pd

from config import TABLE_COLUMNS
from user import UnmotivatedUser, InactiveUser, LearningUser, SavvyUser, User


class Organization:
    """Class for a hypothetical customer organization."""

    def __init__(self, n_users: int, n_simulations: int, training_interval_days: int) -> None:
        """Init the object."""
        self.n_users = n_users
        self.n_simulations = n_simulations
        self.training_interval_days = training_interval_days
        self.users = self._populate_organization()
        assert all(
            issubclass(type(user), User) for user in self.users
        ), "Please create your users as subclasses of the abstract User class."

    def _populate_organization(self) -> List:
        users = []
        # Approximate distribution of user types:
        #  3%:  Inactive
        r1 = self.n_users * 3 // 100
        for i in range(r1):
            users.append(InactiveUser())

        # 15%:  Unmotivated
        r2 = self.n_users * 15 // 100
        for i in range(r2):
            users.append(UnmotivatedUser())

        # 10%:  Savvy
        r3 = self.n_users * 10 // 100
        for i in range(r3):
            users.append(SavvyUser())

        # 72%:  Learning
        r4 = self.n_users - (r1 + r2 + r3)
        for i in range(r4):
            users.append(LearningUser())

        return users

    def do_training(self) -> None:
        """Train organization with Hoxhunt simulations."""
        for i in range(self.n_simulations):
            timestamp = datetime.now() + timedelta(days=self.training_interval_days * i)
            for user in self.users:
                user.complete_simulation(timestamp=timestamp)

    def get_result(self) -> pd.DataFrame:
        """Fetch the results of training."""
        org_history = []
        for user in self.users:
            org_history += user.history
        return pd.DataFrame(org_history, columns=TABLE_COLUMNS)

    def __repr__(self) -> str:
        """Update the representation of a class object."""
        user_names = [user.name for user in self.users]
        name, amount = Counter(user_names).most_common(1)[0]
        return (
            f"Organization(n_users={self.n_users}, n_simulations={self.n_simulations}, "
            f"training_interval_days={self.training_interval_days}, "
            f"random_fact=The most common name in your organization is {name}, "
            f"there are {amount} of them... I wonder who's the best performer 🤔)"
        )
