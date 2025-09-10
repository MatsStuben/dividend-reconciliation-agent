import os
import json
from lib.data_preparation import process_data
from lib.discrepancy_detection import detect_all_discrepancies
from lib.break_classification_agent import classify_breaks 
from lib.shares_break_resolver_agent import resolve_shares_break
from lib.tax_agent import run_tax_agent, build_system_prompt as build_tax_system_prompt

def process_dividend_reconciliation(nbim_file=None, custody_file=None):
    data_folder = "data"  
    
    print(f"Processing files: {nbim_file} and {custody_file}")
    merged_df = process_data(nbim_file, custody_file)
    merged_df = detect_all_discrepancies(merged_df)
    
    results = {}

    for index, row in merged_df.iterrows():
        deviation = abs(row['NET_AMOUNT_SETTLEMENT_CSTD'] - row['NET_AMOUNT_SETTLEMENT_NBIM'])
        if deviation/row['NET_AMOUNT_SETTLEMENT_NBIM'] > 0.01:
            classification_output = classify_breaks(row)
            print("Classification output:")
            print(classification_output)

            organisation_name = row['ORGANISATION_NAME']
            ticker = row['TICKER']
            ex_date_cstd = row['EX_DATE_CSTD']
            coac_id = row['COAC_EVENT_KEY']
            bank_account = row['CUSTODY']
            settlement_currency = row['SETTLEMENT_CURRENCY_CSTD']

            try:
                classification_data = json.loads(classification_output)
                
                # Check for shares break
                shares_break_found = any(
                    problem.get("name") == "Shares Break" 
                    for problem in classification_data.get("problems", [])
                )
                
                if shares_break_found:
                    shares_explanation = next(
                        (problem.get("explanation", "") 
                         for problem in classification_data.get("problems", [])
                         if problem.get("name") == "Shares Break"),
                        "Shares position break detected"
                    )
                    print("\nRunning shares agent...")
                    shares_result = resolve_shares_break(shares_explanation, organisation_name, ticker, ex_date_cstd)
                    print("Shares agent result:")
                    print(shares_result)
                    
                    try:
                        shares_data = json.loads(shares_result)
                        results[(coac_id, bank_account)] = {
                            'conclusion': shares_data.get('conclusion', 'NEED_INFO'),
                            'explanation': shares_data.get('explanation', 'No explanation provided'),
                            'deviation': deviation,
                            'settlement_currency': settlement_currency
                        }
                    except json.JSONDecodeError:
                        results[(coac_id, bank_account)] = {
                            'conclusion': 'NEED_INFO',
                            'explanation': 'Could not parse shares agent result',
                            'deviation': deviation,
                            'settlement_currency': settlement_currency
                        }
                
                # Check for tax break
                tax_break_found = any(
                    problem.get("name") == "Tax Break" 
                    for problem in classification_data.get("problems", [])
                )
                
                if tax_break_found:
                    tax_explanation = next(
                        (problem.get("explanation", "") 
                         for problem in classification_data.get("problems", [])
                         if problem.get("name") == "Tax Break"),
                        "Tax calculation break detected"
                    )
                    print("\nRunning tax agent...")
                    tax_message_config = build_tax_system_prompt(tax_explanation, organisation_name, ticker, ex_date_cstd)
                    tax_result = run_tax_agent(tax_message_config)
                    print("Tax agent result:")
                    print(tax_result)
                    
                    try:
                        tax_data = json.loads(tax_result)
                        results[(coac_id, bank_account)] = {
                            'conclusion': tax_data.get('conclusion', 'NEED_INFO'),
                            'explanation': tax_data.get('explanation', 'No explanation provided'),
                            'deviation': deviation,
                            'settlement_currency': settlement_currency
                        }
                    except json.JSONDecodeError:
                        results[(coac_id, bank_account)] = {
                            'conclusion': 'NEED_INFO',
                            'explanation': 'Could not parse tax agent result',
                            'deviation': deviation,
                            'settlement_currency': settlement_currency
                        }
                    
            except json.JSONDecodeError:
                print("Could not parse classification output as JSON")
                print("Raw output:", classification_output)

    if results:
        import pandas as pd
        csv_data = []
        for (coac_id, bank_account), data in results.items():
            csv_data.append({
                'coac_id': coac_id,
                'bank_account': bank_account,
                'conclusion': data['conclusion'],
                'explanation': data['explanation'],
                'deviation': data['deviation'],
                'settlement_currency': data['settlement_currency']
            })
        
        results_df = pd.DataFrame(csv_data)
        output_path = os.path.join(data_folder, 'output.csv')
        results_df.to_csv(output_path, index=False)
        print(f"\nResults written to {output_path} with {len(results)} entries")
    else:
        print("\nNo results to write to CSV")
    
    return merged_df

