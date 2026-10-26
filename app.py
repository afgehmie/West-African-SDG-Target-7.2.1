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

# Professional Styling & Presentation Polish
st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
    h3 { font-size: 1.35rem !important; font-weight: 700 !important; margin-bottom: 0.1rem !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# Single-line compact header
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
    # Color Palette Setup using Seaborn & Matplotlib
    sns_cmap = sns.color_palette("YlGnBu", as_cmap=True)
    custom_color_scale = [
        [0.0, mcolors.to_hex(sns_cmap(0.15))],
        [0.5, mcolors.to_hex(sns_cmap(0.55))],
        [1.0, mcolors.to_hex(sns_cmap(0.95))],
    ]

    # Prepare complete animation dataset ensuring all 15 countries exist for every year
    anim_frames = []
    for y in available_years:
      df_y = pd.DataFrame({"geoAreaName": all_countries, "Year": y})
      sub = df_filtered[df_filtered["Year"] == y]
      df_y = df_y.merge(
          sub[["geoAreaName", "Value"]], on="geoAreaName", how="left"
      )
      df_y["ISO3"] = df_y["geoAreaName"].map(iso_mapping)
      df_y["DisplayValue"] = df_y["Value"].fillna(-1)  # Grey for missing data
      df_y["TextLabel"] = df_y["Value"].apply(
          lambda x: f"{x:.1f}" if pd.notnull(x) else "N/A"
      )
      anim_frames.append(df_y)
    df_anim = pd.concat(anim_frames)

    st.markdown("---")
    st.info(
        "💡 **Presentation Tip:** Click the **▶️ Play** button at the bottom"
        " left of the Map and Rankings charts below for butter-smooth,"
        " flicker-free animations across all years (2015–2024) with zero white"
        " page reloads!"
    )
    st.markdown("---")

    # --- FOUR CORE DASHBOARD COMPONENTS ---
    col_map, col_bar = st.columns([1.1, 1.0])

    with col_map:
      st.markdown("### 🗺️ 1. West Africa Regional Map (Animated)")
      # Native Plotly client-side animation frame
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
      # Enlarged map bounds with center adjusted so Gambia and Cabo Verde are 100% visible
      fig_anim_map.update_geos(
          center=dict(lat=10.5, lon=-6.5),
          projection_scale=3.5,
          visible=False,
          showcountries=True,
          countrycolor="#B0B0B0",
          countrywidth=1.0,
      )
      fig_anim_map.update_layout(
          height=440,
          margin={"r": 0, "t": 10, "l": 0, "b": 0},
          paper_bgcolor="rgba(0,0,0,0)",
          plot_bgcolor="rgba(0,0,0,0)",
      )
      st.plotly_chart(fig_anim_map, use_container_width=True)

    with col_bar:
      st.markdown("### 📊 2. Country Rankings (Animated)")

      # Sort values for bar chart ordering
      df_anim_sorted = df_anim.sort_values(
          by=["Year", "Value"], ascending=[True, True], na_position="first"
      )

      fig_anim_bar = px.bar(
          df_anim_sorted,
          x="Value",
          y="geoAreaName",
          animation_frame="Year",
          orientation="h",
          color="DisplayValue",
          color_continuous_scale=custom_color_scale,
          text="TextLabel",
          labels={"Value": selected_series, "geoAreaName": "Country"},
      )
      fig_anim_bar.update_traces(textposition="outside")

      # 3 Performance Group Dividers on Bar Chart (after every 5 countries)
      fig_anim_bar.add_shape(
          type="line",
          x0=0,
          x1=1,
          y0=4.5,
          y1=4.5,
          xref="paper",
          yref="y",
          line=dict(color="red", width=2, dash="dash"),
      )
      fig_anim_bar.add_shape(
          type="line",
          x0=0,
          x1=1,
          y0=9.5,
          y1=9.5,
          xref="paper",
          yref="y",
          line=dict(color="red", width=2, dash="dash"),
      )

      fig_anim_bar.update_layout(
          height=440,
          showlegend=False,
          margin={"r": 0, "t": 10, "l": 0, "b": 0},
          xaxis={"title": selected_series},
          yaxis={"title": ""},
      )
      st.plotly_chart(fig_anim_bar, use_container_width=True)

    st.markdown("---")

    col_trend, col_heat = st.columns(2)

    with col_trend:
      st.markdown("### 📈 3. Regional Average Annual Trajectory")
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
          height=380,
          margin={"r": 0, "t": 10, "l": 0, "b": 0},
          showlegend=False,
          xaxis=dict(tickmode="linear", dtick=1),
      )
      st.plotly_chart(fig_trend, use_container_width=True)

    with col_heat:
      st.markdown("### 📉 4. Transition Matrix Heatmap")
      pivot_df = df_filtered.pivot_table(
          index="geoAreaName", columns="Year", values="Value"
      )

      # Sort transition matrix: highest numbers at the TOP
      pivot_df["MeanVal"] = pivot_df.mean(axis=1)
      pivot_df = pivot_df.sort_values(by="MeanVal", ascending=False).drop(
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
        )

        # 3 Group Dividing Lines on Heatmap (after every 5 countries)
        fig_heatmap.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=4.5,
            y1=4.5,
            xref="paper",
            yref="y",
            line=dict(color="red", width=2, dash="dash"),
        )
        fig_heatmap.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=9.5,
            y1=9.5,
            xref="paper",
            yref="y",
            line=dict(color="red", width=2, dash="dash"),
        )

        fig_heatmap.update_layout(
            height=380,
            margin={"r": 0, "t": 10, "l": 0, "b": 10},
            xaxis_title="Year",
            yaxis_title="Country",
            xaxis=dict(tickmode="linear", dtick=1),
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
