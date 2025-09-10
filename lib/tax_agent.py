import os, json, re
from anthropic import Anthropic

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

tools = [{"type": "web_search_20250305", "name": "web_search"}]

def build_system_prompt(classifier_explanation: str, organisation_name: str, ticker: str, ex_date_cstd: str) -> str:
    prompt_text = f"""
    NBIM processes thousands of dividend events each year. For each event, NBIM calculates expected tax amounts based on their understanding of applicable tax rates, while the Custodian reports their own tax calculations. Sometimes these disagree, creating a "Tax Break."
    
    EVENT DETAILS:
    - Organisation: {organisation_name}
    - Ticker: {ticker}
    - Ex-Date: {ex_date_cstd}
    
    Another agent have identified a break in the tax calculation that you need to resolve. Here is the explanation of the break coming from the previous agent:
    {classifier_explanation}
    
    Your responsibility is to determine, using available evidence and web search, whether:
    - Custody's tax calculation is wrong,
    - NBIM's tax calculation is wrong, or
    - There is not enough information to decide (NEED_INFO).
    
    Use web search to research:
    - Current tax rates for dividends from this company/country to Norway
    - Any recent changes in tax treaties or regulations
    - Specific tax treatment for this type of dividend
    - Any withholding tax rates that might apply
    
    CRITICAL: You are only allowed to use the web search tool THREE TIMES. Make your decision based on those few search results. Do not make more web searches.
    
    IMPORTANT:
    - If you cannot find sufficient and reliable information from authoritative sources, you MUST return "NEED_INFO".
    - Do NOT rely on outdated, speculative, or unreliable internet sources.
    - It is always better to conclude NEED_INFO than to give a wrong answer.

    OUTPUT:
    Always return ONLY avalid JSON object with exactly these two fields, without any other text such as '''json'''.
    Do not include any reasoning from a potential web search outside of the explanation field in the json.
    This is the ONLY output format you are allowed to use:
    {{
    "conclusion": "NEED_INFO | CUSTODY_WRONG | NBIM_WRONG",
    "explanation": "Self-contained, operator-ready summary that does not assume any prior context. 
    Include the relevant input data provided to you, as well as any additional facts you retrieved using tools. 
    Clearly state why these values lead you to the chosen conclusion. Be concise, factual, and avoid speculation."
    }}
    """
    return {
        "system": (
            "You are NBIM's Tax Calculation Remediation Agent. "
            "Your ONLY task is to resolve breaks between NBIM and custody data in TAX CALCULATIONS for dividend payments. "
        ),
        "messages": [
            {"role": "user", "content": prompt_text}
        ],
    }

def run_tax_agent(message_config: dict, model="claude-sonnet-4-20250514",) -> str:
    conversation = message_config["messages"].copy()
    
    msg = client.messages.create(
        model=model,
        max_tokens=600,
        tools=tools,
        system=message_config["system"],
        messages=conversation
    )
    
    response_text = "".join([block.text for block in msg.content if getattr(block, "type", None) == "text"]).strip()
    return response_text
