import streamlit as st
import pandas as pd
import os
import tempfile
from app import process_dividend_reconciliation

st.set_page_config(page_title="Dividend Reconciliation Dashboard", layout="wide")

st.title("🏦 Dividend Reconciliation Dashboard")

st.header("📁 Upload CSV Files")

col1, col2 = st.columns(2)

with col1:
    nbim_file = st.file_uploader("Upload NBIM Dividend Bookings CSV", type="csv", key="nbim")

with col2:
    custody_file = st.file_uploader("Upload Custody Dividend Bookings CSV", type="csv", key="custody")

if st.button("Process Files", type="primary"):
    if nbim_file is not None and custody_file is not None:
        with st.spinner("Processing files..."):
            # Save uploaded files temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_nbim:
                tmp_nbim.write(nbim_file.getvalue())
                nbim_path = tmp_nbim.name
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_custody:
                tmp_custody.write(custody_file.getvalue())
                custody_path = tmp_custody.name
            
            try:
                st.info("🔄 Processing files... This may take several minutes due to API calls.")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("Starting processing...")
                progress_bar.progress(10)
                
                result = process_dividend_reconciliation(nbim_file=nbim_path, custody_file=custody_path)
                
                progress_bar.progress(100)
                status_text.text("Processing completed!")
                st.success("✅ Processing completed!")
                
                os.unlink(nbim_path)
                os.unlink(custody_path)
                
            except Exception as e:
                st.error(f"❌ Error processing files: {str(e)}")
                st.info("💡 This might be due to API rate limits or connection timeouts. Try again in a few minutes.")
                try:
                    os.unlink(nbim_path)
                    os.unlink(custody_path)
                except:
                    pass
    else:
        st.warning("⚠️ Please upload both CSV files")

st.header("📊 Results")

output_file = "data/output.csv"
if os.path.exists(output_file):
    try:
        output_df = pd.read_csv(output_file)
        st.dataframe(output_df, use_container_width=True)
        
        csv = output_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv,
            file_name="dividend_reconciliation_results.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error reading output file: {str(e)}")
else:
    st.info("No results available. Please process files first.")
