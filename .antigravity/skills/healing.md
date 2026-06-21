# Skill: Self-Healing Protocol

## Purpose
To automatically correct malformed JSON/Data structures based on pre-defined Pydantic schemas.

## Workflow
1. **Detection:** Catch `ValidationError` from the middleware.
2. **Analysis:** Extract the malformed schema segment.
3. **Inference:** Prompt the LLM with:
   - Original Schema (Contract)
   - Malformed Data
   - Error Context
4. **Correction:** Return the sanitized, valid data structure.
5. **Report:** Update the live dashboard counter (Healed packets +1).

## Constraints
- Do not lose semantic meaning during the healing process.
- If the data is beyond repair (e.g., critical fields missing), block the packet and alert the system.
