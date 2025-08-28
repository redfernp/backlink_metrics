import streamlit as st
import pandas as pd

st.title("🔗 Backlink Metrics Tool")

# Step 1: Choose analysis mode
mode = st.radio("Select what you want to analyze:", ["Domain Metrics Only", "Page Metrics Only", "Both Combined"])

# File uploaders based on mode
ahrefs_domain = majestic_domain = ahrefs_page = majestic_page = None

if mode == "Domain Metrics Only" or mode == "Both Combined":
    ahrefs_domain = st.file_uploader("Upload Domain-Level Ahrefs CSV (UTF-16)", type="csv", key="ahrefs_domain")
    majestic_domain = st.file_uploader("Upload Domain-Level Majestic CSV", type="csv", key="majestic_domain")

if mode == "Page Metrics Only" or mode == "Both Combined":
    ahrefs_page = st.file_uploader("Upload Page-Level Ahrefs CSV (UTF-16)", type="csv", key="ahrefs_page")
    majestic_page = st.file_uploader("Upload Page-Level Majestic CSV", type="csv", key="majestic_page")

# Step 2: Logic for each mode
try:
    if mode == "Domain Metrics Only" and ahrefs_domain and majestic_domain:
        df_ahrefs = pd.read_csv(ahrefs_domain, sep="\t", encoding="utf-16")
        df_majestic = pd.read_csv(majestic_domain)
        df_ahrefs["Domain"] = df_ahrefs["Target"].str.strip("/")
        df_majestic["Domain"] = df_majestic["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")
        domain = pd.merge(df_ahrefs, df_majestic, on="Domain", how="inner")
        domain["LD:RD Ratio"] = domain["Linked Domains"] / domain["Ref domains Dofollow"]
        domain["TF:CF Ratio"] = domain["TrustFlow"] / domain["CitationFlow"]

        output = domain[[
            "Domain", "Domain Rating", "Ref domains Dofollow", "Linked Domains",
            "TrustFlow", "CitationFlow",
            "TopicalTrustFlow_Topic_0", "TopicalTrustFlow_Value_0",
            "TopicalTrustFlow_Topic_1", "TopicalTrustFlow_Value_1",
            "TopicalTrustFlow_Topic_2", "TopicalTrustFlow_Value_2",
            "LD:RD Ratio", "TF:CF Ratio", "Total Traffic"
        ]]

        st.success("✅ Domain metrics processed!")
        st.dataframe(output)
        st.download_button("📥 Download CSV", output.to_csv(index=False), "domain_metrics.csv")

    elif mode == "Page Metrics Only" and ahrefs_page and majestic_page:
        df_ahrefs = pd.read_csv(ahrefs_page, sep="\t", encoding="utf-16")
        df_majestic = pd.read_csv(majestic_page)
        df_ahrefs["Page URL"] = df_ahrefs["Target"].str.strip("/")
        df_majestic["Page URL"] = df_majestic["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")
        page = pd.merge(df_ahrefs, df_majestic, on="Page URL", how="inner")

        output = page[[
            "Page URL", "Total Keywords", "Total Traffic", "TrustFlow", "CitationFlow"
        ]].rename(columns={
            "Total Keywords": "Page URL Total Keywords",
            "Total Traffic": "Page URL Total Traffic",
            "TrustFlow": "Page URL TrustFlow",
            "CitationFlow": "Page URL CitationFlow"
        })

        st.success("✅ Page metrics processed!")
        st.dataframe(output)
        st.download_button("📥 Download CSV", output.to_csv(index=False), "page_metrics.csv")

    elif mode == "Both Combined" and all([ahrefs_domain, majestic_domain, ahrefs_page, majestic_page]):
        # Load & normalize domain data
        df_ahrefs_d = pd.read_csv(ahrefs_domain, sep="\t", encoding="utf-16")
        df_majestic_d = pd.read_csv(majestic_domain)
        df_ahrefs_d["Domain"] = df_ahrefs_d["Target"].str.strip("/")
        df_majestic_d["Domain"] = df_majestic_d["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")
        domain = pd.merge(df_ahrefs_d, df_majestic_d, on="Domain", how="inner")
        domain["LD:RD Ratio"] = domain["Linked Domains"] / domain["Ref domains Dofollow"]
        domain["TF:CF Ratio"] = domain["TrustFlow"] / domain["CitationFlow"]

        # Load & normalize page data
        df_ahrefs_p = pd.read_csv(ahrefs_page, sep="\t", encoding="utf-16")
        df_majestic_p = pd.read_csv(majestic_page)
        df_ahrefs_p["Page URL"] = df_ahrefs_p["Target"].str.strip("/")
        df_majestic_p["Page URL"] = df_majestic_p["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")
        page = pd.merge(df_ahrefs_p, df_majestic_p, on="Page URL", how="inner")

        final = pd.DataFrame()
        final["Domain"] = domain["Domain"]
        final["Domain Rating"] = domain["Domain Rating"]
        final["Ref domains Dofollow"] = domain["Ref domains Dofollow"]
        final["Linked Domains"] = domain["Linked Domains"]
        final["TrustFlow"] = domain["TrustFlow"]
        final["CitationFlow"] = domain["CitationFlow"]
        final["TopicalTrustFlow_Topic_0"] = domain["TopicalTrustFlow_Topic_0"]
        final["TopicalTrustFlow_Value_0"] = domain["TopicalTrustFlow_Value_0"]
        final["TopicalTrustFlow_Topic_1"] = domain["TopicalTrustFlow_Topic_1"]
        final["TopicalTrustFlow_Value_1"] = domain["TopicalTrustFlow_Value_1"]
        final["TopicalTrustFlow_Topic_2"] = domain["TopicalTrustFlow_Topic_2"]
        final["TopicalTrustFlow_Value_2"] = domain["TopicalTrustFlow_Value_2"]
        final["LD:RD Ratio"] = domain["LD:RD Ratio"]
        final["TF:CF Ratio"] = domain["TF:CF Ratio"]
        final["Total Traffic"] = domain["Total Traffic"]
        final["Page URL"] = page["Page URL"]
        final["Page URL Total Keywords"] = page["Total Keywords"]
        final["Page URL Total Traffic"] = page["Total Traffic"]
        final["Page URL TrustFlow"] = page["TrustFlow"]
        final["Page URL CitationFlow"] = page["CitationFlow"]

        st.success("✅ Combined domain + page metrics generated!")
        st.dataframe(final)
        st.download_button("📥 Download Combined CSV", final.to_csv(index=False), "domain_page_combined.csv")

except Exception as e:
    st.error(f"❌ Error: {e}")
