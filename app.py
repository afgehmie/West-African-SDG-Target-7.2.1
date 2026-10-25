import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="West Africa Energy Transition Explorer",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ West Africa Energy Transition Dashboard (2015–2024)")
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

  # Standardize series descriptions
  df_melted["seriesDescription"] = df_melted["seriesDescription"].str.strip()
  df_filtered_all = df_melted.dropna(subset=["Value", "Year"])

  # Comprehensive ISO-3 Code mapping for all West African countries
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

  # Full Metric Selection
  all_types = df_filtered_all["seriesDescription"].unique().tolist()
  selected_series = st.sidebar.selectbox(
      "Select Data Category / Indicator:",
      options=all_types,
      index=0,
  )

  df_filtered = df_filtered_all[
      df_filtered_all["seriesDescription"] == selected_series
  ].sort_values(by=["Year", "geoAreaName"])
  available_years = sorted(df_filtered["Year"].dropna().unique().astype(int))

  if available_years:
    st.sidebar.markdown("---")
    st.sidebar.subheader("▶️ Playback & Year Selector")

    selected_year = st.sidebar.select_slider(
        "Select Year Manually:",
        options=available_years,
        value=available_years[0],
    )

    auto_play = st.sidebar.checkbox(
        "▶️ Auto-Play Smooth Transition Across Years", value=False
    )

    # Performance Color Scale: Cream (Least) -> Green (Average) -> Blue (Best)
    custom_color_scale = [
        [0.0, "#FFFDD0"],  # Cream
        [0.5, "#2ECC71"],  # Green
        [1.0, "#1B4F72"],  # Blue
    ]

    # --- TOP METRIC CARDS ---
    df_curr = df_filtered[df_filtered["Year"] == selected_year]
    regional_avg = df_curr["Value"].mean() if not df_curr.empty else 0.0

    prev_year = selected_year - 1
    df_prev = df_filtered[df_filtered["Year"] == prev_year]
    prev_avg = df_prev["Value"].mean() if not df_prev.empty else regional_avg
    delta_avg = regional_avg - prev_avg

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    c1.metric(
        label=f"🌍 Regional Mean ({selected_year})",
        value=f"{regional_avg:.2f}",
        delta=f"{delta_avg:+.2f} vs {prev_year}"
        if prev_year in available_years
        else "Baseline",
    )
    c2.metric(
        label="📊 Active Category",
        value=selected_series,
        delta=f"{len(df_curr)} Countries Reporting",
    )
    c3.metric(
        label="📅 Timeframe Covered",
        value=f"{min(available_years)} – {max(available_years)}",
        delta="10 Years Tracked",
    )
    st.markdown("---")

    # --- ALL 4 MAIN DASHBOARD SECTIONS DISPLAYED SIMULTANEOUSLY ---
    col_map, col_bar = st.columns(2)

    if auto_play:
      # Plotly Native Animated Map (Smooth transition without screen blinking)
      with col_map:
        st.markdown("### 🗺️ 1. Regional Map (Smooth Auto-Transition)")
        fig_anim_map = px.choropleth(
            df_filtered,
            locations="ISO3",
            color="Value",
            hover_name="geoAreaName",
            animation_frame="Year",
            color_continuous_scale=custom_color_scale,
            scope="africa",
            labels={"Value": selected_series},
        )
        fig_anim_map.update_geos(
            fitbounds="locations", visible=True, showcountries=True
        )
        fig_anim_map.update_layout(
            height=450, margin={"r": 0, "t": 20, "l": 0, "b": 0}
        )
        st.plotly_chart(fig_anim_map, use_container_width=True)

      with col_bar:
        st.markdown("### 📊 2. Country Rankings (Smooth Auto-Transition)")
        fig_anim_bar = px.bar(
            df_filtered,
            x="Value",
            y="geoAreaName",
            color="Value",
            animation_frame="Year",
            orientation="h",
            color_continuous_scale=custom_color_scale,
            text="Value",
            labels={"Value": selected_series, "geoAreaName": "Country"},
        )
        fig_anim_bar.update_traces(
            texttemplate="%{text:.1f}", textposition="outside"
        )
        fig_anim_bar.update_layout(
            height=450,
            showlegend=False,
            margin={"r": 0, "t": 20, "l": 0, "b": 0},
        )
        st.plotly_chart(fig_anim_bar, use_container_width=True)

    else:
      # Static Single-Year View
      with col_map:
        st.markdown(f"### 🗺️ 1. Regional Map ({selected_year})")
        if not df_curr.empty:
          fig_map = px.choropleth(
              df_curr,
              locations="ISO3",
              color="Value",
              hover_name="geoAreaName",
              color_continuous_scale=custom_color_scale,
              scope="africa",
              labels={"Value": selected_series},
          )
          fig_map.update_geos(
              fitbounds="locations", visible=True, showcountries=True
          )
          fig_map.update_layout(
              height=450, margin={"r": 0, "t": 20, "l": 0, "b": 0}
          )
          st.plotly_chart(fig_map, use_container_width=True)

      with col_bar:
        st.markdown(f"### 📊 2. Country Rankings ({selected_year})")
        if not df_curr.empty:
          fig_bar = px.bar(
              df_curr.sort_values(by="Value", ascending=True),
              x="Value",
              y="geoAreaName",
              orientation="h",
              color="Value",
              color_continuous_scale=custom_color_scale,
              text="Value",
              labels={"Value": selected_series, "geoAreaName": "Country"},
          )
          fig_bar.update_traces(
              texttemplate="%{text:.1f}", textposition="outside"
          )
          fig_bar.update_layout(
              height=450,
              showlegend=False,
              margin={"r": 0, "t": 20, "l": 0, "b": 0},
          )
          st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Lower Row: Regional Trajectory & Transition Matrix Heatmap
    col_trend, col_heat = st.columns(2)

    with col_trend:
      st.markdown("### 📈 3. Regional Average Trend (2015–2024)")
      regional_trend = (
          df_filtered.groupby("Year")["Value"].mean().reset_index()
      )
      fig_trend = px.line(
          regional_trend,
          x="Year",
          y="Value",
          markers=True,
          labels={"Value": "Regional Mean", "Year": "Year"},
      )
      fig_trend.update_traces(
          line_color="#1B4F72", line_width=3, marker_size=8
      )
      fig_trend.update_layout(
          height=400, margin={"r": 0, "t": 20, "l": 0, "b": 0}
      )
      st.plotly_chart(fig_trend, use_container_width=True)

    with col_heat:
      st.markdown("### 📉 4. Transition Matrix Heatmap (All Years)")
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
            height=400, margin={"r": 0, "t": 20, "l": 0, "b": 0}
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
