import pandas as pd
import json


def generate_suggestions_structutred(row: pd.Series) -> dict:

    problems = []

    if row.get("BREAK_TAX", 0) == 1:
        problems.append({
            "name": "Tax Break",
            "relevant parameters": (
                f"TOTAL_TAX_QUOTATION_NBIM={row.get('TOTAL_TAX_QUOTATION_NBIM')} vs "
                f"TOTAL_TAX_QUOTATION_CSTD={row.get('TOTAL_TAX_QUOTATION_CSTD')}, "
                f"GROSS_AMOUNT_QUOTATION_NBIM={row.get('GROSS_AMOUNT_QUOTATION_NBIM')}, "
                f"GROSS_AMOUNT_QUOTATION_CSTD={row.get('GROSS_AMOUNT_QUOTATION_CSTD')}, "
                f"NET_AMOUNT_QUOTATION_CSTD={row.get('NET_AMOUNT_QUOTATION_CSTD')}, "
                f"NET_AMOUNT_QUOTATION_NBIM={row.get('NET_AMOUNT_QUOTATION_NBIM')}, "
                f"LOCALTAX_COST_QUOTATION_NBIM_ONLY={row.get('LOCALTAX_COST_QUOTATION_NBIM_ONLY')}, "
                f"WTHTAX_COST_QUOTATION_NBIM_ONLY={row.get('WTHTAX_COST_QUOTATION_NBIM_ONLY')}, "
                f"TOTAL_TAX_RATE_CSTD={row.get('TOTAL_TAX_RATE_CSTD')}, "
                f"TOTAL_TAX_RATE_NBIM={row.get('TOTAL_TAX_RATE_NBIM')}, "
                f"POSSIBLE_RESTITUTION_PAYMENT_CSTD_ONLY={row.get('POSSIBLE_RESTITUTION_PAYMENT_CSTD_ONLY')}, "
                f"POSSIBLE_RESTITUTION_AMOUNT_CSTD_ONLY={row.get('POSSIBLE_RESTITUTION_AMOUNT_CSTD_ONLY')}, "
                f"EXRESPRDIV_COST_QUOTATION_NBIM_ONLY={row.get('EXRESPRDIV_COST_QUOTATION_NBIM_ONLY')}, "
            )
        })

    if row.get("BREAK_SHARES", 0) == 1:

        problems.append({
            "name": "Number of Shares Break",
            "relevant parameters": (
                f"NOMINAL_BASIS_NBIM={row.get('NOMINAL_BASIS_NBIM')}, "
                f"HOLDING_QUANTITY_CSTD={row.get('HOLDING_QUANTITY_CSTD')}, "
                f"NOMINAL_BASIS_CSTD={row.get('NOMINAL_BASIS_CSTD')}, "
                f"LOAN_QUANTITY_CSTD_ONLY={row.get('LOAN_QUANTITY_CSTD_ONLY')}, "
                f"LENDING_PERCENTAGE_CSTD_ONLY={row.get('LENDING_PERCENTAGE_CSTD_ONLY')}, "
            )
        })

    if row.get("BREAK_DPS", 0) == 1:

        problems.append({
            "name": "Dividends Per Share Break",
            "relevant parameters": (
                f"DIV_RATE_NBIM={row.get('DIV_RATE_NBIM')}, "
                f"DIV_RATE_CSTD={row.get('DIV_RATE_CSTD')}, "
            )
        })

    if row.get("BREAK_FX", 0) == 1:

        problems.append({
            "name": "FX Break",
            "relevant parameters": (
                f"FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM={row.get('FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM')}, "
                f"FX_RATE_QUOTATION_TO_SETTLEMENT_CSTD={row.get('FX_RATE_QUOTATION_TO_SETTLEMENT_CSTD')}, "
                f"EX_DATE_CSTD={row.get('EX_DATE_CSTD')}, "
                f"EX_DATE_NBIM={row.get('EX_DATE_NBIM')}, "
                f"PAYMENT_DATE_CSTD={row.get('PAYMENT_DATE_CSTD')}, "
                f"PAYMENT_DATE_NBIM={row.get('PAYMENT_DATE_NBIM')}, "

            )
        })

    return {"problems": problems}

def build_classification_prompt(row: pd.Series) -> dict:

    suggestions = generate_suggestions_structutred(row)

    full_row = {}
    for k, v in row.to_dict().items():
        if pd.isna(v):
            full_row[k] = None
        elif hasattr(v, "item"):
            full_row[k] = v.item()
        elif hasattr(v, "strftime"): 
            full_row[k] = v.strftime("%Y-%m-%d")
        else:
            full_row[k] = v

    system_prompt = (
        "You are a reconciliation assistant for NBIM. "
        "Use only the provided values; do not invent numbers. "
        "Return strict JSON matching the schema."
    )

    instructions = (
        "We are reconciling dividend payments between NBIM (expected) and the custodian (actual). "
        "This specific event has a net dividend mismatch, so at least one break exists.\n\n"
        "Task:\n"
        "• Review the suggested break candidates and the full data.\n"
        "• Confirm which breaks are real, suppress any that are not, and add other breaks if warranted.\n"
        "• Output strict JSON in this form:\n"
        '{\n'
        '  "problems": [\n'
        '    { "name": "Tax Break|Shares Break|DPS Break|FX Break|Other", "explanation": "1–2 short sentences for an operator" }\n'
        '  ]\n'
        '}\n'
        "Guidelines: Be concise and factual. Use only given values. If no break of a suggested type exists, omit it."
    )
    
    content_blocks = [
        {"type": "text", "text": instructions},
        {"type": "text", "text": "Suggested break candidates (from deterministic checks):"},
        {"type": "text", "text": json.dumps(suggestions, indent=2)},
        {"type": "text", "text": (
            "Full data for this event (JSON). "
            "Fields ending with _NBIM_ONLY or _CSTD_ONLY exist only in one file; others are common to both."
        )},
        {"type": "text", "text": json.dumps(full_row, indent=2)},
    ]

    return {
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": content_blocks}
        ],
    }

