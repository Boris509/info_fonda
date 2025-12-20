from pysat.formula import * 
from pysat.solvers import *
from pysat.card import *



# test variables 
Time = 18
Poule = 10
D = {1: 2, 2 : 4, 3: 7, 4 : 10, 5 : 7, 6 : 7, 7: 9, 8: 10}
S = ["a", "r"]


v = IDPool()


class Solver:

    def __init__(self, durations=D, capacity=3, T=Time, P=Poule, S=S):
        self.cnf = CNF()
        self.D = durations
        self.capacity = capacity
        self.T = T
        self.P = P
        self.S = S

    def create_values(self):
        for t in range(0, self.T) :
            # variables onle dependant on t 
            v.id(("side", t))
            v.id(("DEP", t))
            v.id(("ALL", t))

            for item in self.D.items():
                # pas sure
                d = item[1]
                v.id(("dur", t, item[1]) )
                v.id(("ARR", t - d))

            for p in range(0, self.P):
                for s in S : 
                    v.id(("dep", t, p, s))
                    v.id(("A", t, p))
                    v.id(("B", t, p))

    def add_constraint(self):
        # DEP_{t} = 1
        self.cnf.append([v.id("DEP"), v.id("dep")])

        # ARR_{t} = 1
        self.cnf.append([v.id("ARR"), v.id("dur")])

        # ALL_{t} = 1
        self.cnf.append([v.id("ALL"), v.id("B")])
        
        # Capacity constraint
        card = CardEnc.atmost(lits=[self.v.id(("dep", t, p, s))
                                        for t in range(self.T) for p in range(self.P) for s in self.S], 
                                        bound=self.capacity, vpool=self.v, encoding=EncType.totalizer)
        
        self.cnf.extend(card.clauses)

        self.add_arrival_constraints()
        self.add_duration_constraint()


    def add_arrival_constraints(self):

         # if boat on side A and B at time t, then all departures at time t must be from side A or side B
        for t in range(0, self.T):
            for p in range(0, self.P):
                for item in self.D.items():
                    p, d = item
                    # Starting point
                    side_t = v.id(("side", t))

                    # Trip duration
                    dur_t_d = v.id(("dur", t, d))

                    # Leaves from B
                    b_dep_t_p_retour = v.id(("dep", t, p, "r"))
                    # Leaves from A
                    a_dep_t_p_aller  = v.id(("dep", t, p, "a"))

                    # check if arrival time is within bounds
                    if t + d <= self.T:
                        # the must an arrival at time t + d
                        arr_t = v.id(("ARR", t + d))
                        # Boat must be on this side at time t + d
                        side_t_d = v.id(("side", t + d))

                        # Side must contain chickens at time t + d
                        A_p_t = v.id(("A", t + d, p))
                        B_p_t = v.id(("B", t + d, p))

                        # Adding constraints :
                        # Leaving from B to A
                        # B_dep_t_p_retour AND dur_t_d  -> ( arr_t AND side_t_d AND A_p_t AND -side_t)
                        condition = [-b_dep_t_p_retour, -dur_t_d]
                        implied = [arr_t, side_t_d, A_p_t, -side_t]
                        self.add_implication_constraints(condition, implied)

                        condition = [-arr_t, -side_t_d, B_p_t, side_t]
                        implied = [b_dep_t_p_retour, dur_t_d]
                        self.add_implication_constraints(condition, implied)
                        
                        # Leaving from A to B
                        # A_dep_t_p_aller AND dur_t_d  -> ( arr_t AND -side_t_d AND B_p_t AND side_t)
                        condition = [-a_dep_t_p_aller, -dur_t_d]
                        implied = [arr_t, -side_t_d, B_p_t, side_t]
                        self.add_implication_constraints(condition, implied)
        

                        condition = [-arr_t, side_t_d, A_p_t, -side_t]
                        implied = [a_dep_t_p_aller, dur_t_d]
                        self.add_implication_constraints(condition, implied)
            

    def add_implication_constraints(self, left, right):
        """
        Encodes: (AND left) -> (AND right)
        left  : iterable of literals
        right : iterable of literals
        """
        left = list(left)
        right = list(right)

        for r in right:
            self.cnf.append([-lit for lit in left] + [r])


    def add_duration_constraint(self):
          # dur_{t, d} = 1
        for t in range (1, self.T):
            # add every T_{p} <= d
            for item in self.D.items():
                p, d = item
                id_dur = v.id(("dur", t, d))
                for item in self.D.items() : 
                    p_, d_  = item
                    if self.D[p_] > d:
                        continue
                    else: 
                        for s in range(len(S)):
                            v.id(("dep", t, p, s))
                            self.cnf.append([id_dur, -v.id("dur")])

            # at least one dep_{t, p, s} = 1
            clause_phi5 = [-id_dur]
            found_eligible_p = False
            for p in range (0, self.P):
                for s in self.S:
                    if self.D[p] == d:
                        id_dep = v.id(("dep", t, p, s))
                        found_eligible_p = True
                        clause_phi5.append(id_dep)
            
            if found_eligible_p:
                self.cnf.append(clause_phi5)






def main():
    solver = Solver(D)
    solver.create_values()
    solver.add_constraint()

main()

