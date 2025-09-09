import pandas as pd

def apply_rules(df):
    df_with_flags = df.copy()
    
    nbim_cols = [col for col in df.columns if col.endswith('_NBIM')]
    cstd_cols = [col for col in df.columns if col.endswith('_CSTD')]
    
    for nbim_col in nbim_cols:
        cstd_candidate = nbim_col.replace('_NBIM', '_CSTD')
        if cstd_candidate in cstd_cols:
            flag_col = f"MATCH_{nbim_col.replace('_NBIM', '')}"
            df_with_flags[flag_col] = (df_with_flags[nbim_col] == df_with_flags[cstd_candidate]).astype(int)
    
    return df_with_flags
