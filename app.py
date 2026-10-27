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

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1.2rem; padding-bottom: 1.2rem; }
    h3 { font-size: 1.35rem !important; font-weight: 700 !important; margin-bottom: 0.1rem !important; }
    </style>
""",
    unsafe_allow_html=True,
)

# Main Title
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

  df_filtered = df_melted[
      (df_melted["seriesDescription"] == selected_series)
      & (df_melted["geoAreaName"].isin(all_countries))
  ].copy()
  df_filtered["Year"] = df_filtered["Year"].astype(int)
  df_filtered = df_filtered.sort_values(by=["Year", "geoAreaName"])

  if not df_filtered.empty:
    # Prepare complete grid for all countries x years to prevent animation gaps
    years_sorted = sorted(df_filtered["Year"].unique())
    full_grid = []
    for yr in years_sorted:
      for c in all_countries:
        subset = df_filtered[
            (df_filtered["Year"] == yr) & (df_filtered["geoAreaName"] == c)
        ]
        val = subset["Value"].values[0] if not subset.empty else None
        full_grid.append(
            {
                "geoAreaName": c,
                "Year": yr,
                "Value": val,
                "ISO3": iso_mapping[c],
                "DisplayValue": val if val is not None else -1,
                "TextLabel": f"{val:.1f}" if val is not None else "N/A",
            }
        )
    df_anim = pd.DataFrame(full_grid)

    st.markdown("---")
    st.markdown(
        "💡 *Tip: Use the built-in **Play / Pause** buttons and timeline sliders"
        " on each chart below for smooth, flicker-free client-side animation.*"
    )
    st.markdown("---")

    sns_cmap = sns.color_palette("YlGnBu", as_cmap=True)
    custom_color_scale = [
        [0.0, mcolors.to_hex(sns_cmap(0.15))],
        [0.5, mcolors.to_hex(sns_cmap(0.55))],
        [1.0, mcolors.to_hex(sns_cmap(0.95))],
    ]

    # --- 1. REGIONAL MAP (CLIENT-SIDE ANIMATION) ---
    st.markdown("### 🗺️ 1. West Africa Regional Map (2015 - 2024)")
    fig_map = px.choropleth(
        df_anim,
        locations="ISO3",
        color="DisplayValue",
        hover_name="geoAreaName",
        animation_frame="Year",
        color_continuous_scale=custom_color_scale,
        range_color=[0, df_anim["Value"].max() if not df_anim["Value"].dropna().empty else 100],
        scope="africa",
        labels={"DisplayValue": selected_series},
        template="plotly_dark",
    )
    fig_map.update_geos(
        center=dict(lat=10.5, lon=-6.5),
        projection_scale=3.5,
        visible=False,
        showcountries=True,
        countrycolor="#666666",
        countrywidth=1.0,
        bgcolor="rgba(0,0,0,0)",
    )
    fig_map.update_layout(
        height=460,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    # --- 2. COUNTRY RANKINGS (CLIENT-SIDE ANIMATION) ---
    st.markdown("### 📊 2. Country Rankings (2015 - 2024)")
    
    # Sort values per year for ranking bar chart
    df_bar_anim = df_anim.copy()
    df_bar_anim["sort_val"] = df_bar_anim["Value"].fillna(-999)
    df_bar_anim = df_bar_anim.sort_values(by=["Year", "sort_val"], ascending=[True, True])

    fig_bar = px.bar(
        df_bar_anim,
        x="Value",
        y="geoAreaName",
        animation_frame="Year",
        orientation="h",
        color="DisplayValue",
        color_continuous_scale=custom_color_scale,
        text="TextLabel",
        labels={"Value": selected_series, "geoAreaName": "Country"},
        template="plotly_dark",
    )
    fig_bar.update_traces(textposition="outside")

    # 3 Performance Group Dividers
    fig_bar.add_shape(type="line", x0=0, x1=1, y0=4.5, y1=4.5, xref="paper", yref="y", line=dict(color="#FF5252", width=2, dash="dash"))
    fig_bar.add_shape(type="line", x0=0, x1=1, y0=9.5, y1=9.5, xref="paper", yref="y", line=dict(color="#FF5252", width=2, dash="dash"))

    fig_bar.update_layout(
        height=460,
        showlegend=False,
        margin={"r": 0, "t": 30, "l": 0, "b": 0},
        xaxis={"title": selected_series},
        yaxis={"title": ""},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    st.markdown("---")

    col_trend, col_heat = st.columns(2)

    with col_trend:
      st.markdown("### 📈 3. Regional Average Trajectory")
      regional_trend = df_filtered.groupby("Year")["Value"].mean().reset_index()
      fig_trend = px.line(
          regional_trend,
          x="Year",
          y="Value",
          markers=True,
          labels={"Value": "Regional Mean", "Year": "Year"},
          template="plotly_dark",
      )
      fig_trend.update_traces(line_color="#00E5FF", line_width=3.5, line_dash="dot", marker_size=10)
      fig_trend.update_layout(
          height=380,
          margin={"r": 0, "t": 30, "l": 0, "b": 0},
          showlegend=False,
          xaxis=dict(tickmode="linear", dtick=1),
          paper_bgcolor="rgba(0,0,0,0)",
          plot_bgcolor="rgba(0,0,0,0)",
      )
      st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})

    with col_heat:
      st.markdown("### 📉 4. Transition Matrix Heatmap")
      pivot_df = df_filtered.pivot_table(index="geoAreaName", columns="Year", values="Value")
      pivot_df["MeanVal"] = pivot_df.mean(axis=1)
      pivot_df = pivot_df.sort_values(by="MeanVal", ascending=False).drop(columns=["MeanVal"])

      if not pivot_df.empty:
        fig_heatmap = go.Figure(
            data=go.Heatmap(
                z=pivot_df.values,
                x=[str(y) for y in pivot_df.columns],
                y=pivot_df.index.tolist(),
                colorscale="YlGnBu",
                text=[[f"{val:.1f}" if pd.notnull(val) else "" for val in row] for row in pivot_df.values],
                texttemplate="%{text}",
                colorbar=dict(title="Value"),
            )
        )
        fig_heatmap.add_shape(type="line", x0=0, x1=1, y0=4.5, y1=4.5, xref="paper", yref="y", line=dict(color="#FF5252", width=2, dash="dash"))
        fig_heatmap.add_shape(type="line", x0=0, x1=1, y0=9.5, y1=9.5, xref="paper", yref="y", line=dict(color="#FF5252", width=2, dash="dash"))
        fig_heatmap.update_layout(
            height=380,
            margin={"r": 0, "t": 30, "l": 0, "b": 10},
            xaxis_title="Year",
            yaxis_title="Country",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig_heatmap, use_container_width=True, config={"displayModeBar": False})
