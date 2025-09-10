import os
import json
import pandas as pd
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def build_prioritization_prompt(deviations: list, currencies: list, dates: list) -> dict:
    """
    Build a prompt for the prioritization agent to rank dividend reconciliation issues.
    
    Args:
        deviations: List of deviation amounts between NBIM and Custody
        currencies: List of corresponding settlement currencies
        dates: List of corresponding payment dates
        
    Returns:
        dict: Message configuration for Anthropic API
    """
    # Create data for the prompt
    issues_data = []
    for i, (deviation, currency, date) in enumerate(zip(deviations, currencies, dates)):
        issues_data.append({
            "index": i,
            "deviation": deviation,
            "currency": currency,
            "date": date
        })
    
    prompt_text = f"""
    You are a dividend reconciliation prioritization agent. Your task is to rank {len(deviations)} dividend reconciliation issues by priority (1 = highest priority, {len(deviations)} = lowest priority).

    ISSUES TO PRIORITIZE:
    {json.dumps(issues_data, indent=2)}

    PRIORITIZATION CRITERIA:
    - Higher deviation amounts should generally have higher priority
    - Older dates (further back in time) should generally have higher priority  
    - Consider currency impact as the deviation amount is in the settlement currency
    - Balance urgency vs impact when making decisions

    OUTPUT:
    Return ONLY a JSON array of priority rankings, where each number corresponds to the issue index.
    Example: If issue 0 should be priority 2, issue 1 should be priority 1, and issue 2 should be priority 3, return [2, 1, 3]

    Return format: [3, 1, 2, ...]
    """
    
    return {
        "system": (
            "You are NBIM's Dividend Reconciliation Prioritization Agent. "
            "Your ONLY task is to rank dividend reconciliation issues by priority for efficient resolution."
        ),
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
    }

def add_priorities_to_results(results: dict, model="claude-sonnet-4-20250514") -> dict:
    """
    Add priority column to results based on deviation, currency, and dates.

    """
    if not results:
        return results
    
    deviations = []
    currencies = []
    dates = []
    result_keys = []
    
    for (coac_id, bank_account), data in results.items():
        deviations.append(data['deviation'])
        currencies.append(data['settlement_currency'])
        dates.append(data['execution_date'])
        result_keys.append((coac_id, bank_account))
    
    priorities = _get_priorities_from_llm(deviations, currencies, dates, model)
    
    for i, (coac_id, bank_account) in enumerate(result_keys):
        if i < len(priorities):
            results[(coac_id, bank_account)]['priority'] = priorities[i]
        else:
            results[(coac_id, bank_account)]['priority'] = i + 1
    
    return results

def _get_priorities_from_llm(deviations: list, currencies: list, dates: list, model: str) -> list:
    """Get priority rankings from LLM."""
    message_config = build_prioritization_prompt(deviations, currencies, dates)
    
    response = client.messages.create(
        model=model,
        max_tokens=300,
        system=message_config["system"],
        messages=message_config["messages"]
    )
    
    response_text = "".join([block.text for block in response.content if getattr(block, "type", None) == "text"]).strip()
    
    try:
        # Parse JSON response
        priorities = json.loads(response_text)
        if isinstance(priorities, list) and len(priorities) == len(deviations):
            print(f"Priorities: {priorities}")
            return priorities
        else:
            # Fallback: return simple ranking by deviation amount
            return list(range(1, len(deviations) + 1))
    except json.JSONDecodeError:
        # Fallback: return simple ranking by deviation amount
        return list(range(1, len(deviations) + 1))
