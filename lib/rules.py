import pandas as pd
import numpy as np

def add_comparison_flags(df):
    """
    Add comparison flags for NBIM-CSTD pairs.
    Returns 1 if values are the same, 0 if different, NaN if either is missing.
    """
    df_with_flags = df.copy()
    
    # Define matching column pairs
    matching_pairs = [
        ('DIV_RATE_NBIM', 'DIV_RATE_CSTD'),
        ('EX_DATE_NBIM', 'EX_DATE_CSTD'),
        ('PAYMENT_DATE_NBIM', 'PAYMENT_DATE_CSTD'),
        ('NOMINAL_BASIS_NBIM', 'NOMINAL_BASIS_CSTD'),
        ('GROSS_AMOUNT_QUOTATION_NBIM', 'GROSS_AMOUNT_CSTD'),
        ('NET_AMOUNT_QUOTATION_NBIM', 'NET_AMOUNT_QUOTATION_CSTD'),
        ('NET_AMOUNT_SETTLEMENT_NBIM', 'NET_AMOUNT_SETTLEMENT_CSTD'),
        ('TOTAL_TAX_RATE_NBIM', 'TOTAL_TAX_RATE_CSTD'),
        ('TOTAL_TAX_QUOTATION_NBIM', 'TOTAL_TAX_QUOTATION_CSTD'),
        ('SETTLEMENT_CURRENCY_NBIM', 'SETTLEMENT_CURRENCY_CSTD'),
        ('FX_RATE_QUOTATION_TO_SETTLEMENT_NBIM', 'FX_RATE_QUOTATION_TO_SETTLEMENT_CSTD')
    ]
    
    # Add comparison flags for each pair
    for nbim_col, cstd_col in matching_pairs:
        if nbim_col in df_with_flags.columns and cstd_col in df_with_flags.columns:
            # Create flag column name
            flag_col = f"MATCH_{nbim_col.split('_')[0]}_{cstd_col.split('_')[0]}"
            
            # Compare values: 1 if same, 0 if different, NaN if either is missing
            df_with_flags[flag_col] = np.where(
                df_with_flags[nbim_col].isna() | df_with_flags[cstd_col].isna(),
                np.nan,  # NaN if either value is missing
                (df_with_flags[nbim_col] == df_with_flags[cstd_col]).astype(int)
            )
    
    return df_with_flags

def apply_rules(df):
    """
    Apply all reconciliation rules to the merged DataFrame.
    """
    df_with_rules = add_comparison_flags(df)
    return df_with_rules
