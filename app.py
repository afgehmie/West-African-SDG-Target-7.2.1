import time
import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="West Africa SDG 7.2.1 Explorer", page_icon="⚡", layout="wide"
)

st.title("⚡ West Africa SDG Target 7.2.1 Dashboard")
st.markdown(
    "Tracking **Renewable Energy Share in Total Final Energy Consumption** across"
    " 15 West African Nations (2015 onwards)."
)


# Fetch Data from UN API
@st.cache_data(ttl=3600)
def load_un_sdg_data():
  url = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/Data?indicator=7.2.1&pageSize=4000"
  try:
    res = requests.get(url, timeout=10)
    if res.status_code == 200:
      data = res.json().get("data", [])
      df = pd.DataFrame(data)
      return df
  except Exception as e:
    st.error(f"API Connection Error: {e}")
  return pd.DataFrame()


with st.spinner("Retrieving UN SDG 7.2.1 Dataset..."):
  df_raw = load_un_sdg_data()

# 15 ECOWAS West African Countries
WEST_AFRICA_COUNTRIES = [
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

if df_raw.empty:
  st.warning(
      "Unable to pull live UN API data. Please verify network access or try"
      " again later."
  )
else:
  # Filter Data
  df_wa = df_raw[df_raw["geoAreaName"].isin(WEST_AFRICA_COUNTRIES)].copy()
  df_wa["Year"] = pd.to_numeric(df_wa["timePeriodStart"], errors="coerce")
  df_wa["Value"] = pd.to_numeric(df_wa["Value"], errors="coerce")
  df_wa = df_wa[df_wa["Year"] >= 2015]

  # Sidebar Options
  st.sidebar.header("⚙️ Dashboard Controls")

  # 1. Manual Indicator Transition (Total vs Modern Renewables)
  series_list = df_wa["seriesDescription"].dropna().unique().tolist()
  selected_series = st.sidebar.radio(
      "Select Energy Share Indicator:",
      options=series_list if series_list else ["EG_FEC_RNEW - Renewable share"],
  )

  df_filtered = df_wa[df_wa["seriesDescription"] == selected_series]

  # Get available years
  available_years = sorted(df_filtered["Year"].dropna().unique().astype(int))

  if available_years:
    st.sidebar.markdown("---")
    st.sidebar.subheader("▶️ Automated Year Playback")

    # Animation Control State
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

    # Year Selector Slider
    selected_year = st.sidebar.select_slider(
        "Select Year Manually:",
        options=available_years,
        value=available_years[st.session_state.current_year_idx],
    )

    # Automated Step logic
    if st.session_state.is_playing:
      time.sleep(playback_speed)
      st.session_state.current_year_idx = (
          st.session_state.current_year_idx + 1
      ) % len(available_years)
      st.rerun()

    # Layout Tabs
    tab1, tab2, tab3 = st.tabs(
        ["🗺️ Interactive Map & Year View", "📊 Matrix Heatmap", "📈 Data Table"]
    )

    with tab1:
      st.subheader(f"Geographic Distribution — {selected_year}")
      df_year = df_filtered[df_filtered["Year"] == selected_year]

      col1, col2 = st.columns([3, 2])

      with col1:
        # Choropleth Map
        fig_map = px.choropleth(
            df_year,
            locations="geoAreaName",
            locationmode="country names",
            color="Value",
            hover_name="geoAreaName",
            color_continuous_scale="Viridis",
            range_color=[0, 100],
            labels={"Value": "Share (%)"},
            title=f"West Africa Renewable Energy Share ({selected_year})",
        )
        fig_map.update_geos(
            fitbounds="locations", visible=True, showcountries=True
        )
        fig_map.update_layout(height=450, margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)

      with col2:
        # Ranked Bar Chart for Selected Year
        fig_bar = px.bar(
            df_year.sort_values(by="Value", ascending=True),
            x="Value",
            y="geoAreaName",
            orientation="h",
            color="Value",
            color_continuous_scale="Viridis",
            labels={"Value": "Share (%)", "geoAreaName": "Country"},
            title=f"Country Rankings ({selected_year})",
        )
        fig_bar.update_layout(height=450, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
      st.subheader("2015–Present Country vs. Year Heatmap")
      pivot_df = df_filtered.pivot_table(
          index="geoAreaName", columns="Year", values="Value"
      )

      if not pivot_df.empty:
        fig_heatmap = px.imshow(
            pivot_df,
            labels=dict(x="Year", y="Country", color="Share (%)"),
            x=[str(y) for y in pivot_df.columns],
            y=pivot_df.index,
            color_continuous_scale="YlGnBu",
            aspect="auto",
        )
        fig_heatmap.update_layout(height=550)
        st.plotly_chart(fig_heatmap, use_container_width=True)
      else:
        st.info("No matrix data available for the selected indicator.")

    with tab3:
      st.subheader("Raw Data Summary")
      st.dataframe(
          df_filtered[["geoAreaName", "Year", "Value", "seriesDescription"]],
          use_container_width=True,
      )

  else:
    st.error("No valid year data found for West Africa.")
