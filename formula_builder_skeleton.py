from pysat.formula import * 
from pysat.solvers import *
from pysat.card import *
import itertools



from typing import Dict, Iterable, List, Optional, Tuple


class FormulaBuilderSkeleton:
    def __init__(self, durations: Dict[int, int], capacity: int = 2, T: int = 18, P: int = 4,
                    S: Iterable[str] = ("a", "r")):
        self.durations = durations
        self.capacity = capacity
        self.T = T
        self.P = len(durations)
        self.S = tuple(S)

        self.cnf = CNF()
        self.v = IDPool()

    def add_clause(self, clause: List[int]) -> None:
        assert isinstance(clause, list)
        self.cnf.append(clause)

    def build_cnf(self) -> None:

        self.add_initial_state()
        self.add_goal_constraint()
        #
        #self.define_DEP()
        self.ARR()
        self.defines_DEP()
        self.defines_ALL()
        self.add_no_teleport_to_B()

        
        #self.add_backward_B_explanation()
        #self.add_deployment_constraints()
        #self.add_dep_constraints()
        #self.add_arrival_constraints()
        #self.add_capacity_constraint()

        #self.add_frame_constraints
        self.add_duration_constraint()
    def ARR(self):
        for t in range(1, self.T + 1):            
            for p, d in self.durations.items():
                if t + d > self.T:
                    continue
                
                dur_t_d = self.v.id(("dur", t, d))
                dep_t = self.v.id(("dep", t, p, "a")) 
                ARR_target = self.v.id(("ARR", p, t + d))
                
                self.add_implication_constraints([dep_t, dur_t_d], [ARR_target])               

    def add_no_teleport_to_B(self):
        """
        Constraint: B cannot be true unless there was a previous state of B 
        OR a trip 'aller' that just finished.
        """
        for t in range(1, self.T + 1):
            for p, d in self.durations.items():
                
                # 1. Variables
                b_current = self.v.id(("B", p, t))   # At B now
                b_prev    = self.v.id(("B", p, t-1)) # Was at B before
                
                # 2. Identify the specific Departure from A that arrives NOW
                # We arrived at 't', so we must have left at 't - d'
                dep_time = t - d
                trip_aller = None
                
                if dep_time >= 1:
                    # Variable for "Departed from A at valid time"
                    trip_aller = self.v.id(("dep", dep_time, p, "a"))
                
                # 3. Build the Constraint
                # Logic: -B_current OR B_prev OR Trip_Aller
                
                clause = [-b_current, b_prev]
                
                if trip_aller:
                    clause.append(trip_aller)
                
                self.cnf.append(clause)
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


    def defines_ALL(self):
        for t in range(1, self.T + 1):
            ALL_t = self.v.id(("ALL", t))
            chickens_in_B = []
            for p in range(1, self.P + 1):
                B_pt = self.v.id(("B", p, t))
                chickens_in_B.append(B_pt)
            self.add_implication_constraints(chickens_in_B, [ALL_t])
            self.add_implication_constraints([ALL_t], chickens_in_B)

 
    def add_dep_constraints(self):
        """
        Constrains the 'dep' variables:
        1. Preconditions (Location)
        2. Mutual Exclusion
        3. Boat Capacity (At Most K)
        """
        for t in range(1, self.T + 1):
            
            # --- Lists to store all departures at this time step ---
            all_deps_aller = [] # Departures A -> B
            all_deps_retour = [] # Departures B -> A

            for p in range(self.P):
                # Get variables
                dep_a = self.v.id(("dep", t, p, "a"))
                dep_r = self.v.id(("dep", t, p, "r"))
                b_loc = self.v.id(("B", p, t)) # True if at B, False if at A
                
                all_deps_aller.append(dep_a)
                all_deps_retour.append(dep_r)

                # --- 1. MUTUAL EXCLUSION ---
                # A person cannot depart A->B and B->A at the same time
                # Clause: (-dep_a OR -dep_r)
                self.cnf.append([-dep_a, -dep_r])

                # --- 2. LOCATION PRECONDITIONS ---
                
                # Rule: If departing A->B, Person MUST be at A (Not B)
                # Logic: dep_a -> NOT(B_loc)
                # Clause: -dep_a OR -b_loc
                self.cnf.append([-dep_a, -b_loc])

                # Rule: If departing B->A, Person MUST be at B
                # Logic: dep_r -> B_loc
                # Clause: -dep_r OR b_loc
                self.cnf.append([-dep_r, b_loc])

            # --- 4. OPTIONAL: BOAT CANNOT MOVE EMPTY ---
            # If you want to force the boat to have a driver:
            # If the Boat moves (Side changes), at least one person must depart.
            # This is complex to add here, usually handled by "Arrival" logic 
            # implying a departure.
    
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

    def add_frame_constraints(self):
        """
        Ensures objects stay where they are unless moved.
        Logic: B_{t+1} <-> ( (B_t AND NOT Dep_from_B_at_t) OR Arriving_at_B_at_t+1 )
        """
        # Iterate from time 0 up to T-1 (predicting the next state)
        for t in range(self.T):
            for p, d in self.durations.items():
                
                # --- 1. Identify Variables ---
                b_curr = self.v.id(("B", p, t))
                b_next = self.v.id(("B", p, t+1))
                
                # Departure from B at time t (Moves B -> A)
                # Note: Check if t is a valid departure time in your model (e.g. starts at 1)
                if t >= 1: 
                    dep_from_b = self.v.id(("dep", t, p, "r"))
                else:
                    # No departures allowed at t=0 (if your actions start at 1)
                    dep_from_b = None 

                # Arrival at B at time t+1 (Moves A -> B)
                # This is caused by a departure from A at time: (t + 1) - d
                dep_time_a = (t + 1) - d
                if dep_time_a >= 1:
                    arriving_at_b = self.v.id(("dep", dep_time_a, p, "a"))
                else:
                    # Impossible to arrive if duration hasn't passed
                    arriving_at_b = None

                # --- 2. Build the Logic Clauses ---
                
                # CASE 1: If Arriving -> B_next is True
                if arriving_at_b:
                    # Clause: -Arriving v B_next
                    self.cnf.append([-arriving_at_b, b_next])

                # CASE 2: If Staying (At B, Not Leaving) -> B_next is True
                # Logic: (B_curr AND -Dep_B) -> B_next
                # Clause: -B_curr v Dep_B v B_next
                if dep_from_b:
                    self.cnf.append([-b_curr, dep_from_b, b_next])
                else:
                    # If can't depart, staying just means (B_curr -> B_next)
                    self.cnf.append([-b_curr, b_next])

                # CASE 3: The Reverse (B_next -> Arriving OR Staying)
                # If I am at B at t+1, I must have either Just Arrived OR Stayed.
                # Logic: B_next -> (Arriving v (B_curr ^ -Dep_B))
                # Distributes to two clauses:
                # 1. -B_next v Arriving v B_curr
                # 2. -B_next v Arriving v -Dep_B
                
                # Prepare literals (handle None values for edge cases)
                lit_arr   = [arriving_at_b] if arriving_at_b else []
                lit_dep_b = [-dep_from_b]   if dep_from_b else [] # Note negative sign logic below
                
                # Clause 3a: -B_next v Arriving v B_curr
                self.cnf.append([-b_next] + lit_arr + [b_curr])
                
                # Clause 3b: -B_next v Arriving v NOT(Dep_B)
                # If dep_from_b is None, this clause isn't needed (can't leave)
                if dep_from_b:
                    # We want 'NOT Dep_B' in the OR list, so we append -dep_from_b
                    self.cnf.append([-b_next] + lit_arr + [-dep_from_b])

    def add_capacity_constraint(self) -> None:
        for t in range(1, self.T):
            a_lits = [self.v.id(("dep", t, p, "a")) for p in range(self.P)]
            b_lits = [self.v.id(("dep", t, p, "r")) for p in range(self.P)]
            all_lits = a_lits + b_lits

            # capacity: at most self.capacity departures (a or r) at time t
            if all_lits:
                cnf_atmost = CardEnc.atmost(
                    lits=all_lits,
                    bound=self.capacity,
                    vpool=self.v,
                    encoding=EncType.totalizer
                )
                self.cnf.extend(cnf_atmost.clauses)

            # optional: at least 2 'a' if possible
            if len(a_lits) >= 2:
                cnf_atleast_a = CardEnc.atleast(
                    lits=a_lits,
                    bound=2,
                    vpool=self.v,
                    encoding=EncType.totalizer
                )
                self.cnf.extend(cnf_atleast_a.clauses)

    def add_deployment_constraints(self) -> None:
        for t in range(self.T):
            lits = [self.v.id(("dep", t, p, s)) for p in range(self.P) for s in self.S]
            if lits:
                self.add_clause(lits)

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


    def add_goal_constraint(self):
        possible_win_times = []
        for t in range(1, self.T +1) : 
            ALL_t = self.v.id(("ALL", t))
            possible_win_times.append(ALL_t)

        self.cnf.append(possible_win_times)

    def AnotB(self):
        for t in range(self.T):
            for p in range(self.P):
                self.add_implication_constraints([self.v.id(("A", p, t))], [-self.v.id(("B", p, t))])
                self.add_implication_constraints([self.v.id(("B", p, t))], [-self.v.id(("A", p, t))])
    def add_backward_B_explanation(self) -> None:
        """
        For every p, t>0:
            B(p, t) -> ( B(p, t-1) & not dep_from_B(p, t-1) )  OR  (some arrival causing B(p, t))
        Here we assume arrivals are produced only by deps from A with given duration.
        """
        for p, d in self.durations.items():
            for t in range(1, self.T + 1):
                b_t = self.v.id(("B", p, t))

                # Option 1: stayed from t-1 at B without leaving
                if t - 1 >= 0:
                    b_prev = self.v.id(("B", p, t-1))
                    dep_prev = self.v.id(("dep", t-1, p, "r"))
                    # B_t -> (B_{t-1} & not dep_{t-1}^r)
                    self.add_clause([-b_t, b_prev])
                    self.add_clause([-b_t, -dep_prev])

                # Option 2: arrived from A with duration d
                dep_time = t - d
                if dep_time >= 1:
                    dep_from_a = self.v.id(("dep", dep_time, p, "a"))
                    dur_lit = self.v.id(("dur", dep_time, d))
                    # B_t -> dep_from_a(dep_time) & dur(dep_time,d)
                    self.add_clause([-b_t, dep_from_a])
                    self.add_clause([-b_t, dur_lit])        

    def add_arrival_constraints(self) -> None:
        for t in range(1, self.T + 1):
            for p, d in self.durations.items():
                dep_from_a = self.v.id(("dep", t, p, "a"))
                dep_from_b = self.v.id(("dep", t, p, "r"))
                
                # --- Bounds Check ---
                if t + d > self.T:
                    self.add_clause([-dep_from_a]) 
                    self.add_clause([-dep_from_b]) 
                    continue

                dur_t_d = self.v.id(("dur", t, d))
                condition = [dep_from_a, dur_t_d]

                ARR_t_d = self.v.id(("ARR", t+d))
                #side_t_d = self.v.id(("side", t + d))
                #side_t= self.v.id(("side", t))
                B_arrival = self.v.id(("B", p, t + d))

                

                condition = [dep_from_b, dur_t_d]
                ARR_t_d = self.v.id(("ARR", t+d))
                #side_t_d = self.v.id(("side", t + d))
                #side_t= self.v.id(("side", t))
                A_arrival = self.v.id(("A", p, t + d))

                #implied = [ARR_t_d, -side_t_d, B_arrival, -A_arrival, side_t]
                implied = [ARR_t_d, B_arrival, -A_arrival]
            
                self.add_implication_constraints(condition, implied)
                self.add_implication_constraints(implied, condition)
                #implied = [ARR_t_d, side_t_d, A_arrival,- B_arrival, -side_t]
                implied = [ARR_t_d, A_arrival,- B_arrival]
                self.add_implication_constraints(condition, implied)
                self.add_implication_constraints(implied, condition)

    def add_duration_constraint(self) -> None:
        pass

    def solve(self, use_pysat: bool = False) -> Tuple[bool, Optional[Dict[Tuple, bool]]]:
        if use_pysat:
            try:
                from pysat.formula import CNF
                from pysat.solvers import Solver
            except Exception as e:
                raise RuntimeError("PySAT not available: " + str(e))

            pysat_cnf = CNF()
            for clause in self.cnf:
                pysat_cnf.append(clause)

            with Solver(bootstrap_with=pysat_cnf) as s:
                ok = s.solve()
                if not ok:
                    return False, None
                model = s.get_model()
                readable = {k: (model[self.var_map[k] - 1] > 0) if self.var_map[k] <= len(model) else False
                            for k in self.var_map}
                return True, readable

        return False, None

# todo : transfere logique a gen_solution 
def print_model(model):
    departures = {}

    for key, value in model.items():
        if value: 
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
    fb = FormulaBuilderSkeleton(durations=durations, capacity=2, T=18, P=3)
    fb.build_cnf()
    satisfiable, model = check_satisfiability(fb.cnf, fb.v)
    if satisfiable:
        print("The formula is satisfiable.")
        print("A satisfying assignment is:")
        print_model(model)
    else:
        print("The formula is not satisfiable.")

