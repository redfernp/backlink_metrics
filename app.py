import streamlit as st
import pandas as pd

st.set_page_config(page_title="Backlink Metrics Tool", layout="wide")
st.title("🔗 Backlink Metrics Tool")

mode = st.radio("What do you want to analyze?", ["Domain Metrics Only", "Page Metrics Only", "Both Combined"])

ahrefs_domain = majestic_domain = ahrefs_page = majestic_page = None

if mode in ["Domain Metrics Only", "Both Combined"]:
    st.subheader("📁 Domain-Level Files")
    ahrefs_domain = st.file_uploader("Upload Ahrefs Domain CSV (UTF-16, tab-separated)", type="csv", key="ahrefs_domain")
    majestic_domain = st.file_uploader("Upload Majestic Domain CSV", type="csv", key="majestic_domain")

if mode in ["Page Metrics Only", "Both Combined"]:
    st.subheader("📁 Page-Level Files")
    ahrefs_page = st.file_uploader("Upload Ahrefs Page CSV (UTF-16, tab-separated)", type="csv", key="ahrefs_page")
    majestic_page = st.file_uploader("Upload Majestic Page CSV", type="csv", key="majestic_page")

try:
    if mode == "Domain Metrics Only" and ahrefs_domain and majestic_domain:
        df_ahrefs = pd.read_csv(ahrefs_domain, sep="\t", encoding="utf-16", index_col=False)
        df_majestic = pd.read_csv(majestic_domain)

        df_ahrefs.columns = df_ahrefs.columns.str.strip()
        df_majestic.columns = df_majestic.columns.str.strip()

        required_cols = ["Target", "Domain Rating", "Ref domains Dofollow", "Linked Domains", "Total Traffic"]
        missing = [col for col in required_cols if col not in df_ahrefs.columns]
        if missing:
            st.error(f"❌ Missing column(s) in Ahrefs Domain file: {', '.join(missing)}")
            st.stop()

        df_ahrefs["Domain"] = df_ahrefs["Target"].str.strip("/")
        df_majestic["Domain"] = df_majestic["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        domain = pd.merge(df_ahrefs, df_majestic, on="Domain", how="inner")

        if domain.empty:
            st.warning("No matching domains between Ahrefs and Majestic.")
            st.stop()

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
        st.download_button("📅 Download Domain CSV", output.to_csv(index=False), "domain_metrics.csv")

    elif mode == "Page Metrics Only" and ahrefs_page and majestic_page:
        df_ahrefs = pd.read_csv(ahrefs_page, sep="\t", encoding="utf-16", index_col=False)
        df_majestic = pd.read_csv(majestic_page)

        df_ahrefs.columns = df_ahrefs.columns.str.strip()
        df_majestic.columns = df_majestic.columns.str.strip()

        df_ahrefs["Page URL"] = df_ahrefs["Target"].str.strip("/")
        df_majestic["Page URL"] = df_majestic["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        page = pd.merge(df_ahrefs, df_majestic, on="Page URL", how="inner")

        if page.empty:
            st.warning("No matching page URLs between Ahrefs and Majestic.")
            st.stop()

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
        st.download_button("📅 Download Page CSV", output.to_csv(index=False), "page_metrics.csv")

    elif mode == "Both Combined" and all([ahrefs_domain, majestic_domain, ahrefs_page, majestic_page]):
        df_ahrefs_d = pd.read_csv(ahrefs_domain, sep="\t", encoding="utf-16", index_col=False)
        df_majestic_d = pd.read_csv(majestic_domain)
        df_ahrefs_d.columns = df_ahrefs_d.columns.str.strip()
        df_majestic_d.columns = df_majestic_d.columns.str.strip()

        required_cols = ["Target", "Domain Rating", "Ref domains Dofollow", "Linked Domains", "Total Traffic"]
        missing = [col for col in required_cols if col not in df_ahrefs_d.columns]
        if missing:
            st.error(f"❌ Missing column(s) in Ahrefs Domain file: {', '.join(missing)}")
            st.stop()

        df_ahrefs_d["Domain"] = df_ahrefs_d["Target"].str.strip("/")
        df_majestic_d["Domain"] = df_majestic_d["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        domain = pd.merge(df_ahrefs_d, df_majestic_d, on="Domain", how="inner")

        if domain.empty:
            st.warning("No matching domains between Ahrefs and Majestic.")
            st.stop()

        domain["LD:RD Ratio"] = domain["Linked Domains"] / domain["Ref domains Dofollow"]
        domain["TF:CF Ratio"] = domain["TrustFlow"] / domain["CitationFlow"]

        df_ahrefs_p = pd.read_csv(ahrefs_page, sep="\t", encoding="utf-16", index_col=False)
        df_majestic_p = pd.read_csv(majestic_page)
        df_ahrefs_p.columns = df_ahrefs_p.columns.str.strip()
        df_majestic_p.columns = df_majestic_p.columns.str.strip()

        df_ahrefs_p["Page URL"] = df_ahrefs_p["Target"].str.strip("/")
        df_majestic_p["Page URL"] = df_majestic_p["Item"].str.replace(r"https?://", "", regex=True).str.strip("/")

        page = pd.merge(df_ahrefs_p, df_majestic_p, on="Page URL", how="inner")

        if page.empty:
            st.warning("No matching page URLs between Ahrefs and Majestic.")
            st.stop()

        page["Domain"] = page["Page URL"].str.extract(r"([a-zA-Z0-9.-]+\.[a-z]{2,})")
        combined = pd.merge(page, domain, on="Domain", how="left")

        if combined.empty or "Domain Rating" not in combined.columns:
            st.error("❌ 'Domain Rating' column is missing after merge. This means no page URLs matched domain data.")
            st.dataframe(combined.head(10))
            st.stop()

        final = pd.DataFrame()
        final["Domain"] = combined["Domain"]
        final["Domain Rating"] = combined["Domain Rating"]
        final["Ref domains Dofollow"] = combined["Ref domains Dofollow"]
        final["Linked Domains"] = combined["Linked Domains"]
        final["TrustFlow"] = combined["TrustFlow_y"]
        final["CitationFlow"] = combined["CitationFlow_y"]
        final["TopicalTrustFlow_Topic_0"] = combined["TopicalTrustFlow_Topic_0"]
        final["TopicalTrustFlow_Value_0"] = combined["TopicalTrustFlow_Value_0"]
        final["TopicalTrustFlow_Topic_1"] = combined["TopicalTrustFlow_Topic_1"]
        final["TopicalTrustFlow_Value_1"] = combined["TopicalTrustFlow_Value_1"]
        final["TopicalTrustFlow_Topic_2"] = combined["TopicalTrustFlow_Topic_2"]
        final["TopicalTrustFlow_Value_2"] = combined["TopicalTrustFlow_Value_2"]
        final["LD:RD Ratio"] = combined["LD:RD Ratio"]
        final["TF:CF Ratio"] = combined["TF:CF Ratio"]
        final["Total Traffic"] = combined["Total Traffic_y"]
        final["Page URL"] = combined["Page URL"]
        final["Page URL Total Keywords"] = combined["Total Keywords"]
        final["Page URL Total Traffic"] = combined["Total Traffic_x"]
        final["Page URL TrustFlow"] = combined["TrustFlow_x"]
        final["Page URL CitationFlow"] = combined["CitationFlow_x"]

        st.success("✅ Combined domain + page metrics generated!")
        st.dataframe(final)
        st.download_button("📅 Download Combined CSV", final.to_csv(index=False), "domain_page_combined.csv")

except Exception as e:
    st.error(f"❌ Error: {e}")
