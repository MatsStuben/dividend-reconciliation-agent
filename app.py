import os
import glob
from lib.process import process_data
from lib.rules import apply_rules
from lib.prompts import build_classification_prompt
from lib.classify import run_classification

def main():
    data_folder = "data"
    
    nbim_file = os.path.join(data_folder, "NBIM_Dividend_Bookings.csv")
    custody_file = os.path.join(data_folder, "CUSTODY_Dividend_Bookings.csv")
    
    print(f"Processing files: {nbim_file} and {custody_file}")
    merged_df = process_data(nbim_file, custody_file)
    merged_df = apply_rules(merged_df)

    for index, row in merged_df.iterrows():
        if abs(row['NET_AMOUNT_SETTLEMENT_CSTD'] - row['NET_AMOUNT_SETTLEMENT_NBIM'])/row['NET_AMOUNT_SETTLEMENT_NBIM'] > 0.01:
            prompt = build_classification_prompt(row)
            output = run_classification(prompt)
            print(output)

    
    output_path = os.path.join(data_folder, "output.csv")
    merged_df.to_csv(output_path, index=False, sep=';')
    
    print(f"Data processing complete. Merged DataFrame shape: {merged_df.shape}")
    print(f"Columns: {list(merged_df.columns)}")
    print(f"Output saved to: {output_path}")
    
    return merged_df

if __name__ == "__main__":
    result = main()
