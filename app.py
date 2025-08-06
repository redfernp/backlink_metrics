import streamlit as st
import pandas as pd

# Predefined template structure
TEMPLATE_COLUMNS = [
    'Domain',
    'Domain Rating',
    'Ref domains Dofollow',
    'Linked Domains',
    'TrustFlow',
    'CitationFlow',
    'TopicalTrustFlow_Topic_0',
    'TopicalTrustFlow_Value_0',
    'TopicalTrustFlow_Topic_1',
    'TopicalTrustFlow_Value_1',
    'TopicalTrustFlow_Topic_2',
    'TopicalTrustFlow_Value_2',
    'LD:RD Ratio',
    'TF:CF Ratio',
    'Total Traffic'
]

st.title("🔗 Backlink Metrics Tool")
st.write("Upload your Ahrefs and Majestic backlink CSVs. The app will merge, calculate LD:RD and TF:CF ratios, and show the final output.")

# File uploaders
ahrefs_file = st.file_uploader("Upload Ahrefs CSV", type=["csv", "txt"])
majestic_file = st.file_uploader("Upload Majestic CSV", type=["csv", "txt"])

# When both files are uploaded
if ahrefs_file and majestic_file:
    try:
        # Load files
        ahrefs_df = pd.read_csv(ahrefs_file, sep="\t", encoding="utf-16")  # Ahrefs
        majestic_df = pd.read_csv(majestic_file)  # Majestic

        # Normalize domain names
        ahrefs_df["Domain"] = ahrefs_df["Target"].str.strip("/")
        majestic_df["Domain"] = majestic_df["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        # Merge
        merged = pd.merge(ahrefs_df, majestic_df, on="Domain", how="inner")

        # Calculate ratios
        merged["LD:RD Ratio"] = merged["Linked Domains"] / merged["Ref domains Dofollow"]
        merged["TF:CF Ratio"] = merged["TrustFlow"] / merged["CitationFlow"]

        # Final structured output
        final_df = merged[TEMPLATE_COLUMNS]

        st.success("✅ Merged and processed successfully!")
        st.dataframe(final_df)

        # Download button
        csv = final_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", data=csv, file_name="backlink_output.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Something went wrong: {e}")
