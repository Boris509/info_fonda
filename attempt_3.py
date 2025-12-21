from pysat.formula import * 
from pysat.solvers import *
from pysat.card import *
import itertools
from view import export_model_to_csv


from typing import Dict, Iterable, List, Optional, Tuple


class FormulaBuilderSkeleton:
    def __init__(self, speed, durations: Dict[int, int], capacity: int = 2, T: int = 18, P: int = 4,
                    S: Iterable[str] = ("a", "r")):
        self.durations = durations
        self.capacity = capacity
        self.speed = speed
        self.T = T
        self.P = len(durations)
        self.S = tuple(S)

        self.cnf = CNF()
        self.v = IDPool()
    
    def add_clause(self, clause: List[int]) -> None:
        assert isinstance(clause, list)
        self.cnf.append(clause)
        
    def build_cnf(self) -> None:
        self.defines_DEP()
        self.defines_ARR()
        self.defines_ALL()
        self.duration_constraint()
        self.add_arrival_constraints()
        self.add_alternating_constraints()
        self.add_location_constraints()
        self.add_initial_state()
        self.add_capacity_constraints()
        self.add_departure_duration_link()
        # todo :
        #self.add_capacity_constriants()

    def defines_DEP(self):
            """
            Defines the master variable DEP_t.
            Logic: DEP_t <-> (Person1_Departs OR Person2_Departs OR ...)
            Meaning: The boat leaves at time t if and only if at least one person is on it.
            """
            for t in range(1, self.T + 1):
                DEP_t = self.v.id(("DEP", t))
                
                # Collect all individual departures (Aller + Retour) for this time step
                all_person_deps = []
                for p in range(1, self.P + 1):
                    # Did person P leave A -> B?
                    dep_a = self.v.id(("dep", t, p, "a"))
                    # Did person P leave B -> A?
                    dep_r = self.v.id(("dep", t, p, "r"))
                    
                    all_person_deps.append(dep_a)
                    all_person_deps.append(dep_r)

                for dep in all_person_deps:
                    self.cnf.append([-dep, DEP_t])

                self.cnf.append([-DEP_t] + all_person_deps)

    def defines_ARR(self):
        for t_arr in range(1, self.T + 1):
            arr_var = self.v.id(("ARR", t_arr))
            possible_trips = []
            print(self.durations)
            for item in self.durations.items():
                d=item[1]
                start_time = t_arr - d
                if start_time >= 0:
                    dur_var = self.v.id(("dur", start_time, d))
                    possible_trips.append(dur_var)
            
            for trip in possible_trips:
                self.cnf.append([-trip, arr_var])
                
            if possible_trips:
                self.cnf.append([-arr_var] + possible_trips)
            else:
                self.cnf.append([-arr_var])

    def defines_ALL(self):
        goal_constraint = []
        for t in range(1, self.T + 1):
            ALL_t = self.v.id(("ALL", t))
            chickens_in_B = []
            for p in range(1, self.P + 1):
                B_pt = self.v.id(("B", p, t))
                chickens_in_B.append(B_pt)
            self.add_implication_constraints(chickens_in_B, [ALL_t])
            self.add_implication_constraints([ALL_t], chickens_in_B)

            # goal constraint :
            goal_constraint.append(ALL_t)

        self.cnf.append(goal_constraint)

    def add_initial_state(self) -> None:
        side0 = self.v.id(("side", 0))
        self.add_clause([side0])
        for p in range(1, self.P + 1):
            self.add_clause([self.v.id(("A", p, 0))])
            self.add_clause([-self.v.id(("B", p, 0))])

            for s in self.S:
                self.add_clause([-self.v.id(("dep", 0, p, s))])
            arr_0 = self.v.id(("ARR", p, 0))
            self.cnf.append([-arr_0])

    def add_implication_constraints(self, left, right ):
        """
        Encodes: (AND left) -> (AND right)
        left  : iterable of literals
        right : iterable of literals
        """
        left = list(left)
        right = list(right)

        for r in right:
            self.cnf.append([-lit for lit in left] + [r])

    def duration_constraint(self):

        for t in range(1, self.T+1):
            for item in self.durations.items():
                d = item[1]
                dur_t_d = self.v.id(("dur", t, d))
                allowed_trips = []
                forbidden_trips = []

                for p, T_p in self.durations.items():
                    if T_p > d:
                        for s in self.S:
                            forbidden_trips.append(-self.v.id(("dep", t, p, s)))

                    if T_p == d:
                        for s in self.S:
                            allowed_trips.append(self.v.id(("dep", t, p, s)))

                self.add_implication_constraints([dur_t_d], forbidden_trips)
                if allowed_trips:
                    self.cnf.append([-dur_t_d]+ allowed_trips)
                else : 
                    self.cnf.append([-dur_t_d])

    def add_arrival_constraints(self):
        for t in range(1, self.T +1):
            for T_p in self.speed:
                if t + T_p > self.T:
                    continue
                for p in range(1, self.P+1):
                    dep_t_p_a = self.v.id(("dep", t, p, 'a'))
                    dep_t_p_r = self.v.id(("dep", t, p, 'r'))
                    dur_t_d = self.v.id(("dur", t, T_p))

                    B_p_t_future = self.v.id(("B", p, t + T_p))
                    A_p_t_future = self.v.id(("A", p, t + T_p))

                    self.cnf.append([-dep_t_p_a, -dur_t_d, B_p_t_future])
                    self.cnf.append([-dep_t_p_r, -dur_t_d, A_p_t_future])

    def add_alternating_constraints(self):
        for t in range(1, self.T +1):
            side_t = self.v.id(("side", t))
            for p in range(1, self.P+1):
                    dep_t_p_a = self.v.id(("dep", t, p, 'a'))
                    dep_t_p_r = self.v.id(("dep", t, p, 'r'))

                    self.cnf.append([-dep_t_p_a, side_t])
                    self.cnf.append([-dep_t_p_r, -side_t])


            for T_p in self.speed:
                if t + T_p > self.T:
                    continue
                side_t_future = self.v.id(("side", t + T_p))
                dur_t_d = self.v.id(("dur", t, T_p))

                for p in range(1, self.P+1):
                    dep_t_p_a = self.v.id(("dep", t, p, 'a'))
                    dep_t_p_r = self.v.id(("dep", t, p, 'r'))

                    
                    self.cnf.append([-dep_t_p_a, -dur_t_d, -side_t_future])
                    self.cnf.append([-dep_t_p_r, -dur_t_d, side_t_future])

    def add_location_constraints(self):
        for t in range(0, self.T):
            for p in range(1, self.P + 1):
                b_curr = self.v.id(("B", p, t))
                b_next = self.v.id(("B", p, t+1))
                a_curr = self.v.id(("A", p, t))

                # Clause 1: -A OR -B (Cannot be at both)
                #self.cnf.append([-a_curr, -b_curr])
                # Clause 2: A OR B (Must be at one)
                #self.cnf.append([a_curr, b_curr])

                
                arriving_trips = []
                for d in self.speed:
                    start = t + 1 - d
                    if start >= 0:
                        dep_a = self.v.id(("dep", start, p, 'a'))
                        dep_r = self.v.id(("dep", start, p, 'r'))
                        arriving_trips.append(dep_a)
                        arriving_trips.append(dep_r)

                self.cnf.append([-b_curr, b_next] + arriving_trips)
                self.cnf.append([b_curr, -b_next] + arriving_trips)
    
    def add_capacity_constraints(self):
        for t in range(self.T):
            chicken_trips = []

            for p in range(1, self.P+1):
                for s in self.S:
                    dep_t_p = self.v.id(("dep", t, p, s))
                    chicken_trips.append(dep_t_p)
            cnf_atmost = CardEnc.atmost(
                    lits=chicken_trips,
                    bound=2,
                    vpool=self.v,
                    encoding=EncType.seqcounter
                )
            self.cnf.extend(cnf_atmost.clauses)
   

    def add_departure_duration_link(self):
        """
        Forces the solver to pick a duration if anyone departs.
        Logic: (dep_1 OR dep_2 ...) -> (dur_1 OR dur_2 ...)
        """
        for t in range(1, self.T + 1):
            
            # 1. Collect all departure variables at time t
            all_deps = []
            for p in range(1, self.P + 1):
                all_deps.append(self.v.id(("dep", t, p, 'a')))
                all_deps.append(self.v.id(("dep", t, p, 'r')))
            
            # 2. Collect all valid duration variables at time t
            valid_durs = []
            unique_speeds = set(self.durations.values())
            for d in unique_speeds:
                if t + d <= self.T:
                    valid_durs.append(self.v.id(("dur", t, d)))
            
            # 3. Add the Linkage Constraint
            # If any departure is True, at least one duration MUST be True.
            # CNF: -dep_i OR (dur_val_1 OR dur_val_2 ...)
            
            if valid_durs:
                for dep in all_deps:
                    self.cnf.append([-dep] + valid_durs)
            else:
                # If no durations are valid (e.g. near end of T), NO ONE can depart.
                for dep in all_deps:
                    self.cnf.append([-dep])




def print_model(model):
    departures = {}

    for key, value in model.items():
        #if value: 
        #if key[0] == 'dur' or key[0] == "dep":
        print(key, value)

    print(departures)

def check_satisfiability(cnf, v):
    # Using 'g3' (Glucose 3) as the solver
    with Solver(name='g3', bootstrap_with=cnf) as s:
        is_satisfiable = s.solve()
        if is_satisfiable:
            model = s.get_model()
            # Map integers back to variable names for readability
            readable_model = {v.obj(abs(lit)): (lit > 0) for lit in model}
            return True, readable_model
        else:
            return False, None
if __name__ == "__main__":
    durations = {1: 1, 2: 3, 3: 6, 4: 8}
    speed = [1,3,6,8]
    fb = FormulaBuilderSkeleton(speed=speed, durations=durations, capacity=2, T=18, P=3)
    fb.build_cnf()
    satisfiable, model = check_satisfiability(fb.cnf, fb.v)
    if satisfiable:
        print("The formula is satisfiable.")
        print("A satisfying assignment is:")
        print_model(model)
        export_model_to_csv(model=model, T=18, N=4, filename="test" )
    else:
        print("The formula is not satisfiable.")
