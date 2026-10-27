import time
import matplotlib.colors as mcolors
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
import streamlit as st

st.set_page_config(
    page_title="West Africa Energy Transition Explorer",
    page_icon="⚡",
    layout="wide",
)

# Professional Styling & Presentation Polish for Dark Theme
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
    h3 { font-size: 1.35rem !important; font-weight: 700 !important; margin-bottom: 0.1rem !important; color: #FFFFFF !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# Main Title as Requested
st.markdown("### An Evaluation of SDG Indicator 7.2.1 in West Africa (2015 - 2024)")
st.markdown(
    "Interactive regional dashboard tracking **TFEC (PJ)**, **Total"
    " Renewables**, **Modern Renewables**, and **Traditional Biomass** across all"
    " 15 ECOWAS Member States."
)


# Load local ECOWAS Excel File
@st.cache_data
def load_ecowas_data():
  filename = "ECOWAS DATA 22.xlsx"
  try:
    df_raw = pd.read_excel(filename)
    return df_raw
  except Exception as e:
    st.error(f"Error loading '{filename}': {e}")
    return pd.DataFrame()


df_excel = load_ecowas_data()

if df_excel.empty:
  st.warning(
      "Please ensure 'ECOWAS DATA 22.xlsx' and 'openpyxl' are uploaded in your"
      " repository."
  )
else:
  # Melt wide-format years (2015..2024) into a tidy format
  year_cols = [
      c for c in df_excel.columns if str(c).isdigit() and int(c) >= 2015
  ]
  df_melted = df_excel.melt(
      id_vars=["Country", "Type"],
      value_vars=year_cols,
      var_name="Year",
      value_name="Value",
  )

  df_melted["Year"] = pd.to_numeric(df_melted["Year"], errors="coerce")
  df_melted["Value"] = pd.to_numeric(df_melted["Value"], errors="coerce")
  df_melted = df_melted.rename(
      columns={"Country": "geoAreaName", "Type": "seriesDescription"}
  )
  df_melted["geoAreaName"] = df_melted["geoAreaName"].astype(str).str.strip()
  df_melted["seriesDescription"] = df_melted["seriesDescription"].str.strip()

  all_countries = [
      "Benin",
      "Burkina Faso",
      "Cabo Verde",
      "Côte d'Ivoire",
      "Gambia",
      "Ghana",
      "Guinea",
      "Guinea-Bissau",
      "Liberia",
      "Mali",
      "Niger",
      "Nigeria",
      "Senegal",
      "Sierra Leone",
      "Togo",
  ]

  iso_mapping = {
      "Benin": "BEN",
      "Burkina Faso": "BFA",
      "Cabo Verde": "CPV",
      "Côte d'Ivoire": "CIV",
      "Gambia": "GMB",
      "Ghana": "GHA",
      "Guinea": "GIN",
      "Guinea-Bissau": "GNB",
      "Liberia": "LBR",
      "Mali": "MLI",
      "Niger": "NER",
      "Nigeria": "NGA",
      "Senegal": "SEN",
      "Sierra Leone": "SLE",
      "Togo": "TGO",
  }

  # Sidebar Controls
  st.sidebar.header("⚙️ Dashboard Controls")

  all_types = df_melted["seriesDescription"].unique().tolist()
  selected_series = st.sidebar.selectbox(
      "Select Data Category / Indicator:", options=all_types, index=0
  )

  df_filtered = df_melted[df_melted["seriesDescription"] == selected_series]
  available_years = sorted(df_filtered["Year"].dropna().unique().astype(int))

  if available_years:
    st.sidebar.markdown("---")
    st.sidebar.subheader("▶️ General Playback Controls")

    if "current_year_idx" not in st.session_state:
      st.session_state.current_year_idx = 0
    if "is_playing" not in st.session_state:
      st.session_state.is_playing = False

    col_p1, col_p2 = st.sidebar.columns(2)
    if col_p1.button("▶️ Play"):
      st.session_state.is_playing = True
    if col_p2.button("⏸️ Pause"):
      st.session_state.is_playing = False

    playback_speed = st.sidebar.slider(
        "Transition Speed (seconds):", 0.3, 2.0, 0.7
    )

    selected_year = st.sidebar.select_slider(
        "Select Year Manually:",
        options=available_years,
        value=available_years[st.session_state.current_year_idx],
    )

    if selected_year != available_years[st.session_state.current_year_idx]:
      st.session_state.current_year_idx = available_years.index(selected_year)


    # Wrapped in @st.fragment for smooth, flicker-free auto-play updates
    @st.fragment
    def render_animated_dashboard():
      curr_year = available_years[st.session_state.current_year_idx]

      sns_cmap = sns.color_palette("YlGnBu", as_cmap=True)
      custom_color_scale = [
          [0.0, mcolors.to_hex(sns_cmap(0.15))],
          [0.5, mcolors.to_hex(sns_cmap(0.55))],
          [1.0, mcolors.to_hex(sns_cmap(0.95))],
      ]

      df_year_raw = df_filtered[df_filtered["Year"] == curr_year]
      df_year_full = pd.DataFrame(
          {"geoAreaName": all_countries, "Year": curr_year}
      )
      df_year_full = df_year_full.merge(
          df_year_raw[["geoAreaName", "Value"]], on="geoAreaName", how="left"
      )
      df_year_full["ISO3"] = df_year_full["geoAreaName"].map(iso_mapping)
      df_year_full["DisplayValue"] = df_year_full["Value"].fillna(-1)
      df_year_full["TextLabel"] = df_year_full["Value"].apply(
          lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A"
      )
      df_year_sorted = df_year_full.sort_values(
          by="Value", ascending=True, na_position="first"
      )

      valid_vals = df_year_raw["Value"].dropna()
      regional_avg = valid_vals.mean() if not valid_vals.empty else 0.0

      prev_year = curr_year - 1
      df_prev_raw = df_filtered[df_filtered["Year"] == prev_year]
      prev_valid = df_prev_raw["Value"].dropna()
      prev_avg = prev_valid.mean() if not prev_valid.empty else regional_avg
      delta_avg = regional_avg - prev_avg

      st.markdown("---")
      c1, c2, c3 = st.columns(3)
      c1.metric(
          label=f"🌍 Regional Mean ({curr_year})",
          value=f"{regional_avg:.2f}",
