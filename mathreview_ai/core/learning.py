from collections import Counter
from .llm import ask_text


def classify_error(expression: str, text: str=""):
    e=(expression+" "+text).lower()
    if "%" in e or "percent" in e or "percentage" in e: return "Percentage calculations"
    if "/" in expression: return "Division and fractions"
    if "*" in expression or "×" in expression: return "Multiplication"
    if "+" in expression: return "Addition"
    if "-" in expression or "−" in expression: return "Subtraction and signs"
    if "ratio" in e: return "Ratios"
    return "General arithmetic"


def misconception_report(history_rows):
    counts=Counter(r["category"] for r in history_rows if r.get("category"))
    if not counts: return [], "Complete a few exercises to build your learning profile."
    ordered=counts.most_common()
    tips={
      "Percentage calculations":"Practise converting percentages into fractions or decimals before calculating.",
      "Division and fractions":"Review division facts, equivalent fractions, and order of operations.",
      "Multiplication":"Practise multiplication facts and estimate the answer before calculating.",
      "Addition":"Review place value, carrying, and column addition.",
      "Subtraction and signs":"Practise regrouping and positive/negative number rules.",
      "Ratios":"Review equivalent ratios and unit-rate methods.",
      "General arithmetic":"Show each operation clearly and check each intermediate result."
    }
    findings=[{"category":c,"count":n,"tip":tips.get(c,"Practise this topic with worked examples.")} for c,n in ordered]
    return findings, f"Your most frequent recorded error category is {ordered[0][0]}. This is a practice signal, not a diagnosis of ability."


def explanation(problem, steps, verification):
    evidence=[{"step":v["step_id"],"expression":v["expression"],"student_claim":v["claimed_result"],"verified_value":v["actual_result"],"status":v["status"]} for v in verification]
    prompt=f"Problem: {problem}\nStudent steps: {steps}\nCode verification evidence: {evidence}\nExplain the first arithmetic mistake in simple student-friendly language. Do not invent numerical facts. If a step is unverifiable, say so. Keep it concise."
    answer=ask_text("You are a patient mathematics tutor. Use only the supplied verification evidence for numerical claims. Distinguish arithmetic checking from reasoning feedback.",prompt)
    if answer: return answer, "AI-generated explanation; numerical evidence shown separately"
    errors=[v for v in verification if v["status"]=="error"]
    if errors:
        v=errors[0]
        return (f"The first detected arithmetic mismatch is in Step {v['step_id']}. You wrote {v['expression']} = {v['claimed_result']}, but the independent calculation gives {v['actual_result']}. Recheck this operation, then recalculate the later steps using the corrected value."), "Template explanation (no API key)"
    if any(v["status"]=="unverifiable" for v in verification):
        return "Some steps could not be independently checked. Rewrite those steps using explicit arithmetic expressions, then review them again.", "Template explanation (no API key)"
    return "All extracted arithmetic expressions match their claimed results. Check that the expressions themselves correctly represent the original word problem.", "Template explanation (no API key)"


def generate_challenge(category):
    bank={
      "Multiplication":("A box contains 14 pencils. Each pencil costs ₹8. What is the total cost?","14 * 8", "112", "Multiply the number of pencils by the cost of one pencil."),
      "Addition":("A library has 238 storybooks and receives 175 more. How many storybooks are there now?","238 + 175","413","Add the hundreds, tens and ones carefully; check carrying."),
      "Subtraction and signs":("A store had 500 notebooks and sold 186. How many remain?","500 - 186","314","Subtract by place value and regroup where needed."),
      "Division and fractions":("36 students are split equally into 4 groups. How many students are in each group?","36 / 4","9","Divide the total equally among the groups."),
      "Percentage calculations":("Find 20% of 450.","450 * 20 / 100","90","Convert 20% to 20/100, then multiply."),
      "Ratios":("The ratio of red to blue balls is 2:3. If there are 10 red balls, how many blue balls are there?","10 * 3 / 2","15","Scale both parts of the ratio by the same factor.")
    }
    return bank.get(category, bank["Multiplication"])
