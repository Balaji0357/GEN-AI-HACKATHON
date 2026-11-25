import re
from .verifier import safe_numeric_eval

def build_replay(steps, verification):
    """Create an illustrative corrected branch by replacing earlier claimed values in later expressions."""
    replacements=[]
    rows=[]
    for st, vr in zip(steps, verification):
        original=str(st.get("expression", ""))
        corrected=original
        for old,new in replacements:
            if old:
                corrected=re.sub(rf"(?<![\w.]){re.escape(old)}(?![\w.])", f"({new})", corrected)
        try:
            replay_value=str(safe_numeric_eval(corrected)) if corrected else None
        except Exception:
            replay_value=None
        rows.append({"step_id":st.get("step_id"),"original_expression":original,"corrected_expression":corrected,"student_claim":vr.get("claimed_result"),"verified_value":vr.get("actual_result"),"replay_value":replay_value,"original_status":vr.get("status"),"depends_on_earlier_error":vr.get("depends_on_earlier_error")})
        # Carry the corrected branch forward: when a dependent step changes,
        # map its original claimed output to the replayed output for later steps.
        claimed = str(vr.get("claimed_result", ""))
        if claimed and replay_value is not None and replay_value != claimed:
            replacements.append((claimed, replay_value))
        elif vr.get("status")=="error" and vr.get("actual_result") is not None:
            replacements.append((claimed, str(vr.get("actual_result"))))
    return rows
