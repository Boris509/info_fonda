from pysat.formula import * 
from pysat.solvers import *
from pysat.card import *



# test variables 
Time = 18
Poule = 10
D = {1: 2, 2 : 4, 3: 7, 4 : 10, 5 : 7, 6 : 7, 7: 9, 8: 10, 9:12, 10:15, 11:5, 12:3, 13:2, 14:4, 15:6, 16:8, 17:9, 18:11}
S = ["a", "r"]

class FormulaBuilder:

    def __init__(self, durations=D, capacity=3, T=Time, P=Poule, S=S):
        self.cnf = CNF()
        self.v = IDPool()
        self.D = durations
        self.capacity = capacity
        self.T = T
        self.P = P
        self.S = S

        self.add_initial_state()
        self.add_goal_state()
        #self.add_duration_constraint()
         # Capacity constraint
        card = CardEnc.atmost(lits=[self.v.id(("dep", t, p, s))
                                        for t in range(self.T) for p in range(self.P) for s in self.S], 
                                        bound=self.capacity, vpool=self.v, encoding=EncType.totalizer)
    
        self.cnf.extend(card.clauses)
        self.add_arrival_constraints()
        self.add_exactly_one_deployment()

        #self.add_constraint()


    def add_initial_state(self):
        self.cnf.append([self.v.id(("side", 0))])
        self.cnf.append([-self.v.id(("ALL", 0))])

        for p in range(len(self.D)):
            self.cnf.append([-self.v.id(("B", p , 0))])
            self.cnf.append([self.v.id(("A",p , 0))])
        
     
    def add_exactly_one_deployment(self):
        for t in range(1, self.T):  # or range(self.T)
            all_deps_at_t = []
            for p in self.D:
                for s in self.S:
                    dep_id = self.v.id(("dep", t, p, s))
                    all_deps_at_t.append(dep_id)

            if all_deps_at_t:
                # Exactly one: at least one
                self.cnf.append(all_deps_at_t[:])  # OR of all

                # At most one: pairwise negative
                for i in range(len(all_deps_at_t)):
                    for j in range(i+1, len(all_deps_at_t)):
                        self.cnf.append([-all_deps_at_t[i], -all_deps_at_t[j]])
        


    def add_goal_state(self):
        # ALL_{1} = 1
        for t in range(0,self.T): 
            ALL_t = self.v.id(("ALL", t))

            chickens_on_B = []
            for p in range(len(self.D)):
                B_p_t = self.v.id(("B", p, t))
                chickens_on_B.append(B_p_t)

            if not chickens_on_B:
                self.cnf.append([ALL_t])

            self.add_implication_constraints([-ALL_t], chickens_on_B)

            for b_lit in chickens_on_B:
                self.cnf.append([-b_lit, ALL_t])

        all_t_lits = [self.v.id(("ALL", t)) for t in range(self.T)]
        self.cnf.append(all_t_lits)
    

    def add_constraint(self):   
        # DEP_{t} = 1
        for t in range(self.T) :
            DEP_t = self.v.id(("DEP", t))
            for p in range(self.P):
                for s in self.S:
                    dep_t_p_s = self.v.id(("dep", t, p, s))
                    self.cnf.append([-DEP_t, dep_t_p_s])       
                    self.cnf.append([- dep_t_p_s, DEP_t])     

        # ARR_{t} = 1
        for t in range(self.T) : 
            ARR_t = self.v.id(("ARR", t))
            for p, d in self.D.items():

                for t_ in range(self.T ):
                    dur_t_d = self.v.id(("dur", t, d))
                    if t_ == t + d :
                        self.cnf.append([-dur_t_d, ARR_t])
                        self.cnf.append([-ARR_t, dur_t_d])


        self.add_arrival_constraints()
        self.add_duration_constraint()

    def add_arrival_constraints(self):

         # if boat on side A and B at time t, then all departures at time t must be from side A or side B
        for t in range(0, self.T):
            # Starting point
            side_t = self.v.id(("side", t))
            for p in range(0, self.P):
                # Leaves from B
                b_dep_t_p_retour = self.v.id(("dep", t, p, "r"))
                # Leaves from A
                a_dep_t_p_aller  = self.v.id(("dep", t, p, "a"))

                for item in self.D.items():
                    d = item[1]
                    # Trip duration
                    dur_t_d = self.v.id(("dur", t, d))

  
                    # check if arrival time is within bounds
                    if t + d <= self.T:
                        # the must an arrival at time t + d
                        arr_t = self.v.id(("ARR", t + d))
                        # Boat must be on this side at time t + d
                        side_t_d = self.v.id(("side", t + d))

                        # Side must contain chickens at time t + d
                        A_p_t = self.v.id(("A", t + d, p))
                        B_p_t = self.v.id(("B", t + d, p))

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
            self.cnf.append([lit for lit in left] + [r])

    
   
    def add_duration_constraint(self):
        """
        Define dur(t, d) as: maximum duration of running processes at t is EXACTLY d
        Using intermediate: max_duration_leq(t, k) = true iff all running processes have duration <= k
        Then dur(t, d) ⇔ max_leq(t, d) ∧ ¬max_leq(t, d_prev)  (for sorted d)
        """
        for t in range(self.T):
            dur_dict = {} # dur_list = {2: [dur_id_2, dur_id_4], 4: dur_id_3, ...}
            for p, d in self.D.items():
                dur_id = self.v.id(("dur", t, d))
                dur_dict.setdefault(d, []).append(dur_id)

            
            for dur, dur_ids in dur_dict.items():
                for dur_id in dur_ids:
                    forbidden_deps = []
                    authorized_dep = []
                    for p, p_dur in self.D.items():
                        for s in self.S:
                            dep_id = self.v.id(("dep", t, p, s))

                            if p_dur > dur:
                                forbidden_deps.append(dep_id)
                            else:
                                if p_dur == dur:
                                    authorized_dep.append(dep_id)
                    for dep_id in forbidden_deps:
                        self.cnf.append([-dur_id, -dep_id])
                    if authorized_dep:
                        self.cnf.append([-dur_id] + authorized_dep)
    




        

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

# todo : transfere logique a gen_solution 
def print_model(model):
    departures = {}

    for key, value in model.items():
        print(key, value)

    print(departures)


def main():
    durations = [1, 3, 6, 8]
    dict_durations = {i+1: durations[i] for i in range(len(durations))}

    formula_builder = FormulaBuilder(dict_durations, capacity=2, T=18, P=4, S=["a", "r"])
    satisfiable, model = check_satisfiability(formula_builder.cnf, formula_builder.v)
    if satisfiable:
        print("The formula is satisfiable.")
        print("A satisfying assignment is:")
        print_model(model)
    else:
        print("The formula is not satisfiable.")

main()

