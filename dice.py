from dataclasses import dataclass   
import random

@dataclass
class Die:
    
    def roll(self):
        ''' Returns a random integer between 1 and 6 '''
        return random.randint(1, 6)
    
@dataclass
class DieSet:
    die1: Die
    die2: Die
    
    def roll_twice(self):
        ''' Returns a list of the two rolls and the sum of the two rolls '''
        roll1 = self.die1.roll()
        roll2 = self.die2.roll()
        return [roll1, roll2, roll1 + roll2]
    
    def roll_and_check_doubles(self):
        ''' Returns a tuple of (die1, die2, sum, is_doubles) '''
        roll1 = self.die1.roll()
        roll2 = self.die2.roll()
        is_doubles = roll1 == roll2
        return (roll1, roll2, roll1 + roll2, is_doubles)
