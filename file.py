from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

def build_formula():
    # In PySAT, we use an IDPool to manage variable names to integer mappings
    v = IDPool()
    
    # We create a CNF object
    cnf = CNF()
    
    # Example formula: (a OR NOT b) AND (b OR c)
    # In PySAT logic: 
    # a = v.id('a'), b = v.id('b'), c = v.id('c')
    # NOT b is represented as -v.id('b')
    
    cnf.append([v.id('a'), -v.id('b')]) # (a OR NOT b)
    cnf.append([v.id('b'), v.id('c')])  # (b OR c)
    
    return cnf, v

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

def main():
    cnf, v = build_formula()
    satisfiable, model = check_satisfiability(cnf, v)
    
    if satisfiable:
        print("The formula is satisfiable.")
        print("A satisfying assignment is:", model)
    else:
        print("The formula is not satisfiable.")

if __name__ == "__main__":
    main()