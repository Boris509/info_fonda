from pysat.formula import * 
from pysat.solvers import *


# test variables 
T = 18
P = 10
D = {1: 2, 2 : 4, 3: 7, 4 : 10, 5 : 7, 6 : 7, 7: 9, 8: 10}
S = ["a", "r"]


v = IDPool()


class Solver:

    def __init__(self):
        cnf = CNF()
        

    def create_values(self):
        for t in T :
            # variables onle dependant on t 
            v.id("side", t)
            v.id("DEP", t)
            v.id("ALL", t)

            for item in D.items():
                # pas sure
                d = item[1]
                v.id("dur", t, item[1]) 
                v.id("ARR", t - d)

            
            for p in p:
                for s in S : 
                    v.id("dep", t, p, s)
                    v.id("A", t, p)
                    v.id("B", t, p)

    def add_constraint(self):
        # DEP_{t} = 1
        self.cnf.append([v.id("DEP"), v.id("dep")])

        # ARR_{t} = 1
        self.cnf.append([v.id("ARR"), v.id("dur")])

        # ALL_{t} = 1
        self.cnf.append([v.id("ALL"), v.id("B")])

        # dur_{t, d} = 1
        self.cnf.append([-v.id("dep")])







