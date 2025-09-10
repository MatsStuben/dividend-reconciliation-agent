import os
import json
import pandas as pd
from lib.data_preparation import process_data
from lib.discrepancy_detection import detect_all_discrepancies
from lib.break_classification_agent import classify_breaks 
from lib.shares_break_resolver_agent import resolve_shares_break
from lib.tax_break_resolver_agent import resolve_tax_break
from lib.prioritization_agent import add_priorities_to_results

def _process_break(break_type: str, explanation: str, organisation_name: str, ticker: str, ex_date_cstd: str) -> dict:
    """Process a specific break type using the appropriate agent."""
    print(f"\nRunning {break_type.lower()} agent...")
    
    if break_type == "Shares Break":
        result = resolve_shares_break(explanation, organisation_name, ticker, ex_date_cstd)
    elif break_type == "Tax Break":
        result = resolve_tax_break(explanation, organisation_name, ticker, ex_date_cstd)
    else:
        return {'conclusion': 'NEED_INFO', 'explanation': f'Agent not yet implemented for: {break_type}'}
    
    print(f"{break_type} agent result:")
    print(result)
    
    try:
        return json.loads(result)
    except json.JSONDecodeError:
        return {
            'conclusion': 'NEED_INFO', 
            'explanation': f'Could not parse {break_type.lower()} agent result'
        }

def _save_results(results: dict, data_folder: str = "data") -> None:
    """Save results to CSV file."""
    if not results:
        print("\nNo results to write to CSV")
        return
    
    csv_data = []
    for (coac_id, bank_account), data in results.items():
        csv_data.append({
            'coac_id': coac_id,
            'bank_account': bank_account,
            'conclusion': data['conclusion'],
            'explanation': data['explanation'],
            'deviation': data['deviation'],
            'settlement_currency': data['settlement_currency'],
            'execution_date': data['execution_date'],
            'priority': data.get('priority', 'N/A')
        })
    
    results_df = pd.DataFrame(csv_data)
    output_path = os.path.join(data_folder, 'output.csv')
    results_df.to_csv(output_path, index=False)
    print(f"\nResults written to {output_path} with {len(results)} entries")

def process_dividend_reconciliation(nbim_file=None, custody_file=None):
    """
    Main function to process dividend reconciliation with break detection and resolution.
    First, it processes the data and detects all discrepancies using simple rules.
    Then, it classifies the discrepancies into different types of breaks using an LLM.
    Finally, it resolves the breaks using specialized agents for each type of break.
    """
    print(f"Processing files: {nbim_file} and {custody_file}")
    
    merged_df = process_data(nbim_file, custody_file)
    merged_df = detect_all_discrepancies(merged_df)
    
    results = {}
    
    for index, row in merged_df.iterrows():
        deviation = abs(row['NET_AMOUNT_SETTLEMENT_CSTD'] - row['NET_AMOUNT_SETTLEMENT_NBIM'])
        if deviation / row['NET_AMOUNT_SETTLEMENT_NBIM'] <= 0.01:
            continue
            
        breaks_raw = classify_breaks(row)
        print("Breaks detected:")
        print(breaks_raw)
        
        row_data = {
            'organisation_name': row['ORGANISATION_NAME'],
            'ticker': row['TICKER'],
            'ex_date_cstd': row['EX_DATE_CSTD'],
            'coac_id': row['COAC_EVENT_KEY'],
            'bank_account': row['CUSTODY'],
            'settlement_currency': row['SETTLEMENT_CURRENCY_CSTD'],
            'deviation': deviation,
            'currency': row['SETTLEMENT_CURRENCY_CSTD'],
            'execution_date': row['EX_DATE_CSTD'].strftime('%Y-%m-%d') if pd.notna(row['EX_DATE_CSTD']) else "2024-01-01"
        }
        
        try:
            breaks = json.loads(breaks_raw)
            breaks = breaks.get("problems", [])
            
            # Process each identified break
            for pot_break in breaks:
                break_type = pot_break.get("name")
                explanation = pot_break.get("explanation", f"{break_type} detected")
                
                agent_result = _process_break(
                    break_type, explanation, 
                    row_data['organisation_name'], 
                    row_data['ticker'], 
                    row_data['ex_date_cstd']
                )
                
                results[(row_data['coac_id'], row_data['bank_account'])] = {
                    'conclusion': agent_result.get('conclusion', 'NEED_INFO'),
                    'explanation': agent_result.get('explanation', 'No explanation provided'),
                    'deviation': row_data['deviation'],
                    'settlement_currency': row_data['settlement_currency'],
                    'execution_date': row_data['execution_date']
                }
                
        except json.JSONDecodeError:
            print("Could not parse classification output as JSON")
            print("Raw output:", breaks_raw)
    
    results = add_priorities_to_results(results)
    
    _save_results(results)
    
    return merged_df

