import sympy as sp
import numpy as np

def solve_equation(equation_str: str):
    # E.g., "2*x + 3 = 0"
    try:
        if "=" in equation_str:
            left, right = equation_str.split("=")
            eq = sp.Eq(sp.sympify(left), sp.sympify(right))
        else:
            eq = sp.sympify(equation_str)
            
        x = sp.Symbol('x')
        solutions = sp.solve(eq, x)
        return {"solutions": [str(s) for s in solutions]}
    except Exception as e:
        return {"error": str(e)}

def evaluate_expression(expr_str: str):
    try:
        expr = sp.sympify(expr_str)
        result = expr.evalf()
        return {"result": str(result)}
    except Exception as e:
        return {"error": str(e)}
