import re
from .llm import ask_json

SYSTEM = """You are a parser, not a solver. Extract the student's existing mathematical work without correcting it. Never invent missing steps or change a claimed result. Return JSON: {\"steps\":[{\"step_id\":1,\"text\":\"original step\",\"expression\":\"12 * 15\",\"claimed_result\":\"170\"}],\"final_answer\":\"student's stated final answer or empty\",\"topic\":\"one of arithmetic, percentage, ratio, algebra, geometry, other\"}. Use only simple arithmetic expressions with numbers and + - * / ** parentheses. If a line cannot be represented safely, leave expression and claimed_result empty. Percentages should be represented as fractions, e.g. 15% as 15/100. Preserve the student's numbers exactly."""

LINE_PATTERNS = [
    re.compile(r"(?P<expr>[0-9.()\s+*/^%-]+?)\s*=\s*(?P<result>-?\d+(?:\.\d+)?)\s*$"),
]

def fallback_parse(solution: str):
    steps=[]
    for line in solution.splitlines():
        line=line.strip()
        if not line:
            continue
        match=None
        for pat in LINE_PATTERNS:
            match=pat.match(line)
            if match: break
        if match:
            expr=match.group("expr").replace("^", "**")
            result=match.group("result")
            steps.append({"step_id":len(steps)+1,"text":line,"expression":expr.strip(),"claimed_result":result})
        else:
            steps.append({"step_id":len(steps)+1,"text":line,"expression":"","claimed_result":""})
    return {"steps":steps,"final_answer":"","topic":"arithmetic"}


def parse_solution(problem: str, solution: str):
    data=ask_json(SYSTEM, f"WORD PROBLEM:\n{problem}\n\nSTUDENT SOLUTION:\n{solution}")
    if not isinstance(data, dict) or not isinstance(data.get("steps"), list) or not data["steps"]:
        data=fallback_parse(solution)
        data["parser_mode"]="basic fallback parser"
    else:
        # Sanitize and normalize model output. Never trust model-supplied results as verified.
        cleaned=[]
        for i, st in enumerate(data["steps"]):
            if not isinstance(st, dict): continue
            cleaned.append({
                "step_id": i+1,
                "text": str(st.get("text", ""))[:500],
                "expression": str(st.get("expression", ""))[:200].replace("^", "**"),
                "claimed_result": str(st.get("claimed_result", ""))[:80],
            })
        data["steps"]=cleaned
        data["parser_mode"]="OpenAI parser"
    return data
