import pandas as pd
import numpy as np

def apply_general_flags(df):
    """
    This is a simple check to see if the NBIM and CSTD columns have the same value.
    """
    df_with_flags = df.copy()
    
    nbim_cols = [col for col in df.columns if col.endswith('_NBIM')]
    cstd_cols = [col for col in df.columns if col.endswith('_CSTD')]
    
    for nbim_col in nbim_cols:
        cstd_candidate = nbim_col.replace('_NBIM', '_CSTD')
        if cstd_candidate in cstd_cols:
            flag_col = f"MATCH_{nbim_col.replace('_NBIM', '')}"
            df_with_flags[flag_col] = (df_with_flags[nbim_col] == df_with_flags[cstd_candidate]).astype(int)
    
    return df_with_flags

def apply_breaks_flags(df: pd.DataFrame,
                       tol_percentage=0.01):
    """
    This is a check to see if there are any breaks in the data.
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

        
        gross_match = abs((gross_nbim - gross_cstd))/gross_nbim <= tol_percentage
        if not gross_match:
            if not abs((dps_nbim - dps_cstd))/dps_nbim <= tol_percentage:
                df.at[i, "BREAK_DPS"] = 1
                
            implied_dps_match = abs(gross_nbim/dps_nbim - gross_cstd/dps_cstd) <= tol_percentage
            if not implied_dps_match:
                df.at[i, "BREAK_SHARES"] = 1

        implied_tax_rate_match = abs((tax_nbim/gross_nbim - tax_cstd/gross_cstd)) <= tol_percentage
        if not implied_tax_rate_match:
            df.at[i, "BREAK_TAX"] = 1
        
        if not abs((fx_nbim - fx_cstd)) <= tol_percentage:
            df.at[i, "BREAK_FX"] = 1

    return df

def apply_rules(df):
    df_with_rules = df.copy()

    df_with_general_flags = apply_general_flags(df_with_rules)
    df_with_all_flags = apply_breaks_flags(df_with_general_flags)
    
    return df_with_all_flags