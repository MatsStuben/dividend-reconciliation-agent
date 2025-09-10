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
        how='outer',
        indicator=True,
        suffixes=('_NBIM', '_CSTD') 
    )
    
    merged_df['NO_MATCH_FLAG'] = merged_df['_merge'] != 'both'
    merged_df.drop(columns=['_merge'], inplace=True)
    return merged_df

def convert_date_columns(df):
    for col in df.columns:
        if 'DATE' in col.upper():
            df[col] = pd.to_datetime(df[col], format='%d.%m.%Y', errors='coerce')
    return df

def remove_columns(df):
    columns_to_remove = [
        'ISIN_NBIM', 'ISIN_CSTD', 'SEDOL_NBIM', 'SEDOL_CSTD',
        'CUSTODIAN_NBIM', 'CUSTODIAN_CSTD',
        'EVENT_TYPE', 'BANK_ACCOUNTS', 'GROSS_AMOUNT_PORTFOLIO',
        'NET_AMOUNT_PORTFOLIO', 'WTHTAX_COST_PORTFOLIO', 'RECORD_DATE',
        'EX_DATE', 'PAY_DATE', 'AVG_FX_RATE_QUOTATION_TO_PORTFOLIO'
    ]
    
    existing_columns = [col for col in columns_to_remove if col in df.columns]
    df_cleaned = df.drop(columns=existing_columns)
    
    return df_cleaned

def add_total_tax_quotation(df):
    if 'LOCALTAX_COST_QUOTATION' in df.columns and 'WTHTAX_COST_QUOTATION' in df.columns:
        df['TOTAL_TAX_QUOTATION_NBIM'] = df['LOCALTAX_COST_QUOTATION'] + df['WTHTAX_COST_QUOTATION']
    return df

def add_fx_rate_quotation_to_settlement(df):
    if 'NET_AMOUNT_QUOTATION' in df.columns and 'NET_AMOUNT_SETTLEMENT' in df.columns:
        df['FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM'] = df['NET_AMOUNT_QUOTATION'] / df['NET_AMOUNT_SETTLEMENT'].replace(0, float('nan'))
    return df

def organize_columns(df):
    
    column_mappings = {
        # General columns
        'COAC_EVENT_KEY': 'COAC_EVENT_KEY',
        'INSTRUMENT_DESCRIPTION': 'INSTRUMENT_DESCRIPTION',
        'TICKER': 'TICKER',
        'ORGANISATION_NAME': 'ORGANISATION_NAME',
        'CUSTODY': 'CUSTODY',
        
       # Matching columns
        'EVENT_EX_DATE': 'EX_DATE_CSTD',
        'EXDATE': 'EX_DATE_NBIM',
        'EVENT_PAYMENT_DATE': 'PAYMENT_DATE_CSTD', 
        'PAYMENT_DATE': 'PAYMENT_DATE_NBIM',
        'DIVIDENDS_PER_SHARE': 'DIV_RATE_NBIM',
        'DIV_RATE': 'DIV_RATE_CSTD',
        'NOMINAL_BASIS_CSTD': 'NOMINAL_BASIS_CSTD',
        'NOMINAL_BASIS_NBIM': 'NOMINAL_BASIS_NBIM',
        'GROSS_AMOUNT': 'GROSS_AMOUNT_QUOTATION_CSTD',
        'GROSS_AMOUNT_QUOTATION': 'GROSS_AMOUNT_QUOTATION_NBIM',
        'NET_AMOUNT_QC': 'NET_AMOUNT_QUOTATION_CSTD',
        'NET_AMOUNT_QUOTATION': 'NET_AMOUNT_QUOTATION_NBIM',
        'NET_AMOUNT_SC': 'NET_AMOUNT_SETTLEMENT_CSTD',
        'NET_AMOUNT_SETTLEMENT': 'NET_AMOUNT_SETTLEMENT_NBIM',
        'TAX_RATE': 'TOTAL_TAX_RATE_CSTD',
        'TOTAL_TAX_RATE': 'TOTAL_TAX_RATE_NBIM',
        'TAX': 'TOTAL_TAX_QUOTATION_CSTD',
        'TOTAL_TAX_QUOTATION_NBIM': 'TOTAL_TAX_QUOTATION_NBIM',
        'SETTLED_CURRENCY': 'SETTLEMENT_CURRENCY_CSTD',
        'SETTLEMENT_CURRENCY': 'SETTLEMENT_CURRENCY_NBIM',
        'FX_RATE': 'FX_RATE_QUOTATION_TO_SETTLEMENT_CSTD',
        'FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM': 'FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM',

        #NBIM specific columns
        'WTHTAX_COST_QUOTATION': 'WTHTAX_COST_QUOTATION_NBIM_ONLY',
        'WTHTAX_COST_SETTLEMENT': 'WTHTAX_COST_SETTLEMENT_NBIM_ONLY',
        'WTHTAX_RATE': 'WTHTAX_RATE_NBIM_ONLY',
        'LOCALTAX_COST_QUOTATION': 'LOCALTAX_COST_QUOTATION_NBIM_ONLY',
        'LOCALTAX_COST_SETTLEMENT': 'LOCALTAX_COST_SETTLEMENT_NBIM_ONLY',
        'QUOTATION_CURRENCY': 'QUOTATION_CURRENCY_NBIM_ONLY',
        'EXRESPRDIV_COST_QUOTATION': 'EXRESPRDIV_COST_QUOTATION_NBIM_ONLY',
        'EXRESPRDIV_COST_SETTLEMENT': 'EXRESPRDIV_COST_SETTLEMENT_NBIM_ONLY',
        'RESTITUTION_RATE': 'RESTITUTION_RATE_NBIM_ONLY',
        
        # Custody specific columns
        'CURRENCIES': 'CURRENCIES_CSTD_ONLY',
        'LOAN_QUANTITY': 'LOAN_QUANTITY_CSTD_ONLY',
        'HOLDING_QUANTITY': 'HOLDING_QUANTITY_CSTD_ONLY',
        'LENDING_PERCENTAGE': 'LENDING_PERCENTAGE_CSTD_ONLY',
        'IS_CROSS_CURRENCY_REVERSAL': 'IS_CROSS_CURRENCY_REVERSAL_CSTD_ONLY',
        'POSSIBLE_RESTITUTION_PAYMENT': 'POSSIBLE_RESTITUTION_PAYMENT_CSTD_ONLY',
        'POSSIBLE_RESTITUTION_AMOUNT': 'POSSIBLE_RESTITUTION_AMOUNT_CSTD_ONLY',
        'ADR_FEE': 'ADR_FEE_CSTD_ONLY',
        'ADR_FEE_RATE': 'ADR_FEE_RATE_CSTD_ONLY'
    }

    df_renamed = df.rename(columns=column_mappings)
    final_columns = [new_name for old_name, new_name in column_mappings.items() if new_name in df_renamed.columns]
    
    return df_renamed[final_columns]  

def process_data(NBIM_file, custody_file):
    from lib.rules import apply_rules
    
    NBIM_df, custody_df = read_data(NBIM_file, custody_file)
    merged_df = merge_df(NBIM_df, custody_df)
    merged_df = convert_date_columns(merged_df)
    merged_df = remove_columns(merged_df)
    merged_df = add_total_tax_quotation(merged_df)
    merged_df = add_fx_rate_quotation_to_settlement(merged_df)
    merged_df = organize_columns(merged_df)
    merged_df = apply_rules(merged_df)
    return merged_df
