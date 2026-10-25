import time
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="West Africa Energy & SDG 7.2.1 Explorer",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ West Africa Energy Transition Dashboard (2015–2024)")
st.markdown(
    "Analyzing **Total Renewables**, **Modern Renewables**, and **Traditional"
    " Biomass** across West African Nations from local ECOWAS dataset."
)


# Load data from the uploaded Excel file in the repository root
@st.cache_data
def load_ecowas_excel():
  filename = "ECOWAS DATA 22.xlsx"
  try:
    df_raw = pd.read_excel(filename)
    return df_raw
  except Exception as e:
    st.error(
        f"Could not load '{filename}': {e}. Please check the exact file name in"
        " your repository."
    )
    return pd.DataFrame()


df_excel = load_ecowas_excel()

if df_excel.empty:
  st.warning("Please ensure 'ECOWAS DATA 22.xlsx' is uploaded in your repository.")
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

  # Data cleansing
  df_melted["Year"] = pd.to_numeric(df_melted["Year"], errors="coerce")
  df_melted["Value"] = pd.to_numeric(df_melted["Value"], errors="coerce")
  df_melted = df_melted.rename(
      columns={"Country": "geoAreaName", "Type": "seriesDescription"}
  )
  df_filtered_all = df_melted.dropna(subset=["Value", "Year"])

  # Sidebar Controls
  st.sidebar.header("⚙️ Dashboard Controls")

  # Manual switch between metrics as requested
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

    col_btn1, col_btn2 = st.sidebar.columns(2)
    if col_btn1.button("▶️ Play Loop"):
      st.session_state.is_playing = True
    if col_btn2.button("⏸️ Pause"):
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

    # Layout Tabs
    tab1, tab2, tab3 = st.tabs(
        ["🗺️ Dynamic Map & Rankings", "📊 Matrix Heatmap", "📈 Raw Data"]
    )

    with tab1:
      st.subheader(
          f"Indicator: **{selected_series}** — Year: **{selected_year}**"
      )
      df_year = df_filtered[df_filtered["Year"] == selected_year]

      col1, col2 = st.columns([3, 2])

      with col1:
        # Choropleth Map with dynamic values written/hovered
        fig_map = px.choropleth(
            df_year,
            locations="geoAreaName",
            locationmode="country names",
            color="Value",
            hover_name="geoAreaName",
            color_continuous_scale="YlGnBu",
            labels={"Value": "Share / Value"},
            title=f"Geographic Map ({selected_year})",
        )
        fig_map.update_geos(
            fitbounds="locations", visible=True, showcountries=True
        )
        fig_map.update_layout(height=450, margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)

      with col2:
        # Dynamic Ranked Bar Chart
        fig_bar = px.bar(
            df_year.sort_values(by="Value", ascending=True),
            x="Value",
            y="geoAreaName",
            orientation="h",
            color="Value",
            color_continuous_scale="YlGnBu",
            text="Value",
            labels={"Value": "Value", "geoAreaName": "Country"},
            title=f"Country Rankings ({selected_year})",
        )
        fig_bar.update_traces(texttemplate="%{text:.1f}", textposition="outside")
        fig_bar.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
      st.subheader(
          f"Matrix Heatmap (2015–2024) for {selected_series}"
      )
      pivot_df = df_filtered.pivot_table(
          index="geoAreaName", columns="Year", values="Value"
      )

      if not pivot_df.empty:
        fig_heatmap = px.imshow(
            pivot_df,
            labels=dict(x="Year", y="Country", color="Value"),
            x=[str(y) for y in pivot_df.columns],
            y=pivot_df.index,
            color_continuous_scale="YlGnBu",
            text_auto=".1f",
            aspect="auto",
        )
        fig_heatmap.update_layout(height=550)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    with tab3:
      st.subheader("Filtered Dataset Table")
      st.dataframe(df_filtered, use_container_width=True)
