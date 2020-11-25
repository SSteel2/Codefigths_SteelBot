from codefights.model.IFighter import *
import codefights.boilerplate.SDK
import sys
from random import randint


class Action:
    A10 = "A10"
    A8 = "A08"
    A6 = "A06"
    A4 = "A04"
    A3 = "A03"
    B10 = "B10"
    B8 = "B08"
    B6 = "B06"
    B4 = "B04"
    B3 = "B03"

    @staticmethod
    def is_attack(action):
        return action[0] == 'A'

    @staticmethod
    def is_block(action):
        return action[0] == 'B'

    @staticmethod
    def get_area(action):
        if action == Action.A10:
            return Area.NOSE
        elif action == Action.A8:
            return Area.JAW
        elif action == Action.A6:
            return Area.BELLY
        elif action == Action.A4:
            return Area.GROIN
        elif action == Action.A3:
            return Area.LEGS
        elif action == Action.B10:
            return Area.NOSE
        elif action == Action.B8:
            return Area.JAW
        elif action == Action.B6:
            return Area.BELLY
        elif action == Action.B4:
            return Area.GROIN
        else:
            return Area.LEGS

    @staticmethod
    def get_attack(area):
        if area == Area.NOSE:
            return Action.A10
        elif area == Area.JAW:
            return Action.A8
        elif area == Area.BELLY:
            return Action.A6
        elif area == Area.GROIN:
            return Action.A4
        else:
            return Action.A3

    @staticmethod
    def get_block(area):
        if area == Area.NOSE:
            return Action.B10
        elif area == Area.JAW:
            return Action.B8
        elif area == Area.BELLY:
            return Action.B6
        elif area == Area.GROIN:
            return Action.B4
        else:
            return Action.B3

    @staticmethod
    def add_move(move, action):
        if action == Action.A10:
            move.add_attack(Area.NOSE)
        elif action == Action.A8:
            move.add_attack(Area.JAW)
        elif action == Action.A6:
            move.add_attack(Area.BELLY)
        elif action == Action.A4:
            move.add_attack(Area.GROIN)
        elif action == Action.A3:
            move.add_attack(Area.LEGS)
        elif action == Action.B10:
            move.add_block(Area.NOSE)
        elif action == Action.B8:
            move.add_block(Area.JAW)
        elif action == Action.B6:
            move.add_block(Area.BELLY)
        elif action == Action.B4:
            move.add_block(Area.GROIN)
        elif action == Action.B3:
            move.add_block(Area.LEGS)


class MyFighter (IFighter):
    """
    analyze your opponent's last move and make your next move
    :returns fighter's next Move
    NOTE: rules allow max 3 actions per Move.
    I.e. attack nose (1), attack groin (2) and defend nose (3).
    The areas are:
    +------------+---------+
    | Area.NOSE  | (10pts) |
    |------------+---------|
    | Area.JAW   | (8pts)  |
    |------------+---------|
    | Area.BELLY | (6pts)  |
    |------------+---------|
    | Area.GROIN | (4pts)  |
    |------------+---------|
    | Area.LEGS  | (3pts)  |
    +------------+---------+
    """
    areas = [Area.NOSE, Area.JAW, Area.BELLY, Area.GROIN, Area.LEGS]
    opponent_attacks = {}
    opponent_blocks = {}
    opponent_moves = []

    def make_next_move(self,
                       opponents_last_move=None,
                       my_last_score=0,
                       opponents_last_score=0):
        """
        You must implement make_next_move method in MyFighter class.
        Feel free to create helper classes in this file.
        """
        move = Move()

        # Initial move
        if opponents_last_move is None:
            move.add_attack(Area.NOSE)
            move.add_attack(Area.JAW)
            move.add_block(Area.NOSE)
            self.opponent_attacks = {i: 0 for i in self.areas}
            self.opponent_blocks = {i: 0 for i in self.areas}
            return move

        # Add last opponent actions to stats tracking
        for i in opponents_last_move.get_attacks():
            self.opponent_attacks[i] += 1
        for i in opponents_last_move.get_blocks():
            self.opponent_blocks[i] += 1
        self.add_opponent_moves(opponents_last_move)

        # Pattern checking
        if self.check_patterns(move):
            return move

        # Sliding windown of last moves - take into account only the last 5 moves
        last_attacks, last_blocks = self.get_last_opponent_moves(5)

        # Add attacks
        if last_blocks[Area.NOSE] + last_blocks[Area.JAW] == 0:
            move.add_attack(Area.NOSE)
            move.add_attack(Area.JAW)
        else:
            inverse_factor = self.lcm3(last_blocks[Area.NOSE] + 1,
                                       last_blocks[Area.JAW] + 1,
                                       last_blocks[Area.BELLY] + 1)
            weight_nose = inverse_factor // (last_blocks[Area.NOSE] + 1) * 10
            weight_jaw = inverse_factor // (last_blocks[Area.JAW] + 1) * 8
            weight_belly = inverse_factor // (last_blocks[Area.BELLY] + 1) * 6
            move.add_attack(self.select_area(weight_nose, weight_jaw, weight_belly))
            move.add_attack(self.select_area(weight_nose, weight_jaw, weight_belly))

        # Add block
        if last_attacks[Area.NOSE] + last_attacks[Area.JAW] == 0:
            move.add_attack(Area.NOSE)
        else:
            weight_nose = (last_attacks[Area.NOSE] + 1) * 10
            weight_jaw = (last_attacks[Area.JAW] + 1) * 8
            weight_belly = (last_attacks[Area.BELLY]) * 6
            move.add_block(self.select_area(weight_nose, weight_jaw, weight_belly))

        return move

    def get_last_opponent_moves(self, window_size):
        """Parses opponent attacks list and returns attacks and blocks aggregated values of last 'window_size' turns.
        window_size - int, how many last turns to consider.
        returns tuple(attacks, blocks)"""
        last_moves = self.opponent_moves[-window_size:]
        attacks = {i: 0 for i in self.areas}
        blocks = {i: 0 for i in self.areas}
        for i in last_moves:
            for j in i:
                if Action.is_attack(j):
                    attacks[Action.get_area(j)] += 1
                elif Action.is_block(j):
                    blocks[Action.get_area(j)] += 1
        return (attacks, blocks)

    def abuse_pattern(self, move, opponent_next_move):
        """Takes in estimated next opponent move and creates an optimal move against it.
        move - move to fill with abuse actions
        opponent_next_move - next move opponent is about to make."""
        move_list = []

        # Add blocks where attacks should be hitting
        for i in set(opponent_next_move):
            if i == Action.A10:
                move_list.append(Action.B10)
            elif i == Action.A8:
                move_list.append(Action.B8)
            elif i == Action.A6:
                move_list.append(Action.B6)
            elif i == Action.A4:
                move_list.append(Action.B4)
            elif i == Action.A3:
                move_list.append(Action.B3)

        # if opponent has 3 attacks, we don't want 3 blocks
        if len(move_list) >= 3:
            move_list = sorted(move_list)[1:]

        # Select highest attack where opponent shouldn't be blocking
        highest_unblocked_move = Action.A10
        if Action.B10 not in opponent_next_move:
            highest_unblocked_move = Action.A10
        elif Action.B8 not in opponent_next_move:
            highest_unblocked_move = Action.A8
        elif Action.B6 not in opponent_next_move:
            highest_unblocked_move = Action.A6
        else:
            highest_unblocked_move = Action.A4

        # Attack with highest attack
        remaining_moves = 3 - len(move_list)
        for i in range(remaining_moves):
            move_list.append(highest_unblocked_move)

        # Convert moves to attacks
        for i in move_list:
            Action.add_move(move, i)

    def check_pattern(self, move, ignore_first_actions):
        """Checks for single non-overlapping pattern and abuses move if pattern is found.
        move - move to fill with abuse actions if pattern found
        ignore_first_actions - number of first actions of opponent to ignore while looking for pattern.
        return True if opponent move abused."""
        for pattern_size in range(len(self.opponent_moves) - 2, 1, -1):
            for i in range(ignore_first_actions, len(self.opponent_moves) - pattern_size):
                if self.opponent_moves[i] != self.opponent_moves[i + pattern_size]:
                    break
            else:
                self.abuse_pattern(move, self.opponent_moves[-pattern_size])
                return True
        return False

    def check_patterns(self, move):
        """Checks for multiple non-overlapping pattern and abuses move if any pattern is found.
        move - move to fill with abuse actions if pattern found
        return True if opponent move abused."""
        if len(self.opponent_moves) < 6:
            return False

        return self.check_pattern(move, 0) or self.check_pattern(move, 1)

    def add_opponent_moves(self, opponents_last_move):
        """Adds opponent's last move to memory."""
        actions = []
        for i in opponents_last_move.get_attacks():
            actions.append(Action.get_attack(i))
        for i in opponents_last_move.get_blocks():
            actions.append(Action.get_block(i))
        self.opponent_moves.append(tuple(sorted(actions)))

    def select_area(self, weight_a, weight_b, weight_c):
        """Selects area randomly from NOSE, JAW and BELLY based on weights."""
        weight_sum = weight_a + weight_b + weight_c
        random = randint(1, weight_sum)
        if random <= weight_a:
            return Area.NOSE
        if random > weight_a and random <= weight_a + weight_b:
            return Area.JAW
        else:
            return Area.BELLY

    def gcd(self, a, b):
        """Returns greatest common divider out of 2 numbers"""
        if a < b:
            a, b = b, a
        if a == b:
            return a
        return self.gcd(a - b, b)

    def lcm(self, a, b):
        """Returns least common multiple out of 2 numbers"""
        return a * b // self.gcd(a, b)

    def lcm3(self, a, b, c):
        """Returns least common multiple out of 3 numbers"""
        return self.lcm(self.lcm(a, b), c)


# DO NOT EDIT THE LINES BELOW!
if __name__ == '__main__':
    codefights.boilerplate.SDK.SDK.run(MyFighter, sys.argv)
