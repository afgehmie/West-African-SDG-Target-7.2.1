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
          delta=f"{delta_avg:+.2f} vs {prev_year}"
          if prev_year in available_years
          else "Baseline",
      )
      c2.metric(
          label="📊 Active Indicator",
          value=selected_series,
          delta=f"{len(valid_vals)} / {len(all_countries)} Reporting",
      )
      c3.metric(
          label="📅 Active Timeline",
          value=f"Year: {curr_year}",
          delta="Auto-Playing 🔄" if st.session_state.is_playing else "Paused ⏸️",
      )
      st.markdown("---")

      # --- FOUR CORE DASHBOARD COMPONENTS ---
      col_map, col_bar = st.columns([1.1, 1.0])

      with col_map:
        st.markdown(f"### 🗺️ 1. West Africa Regional Map — Year: {curr_year}")
        fig_map = px.choropleth(
            df_year_full,
            locations="ISO3",
            color="DisplayValue",
            hover_name="geoAreaName",
            color_continuous_scale=custom_color_scale,
            range_color=[
                0,
                df_filtered["Value"].max()
                if not df_filtered["Value"].dropna().empty
                else 100,
            ],
            scope="africa",
            labels={"DisplayValue": selected_series},
            template="plotly_dark",
        )
        fig_map.update_geos(
            center=dict(lat=10.5, lon=-6.5),
            projection_scale=3.5,
            visible=False,
            showcountries=True,
            countrycolor="#444444",
            countrywidth=1.0,
            bgcolor="rgba(0,0,0,0)",
        )
        fig_map.update_layout(
            height=440,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_map, use_container_width=True)

      with col_bar:
        st.markdown(f"### 📊 2. Country Rankings — Year: {curr_year}")
        fig_bar = px.bar(
            df_year_sorted,
            x="Value",
            y="geoAreaName",
            orientation="h",
            color="DisplayValue",
            color_continuous_scale=custom_color_scale,
            text="TextLabel",
            labels={"Value": selected_series, "geoAreaName": "Country"},
            template="plotly_dark",
        )
        fig_bar.update_traces(textposition="outside")

        # 3 Performance Group Dividers on Bar Chart (after every 5 countries)
        fig_bar.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=4.5,
            y1=4.5,
            xref="paper",
            yref="y",
            line=dict(color="#FF5252", width=2, dash="dash"),
        )
        fig_bar.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=9.5,
            y1=9.5,
            xref="paper",
            yref="y",
            line=dict(color="#FF5252", width=2, dash="dash"),
        )

        fig_bar.update_layout(
            height=440,
            showlegend=False,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            yaxis={
                "categoryorder": "array",
                "categoryarray": df_year_sorted["geoAreaName"].tolist(),
                "title": "",
            },
            xaxis={"title": f"{selected_series} ({curr_year})"},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

      st.markdown("---")

      col_trend, col_heat = st.columns(2)

      with col_trend:
        st.markdown(
            f"### 📈 3. Regional Average Trajectory — Year: {curr_year}"
        )
        regional_trend = (
            df_filtered.groupby("Year")["Value"].mean().reset_index()
        )

        # High-visibility Cyan Dotted Trendline for Dark Background
        fig_trend = px.line(
            regional_trend,
            x="Year",
            y="Value",
            markers=True,
            labels={"Value": "Regional Mean", "Year": "Year"},
            template="plotly_dark",
        )
        fig_trend.update_traces(
            line_color="#00E5FF", line_width=3.5, line_dash="dot", marker_size=10
        )

        # Bigger bright red movement point showing year-on-year movement synchronously
        curr_val_row = regional_trend[regional_trend["Year"] == curr_year]
        if not curr_val_row.empty:
          fig_trend.add_trace(
              go.Scatter(
                  x=curr_val_row["Year"],
                  y=curr_val_row["Value"],
                  mode="markers+text",
                  marker=dict(color="#FF1744", size=18, symbol="circle"),
                  text=[f"{curr_val_row['Value'].values[0]:.2f}"],
                  textposition="top center",
                  name=str(curr_year),
              )
          )

        fig_trend.update_layout(
            height=380,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            showlegend=False,
            xaxis=dict(tickmode="linear", dtick=1),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_trend, use_container_width=True)

      with col_heat:
        st.markdown(f"### 📉 4. Transition Matrix Heatmap — Year: {curr_year}")

        df_filtered_ecowas = df_filtered[
            df_filtered["geoAreaName"].isin(all_countries)
        ]
        pivot_df = df_filtered_ecowas.pivot_table(
            index="geoAreaName", columns="Year", values="Value"
        )

        # Sort ascending so highest values appear at the TOP when plotted bottom-up by Plotly
        pivot_df["MeanVal"] = pivot_df.mean(axis=1)
        pivot_df = pivot_df.sort_values(by="MeanVal", ascending=True).drop(
            columns=["MeanVal"]
        )

        if not pivot_df.empty:
          fig_heatmap = px.imshow(
              pivot_df,
              labels=dict(x="Year", y="Country", color="Value"),
              x=[str(y) for y in pivot_df.columns],
              y=pivot_df.index,
              color_continuous_scale=custom_color_scale,
              text_auto=".1f",
              template="plotly_dark",
          )

          # 3-tier performance group dividing lines perfectly aligned top-down
          fig_heatmap.add_shape(
              type="line",
              x0=0,
              x1=1,
              y0=4.5,
              y1=4.5,
              xref="paper",
              yref="y",
              line=dict(color="#FF5252", width=2, dash="dash"),
          )
          fig_heatmap.add_shape(
              type="line",
              x0=0,
              x1=1,
              y0=9.5,
              y1=9.5,
              xref="paper",
              yref="y",
              line=dict(color="#FF5252", width=2, dash="dash"),
          )

          fig_heatmap.update_layout(
              height=380,
              margin={"r": 0, "t": 10, "l": 0, "b": 10},
              xaxis_title="Year",
              yaxis_title="Country",
              xaxis=dict(tickmode="linear", dtick=1),
              paper_bgcolor="rgba(0,0,0,0)",
              plot_bgcolor="rgba(0,0,0,0)",
          )
          st.plotly_chart(fig_heatmap, use_container_width=True)

      # Automatic playback loop advancing timeline smoothly
      if st.session_state.is_playing:
        time.sleep(playback_speed)
        st.session_state.current_year_idx = (
            st.session_state.current_year_idx + 1
        ) % len(available_years)
        st.rerun()


    # Invoke the animated fragment block
    render_animated_dashboard()
