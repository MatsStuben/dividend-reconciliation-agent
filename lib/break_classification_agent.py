from anthropic import Anthropic
import os
import pandas as pd
import json

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def structure_break_candidates(row: pd.Series) -> dict:

    problems = []

    if row.get("BREAK_TAX", 0) == 1:
        problems.append({
            "name": "Tax Break",
            "relevant parameters": _format_tax_parameters(row)
        })

    if row.get("BREAK_SHARES", 0) == 1:
        problems.append({
            "name": "Shares Break",
            "relevant parameters": _format_shares_parameters(row)
        })

    if row.get("BREAK_DPS", 0) == 1:
        problems.append({
            "name": "DPS Break",
            "relevant parameters": _format_dps_parameters(row)
        })

    if row.get("BREAK_FX", 0) == 1:
        problems.append({
            "name": "FX Break",
            "relevant parameters": _format_fx_parameters(row)
        })

    return {"problems": problems}

def _format_tax_parameters(row: pd.Series) -> str:
    return (
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
        f"EXRESPRDIV_COST_QUOTATION_NBIM_ONLY={row.get('EXRESPRDIV_COST_QUOTATION_NBIM_ONLY')}"
    )

def _format_shares_parameters(row: pd.Series) -> str:
    return (
        f"NOMINAL_BASIS_NBIM={row.get('NOMINAL_BASIS_NBIM')}, "
        f"HOLDING_QUANTITY_CSTD_ONLY={row.get('HOLDING_QUANTITY_CSTD_ONLY')}, "
        f"NOMINAL_BASIS_CSTD={row.get('NOMINAL_BASIS_CSTD')}, "
        f"LOAN_QUANTITY_CSTD_ONLY={row.get('LOAN_QUANTITY_CSTD_ONLY')}, "
        f"LENDING_PERCENTAGE_CSTD_ONLY={row.get('LENDING_PERCENTAGE_CSTD_ONLY')}"
    )

def _format_dps_parameters(row: pd.Series) -> str:
    return (
        f"DIV_RATE_NBIM={row.get('DIV_RATE_NBIM')}, "
        f"DIV_RATE_CSTD={row.get('DIV_RATE_CSTD')}"
    )

def _format_fx_parameters(row: pd.Series) -> str:
    return (
        f"FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM={row.get('FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM')}, "
        f"FX_RATE_QUOTATION_TO_SETTLEMENT_CSTD={row.get('FX_RATE_QUOTATION_TO_SETTLEMENT_CSTD')}, "
        f"EX_DATE_CSTD={row.get('EX_DATE_CSTD')}, "
        f"EX_DATE_NBIM={row.get('EX_DATE_NBIM')}, "
        f"PAYMENT_DATE_CSTD={row.get('PAYMENT_DATE_CSTD')}, "
        f"PAYMENT_DATE_NBIM={row.get('PAYMENT_DATE_NBIM')}"
    )

def build_classification_prompt(row: pd.Series) -> dict:
    """
    Build a classification prompt for the LLM to analyze dividend breaks.
    
    """
    def clean_value(v):
        """Clean data values for JSON serialization."""
        if pd.isna(v):
            return "N/A"
        elif hasattr(v, "item"):
            return v.item()
        elif hasattr(v, "strftime"): 
            return v.strftime("%Y-%m-%d")
        else:
            return v
    
    suggestions = structure_break_candidates(row)
    
    prompt_text = f"""We are reviewing a single dividend event to detect and classify **breaks** 
    (discrepancies) between NBIM’s expected dividend data and the custodian’s actual dividend data. 
    This event shows a net dividend mismatch, so at least one break exists.

    TASK:
    Your role is to classify breaks only, not to resolve them.
    A rule-based program has pre-flagged up to 4 types of potential breaks: Tax, Shares, Dividends Per Share, and FX-conversion.
    You are shown only the flagged candidates, but these may be incorrect because the rules do not cover every scenario.
    Carefully review each suggested break:
    – Confirm it if the evidence supports it
    – Suppress it if it is not actually a break
    Add any other break types you identify from the data (including types beyond the 4 categories)
    For each confirmed break, provide a **clear and factual explanation**:
    – The explanation together with the break name is the **only information available** to the person who will fix the problem.
    – Therefore, the explanation must include all relevant information from the provided data so that the operator understands the break without looking at the raw data.
    – Do not omit important details
    – Do not include irrelevant values
    – Absolutely do not invent or speculate; only use information explicitly present in the data
    • Return ONLY valid JSON in this exact format, without any other text such as '''json''':
    {{
    "problems": [
        {{ "name": "Tax Break|Shares Break|DPS Break|FX Break|Other", "explanation": "Full but concise explanation for a human operator. Include the relevant input data provided to you."}}
    ]
    }}

    SUGGESTED BREAK CANDIDATES:
    {json.dumps(suggestions, indent=2)}

    FULL EVENT DATA:
    {json.dumps({k: clean_value(v) for k, v in row.to_dict().items()}, indent=2)}

    Note: Fields ending with _NBIM_ONLY or _CSTD_ONLY exist only in one file; others are common to both.
    Be concise and factual. Use only given values. If no break of a suggested type exists, omit it."""
    return {
        "system": "You are a break classification assistant for NBIM dividend reconciliation. Your sole task is to detect and classify breaks between NBIM’s expected dividend data and the custodian’s actual dividend data.”",
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
    }

def classify_breaks(row: pd.Series, model="claude-sonnet-4-20250514", max_tokens=600) -> str:

    message_config = build_classification_prompt(row)
    
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=message_config["system"],
        messages=message_config["messages"]
    )

    for block in response.content:
        if block.type == "text":
            return block.text

    return "" 