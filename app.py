import streamlit as st
import pandas as pd
import tldextract
from typing import Optional, List, Dict

# =====================================================
# UI SETUP
# =====================================================
st.set_page_config(page_title="Backlink Metrics Tool", layout="wide")
st.title("🔗 Backlink Metrics Tool")

# =====================================================
# HELPERS
# =====================================================
def extract_root_domain(url: Optional[str]) -> Optional[str]:
    if not isinstance(url, str) or not url.strip():
        return None
    extracted = tldextract.extract(url)
    if extracted.domain and extracted.suffix:
        return f"{extracted.domain}.{extracted.suffix}"
    return None

def normalize_domain_like(s: pd.Series) -> pd.Series:
    # Lowercase, strip protocol, leading www., trailing slash
    return (
        s.astype(str)
         .str.replace(r"^\s*https?://", "", regex=True)
         .str.replace(r"^www\.", "", regex=True)
         .str.strip("/")
         .str.lower()
    )

def normalize_page_url(s: pd.Series) -> pd.Series:
    # Keep host+path (no protocol), lowercase, strip trailing slash
    return (
        s.astype(str)
         .str.replace(r"^\s*https?://", "", regex=True)
         .str.strip("/")
         .str.lower()
    )

def read_ahrefs_csv(uploaded_file) -> pd.DataFrame:
    """
    Ahrefs exports are often UTF-16 with tab sep; sometimes UTF-8.
    Try common combos in order. We always read as strings to avoid type issues and coerce later.
    """
    tried = []
    for enc, sep in [("utf-16", "\t"), ("utf-8-sig", "\t"), ("utf-8", "\t")]:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, sep=sep, encoding=enc, dtype=str)
            return df
        except Exception as e:
            tried.append(f"{enc}/{sep}: {e}")
    raise ValueError("Could not read Ahrefs file. Tried -> " + " | ".join(tried))

def read_csv_flex(uploaded_file) -> pd.DataFrame:
    """
    Majestic is usually UTF-8 comma-separated; fall back to utf-8-sig.
    """
    tried = []
    for enc in ["utf-8", "utf-8-sig"]:
        try:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=enc, dtype=str)
            return df
        except Exception as e:
            tried.append(f"{enc}: {e}")
    raise ValueError("Could not read CSV. Tried -> " + " | ".join(tried))

def map_alias(df: pd.DataFrame, canonical: str, aliases: List[str]) -> bool:
    """
    Strict, exact mapping:
    - Trim surrounding whitespace on headers
    - Match exactly to one of the allowed aliases
    - Rename the first match to the canonical name
    Returns True if mapped/found; False otherwise.
    """
    # normalize header whitespace once
    df.columns = df.columns.str.strip()
    # map of stripped->original (to preserve exact column casing if needed)
    cols_norm: Dict[str, str] = {c.strip(): c for c in df.columns}

    # Check canonical already present (after strip)
    if canonical in cols_norm:
        # Canonical already exists under (possibly) different original casing
        if cols_norm[canonical] != canonical:
            df.rename(columns={cols_norm[canonical]: canonical}, inplace=True)
        return True

    # Try each alias in order
    for a in aliases:
        if a in cols_norm:
            if cols_norm[a] != canonical:
                df.rename(columns={cols_norm[a]: canonical}, inplace=True)
            return True

    return False

def to_numeric(df: pd.DataFrame, cols: List[str]) -> None:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

# =====================================================
# STRICT ALIAS MAPS (old names + new 2025 names)
# Note: We keep Traffic & Keywords locked to combined organic totals only.
# =====================================================
AHREFS_DOMAIN_ALIASES = {
    # Target (root/domain field)
    "Target": [
        "Target", "Target URL", "Domain", "Root domain", "URL", "Target domain"
    ],
    # Domain Rating (DR)
    "Domain Rating": [
        "Domain Rating", "Domain Rating (DR)", "DR"
    ],
    # Referring domains (followed)
    "Ref domains Dofollow": [
        "Ref domains Dofollow",
        "Referring domains (dofollow)",
        "Referring domains dofollow",
        "Ref. domains (dofollow)",
        "Ref. domains / Followed",          # NEW (2025)
    ],
    # Linked domains (outgoing) - followed only
    "Linked Domains": [
        "Linked Domains",
        "Linked domains",
        "Outgoing domains / Followed",      # NEW (2025)
    ],
    # Organic traffic (combined total ONLY)
    "Total Traffic": [
        "Total Traffic",
        "Organic traffic",
        "Traffic",
        "Organic / Traffic",                # NEW (2025) - exact only
    ],
}

AHREFS_PAGE_ALIASES = {
    # Target page URL
    "Target": [
        "Target", "Target URL", "URL"
    ],
    # Organic keywords (combined total ONLY)
    "Total Keywords": [
        "Total Keywords",
        "Organic keywords",
        "Keywords",
        "Organic / Total Keywords",         # NEW (2025) - exact only
    ],
    # Organic traffic (combined total ONLY)
    "Total Traffic": [
        "Total Traffic",
        "Organic traffic",
        "Traffic",
        "Organic / Traffic",                # NEW (2025) - exact only
    ],
}

# =====================================================
# UI CONTROLS
# =====================================================
mode = st.radio(
    "What do you want to analyze?",
    ["Domain Metrics Only", "Page Metrics Only", "Both Combined"]
)

ahrefs_domain = majestic_domain = ahrefs_page = majestic_page = None

if mode in ["Domain Metrics Only", "Both Combined"]:
    st.subheader("📁 Domain-Level Files")
    ahrefs_domain = st.file_uploader(
        "Upload Ahrefs Domain CSV (UTF-16 tab-separated or UTF-8)",
        type=["csv", "tsv"], key="ahrefs_domain"
    )
    majestic_domain = st.file_uploader(
        "Upload Majestic Domain CSV (UTF-8)",
        type=["csv"], key="majestic_domain"
    )

if mode in ["Page Metrics Only", "Both Combined"]:
    st.subheader("📁 Page-Level Files")
    ahrefs_page = st.file_uploader(
        "Upload Ahrefs Page CSV (UTF-16 tab-separated or UTF-8)",
        type=["csv", "tsv"], key="ahrefs_page"
    )
    majestic_page = st.file_uploader(
        "Upload Majestic Page CSV (UTF-8)",
        type=["csv"], key="majestic_page"
    )

# =====================================================
# MAIN LOGIC
# =====================================================
try:
    # ----------------------------
    # DOMAIN METRICS ONLY
    # ----------------------------
    if mode == "Domain Metrics Only" and ahrefs_domain and majestic_domain:
        df_ahrefs = read_ahrefs_csv(ahrefs_domain)
        df_majestic = read_csv_flex(majestic_domain)

        # Normalize headers
        df_ahrefs.columns = df_ahrefs.columns.str.strip()
        df_majestic.columns = df_majestic.columns.str.strip()

        # Strict alias mapping for Ahrefs (errors if any canonical missing)
        missing = []
        for canon, aliases in AHREFS_DOMAIN_ALIASES.items():
            if not map_alias(df_ahrefs, canon, aliases):
                missing.append(canon)
        if missing:
            st.error("❌ Missing required Ahrefs Domain column(s): " + ", ".join(missing))
            st.stop()

        # Majestic must have "Item" and Trust/Citation/Topical columns
        if "Item" not in df_majestic.columns:
            st.error("❌ Missing 'Item' column in Majestic Domain file.")
            st.stop()

        # Normalize domains for joining
        df_ahrefs["Domain"] = normalize_domain_like(df_ahrefs["Target"])
        df_majestic["Domain"] = normalize_domain_like(df_majestic["Item"])

        # Coerce numerics
        to_numeric(df_ahrefs, ["Domain Rating", "Ref domains Dofollow", "Linked Domains", "Total Traffic"])
        to_numeric(df_majestic, [
            "TrustFlow", "CitationFlow",
            "TopicalTrustFlow_Value_0", "TopicalTrustFlow_Value_1", "TopicalTrustFlow_Value_2"
        ])

        # Merge
        domain = pd.merge(df_ahrefs, df_majestic, on="Domain", how="inner")
        if domain.empty:
            st.warning("No matching domains between Ahrefs and Majestic.")
            st.stop()

        # Safe ratios
        domain["LD:RD Ratio"] = domain["Linked Domains"] / domain["Ref domains Dofollow"].replace(0, pd.NA)
        domain["TF:CF Ratio"] = domain["TrustFlow"] / domain["CitationFlow"].replace(0, pd.NA)

        # Output
        output_cols = [
            "Domain", "Domain Rating", "Ref domains Dofollow", "Linked Domains",
            "TrustFlow", "CitationFlow",
            "TopicalTrustFlow_Topic_0", "TopicalTrustFlow_Value_0",
            "TopicalTrustFlow_Topic_1", "TopicalTrustFlow_Value_1",
            "TopicalTrustFlow_Topic_2", "TopicalTrustFlow_Value_2",
            "LD:RD Ratio", "TF:CF Ratio", "Total Traffic"
        ]
        # Some Topical columns may be absent in certain Majestic exports; guard with .get
        output = pd.DataFrame({
            "Domain": domain["Domain"],
            "Domain Rating": domain["Domain Rating"],
            "Ref domains Dofollow": domain["Ref domains Dofollow"],
            "Linked Domains": domain["Linked Domains"],
            "TrustFlow": domain.get("TrustFlow"),
            "CitationFlow": domain.get("CitationFlow"),
            "TopicalTrustFlow_Topic_0": domain.get("TopicalTrustFlow_Topic_0"),
            "TopicalTrustFlow_Value_0": domain.get("TopicalTrustFlow_Value_0"),
            "TopicalTrustFlow_Topic_1": domain.get("TopicalTrustFlow_Topic_1"),
            "TopicalTrustFlow_Value_1": domain.get("TopicalTrustFlow_Value_1"),
            "TopicalTrustFlow_Topic_2": domain.get("TopicalTrustFlow_Topic_2"),
            "TopicalTrustFlow_Value_2": domain.get("TopicalTrustFlow_Value_2"),
            "LD:RD Ratio": domain["LD:RD Ratio"],
            "TF:CF Ratio": domain["TF:CF Ratio"],
            "Total Traffic": domain["Total Traffic"],
        })

        st.success("✅ Domain metrics processed!")
        st.dataframe(output, use_container_width=True)
        st.download_button("📥 Download Domain CSV", output.to_csv(index=False), "domain_metrics.csv")

    # ----------------------------
    # PAGE METRICS ONLY
    # ----------------------------
    elif mode == "Page Metrics Only" and ahrefs_page and majestic_page:
        df_ahrefs = read_ahrefs_csv(ahrefs_page)
        df_majestic = read_csv_flex(majestic_page)

        df_ahrefs.columns = df_ahrefs.columns.str.strip()
        df_majestic.columns = df_majestic.columns.str.strip()

        # Strict alias mapping for Ahrefs Page
        missing = []
        for canon, aliases in AHREFS_PAGE_ALIASES.items():
            if not map_alias(df_ahrefs, canon, aliases):
                missing.append(canon)
        if missing:
            st.error("❌ Missing required Ahrefs Page column(s): " + ", ".join(missing))
            st.stop()

        if "Item" not in df_majestic.columns:
            st.error("❌ Missing 'Item' column in Majestic Page file.")
            st.stop()

        # Normalize URLs and coerce numerics
        df_ahrefs["Page URL"] = normalize_page_url(df_ahrefs["Target"])
        df_majestic["Page URL"] = normalize_page_url(df_majestic["Item"])

        to_numeric(df_ahrefs, ["Total Keywords", "Total Traffic"])
        to_numeric(df_majestic, ["TrustFlow", "CitationFlow"])

        page = pd.merge(
            df_ahrefs[["Page URL", "Total Keywords", "Total Traffic"]],
            df_majestic[["Page URL", "TrustFlow", "CitationFlow"]],
            on="Page URL",
            how="inner"
        )

        if page.empty:
            st.warning("No matching page URLs between Ahrefs and Majestic.")
            st.stop()

        output = page.rename(columns={
            "Total Keywords": "Page URL Total Keywords",
            "Total Traffic": "Page URL Total Traffic",
            "TrustFlow": "Page URL TrustFlow",
            "CitationFlow": "Page URL CitationFlow"
        })

        st.success("✅ Page metrics processed!")
        st.dataframe(output, use_container_width=True)
        st.download_button("📥 Download Page CSV", output.to_csv(index=False), "page_metrics.csv")

    # ----------------------------
    # BOTH COMBINED
    # ----------------------------
    elif mode == "Both Combined" and all([ahrefs_domain, majestic_domain, ahrefs_page, majestic_page]):
        # --- DOMAIN side ---
        df_ahrefs_d = read_ahrefs_csv(ahrefs_domain)
        df_majestic_d = read_csv_flex(majestic_domain)
        df_ahrefs_d.columns = df_ahrefs_d.columns.str.strip()
        df_majestic_d.columns = df_majestic_d.columns.str.strip()

        missing_d = []
        for canon, aliases in AHREFS_DOMAIN_ALIASES.items():
            if not map_alias(df_ahrefs_d, canon, aliases):
                missing_d.append(canon)
        if missing_d:
            st.error("❌ Missing required Ahrefs Domain column(s): " + ", ".join(missing_d))
            st.stop()

        if "Item" not in df_majestic_d.columns:
            st.error("❌ Missing 'Item' column in Majestic Domain file.")
            st.stop()

        df_ahrefs_d["Domain"] = normalize_domain_like(df_ahrefs_d["Target"])
        df_majestic_d["Domain"] = normalize_domain_like(df_majestic_d["Item"])

        to_numeric(df_ahrefs_d, ["Domain Rating", "Ref domains Dofollow", "Linked Domains", "Total Traffic"])
        to_numeric(df_majestic_d, [
            "TrustFlow", "CitationFlow",
            "TopicalTrustFlow_Value_0", "TopicalTrustFlow_Value_1", "TopicalTrustFlow_Value_2"
        ])

        domain = pd.merge(
            df_ahrefs_d[["Domain", "Domain Rating", "Ref domains Dofollow", "Linked Domains", "Total Traffic"]],
            df_majestic_d[[
                "Domain", "TrustFlow", "CitationFlow",
                "TopicalTrustFlow_Topic_0", "TopicalTrustFlow_Value_0",
                "TopicalTrustFlow_Topic_1", "TopicalTrustFlow_Value_1",
                "TopicalTrustFlow_Topic_2", "TopicalTrustFlow_Value_2"
            ]],
            on="Domain", how="inner"
        )
        if domain.empty:
            st.warning("No matching domains between Ahrefs and Majestic.")
            st.stop()

        domain["LD:RD Ratio"] = domain["Linked Domains"] / domain["Ref domains Dofollow"].replace(0, pd.NA)
        domain["TF:CF Ratio"] = domain["TrustFlow"] / domain["CitationFlow"].replace(0, pd.NA)

        # --- PAGE side ---
        df_ahrefs_p = read_ahrefs_csv(ahrefs_page)
        df_majestic_p = read_csv_flex(majestic_page)
        df_ahrefs_p.columns = df_ahrefs_p.columns.str.strip()
        df_majestic_p.columns = df_majestic_p.columns.str.strip()

        missing_p = []
        for canon, aliases in AHREFS_PAGE_ALIASES.items():
            if not map_alias(df_ahrefs_p, canon, aliases):
                missing_p.append(canon)
        if missing_p:
            st.error("❌ Missing required Ahrefs Page column(s): " + ", ".join(missing_p))
            st.stop()

        if "Item" not in df_majestic_p.columns:
            st.error("❌ Missing 'Item' column in Majestic Page file.")
            st.stop()

        df_ahrefs_p["Page URL"] = normalize_page_url(df_ahrefs_p["Target"])
        df_majestic_p["Page URL"] = normalize_page_url(df_majestic_p["Item"])

        to_numeric(df_ahrefs_p, ["Total Keywords", "Total Traffic"])
        to_numeric(df_majestic_p, ["TrustFlow", "CitationFlow"])

        page = pd.merge(
            df_ahrefs_p[["Page URL", "Total Keywords", "Total Traffic"]],
            df_majestic_p[["Page URL", "TrustFlow", "CitationFlow"]],
            on="Page URL",
            how="inner"
        )

        # Map pages to root domain for left-join to domain table
        page["Domain"] = page["Page URL"].apply(extract_root_domain).str.lower()

        combined = pd.merge(domain, page, on="Domain", how="left", suffixes=("", "_page"))

        # Fill page-level NaNs where missing
        combined["Page URL"] = combined["Page URL"].fillna("")
        for c in ["Total Keywords", "Total Traffic_page", "TrustFlow_page", "CitationFlow_page"]:
            if c in combined.columns:
                combined[c] = pd.to_numeric(combined[c], errors="coerce").fillna(0)

        # Final tidy output (no _x/_y confusion)
        final = pd.DataFrame({
            "Domain": combined["Domain"],
            "Domain Rating": combined["Domain Rating"],
            "Ref domains Dofollow": combined["Ref domains Dofollow"],
            "Linked Domains": combined["Linked Domains"],
            "TrustFlow": combined.get("TrustFlow"),
            "CitationFlow": combined.get("CitationFlow"),
            "TopicalTrustFlow_Topic_0": combined.get("TopicalTrustFlow_Topic_0"),
            "TopicalTrustFlow_Value_0": combined.get("TopicalTrustFlow_Value_0"),
            "TopicalTrustFlow_Topic_1": combined.get("TopicalTrustFlow_Topic_1"),
            "TopicalTrustFlow_Value_1": combined.get("TopicalTrustFlow_Value_1"),
            "TopicalTrustFlow_Topic_2": combined.get("TopicalTrustFlow_Topic_2"),
            "TopicalTrustFlow_Value_2": combined.get("TopicalTrustFlow_Value_2"),
            "LD:RD Ratio": combined["LD:RD Ratio"],
            "TF:CF Ratio": combined["TF:CF Ratio"],
            "Total Traffic": combined["Total Traffic"],               # domain-level combined organic traffic
            "Page URL": combined["Page URL"],
            "Page URL Total Keywords": combined["Total Keywords"],
            "Page URL Total Traffic": combined["Total Traffic_page"],
            "Page URL TrustFlow": combined["TrustFlow_page"],
            "Page URL CitationFlow": combined["CitationFlow_page"],
        })

        st.success("✅ Combined domain + page metrics generated!")
        st.dataframe(final, use_container_width=True)
        st.download_button("📥 Download Combined CSV", final.to_csv(index=False), "domain_page_combined.csv")

except Exception as e:
    st.error(f"❌ Error: {e}")
