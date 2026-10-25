import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="West Africa Energy Transition Explorer",
    page_icon="⚡",
    layout="wide",
)

# Single-line header
st.markdown("### ⚡ West Africa Energy Transition Dashboard (2015–2024)")
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
    st.sidebar.subheader("▶️ Playback & Year Selector")

    selected_year = st.sidebar.select_slider(
        "Select Year Manually:",
        options=available_years,
        value=available_years[0],
    )

    auto_play = st.sidebar.checkbox(
        "▶️ Auto-Play Smooth Transition Across Years", value=False
    )

    custom_color_scale = [
        [0.0, "#FFFDD0"],  # Cream (Lowest)
        [0.5, "#2ECC71"],  # Green (Average)
        [1.0, "#1B4F72"],  # Blue (Highest)
    ]

    df_year_raw = df_filtered[df_filtered["Year"] == selected_year]
    df_year_full = pd.DataFrame(
        {"geoAreaName": all_countries, "Year": selected_year}
    )
    df_year_full = df_year_full.merge(
        df_year_raw[["geoAreaName", "Value"]], on="geoAreaName", how="left"
    )
    df_year_full["ISO3"] = df_year_full["geoAreaName"].map(iso_mapping)
    df_year_full["DisplayValue"] = df_year_full["Value"].fillna(0)
    df_year_full["TextLabel"] = df_year_full["Value"].apply(
        lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A"
    )

    # Sort ascending for bar charts (lowest to highest)
    df_year_sorted = df_year_full.sort_values(
        by="Value", ascending=True, na_position="first"
    )

    # --- TOP METRIC BANNER ---
    valid_vals = df_year_raw["Value"].dropna()
    regional_avg = valid_vals.mean() if not valid_vals.empty else 0.0

    prev_year = selected_year - 1
    df_prev_raw = df_filtered[df_filtered["Year"] == prev_year]
    prev_valid = df_prev_raw["Value"].dropna()
    prev_avg = prev_valid.mean() if not prev_valid.empty else regional_avg
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
        delta=f"{len(valid_vals)} / {len(all_countries)} Reporting",
    )
    c3.metric(
        label="📅 Timeframe Covered",
        value=f"{min(available_years)} – {max(available_years)}",
        delta="10 Years Tracked",
    )
    st.markdown("---")

    # --- FOUR COMPACT DASHBOARD SECTIONS ON ONE SCREEN ---
    col_map, col_bar = st.columns(2)

    if auto_play:
      anim_frames = []
      for y in available_years:
        df_y = pd.DataFrame({"geoAreaName": all_countries, "Year": y})
        sub = df_filtered[df_filtered["Year"] == y]
        df_y = df_y.merge(
            sub[["geoAreaName", "Value"]], on="geoAreaName", how="left"
        )
        df_y["ISO3"] = df_y["geoAreaName"].map(iso_mapping)
        df_y["DisplayValue"] = df_y["Value"].fillna(-1)
        df_y["TextLabel"] = df_y["Value"].apply(
            lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A"
        )
        anim_frames.append(df_y)
      df_anim = pd.concat(anim_frames)

      with col_map:
        st.markdown("### 🗺️ 1. West Africa Regional Map")
        fig_anim_map = px.choropleth(
            df_anim,
            locations="ISO3",
            color="DisplayValue",
            hover_name="geoAreaName",
            animation_frame="Year",
            color_continuous_scale=custom_color_scale,
            range_color=[0, df_anim["Value"].max() if not df_anim.empty else 100],
            scope="africa",
            labels={"DisplayValue": selected_series},
        )
        # Frameless, borderless map layout
        fig_anim_map.update_geos(
            center=dict(lat=9.5, lon=-3.5),
            projection_scale=3.8,
            visible=False,
            showcountries=False,
        )
        fig_anim_map.update_layout(
            height=360,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_anim_map, use_container_width=True)

      with col_bar:
        st.markdown("### 📊 2. Country Rankings (Lowest to Highest)")
        fig_anim_bar = px.bar(
            df_anim,
            x="Value",
            y="geoAreaName",
            color="DisplayValue",
            animation_frame="Year",
            orientation="h",
            color_continuous_scale=custom_color_scale,
            text="TextLabel",
            labels={"Value": selected_series, "geoAreaName": "Country"},
        )
        fig_anim_bar.update_traces(textposition="outside")
        fig_anim_bar.update_layout(
            height=360,
            showlegend=False,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_anim_bar, use_container_width=True)

    else:
      with col_map:
        st.markdown(f"### 🗺️ 1. West Africa Regional Map ({selected_year})")
        fig_map = px.choropleth(
            df_year_full,
            locations="ISO3",
            color="DisplayValue",
            hover_name="geoAreaName",
            color_continuous_scale=custom_color_scale,
            range_color=[
                0,
                df_year_full["Value"].max()
                if not df_year_full["Value"].dropna().empty
                else 100,
            ],
            scope="africa",
            labels={"DisplayValue": selected_series},
        )
        # Frameless, borderless map layout
        fig_map.update_geos(
            center=dict(lat=9.5, lon=-3.5),
            projection_scale=3.8,
            visible=False,
            showcountries=False,
        )
        fig_map.update_layout(
            height=360,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_map, use_container_width=True)

      with col_bar:
        st.markdown(f"### 📊 2. Country Rankings ({selected_year})")

        # Sorted lowest to highest bar chart
        fig_bar = px.bar(
            df_year_sorted,
            x="Value",
            y="geoAreaName",
            orientation="h",
            color="DisplayValue",
            color_continuous_scale=custom_color_scale,
            text="TextLabel",
            labels={"Value": selected_series, "geoAreaName": "Country"},
        )
        fig_bar.update_traces(textposition="outside")
        fig_bar.update_layout(
            height=360,
            showlegend=False,
            margin={"r": 0, "t": 10, "l": 0, "b": 0},
            yaxis={
                "categoryorder": "array",
                "categoryarray": df_year_sorted["geoAreaName"].tolist(),
            },
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Lower Row: Regional Trend & Transition Matrix Heatmap
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
          height=360, margin={"r": 0, "t": 10, "l": 0, "b": 0}
      )
      st.plotly_chart(fig_trend, use_container_width=True)

    with col_heat:
      st.markdown("### 📉 4. Transition Matrix Heatmap (All Years)")
      pivot_df = df_filtered.pivot_table(
          index="geoAreaName", columns="Year", values="Value"
      )
      # Sort pivot rows alphabetically or by average performance
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
            px_ortho=False,
        )
        fig_heatmap.update_layout(
            height=360,
            margin={"r": 0, "t": 10, "l": 0, "b": 10},
            xaxis_title="Year",
            yaxis_title="Country",
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
