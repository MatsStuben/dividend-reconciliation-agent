import os, json, re
from anthropic import Anthropic
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

tools = [
    {
        "name": "get_position_on_date",
        "description": "Return NBIM position for a given TICKER and date",
        "input_schema": {
            "type": "object",
            "properties": {
                "TICKER": {"type": "string"},
                "date": {"type": "string", "format": "date"}
            },
            "required": ["TICKER", "date"]
        },
    },
    {
        "name": "get_settlement_movements",
        "description": "Return trades impacting entitlement around date for a given TICKER",
        "input_schema": {
            "type": "object",
            "properties": {
                "TICKER": {"type": "string"},
                "date": {"type": "string", "format": "date"}
            },
            "required": ["TICKER", "date"]
        },
    }
]

def build_system_prompt(classifier_explanation: str, organisation_name: str, ticker: str, ex_date_cstd: str) -> str:
    prompt_text = f"""
    NBIM processes thousands of dividend events each year. For each event, NBIM has an internally expected number of shares entitled to dividends, while the Custodian reports their own booked position. Sometimes these disagree, creating a "Shares Position Break."
    
    EVENT DETAILS:
    - Organisation: {organisation_name}
    - Ticker: {ticker}
    - Ex-Date: {ex_date_cstd}
    
    Another agent have identified a break in the shares position that you need to resolve. Here is the explanation of the break coming from the previous agent:
    {classifier_explanation}
    
    Your responsibility is to determine, using available evidence and the tools provided, whether:
    - Custody's booked position is wrong,
    - NBIM's expected position is wrong, or
    - There is not enough information to decide (NEED_INFO).
    OUTPUT:
    Always return a valid JSON object with exactly these two fields, without any other text such as '''json''':
    {{
    "conclusion": "NEED_INFO | CUSTODY_WRONG | NBIM_WRONG",
    "explanation": "Self-contained, operator-ready summary that does not assume any prior context. 
    Include the relevant input data provided to you, as well as any additional facts you retrieved using tools. 
    Clearly state why these values lead you to the chosen conclusion. Be concise, factual, and avoid speculation."
    "
    }}
    """
    return {
        "system": (
            "You are NBIM's Shares Position Remediation Agent. "
            "Your ONLY task is to resolve breaks between NBIM and custody data in the NUMBER OF SHARES used for dividend entitlement. "
        ),
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
    }

# Hardcoded results from the tools. In production, these would be replaced with actual data from the database, which is not available in this example.
def tool_impl(name, args):
    if name == "get_position_on_date":
        ticker = args.get("TICKER", "Unknown")
        date = args.get("date", "Unknown")
        return {
            "position": 12000,
            "ticker": ticker,
            "date": date,
        }
    if name == "get_settlement_movements":
        ticker = args.get("TICKER", "Unknown")
        date = args.get("date", "Unknown")
        return {
            "ticker": ticker,
            "date": date,
            "movements": [
                {
                    "trade_date": date,
                    "quantity": 2000,
                    "side": "BUY",
                    "settlement_status": "SETTLED"
                }
            ]
        }
    return {}
 
def run_shares_agent(message_config: dict, model="claude-sonnet-4-20250514",) -> str:
    conversation = message_config["messages"].copy()
    
    msg = client.messages.create(
        model=model,
        max_tokens=1000,
        tools=tools,
        system=message_config["system"],
        messages=conversation
    )
    # Allow up to 2 tool-use cycles
    for cycle in range(2):
        tool_calls = [block for block in msg.content if getattr(block, "type", None) == "tool_use"]
        if not tool_calls:
            break
            
        conversation.append({
            "role": "assistant",
            "content": [{"type": "tool_use", "id": tool_call.id, "name": tool_call.name, "input": tool_call.input} for tool_call in tool_calls]
        })
        
        for tool_call in tool_calls:
            print(f'Tool call: {tool_call.name} with input: {tool_call.input}')
            tool_result = tool_impl(tool_call.name, tool_call.input)
            conversation.append({
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": tool_call.id, "content": json.dumps(tool_result)}]
            })
        
        msg = client.messages.create(
            model=model,
            max_tokens=600,
            tools=tools,
            system=message_config["system"],
            messages=conversation
        )

    response_text = "".join([block.text for block in msg.content if getattr(block, "type", None) == "text"]).strip()
    return response_text
