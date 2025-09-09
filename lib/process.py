import pandas as pd
from datetime import datetime

def read_data(NBIM_file, custody_file):
    NBIM_df = pd.read_csv(NBIM_file, sep=';')
    custody_df = pd.read_csv(custody_file, sep=';')
    return NBIM_df, custody_df

def merge_df(NBIM_df, custody_df):
    NBIM_df = NBIM_df.rename(columns={'BANK_ACCOUNT': 'CUSTODY'})
    
    merged_df = pd.merge(
        NBIM_df, 
        custody_df, 
        on=['COAC_EVENT_KEY', 'CUSTODY'], 
        how='outer'
    )
    return merged_df

def convert_date_columns(df):
    for col in df.columns:
        if 'DATE' in col.upper():
            df[col] = pd.to_datetime(df[col], format='%d.%m.%Y', errors='coerce')
    return df

def process_data(NBIM_file, custody_file):
    NBIM_df, custody_df = read_data(NBIM_file, custody_file)
    merged_df = merge_df(NBIM_df, custody_df)
    merged_df = convert_date_columns(merged_df)
    return merged_df