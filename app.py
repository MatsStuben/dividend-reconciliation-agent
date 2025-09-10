import os
import json
from lib.process_data import process_data
from lib.rules import apply_rules
from lib.classify import run_classification, build_classification_prompt
from lib.num_shares_agent import run_shares_agent, build_system_prompt

def main():
    data_folder = "data"
    
    nbim_file = os.path.join(data_folder, "NBIM_Dividend_Bookings.csv")
    custody_file = os.path.join(data_folder, "CUSTODY_Dividend_Bookings.csv")
    
    print(f"Processing files: {nbim_file} and {custody_file}")
    merged_df = process_data(nbim_file, custody_file)
    merged_df = apply_rules(merged_df)

    for index, row in merged_df.iterrows():
        if abs(row['NET_AMOUNT_SETTLEMENT_CSTD'] - row['NET_AMOUNT_SETTLEMENT_NBIM'])/row['NET_AMOUNT_SETTLEMENT_NBIM'] > 0.01:
            # Run classification
            message_config = build_classification_prompt(row)
            classification_output = run_classification(message_config)
            print("Classification output:")
            print(classification_output)

            organisation_name = row['ORGANISATION_NAME']
            ticker = row['TICKER']
            ex_date_cstd = row['EX_DATE_CSTD']
            try:
                classification_data = json.loads(classification_output)
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
                    shares_message_config = build_system_prompt(shares_explanation, organisation_name, ticker, ex_date_cstd)
                    shares_result = run_shares_agent(shares_message_config)
                    print("Shares agent result:")
                    print(shares_result)
                    
            except json.JSONDecodeError:
                print("Could not parse classification output as JSON")
                print("Raw output:", classification_output)

    
    return merged_df

if __name__ == "__main__":
    result = main()
