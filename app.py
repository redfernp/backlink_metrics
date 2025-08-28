import streamlit as st
import pandas as pd

st.title("🔗 Domain + Page Backlink Metrics Tool")

st.write("""
Upload the following **4 CSV files**:
1. 📄 Domain-level Ahrefs export (`.csv`, UTF-16 tab-separated)
2. 📄 Domain-level Majestic export (`.csv`)
3. 📄 Page-level Ahrefs export (`.csv`, UTF-16 tab-separated)
4. 📄 Page-level Majestic export (`.csv`)
""")

# Upload files
ahrefs_domain = st.file_uploader("Upload Domain-Level Ahrefs CSV", type="csv", key="ahrefs_domain")
majestic_domain = st.file_uploader("Upload Domain-Level Majestic CSV", type="csv", key="majestic_domain")
ahrefs_page = st.file_uploader("Upload Page-Level Ahrefs CSV", type="csv", key="ahrefs_page")
majestic_page = st.file_uploader("Upload Page-Level Majestic CSV", type="csv", key="majestic_page")

if all([ahrefs_domain, majestic_domain, ahrefs_page, majestic_page]):
    try:
        # Load CSVs
        df_ahrefs_domain = pd.read_csv(ahrefs_domain, sep="\t", encoding="utf-16")
        df_majestic_domain = pd.read_csv(majestic_domain)
        df_ahrefs_page = pd.read_csv(ahrefs_page, sep="\t", encoding="utf-16")
        df_majestic_page = pd.read_csv(majestic_page)

        # Normalize domain and URL
        df_ahrefs_domain["Domain"] = df_ahrefs_domain["Target"].str.strip("/")
        df_majestic_domain["Domain"] = df_majestic_domain["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        df_ahrefs_page["Page URL"] = df_ahrefs_page["Target"].str.strip("/")
        df_majestic_page["Page URL"] = df_majestic_page["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        # Merge domain-level
        domain_merged = pd.merge(df_ahrefs_domain, df_majestic_domain, on="Domain", how="inner")
        domain_merged["LD:RD Ratio"] = domain_merged["Linked Domains"] / domain_merged["Ref domains Dofollow"]
        domain_merged["TF:CF Ratio"] = domain_merged["TrustFlow"] / domain_merged["CitationFlow"]

        # Merge page-level
        page_merged = pd.merge(df_ahrefs_page, df_majestic_page, on="Page URL", how="inner")

        # Build final output
        final_df = pd.DataFrame()
        final_df["Domain"] = domain_merged["Domain"]
        final_df["Domain Rating"] = domain_merged["Domain Rating"]
        final_df["Ref domains Dofollow"] = domain_merged["Ref domains Dofollow"]
        final_df["Linked Domains"] = domain_merged["Linked Domains"]
        final_df["TrustFlow"] = domain_merged["TrustFlow"]
        final_df["CitationFlow"] = domain_merged["CitationFlow"]
        final_df["TopicalTrustFlow_Topic_0"] = domain_merged["TopicalTrustFlow_Topic_0"]
        final_df["TopicalTrustFlow_Value_0"] = domain_merged["TopicalTrustFlow_Value_0"]
        final_df["TopicalTrustFlow_Topic_1"] = domain_merged["TopicalTrustFlow_Topic_1"]
        final_df["TopicalTrustFlow_Value_1"] = domain_merged["TopicalTrustFlow_Value_1"]
        final_df["TopicalTrustFlow_Topic_2"] = domain_merged["TopicalTrustFlow_Topic_2"]
        final_df["TopicalTrustFlow_Value_2"] = domain_merged["TopicalTrustFlow_Value_2"]
        final_df["LD:RD Ratio"] = domain_merged["LD:RD Ratio"]
        final_df["TF:CF Ratio"] = domain_merged["TF:CF Ratio"]
        final_df["Total Traffic"] = domain_merged["Total Traffic"]
        final_df["Page URL"] = page_merged["Page URL"]
        final_df["Page URL Total Keywords"] = page_merged["Total Keywords"]
        final_df["Page URL Total Traffic"] = page_merged["Total Traffic"]
        final_df["Page URL TrustFlow"] = page_merged["TrustFlow"]
        final_df["Page URL CitationFlow"] = page_merged["CitationFlow"]

        # Show preview
        st.success("✅ Successfully processed!")
        st.dataframe(final_df)

        # Download
        csv_data = final_df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Final CSV", data=csv_data, file_name="domain_page_backlink_metrics.csv", mime="text/csv")

    except Exception as e:
        st.error(f"❌ An error occurred: {e}")
