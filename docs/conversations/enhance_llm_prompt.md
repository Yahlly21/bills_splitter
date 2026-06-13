# Enhanced LLM Receipt Extraction Prompt

## Context
Improved the system prompt in `app/llm.py` to provide Claude with more contextual guidance about receipt structure and extraction rules.

## Changes Made

### Original Instruction
```python
_INSTRUCTION = (
    "Extract every line item from this receipt as final, per-unit rows. "
    "Return a JSON array of {name, price}; ignore subtotal / tax / total / tip "
    "rows; prices as numbers. If a line shows a quantity (e.g. `2 X 6.60`), emit "
    "one row per unit at the unit price — never a combined line."
)
```

### Enhanced Instruction
Added detailed guidance on:
- **Receipt structure**: Explains typical layout (header at top, items in middle, totals/footer at bottom)
- **Comprehensive ignore list**: Store info, dates, receipt numbers, payment methods, loyalty programs, etc.
- **Extraction rules**: Clear rules for quantities, size descriptors, language preservation
- **Expected format**: Explicit JSON structure showing nested `{"items": [...]}` format

The enhanced prompt is more explicit and helps Claude better distinguish actual line items from receipt metadata and summaries across different receipt formats.

## Motivation
The original prompt was concise but lacked context about receipt anatomy. By providing more structural guidance, the LLM can better:
- Filter out noise (store headers, payment info, totals)
- Handle quantity formats consistently
- Preserve product details (sizes, weights) in names
- Support multi-language receipts

## Commit
- **SHA**: 977dfeb
- **Message**: "Enhance receipt extraction system prompt"
- **Files**: `app/llm.py`
