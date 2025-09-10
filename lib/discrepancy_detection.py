import pandas as pd
import numpy as np

def add_exact_match_flags(df):
    """
    Add MATCH flags for all corresponding NBIM/CSTD column pairs.
    Returns 1 if values match exactly, 0 if they don't.
    """
    df_result = df.copy()
    
    nbim_cols = [col for col in df.columns if col.endswith('_NBIM')]
    
    for nbim_col in nbim_cols:
        cstd_col = nbim_col.replace('_NBIM', '_CSTD')
        
        if cstd_col in df.columns:
            field_name = nbim_col.replace('_NBIM', '')
            match_col = f"MATCH_{field_name}"
            
            df_result[match_col] = (df_result[nbim_col] == df_result[cstd_col]).astype(int)
    
    return df_result

def detect_breaks(df: pd.DataFrame, tolerance=0.01):
    """
    Detect breaks in dividend data by comparing NBIM vs Custody values.
    
    Break types:
    - BREAK_DPS: Dividend per share mismatch
    - BREAK_SHARES: Share quantity mismatch (implied)
    - BREAK_TAX: Tax rate mismatch (implied)
    - BREAK_FX: Foreign exchange rate mismatch
    We need to use gross/dps as shares to see the amount of shares actually used as several number are provided.
    We need to use tax/gross as tax rate instead of just tax as difference in tax could be due to other factors (ex. num shares)
    """

    df = df.copy()
    df["BREAK_TAX"] = 0
    df["BREAK_SHARES"] = 0
    df["BREAK_DPS"] = 0
    df["BREAK_FX"] = 0

    for i, row in df.iterrows():
        dps_nbim = row["DIV_RATE_NBIM"]
        dps_cstd = row["DIV_RATE_CSTD"]
        gross_nbim = row["GROSS_AMOUNT_QUOTATION_NBIM"]
        gross_cstd = row["GROSS_AMOUNT_QUOTATION_CSTD"]
        tax_nbim = row["TOTAL_TAX_QUOTATION_NBIM"]
        tax_cstd = row["TOTAL_TAX_QUOTATION_CSTD"]
        fx_nbim = row["FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM"]
        fx_cstd = row["FX_RATE_QUOTATION_TO_SETTLEMENT_CSTD"]

        
        gross_match = abs((gross_nbim - gross_cstd))/gross_nbim <= tolerance
        if not gross_match:
            if abs((dps_nbim - dps_cstd)) / dps_nbim > tolerance:
                df.at[i, "BREAK_DPS"] = 1

            implied_shares_nbim = gross_nbim / dps_nbim
            implied_shares_cstd = gross_cstd / dps_cstd
            if abs(implied_shares_nbim - implied_shares_cstd) / implied_shares_nbim > tolerance:
                df.at[i, "BREAK_SHARES"] = 1

        tax_rate_nbim = tax_nbim / gross_nbim
        tax_rate_cstd = tax_cstd / gross_cstd
        if abs(tax_rate_nbim - tax_rate_cstd) > tolerance:
            df.at[i, "BREAK_TAX"] = 1
        
        # Check FX rate break
        if abs((fx_nbim - fx_cstd) / fx_nbim) > tolerance:
            df.at[i, "BREAK_FX"] = 1

    return df

def detect_all_discrepancies(df):
    """
    Apply all validation rules to detect breaks and match indicators in dividend data.
    
    Returns:
        pd.DataFrame: Original data with added MATCH_* and BREAK_* columns
    """
    df = add_exact_match_flags(df)
    df= detect_breaks(df)
    
    return df