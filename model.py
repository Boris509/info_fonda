from pysat.formula import * 
from pysat.solvers import *



# test variables 
T = 18
P = 10
D = {1: 2, 2 : 4, 3: 7, 4 : 10, 5 : 7, 6 : 7, 7: 9, 8: 10}
S = ["a", "r"]


v = IDPool()


class Solver:

    def __init__(self, d):
        self.cnf = CNF()
        self.D = d
        

    def create_values(self):
        for t in range(0, T) :
            # variables onle dependant on t 
            v.id(("side", t))
            v.id(("DEP", t))
            v.id(("ALL", t))

            for item in D.items():
                # pas sure
                d = item[1]
                v.id(("dur", t, item[1]) )
                v.id(("ARR", t - d))

            
            for p in  range(0, P):
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

        # dur_{t, d} = 1
        for t in range (1, T):
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
            for p in range (0, P):
                for s in S:
                    if self.D[p] == d:
                        id_dep = v.id(("dep", t, p, s))
                        found_eligible_p = True
                        clause_phi5.append(id_dep)
            
            if found_eligible_p:
                self.cnf.append(clause_phi5)

            # if boat on side A and B at time t, then all departures at time t must be from side A or side B
            for t in range(0, T):
                for p in range(0, P):
                    for item in self.D.items():
                        p, d = item
                        side_t = v.id(("side", t))
                        dur_t_d = v.id(("dur", t, d))

                        # Arrives in A
                        b_dep_t_p_retour = v.id(("dep", t, p, "r"))
                        # Arrives in B
                        a_dep_t_p_aller  = v.id(("dep", t, p, "a"))

                        if t + d <= T:
                            arr_t = v.id(("ARR", t + d))
                            side_t_d = v.id(("side", t + d))

                            A_p_t = v.id(("A", t + d, p))
                            B_p_t = v.id(("B", t + d, p))

                            # todo : revoir

                            # B_dep_t_p_retour AND dur_t_d  -> ( arr_t AND side_t_d AND A_p_t AND side_t)
                            condition = [-b_dep_t_p_retour, -dur_t_d]
                            self.cnf.append([condition + [-arr_t]])
                            self.cnf.append([condition + [side_t_d]]) # Force Side 0 (B)
                            self.cnf.append([condition + [B_p_t]])
                            self.cnf.append([condition + [side_t]])

                            combined_right_b = [arr_t, -side_t_d, A_p_t, -side_t]
                            self.cnf.append(combined_right_b + [b_dep_t_p_retour])
                            self.cnf.append(combined_right_b + [dur_t_d])

                            # A_dep_t_p_aller AND dur_t_d  -> ( arr_t AND side_t_d AND B_p_t AND side_t)
                            condition = [-a_dep_t_p_aller, -dur_t_d]
                            self.cnf.append([condition + [arr_t]])
                            self.cnf.append([condition + [side_t_d]])
                            self.cnf.append([condition + [B_p_t]])
                            self.cnf.append([condition + [-side_t]])

                            combined_right_a = [-arr_t, -side_t_d, A_p_t, side_t]
                            self.cnf.append(combined_right_a + [a_dep_t_p_aller])
                            self.cnf.append(combined_right_a + [dur_t_d])
                  


                    
              

        
        
        # A -> B                        
                    
                # with A -> B is truth when B = 0 only when A=0
        







def main():
    solver = Solver(D)
    solver.create_values()
    solver.add_constraint()

main()

