import ast, operator, re
from decimal import Decimal, InvalidOperation
import sympy as sp

OPS={ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul, ast.Div:operator.truediv, ast.Pow:operator.pow, ast.USub:operator.neg, ast.UAdd:operator.pos}

def safe_numeric_eval(expression: str):
    """Evaluate a restricted arithmetic AST. No eval(), names, calls, or attributes."""
    if not expression or len(expression)>200:
        raise ValueError("No supported expression was extracted")
    expression=expression.replace("×","*").replace("÷","/").replace("−","-").replace("^","**")
    tree=ast.parse(expression, mode="eval")
    def visit(node):
        if isinstance(node, ast.Expression): return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value,(int,float)) and not isinstance(node.value,bool):
            return sp.Rational(str(node.value))
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            left,right=visit(node.left),visit(node.right)
            if isinstance(node.op, ast.Pow) and abs(float(right))>10: raise ValueError("Exponent is outside the supported range")
            return OPS[type(node.op)](left,right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS: return OPS[type(node.op)](visit(node.operand))
        raise ValueError("Unsupported expression: use numbers, parentheses, +, -, *, /, and **")
    value=visit(tree)
    if value.is_finite is False: raise ValueError("Result is not finite")
    return sp.simplify(value)

def numeric_equal(a,b):
    # Compare numeric strings only; never pass arbitrary user text to sympify/eval.
    try:
        left, right = sp.Rational(str(a)), sp.Rational(str(b))
        return sp.simplify(left-right) == 0
    except Exception:
        try:
            return abs(float(a)-float(b)) < 1e-9
        except Exception:
            return False

def verify_steps(steps):
    results=[]
    first_error=False
    for st in steps:
        expr=str(st.get("expression", "")).strip()
        claimed=str(st.get("claimed_result", "")).strip()
        row={"step_id":st.get("step_id"),"expression":expr,"claimed_result":claimed,"actual_result":None,"status":"unverifiable","reason":"Expression or claimed result is missing.","depends_on_earlier_error":False}
        if expr and claimed:
            try:
                actual=safe_numeric_eval(expr)
                row["actual_result"]=str(actual)
                row["status"]="correct" if numeric_equal(actual,claimed) else "error"
                row["reason"]="Claim matches the independently calculated value." if row["status"]=="correct" else "Claim differs from the independently calculated value."
            except Exception as e:
                row["reason"]=str(e)
        if first_error and row["status"]=="correct":
            row["depends_on_earlier_error"]=True
        if row["status"]=="error": first_error=True
        results.append(row)
    return results
