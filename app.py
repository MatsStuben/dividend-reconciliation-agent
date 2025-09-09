import os
import glob
from lib.process import process_data

def main():
    data_folder = "data"
    
    csv_files = glob.glob(os.path.join(data_folder, "*.csv"))
    
    print(f"Processing files: {csv_files[0]} and {csv_files[1]}")
    merged_df = process_data(csv_files[0], csv_files[1])
    
    print(f"Data processing complete. Merged DataFrame shape: {merged_df.shape}")
    print(f"Columns: {list(merged_df.columns)}")
    
    return merged_df

if __name__ == "__main__":
    result = main()
