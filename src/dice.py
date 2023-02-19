from typing import List, Dict
import random


def calc_roll_value(t: int, a: int, b: int) -> int:
    """Calcuates roll value of 3 SI baseball dice

    Args:
        t: roll value of the "tens" black die
        a: roll value of the first "ones" die
        b: roll value of the second "ones" die

    Returns:
        Total roll value of the 3 dice
    """
    return (10 * t) + a + b


class Die:

    def __init__(self, sides: List[int]):

        self.n_sides = len(sides)
        self.sides = sides

    def roll(self) -> int:

        return random.choice(self.sides)


def get_roll_value_probs() -> Dict[int, float]:
    """Defines a map of possible roll values to their respective probabilities

    Returns:
        Dict mapping roll value to probability
    """

    tens_die_sides = [1, 2, 2, 3, 3, 3]
    small_ones_die_sides = [0, 0, 1, 2, 3, 4]
    large_ones_die_sides = [0, 1, 2, 3, 4, 5]

    microstates = [
        calc_roll_value(t, a, b)
        for t in tens_die_sides
        for a in small_ones_die_sides
        for b in large_ones_die_sides
    ]
    macrostates = sorted(list(set(microstates)))

    roll_value_prob_map = {
        mac: len([mic for mic in microstates if mic == mac]) / len(microstates)
        for mac in macrostates
    }

    return roll_value_prob_map
