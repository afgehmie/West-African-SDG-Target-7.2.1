import time
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="West Africa Energy Transition Dashboard",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ West Africa Energy Transition Dashboard (2015–2024)")
st.markdown(
    "Comprehensive regional analysis tracking **Total Renewables**, **Modern"
    " Renewables**, and **Traditional Biomass** across West African Nations."
)


# Load ECOWAS Excel dataset
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
      "Please ensure 'ECOWAS DATA 22.xlsx' and 'openpyxl' are in your repository."
  )
else:
  # Melt wide-format year columns into tidy format
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
  df_filtered_all = df_melted.dropna(subset=["Value", "Year"])

  # Map Country Names to ISO-3 codes for reliable mapping
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
  df_filtered_all["ISO3"] = df_filtered_all["geoAreaName"].map(iso_mapping)

  # Sidebar Controls
  st.sidebar.header("⚙️ Dashboard Controls")

  series_options = [
      "Total Renewables",
      "Modern renewables",
      "Traditional Biomass",
      "TFEC(PJ)",
  ]
  available_series = [
      s for s in series_options if s in df_filtered_all["seriesDescription"].unique()
  ]
  if not available_series:
    available_series = df_filtered_all["seriesDescription"].unique().tolist()

  selected_series = st.sidebar.selectbox(
      "Select Energy Category:", options=available_series
  )

  df_filtered = df_filtered_all[
      df_filtered_all["seriesDescription"] == selected_series
  ]
  available_years = sorted(df_filtered["Year"].dropna().unique().astype(int))

  if available_years:
    st.sidebar.markdown("---")
    st.sidebar.subheader("▶️ Automated Year Playback")

    if "is_playing" not in st.session_state:
      st.session_state.is_playing = False
    if "current_year_idx" not in st.session_state:
      st.session_state.current_year_idx = 0

    col_b1, col_b2 = st.sidebar.columns(2)
    if col_b1.button("▶️ Play Loop"):
      st.session_state.is_playing = True
    if col_b2.button("⏸️ Pause"):
      st.session_state.is_playing = False

    playback_speed = st.sidebar.slider(
        "Transition Speed (seconds)", 0.5, 3.0, 1.2
    )

    if st.session_state.is_playing:
      time.sleep(playback_speed)
      st.session_state.current_year_idx = (
          st.session_state.current_year_idx + 1
      ) % len(available_years)
      st.rerun()

    selected_year = st.sidebar.select_slider(
        "Select Year Manually:",
        options=available_years,
        value=available_years[st.session_state.current_year_idx],
    )

    # --- REGIONAL METRICS CALCULATION ---
    df_year = df_filtered[df_filtered["Year"] == selected_year]
    regional_avg = df_year["Value"].mean()

    # Calculate previous year for movement comparison
    prev_year = selected_year - 1
    df_prev = df_filtered[df_filtered["Year"] == prev_year]
    prev_regional_avg = (
        df_prev["Value"].mean() if not df_prev.empty else regional_avg
    )
    avg_change = regional_avg - prev_regional_avg

    # --- TOP METRIC BANNER ---
    st.markdown("---")
    m1, m2, m3 = st.columns(3)
    m1.metric(
        label=f"🌍 Regional Average ({selected_year})",
        value=f"{regional_avg:.2f}",
        delta=f"{avg_change:+.2f} vs {prev_year}"
        if prev_year in available_years
        else "Baseline",
    )
    m2.metric(
        label="📊 Active Indicator",
        value=selected_series,
        delta=f"{len(df_year)} Countries Reporting",
    )
    m3.metric(
        label="⏱️ Playback Status",
        value="Playing 🔄" if st.session_state.is_playing else "Paused ⏸️",
        delta=f"Year {selected_year}",
    )
    st.markdown("---")

    # Custom Color Scale: Cream (Least) -> Green (Average) -> Blue (Best)
    custom_color_scale = [
        [0.0, "#FFFDD0"],  # Cream (Lowest performers)
        [0.5, "#2ECC71"],  # Green (Average performers)
        [1.0, "#1B4F72"],  # Blue (Best performers)
    ]

    # --- FOUR MAIN DASHBOARD SECTIONS ON ONE SCREEN ---
    st.subheader(
        f"🎯 Multi-Metric Overview for {selected_series} ({selected_year})"
    )

    # Row 1: Map and Country Bar Chart
    col_map, col_bar = st.columns(2)

    with col_map:
      st.markdown(### `🗺️ 1. Country-Level Geographic Map`)
      if not df_year.empty:
        fig_map = px.choropleth(
            df_year,
            locations="ISO3",
            color="Value",
            hover_name="geoAreaName",
            color_continuous_scale=custom_color_scale,
            labels={"Value": "Value"},
            scope="africa",
        )
        fig_map.update_geos(
            fitbounds="locations", visible=True, showcountries=True
        )
        fig_map.update_layout(
            height=400, margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_bar:
      st.markdown(### `📊 2. Country Rankings Bar Chart`)
      if not df_year.empty:
        fig_bar = px.bar(
            df_year.sort_values(by="Value", ascending=True),
            x="Value",
            y="geoAreaName",
            orientation="h",
            color="Value",
            color_continuous_scale=custom_color_scale,
            text="Value",
            labels={"Value": "Value", "geoAreaName": "Country"},
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_bar.update_layout(
            height=400, showlegend=False, margin={"r": 0, "t": 0, "l": 0, "b": 0}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Row 2: Regional Trend & Annual Transition Matrix Heatmap
    col_trend, col_heat = st.columns(2)

    with col_trend:
      st.markdown(### `📈 3. Regional Average Annual Trend`)
      regional_trend = (
          df_filtered.groupby("Year")["Value"].mean().reset_index()
      )
      fig_trend = px.line(
          regional_trend,
          x="Year",
          y="Value",
          markers=True,
          labels={"Value": "Regional Mean Value", "Year": "Year"},
          title="Regional Trajectory (2015–2024)",
      )
      fig_trend.update_traces(
          line_color="#2980B9", line_width=3, marker_size=8
      )
      fig_trend.update_layout(
          height=400, margin={"r": 0, "t": 40, "l": 0, "b": 0}
      )
      st.plotly_chart(fig_trend, use_container_width=True)

    with col_heat:
      st.markdown(### `📉 4. Annual Transition Matrix Heatmap`)
      pivot_df = df_filtered.pivot_table(
          index="geoAreaName", columns="Year", values="Value"
      )
      if not pivot_df.empty:
        fig_heatmap = px.imshow(
            pivot_df,
            labels=dict(x="Year", y="Country", color="Value"),
            x=[str(y) for y in pivot_df.columns],
            y=pivot_df.index,
            color_continuous_scale=custom_color_scale,
            text_auto=".1f",
            aspect="auto",
        )
        fig_heatmap.update_layout(
            height=400, margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
