import streamlit as st
import pandas as pd

st.title("🔗 Backlink Metrics Tool")
st.write("Upload Ahrefs and Majestic CSVs to generate a combined backlink analysis sheet with LD:RD and TF:CF ratios.")

# File uploads
ahrefs_file = st.file_uploader("Upload Ahrefs CSV", type=["csv", "txt"])
majestic_file = st.file_uploader("Upload Majestic CSV", type=["csv", "txt"])
template_file = st.file_uploader("Upload Template CSV", type="csv")

# Processing logic
if ahrefs_file and majestic_file and template_file:
    try:
        # Read files
        ahrefs_df = pd.read_csv(ahrefs_file, sep="\t", encoding="utf-16")  # Ahrefs
        majestic_df = pd.read_csv(majestic_file)  # Majestic
        template_df = pd.read_csv(template_file)

        # Normalize domain names
        ahrefs_df["Domain"] = ahrefs_df["Target"].str.strip("/")
        majestic_df["Domain"] = majestic_df["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        # Merge
        merged = pd.merge(ahrefs_df, majestic_df, on="Domain", how="inner")

        # Compute ratios
        merged["LD:RD Ratio"] = merged["Linked Domains"] / merged["Ref domains Dofollow"]
        merged["TF:CF Ratio"] = merged["TrustFlow"] / merged["CitationFlow"]

        # Apply template structure
        final_columns = template_df.columns.tolist()
        final_df = merged[final_columns]

        # Show preview
        st.success("✅ Successfully merged and processed!")
        st.dataframe(final_df.head())

        # Download button
        csv = final_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Final Output", data=csv, file_name="backlink_report.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ Error processing files: {e}")
