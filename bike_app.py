"""
Indian Bike Market Analytics Dashboard
--------------------------------------
Interactive Dash application for the analysis of bike pricing,
mileage efficiency, brand positioning, and fuel distribution
in the Indian two-wheeler market.
"""

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from scipy import stats

# ── Load & Clean ──────────────────────────────────────────────────────────────

_HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_excel(os.path.join(_HERE, "bike_sales.xlsx"))
df_clean = df.copy()
df_clean = df_clean.dropna(subset=["Brand", "Price (INR)", "Fuel Type", "Mileage (km/l)"])

df_clean["Engine_Category"] = pd.cut(
    df_clean["Engine Capacity (cc)"],
    bins=[0, 150, 300, 500, 1000, float("inf")],
    labels=["Small (≤150cc)", "Medium (151–300cc)", "Large (301–500cc)",
            "Very Large (501–1000cc)", "Extra Large (>1000cc)"]
)

df_clean["Price_Category"] = pd.cut(
    df_clean["Price (INR)"],
    bins=[0, 100000, 300000, 600000, 1000000, float("inf")],
    labels=["Budget (≤1L)", "Mid-range (1–3L)", "Premium (3–6L)",
            "Luxury (6–10L)", "Super Luxury (>10L)"]
)

top_brands  = df_clean["Brand"].value_counts().head(10).index
df_filtered = df_clean[df_clean["Brand"].isin(top_brands)]

# ── Key Findings ──────────────────────────────────────────────────────────────

findings = {}
findings["top_engine"]   = df_clean.groupby("Engine_Category")["Brand"].count().idxmax()
findings["premium_fuel"] = df_clean.groupby("Fuel Type")["Price (INR)"].mean().idxmax()
findings["efficient_fuel"] = df_clean.groupby("Fuel Type")["Mileage (km/l)"].mean().idxmax()

if "Resale Price (INR)" in df_clean.columns:
    df_clean["Resale_Retention"] = df_clean["Resale Price (INR)"] / df_clean["Price (INR)"]
    findings["best_resale_brand"] = df_clean.groupby("Brand")["Resale_Retention"].mean().idxmax()
    findings["best_resale_pct"]   = round(df_clean.groupby("Brand")["Resale_Retention"].mean().max() * 100, 1)
else:
    findings["best_resale_brand"] = "N/A"
    findings["best_resale_pct"]   = "N/A"

corr, _ = stats.pearsonr(df_clean["Price (INR)"], df_clean["Mileage (km/l)"])
findings["price_mileage_corr"]      = round(corr, 3)
findings["price_mileage_direction"] = "negative" if corr < 0 else "positive"

# ── Helpers ───────────────────────────────────────────────────────────────────

def fmt(val):
    if val >= 100000: return f"₹{val/100000:.1f}L"
    elif val >= 1000: return f"₹{val/1000:.0f}K"
    return f"₹{val:.0f}"

def apply_filters(price_range, fuel, brands=None, models=None):
    fdf = df_clean.copy()
    fdf = fdf[(fdf["Price (INR)"] >= price_range[0]) & (fdf["Price (INR)"] <= price_range[1])]
    if fuel and fuel != "All":
        fdf = fdf[fdf["Fuel Type"] == fuel]
    if brands:
        valid = [b for b in brands if b in fdf["Brand"].unique()]
        if valid:
            fdf = fdf[fdf["Brand"].isin(valid)]
    if models and "All" not in models:
        fdf = fdf[fdf["Model"].isin(models)]
    return fdf

def get_metrics(perspective):
    m = {
        "financial":   {"trend": "avg_price",  "fuel": "avg_price"},
        "market":      {"trend": "count",       "fuel": "count"},
        "performance": {"trend": "avg_mileage", "fuel": "avg_mileage"},
    }
    return m.get(perspective, m["financial"])

# ── Design Tokens ─────────────────────────────────────────────────────────────

SIDEBAR_BG   = "#0D1117"   # near-black
SIDEBAR_2    = "#161B22"   # card bg in sidebar
CANVAS_BG    = "#F4F6F9"   # main area
WHITE        = "#FFFFFF"
BORDER       = "#E1E4E8"
BORDER_DARK  = "#30363D"

BLUE         = "#2F81F7"   # accent
BLUE_MUTED   = "#1F6FEB"
GREEN        = "#3FB950"
AMBER        = "#D29922"
RED          = "#F85149"
PURPLE       = "#8B949E"
TEAL         = "#39D353"

TEXT_PRIMARY   = "#24292F"
TEXT_SECONDARY = "#57606A"
TEXT_MUTED     = "#8B949E"
TEXT_SIDEBAR   = "#CDD9E5"
TEXT_SIDEBAR_M = "#768390"

FUEL_COLORS = {
    "Petrol":   "#F85149",
    "Electric": "#3FB950",
    "Hybrid":   "#D29922",
    "Diesel":   "#2F81F7",
}
FUEL_SYMBOLS = {"Electric": "🔋", "Hybrid": "⚡", "Petrol": "⛽", "Diesel": "🛢"}

# ── Chart Base Layout ─────────────────────────────────────────────────────────

def chart_layout(**kwargs):
    base = dict(
        paper_bgcolor=WHITE,
        plot_bgcolor="#FAFBFC",
        font=dict(family="'IBM Plex Sans', sans-serif", size=11, color=TEXT_PRIMARY),
        margin=dict(l=50, r=30, t=30, b=50),
        height=300,
        xaxis=dict(gridcolor="#EAECEF", linecolor=BORDER, tickcolor=BORDER, showline=True),
        yaxis=dict(gridcolor="#EAECEF", linecolor=BORDER, tickcolor=BORDER, showline=True),
        legend=dict(bgcolor="rgba(255,255,255,0.9)", bordercolor=BORDER, borderwidth=1,
                    font=dict(size=10)),
        hovermode="closest",
    )
    base.update(kwargs)
    return base

# ── Chart Functions ───────────────────────────────────────────────────────────

def create_pie(data):
    counts = data["Brand"].value_counts().head(8)
    colors = ["#2F81F7","#3FB950","#D29922","#F85149","#8B949E",
              "#39D353","#79C0FF","#FFA657"]
    fig = px.pie(values=counts.values, names=counts.index, hole=0.45,
                 color_discrete_sequence=colors)
    fig.update_traces(
        textposition="inside", textinfo="percent",
        hovertemplate="<b>%{label}</b><br>%{value} models · %{percent}<extra></extra>",
        marker=dict(line=dict(color=WHITE, width=2))
    )
    fig.update_layout(
        paper_bgcolor=WHITE, plot_bgcolor=WHITE,
        font=dict(family="'IBM Plex Sans', sans-serif", size=11, color=TEXT_PRIMARY),
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5,
                    xanchor="left", x=1.02, font=dict(size=10),
                    bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def create_trend(data, metric="avg_price"):
    order = ["Small (≤150cc)", "Medium (151–300cc)", "Large (301–500cc)",
             "Very Large (501–1000cc)", "Extra Large (>1000cc)"]

    if metric == "avg_price":
        agg = data.groupby("Engine_Category")["Price (INR)"].agg(["mean","count"]).reset_index()
        agg.columns = ["Engine_Category","Value","Count"]
        y_title = "Avg Price (₹)"
    elif metric == "avg_mileage":
        agg = data.groupby("Engine_Category")["Mileage (km/l)"].agg(["mean","count"]).reset_index()
        agg.columns = ["Engine_Category","Value","Count"]
        y_title = "Avg Mileage (km/l)"
    else:
        agg = data["Engine_Category"].value_counts().reset_index()
        agg.columns = ["Engine_Category","Value"]
        agg["Count"] = agg["Value"]
        y_title = "Model Count"

    agg["Engine_Category"] = pd.Categorical(agg["Engine_Category"], categories=order, ordered=True)
    agg = agg.sort_values("Engine_Category")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=agg["Engine_Category"], y=agg["Value"],
        mode="lines+markers", name=y_title,
        line=dict(width=2.5, color=BLUE),
        marker=dict(size=8, color=WHITE, line=dict(width=2, color=BLUE)),
        hovertemplate="<b>%{x}</b><br>" + f"{y_title}: %{{y:,.0f}}<extra></extra>"
    ))
    if "Count" in agg.columns and metric != "count":
        scale = agg["Value"].max() / max(agg["Count"].max(), 1)
        fig.add_scatter(
            x=agg["Engine_Category"], y=agg["Count"] * scale,
            mode="lines+markers", name="Volume (scaled)", yaxis="y2",
            line=dict(color=AMBER, dash="dot", width=1.5),
            marker=dict(size=5, color=AMBER)
        )
    layout = chart_layout(
        xaxis=dict(title="Engine Category", gridcolor="#EAECEF",
                   linecolor=BORDER, tickcolor=BORDER, showline=True,
                   tickangle=-20, tickfont=dict(size=9)),
        yaxis=dict(title=y_title, gridcolor="#EAECEF",
                   linecolor=BORDER, tickcolor=BORDER, showline=True),
        yaxis2=dict(title="Volume", overlaying="y", side="right",
                    gridcolor="#EAECEF", showgrid=False),
        hovermode="x unified",
        margin=dict(l=55, r=55, t=20, b=70),
    )
    fig.update_layout(layout)
    return fig


def create_fuel_bar(data, metric="avg_price"):
    top_b = data["Brand"].value_counts().head(8).index
    fdata = data[data["Brand"].isin(top_b)]

    if len(fdata) == 0:
        fig = go.Figure()
        fig.update_layout(**chart_layout(title="No data for current filters"))
        return fig

    def _fmt(num):
        if metric == "avg_mileage": return f"{num:.1f}"
        if metric == "avg_price":   return fmt(num)
        return f"{int(num)}"

    if metric == "avg_price":
        agg = fdata.groupby(["Fuel Type","Brand"])["Price (INR)"].mean().reset_index()
        val_col = "Price (INR)"; y_title = "Avg Price (₹)"
    elif metric == "avg_mileage":
        agg = fdata.groupby(["Fuel Type","Brand"])["Mileage (km/l)"].mean().reset_index()
        agg.columns = ["Fuel Type","Brand","Price (INR)"]
        val_col = "Price (INR)"; y_title = "Avg Mileage (km/l)"
    else:
        agg = fdata.groupby(["Fuel Type","Brand"]).size().reset_index(name="Price (INR)")
        val_col = "Price (INR)"; y_title = "Model Count"

    fig = px.bar(agg, x=val_col, y="Brand", color="Fuel Type",
                 orientation="h", barmode="group",
                 color_discrete_map=FUEL_COLORS, text=val_col)
    fig.update_traces(
        texttemplate="%{customdata}",
        textposition="outside",
        customdata=[_fmt(v) for v in agg[val_col]],
        hovertemplate="<b>%{fullData.name}</b> — %{y}<br>"
                      + f"{y_title}: %{{customdata}}<extra></extra>",
        marker_line_color=WHITE, marker_line_width=1,
    )
    fig.update_layout(**chart_layout(
        xaxis=dict(title=y_title, gridcolor="#EAECEF",
                   linecolor=BORDER, tickcolor=BORDER, showline=True),
        yaxis=dict(title=None, gridcolor="#EAECEF",
                   linecolor=BORDER, tickcolor=BORDER, showline=True),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    font=dict(size=10), bgcolor="rgba(0,0,0,0)",
                    title=dict(text="")),
        margin=dict(l=90, r=120, t=40, b=40),
    ))
    return fig


def create_scatter(data, selected_brands=None):
    if selected_brands:
        fdata = data[data["Brand"].isin(selected_brands)]
    else:
        fdata = data[data["Brand"].isin(data["Brand"].value_counts().head(6).index)]

    if len(fdata) == 0:
        fig = go.Figure()
        fig.update_layout(**chart_layout(title="No data for current filters"))
        return fig

    sample = fdata.sample(min(500, len(fdata)), random_state=42)
    fig = go.Figure()

    for fuel, grp in sample.groupby("Fuel Type"):
        sym = FUEL_SYMBOLS.get(fuel, "🔧")
        fig.add_trace(go.Scatter(
            x=grp["Price (INR)"], y=grp["Mileage (km/l)"],
            mode="markers",
            name=f"{sym} {fuel}",
            marker=dict(size=9, color=FUEL_COLORS.get(fuel, BLUE),
                        opacity=0.8, line=dict(width=1.5, color=WHITE)),
            customdata=list(zip(grp["Brand"], grp["Engine Capacity (cc)"],
                                [fmt(p) for p in grp["Price (INR)"]])),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Price: %{customdata[2]}<br>"
                "Mileage: %{y:.1f} km/l<br>"
                "Engine: %{customdata[1]:.0f}cc<extra></extra>"
            )
        ))

    if len(sample) > 10:
        slope, intercept, r_val, *_ = stats.linregress(
            sample["Price (INR)"], sample["Mileage (km/l)"]
        )
        x_range = [sample["Price (INR)"].min(), sample["Price (INR)"].max()]
        fig.add_trace(go.Scatter(
            x=x_range, y=[slope * x + intercept for x in x_range],
            mode="lines", name=f"Trend  R²={r_val**2:.3f}",
            line=dict(color=TEXT_PRIMARY, dash="dash", width=1.5)
        ))

    fig.update_layout(**chart_layout(
        xaxis=dict(title="Price (₹)", tickformat=",.0f", gridcolor="#EAECEF",
                   linecolor=BORDER, tickcolor=BORDER, showline=True),
        yaxis=dict(title="Mileage (km/l)", gridcolor="#EAECEF",
                   linecolor=BORDER, tickcolor=BORDER, showline=True),
        height=360,
        margin=dict(l=55, r=30, t=20, b=50),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="right", x=1,
                    bgcolor="rgba(255,255,255,0.92)", bordercolor=BORDER, borderwidth=1,
                    font=dict(size=10)),
    ))
    return fig

# ── Analytics Panel ───────────────────────────────────────────────────────────

LI_STYLE = {"fontSize": "12px", "margin": "5px 0", "color": TEXT_SECONDARY, "lineHeight": "1.6"}
H6_STYLE = {"color": BLUE, "fontWeight": "700", "marginBottom": "10px",
            "fontSize": "12px", "textTransform": "uppercase", "letterSpacing": "0.06em"}

def stat_row(label, value, color=TEXT_PRIMARY):
    return html.Div([
        html.Span(label, style={"fontSize": "11px", "color": TEXT_MUTED,
                                "display": "block", "marginBottom": "1px"}),
        html.Span(value, style={"fontSize": "13px", "fontWeight": "600",
                                "color": color}),
    ], style={"padding": "6px 0", "borderBottom": f"1px solid {BORDER}"})

def analytics_market_summary(fdf):
    if len(fdf) == 0:
        return html.P("No data for current filters.", style={"fontSize": "12px", "color": TEXT_MUTED})
    bc = fdf["Brand"].value_counts()
    total = len(fdf)
    hhi = sum((bc / total) ** 2)
    conc = "High" if hhi > 0.25 else "Moderate" if hhi > 0.15 else "Low"
    avg_p = fdf["Price (INR)"].mean()
    med_p = fdf["Price (INR)"].median()
    avg_m = fdf["Mileage (km/l)"].mean()
    dom_fuel = fdf["Fuel Type"].value_counts().index[0]

    return html.Div([
        html.P("Market Overview", style=H6_STYLE),
        stat_row("Total models", f"{total:,}"),
        stat_row("Active brands", f"{len(bc)}"),
        stat_row("Market leader", f"{bc.index[0]} ({bc.iloc[0]/total*100:.1f}%)", BLUE),
        stat_row("Concentration", conc),
        stat_row("Avg price", fmt(avg_p), AMBER),
        stat_row("Median price", fmt(med_p)),
        stat_row("Avg mileage", f"{avg_m:.1f} km/l", GREEN),
        stat_row("Dominant fuel", dom_fuel),
    ], style={"padding": "4px 0"})

def analytics_scatter(fdf):
    if len(fdf) < 5:
        return html.P("Not enough data.", style={"fontSize": "12px", "color": TEXT_MUTED})
    corr = fdf["Price (INR)"].corr(fdf["Mileage (km/l)"])
    desc = ("Strong negative" if corr < -0.6 else "Moderate negative" if corr < -0.3
            else "Weak negative" if corr < 0 else "Weak positive" if corr < 0.3
            else "Moderate positive" if corr < 0.6 else "Strong positive")
    avg_p = fdf["Price (INR)"].mean(); avg_m = fdf["Mileage (km/l)"].mean()
    hi_lo = len(fdf[(fdf["Price (INR)"] > avg_p) & (fdf["Mileage (km/l)"] < avg_m)])
    lo_hi = len(fdf[(fdf["Price (INR)"] < avg_p) & (fdf["Mileage (km/l)"] > avg_m)])

    return html.Div([
        html.P("Price vs Mileage", style=H6_STYLE),
        stat_row("Correlation", f"{corr:.3f}  ({desc})",
                 RED if corr < 0 else GREEN),
        stat_row("Avg price benchmark", fmt(avg_p), AMBER),
        stat_row("Avg mileage benchmark", f"{avg_m:.1f} km/l", GREEN),
        stat_row("High price / low mileage", f"{hi_lo} models"),
        stat_row("Low price / high mileage", f"{lo_hi} models"),
    ], style={"padding": "4px 0"})

def analytics_pie(fdf):
    if len(fdf) == 0:
        return html.P("No data.", style={"fontSize": "12px", "color": TEXT_MUTED})
    bc = fdf["Brand"].value_counts()
    total = len(fdf)
    top3 = bc.head(3).sum() / total * 100
    adv = bc.iloc[0] - bc.iloc[1] if len(bc) > 1 else bc.iloc[0]
    mix = "Concentrated" if top3 > 60 else "Balanced" if top3 >= 40 else "Fragmented"

    return html.Div([
        html.P("Brand Share", style=H6_STYLE),
        stat_row("Leader", f"{bc.index[0]}  ({bc.iloc[0]/total*100:.1f}%)", BLUE),
        stat_row("Top-3 share", f"{top3:.1f}%"),
        stat_row("Market structure", mix),
        stat_row("Active brands", f"{len(bc)}"),
        stat_row("Leader vs #2", f"+{adv} models"),
    ], style={"padding": "4px 0"})

def analytics_line(fdf, perspective):
    if len(fdf) == 0:
        return html.P("No data.", style={"fontSize": "12px", "color": TEXT_MUTED})
    ed = fdf["Engine_Category"].value_counts()

    if perspective == "financial":
        ep = fdf.groupby("Engine_Category")["Price (INR)"].mean()
        hi = ep.idxmax(); lo = ep.idxmin()
        gap = (ep.max() - ep.min()) / 100000
        extra = stat_row("Price gap", f"₹{gap:.1f}L", AMBER)
    elif perspective == "performance":
        em = fdf.groupby("Engine_Category")["Mileage (km/l)"].mean()
        hi = em.idxmax(); lo = em.idxmin()
        gap = em.max() - em.min()
        extra = stat_row("Mileage gap", f"{gap:.1f} km/l", GREEN)
    else:
        hi = ed.index[0]; lo = ed.index[-1] if len(ed) > 1 else ed.index[0]
        extra = stat_row("Top category", f"{ed.iloc[0]} models")

    return html.Div([
        html.P("Engine Capacity", style=H6_STYLE),
        stat_row("Dominant category", ed.index[0]),
        stat_row("Categories present", str(len(ed))),
        extra,
        stat_row("Highest value", hi, BLUE),
        stat_row("Lowest value", lo),
    ], style={"padding": "4px 0"})

def analytics_fuel(fdf):
    if len(fdf) == 0:
        return html.P("No data.", style={"fontSize": "12px", "color": TEXT_MUTED})
    fd = fdf["Fuel Type"].value_counts()
    total = len(fdf)
    ev_b = len(fdf[fdf["Fuel Type"] == "Electric"]["Brand"].unique()) if "Electric" in fd.index else 0
    ea = fdf[fdf["Fuel Type"] == "Electric"]["Price (INR)"].mean() if "Electric" in fd.index else 0
    pa = fdf[fdf["Fuel Type"] == "Petrol"]["Price (INR)"].mean() if "Petrol" in fd.index else 0
    if ea > 0 and pa > 0:
        diff = (ea - pa) / 100000
        prem = f"{'+'if diff>0 else ''}₹{diff:.2f}L vs petrol"
    else:
        prem = "N/A"

    return html.Div([
        html.P("Fuel Mix", style=H6_STYLE),
        stat_row("Dominant fuel", f"{fd.index[0]}  ({fd.iloc[0]/total*100:.1f}%)"),
        stat_row("Powertrain types", str(len(fd))),
        stat_row("Brands with electric", str(ev_b), GREEN),
        stat_row("Electric premium", prem, AMBER if ea > pa else GREEN),
    ], style={"padding": "4px 0"})

# ── Shared CSS injected via assets (inline style block) ───────────────────────

EXTERNAL_CSS = [
    dbc.themes.BOOTSTRAP,
    "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap",
]

# ── App ───────────────────────────────────────────────────────────────────────

app = dash.Dash(__name__, external_stylesheets=EXTERNAL_CSS)
app.title = "Bike Market Analytics"

# ── Sidebar helpers ───────────────────────────────────────────────────────────

def sidebar_label(text):
    return html.P(text, style={
        "fontSize": "10px", "fontWeight": "600", "color": TEXT_SIDEBAR_M,
        "textTransform": "uppercase", "letterSpacing": "0.1em",
        "marginBottom": "6px", "marginTop": "0",
    })

def section_divider():
    return html.Hr(style={"borderColor": BORDER_DARK, "margin": "16px 0"})

def kpi_block(kpi_id, label, color=BLUE):
    return html.Div([
        html.Div(id=kpi_id, style={
            "fontSize": "22px", "fontWeight": "700",
            "color": color, "fontFamily": "'IBM Plex Mono', monospace",
            "lineHeight": "1",
        }),
        html.Div(label, style={
            "fontSize": "10px", "color": TEXT_SIDEBAR_M,
            "marginTop": "3px", "fontWeight": "500",
            "textTransform": "uppercase", "letterSpacing": "0.06em",
        }),
    ], style={
        "backgroundColor": SIDEBAR_2, "padding": "12px 14px",
        "borderRadius": "8px", "border": f"1px solid {BORDER_DARK}",
        "marginBottom": "8px",
    })

def finding_block(label, value_id_or_value, color=TEXT_SIDEBAR):
    val = html.Span(value_id_or_value, style={"color": color, "fontWeight": "600"})
    return html.Div([
        html.Span(label + "  ", style={"color": TEXT_SIDEBAR_M, "fontSize": "11px"}),
        val,
    ], style={"fontSize": "11px", "padding": "5px 0",
               "borderBottom": f"1px solid {BORDER_DARK}"})

def chart_card(title, graph_id, zoom_btn_id, height="300px"):
    return html.Div([
        html.Div([
            html.Span(title, style={
                "fontSize": "12px", "fontWeight": "600",
                "color": TEXT_SECONDARY, "textTransform": "uppercase",
                "letterSpacing": "0.06em",
            }),
            dbc.Button("⤢", id=zoom_btn_id, size="sm", color="light",
                       style={"padding": "1px 7px", "fontSize": "13px",
                              "border": f"1px solid {BORDER}", "lineHeight": "1.4",
                              "color": TEXT_MUTED, "backgroundColor": "transparent"}),
        ], style={"display": "flex", "justifyContent": "space-between",
                  "alignItems": "center", "marginBottom": "10px"}),
        dcc.Graph(id=graph_id, config={"displayModeBar": False},
                  style={"height": height}),
    ], style={
        "backgroundColor": WHITE, "borderRadius": "10px",
        "border": f"1px solid {BORDER}", "padding": "16px",
        "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
    })

# ── Layout ────────────────────────────────────────────────────────────────────

SIDEBAR_W = "260px"

app.layout = html.Div([

    # ── Sidebar ──────────────────────────────────────────────────────────────
    html.Div([

        # Logo / Title
        html.Div([
            html.Div("◈", style={"fontSize": "24px", "color": BLUE,
                                  "lineHeight": "1", "marginBottom": "4px"}),
            html.Div("BIKE MARKET", style={
                "fontSize": "13px", "fontWeight": "700", "color": TEXT_SIDEBAR,
                "letterSpacing": "0.12em",
            }),
            html.Div("ANALYTICS", style={
                "fontSize": "13px", "fontWeight": "300", "color": TEXT_SIDEBAR_M,
                "letterSpacing": "0.16em", "marginTop": "-2px",
            }),
        ], style={"padding": "24px 20px 20px", "borderBottom": f"1px solid {BORDER_DARK}"}),

        # Scrollable content
        html.Div([

            # KPIs
            html.Div([
                sidebar_label("Live Metrics"),
                kpi_block("total-bikes-kpi", "Total Bikes", GREEN),
                kpi_block("avg-price-kpi",   "Average Price", AMBER),
                kpi_block("top-brand-kpi",   "Leading Brand", BLUE),
                kpi_block("total-brands-kpi","Active Brands", PURPLE),
            ], style={"marginBottom": "4px"}),

            section_divider(),

            # Key Findings
            html.Div([
                sidebar_label("Dataset Findings"),
                finding_block("Price–mileage",
                              f"{findings['price_mileage_corr']} ({findings['price_mileage_direction']})",
                              BLUE),
                finding_block("Priciest fuel", findings["premium_fuel"], AMBER),
                finding_block("Best mileage",  findings["efficient_fuel"], GREEN),
                finding_block("Best resale",
                              f"{findings['best_resale_brand']} ({findings['best_resale_pct']}%)",
                              PURPLE),
            ], style={"marginBottom": "4px"}),

            section_divider(),

            # Analysis Type
            html.Div([
                sidebar_label("Analysis Type"),
                dbc.RadioItems(
                    id="analysis-radio",
                    options=[
                        {"label": "Financial  (Price)",       "value": "financial"},
                        {"label": "Market  (Volume)",          "value": "market"},
                        {"label": "Performance  (Mileage)",    "value": "performance"},
                    ],
                    value="financial",
                    style={"fontSize": "12px", "color": TEXT_SIDEBAR},
                    input_style={"accentColor": BLUE},
                    label_style={"color": TEXT_SIDEBAR, "marginBottom": "6px",
                                 "cursor": "pointer"},
                ),
            ], style={"marginBottom": "4px"}),

            section_divider(),

            # Price Range
            html.Div([
                sidebar_label("Price Range"),
                dcc.RangeSlider(
                    id="price-range-slider",
                    min=df_clean["Price (INR)"].min(),
                    max=df_clean["Price (INR)"].max(),
                    step=50000,
                    value=[df_clean["Price (INR)"].min(), df_clean["Price (INR)"].max()],
                    marks={
                        int(df_clean["Price (INR)"].min()): {
                            "label": fmt(df_clean["Price (INR)"].min()),
                            "style": {"color": TEXT_SIDEBAR_M, "fontSize": "9px"}
                        },
                        int(df_clean["Price (INR)"].max()): {
                            "label": fmt(df_clean["Price (INR)"].max()),
                            "style": {"color": TEXT_SIDEBAR_M, "fontSize": "9px"}
                        },
                    },
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
                html.Div(id="price-range-label",
                         style={"fontSize": "11px", "color": TEXT_SIDEBAR_M,
                                "marginTop": "6px", "textAlign": "center",
                                "fontFamily": "'IBM Plex Mono', monospace"}),
            ], style={"marginBottom": "4px"}),

            section_divider(),

            # Fuel Type
            html.Div([
                sidebar_label("Fuel Type"),
                dcc.Dropdown(
                    id="fuel-dropdown",
                    options=[{"label": f, "value": f}
                             for f in sorted(df_clean["Fuel Type"].unique())]
                            + [{"label": "All Types", "value": "All"}],
                    value="All",
                    placeholder="All Types",
                    style={"fontSize": "12px"},
                ),
            ], style={"marginBottom": "4px"}),

            section_divider(),

            # Brand Selection
            html.Div([
                sidebar_label("Brand Selection"),
                dbc.Checklist(
                    id="brand-checklist",
                    options=[], value=[],
                    style={"fontSize": "12px"},
                    input_style={"accentColor": BLUE},
                    label_style={"color": TEXT_SIDEBAR, "marginBottom": "5px",
                                 "cursor": "pointer"},
                ),
            ], style={"marginBottom": "4px"}),

            section_divider(),

            # Model Selection
            html.Div([
                sidebar_label("Model Selection"),
                html.Div(id="model-checklist-wrapper", children=[
                    dbc.Checklist(
                        id="model-checklist",
                        options=[{"label": "Select a brand first",
                                  "value": "placeholder", "disabled": True}],
                        value=[],
                        style={"fontSize": "11px", "maxHeight": "140px",
                               "overflowY": "auto"},
                        input_style={"accentColor": BLUE},
                        label_style={"color": TEXT_SIDEBAR_M, "marginBottom": "4px",
                                     "cursor": "pointer"},
                    ),
                ]),
            ]),

            # Synthetic data note
            html.Div("Dataset is synthetic — for demonstration only.",
                     style={"fontSize": "10px", "color": TEXT_SIDEBAR_M,
                            "marginTop": "24px", "lineHeight": "1.5",
                            "borderTop": f"1px solid {BORDER_DARK}",
                            "paddingTop": "12px"}),

        ], style={"padding": "16px 20px", "overflowY": "auto",
                  "flex": "1", "scrollbarWidth": "thin"}),

    ], style={
        "width": SIDEBAR_W, "minWidth": SIDEBAR_W,
        "backgroundColor": SIDEBAR_BG,
        "height": "100vh", "position": "fixed", "top": 0, "left": 0,
        "display": "flex", "flexDirection": "column",
        "overflowY": "hidden",
        "fontFamily": "'IBM Plex Sans', sans-serif",
        "zIndex": "100",
    }),

    # ── Main Canvas ──────────────────────────────────────────────────────────
    html.Div([

        # Top bar
        html.Div([
            html.Div([
                html.Span("Indian Bike Market  ", style={
                    "fontSize": "17px", "fontWeight": "600", "color": TEXT_PRIMARY,
                }),
                html.Span("/ Analytics Dashboard", style={
                    "fontSize": "17px", "fontWeight": "300", "color": TEXT_MUTED,
                }),
            ]),
            html.Div(id="filter-summary", style={
                "fontSize": "11px", "color": TEXT_MUTED,
                "fontFamily": "'IBM Plex Mono', monospace",
            }),
        ], style={
            "display": "flex", "justifyContent": "space-between",
            "alignItems": "center",
            "padding": "16px 28px", "backgroundColor": WHITE,
            "borderBottom": f"1px solid {BORDER}",
            "position": "sticky", "top": 0, "zIndex": "50",
        }),

        # Content
        html.Div([

            # Row 1: Scatter + Analytics
            dbc.Row([
                dbc.Col([
                    chart_card("Price vs Mileage", "scatter-plot",
                               "zoom-scatter-btn", height="360px"),
                ], width=8),

                dbc.Col([
                    html.Div([
                        # Tab strip
                        dbc.Tabs([
                            dbc.Tab(label="Overview",  tab_id="market-summary"),
                            dbc.Tab(label="Scatter",   tab_id="scatter-analysis"),
                            dbc.Tab(label="Brands",    tab_id="pie-analysis"),
                            dbc.Tab(label="Engine",    tab_id="line-analysis"),
                            dbc.Tab(label="Fuel",      tab_id="fuel-analysis"),
                        ], id="chart-description-tabs", active_tab="market-summary",
                           style={"marginBottom": "12px"},
                           ),
                        html.Div(id="chart-description-content",
                                 style={"overflowY": "auto", "maxHeight": "320px"}),
                    ], style={
                        "backgroundColor": WHITE, "borderRadius": "10px",
                        "border": f"1px solid {BORDER}", "padding": "16px",
                        "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
                        "height": "100%",
                    }),
                ], width=4),
            ], className="mb-3"),

            # Row 2: Three bottom charts
            dbc.Row([
                dbc.Col(chart_card("Brand Market Share",    "pie-chart",      "zoom-pie-btn"),  width=4),
                dbc.Col(chart_card("Engine Capacity Trends","line-chart",     "zoom-line-btn"), width=4),
                dbc.Col(chart_card("Fuel Type Analysis",    "fuel-bar-chart", "zoom-fuel-btn"), width=4),
            ]),

        ], style={"padding": "24px 28px"}),

    ], style={
        "marginLeft": SIDEBAR_W,
        "backgroundColor": CANVAS_BG,
        "minHeight": "100vh",
        "fontFamily": "'IBM Plex Sans', sans-serif",
    }),

    # ── Modals ────────────────────────────────────────────────────────────────
    dbc.Modal([
        dbc.ModalHeader("Price vs Mileage — Expanded",
                        style={"fontFamily": "'IBM Plex Sans', sans-serif"}),
        dbc.ModalBody(dcc.Graph(id="zoomed-scatter-plot", style={"height": "550px"})),
    ], id="scatter-modal", size="xl", is_open=False),

    dbc.Modal([
        dbc.ModalHeader("Brand Market Share — Expanded",
                        style={"fontFamily": "'IBM Plex Sans', sans-serif"}),
        dbc.ModalBody(dcc.Graph(id="zoomed-pie-chart", style={"height": "550px"})),
    ], id="pie-modal", size="xl", is_open=False),

    dbc.Modal([
        dbc.ModalHeader("Engine Capacity Trends — Expanded",
                        style={"fontFamily": "'IBM Plex Sans', sans-serif"}),
        dbc.ModalBody(dcc.Graph(id="zoomed-line-chart", style={"height": "550px"})),
    ], id="line-modal", size="xl", is_open=False),

    dbc.Modal([
        dbc.ModalHeader("Fuel Type Analysis — Expanded",
                        style={"fontFamily": "'IBM Plex Sans', sans-serif"}),
        dbc.ModalBody(dcc.Graph(id="zoomed-fuel-chart", style={"height": "550px"})),
    ], id="fuel-modal", size="xl", is_open=False),

], style={"margin": "0", "padding": "0"})

# ── Callbacks ─────────────────────────────────────────────────────────────────

@app.callback(
    Output("price-range-label", "children"),
    Input("price-range-slider", "value"),
)
def update_price_label(val):
    return f"{fmt(val[0])}  —  {fmt(val[1])}"


@app.callback(
    Output("brand-checklist", "options"),
    Output("brand-checklist", "value"),
    Input("analysis-radio", "value"),
)
def init_brands(_):
    brands = sorted(df_clean["Brand"].value_counts().head(10).index)
    return [{"label": b, "value": b} for b in brands], brands[:6]


@app.callback(
    Output("model-checklist", "options"),
    Output("model-checklist", "value"),
    Input("brand-checklist", "value"),
)
def update_models(selected_brands):
    if not selected_brands:
        return [{"label": "Select a brand first", "value": "placeholder",
                 "disabled": True}], []
    models = sorted(df_clean[df_clean["Brand"].isin(selected_brands)]["Model"].unique())
    opts = [{"label": "All Models", "value": "All"}] + \
           [{"label": m, "value": m} for m in models]
    return opts, ["All"]


@app.callback(
    Output("total-bikes-kpi",  "children"),
    Output("avg-price-kpi",    "children"),
    Output("top-brand-kpi",    "children"),
    Output("total-brands-kpi", "children"),
    Output("filter-summary",   "children"),
    Input("price-range-slider", "value"),
    Input("fuel-dropdown",      "value"),
    Input("brand-checklist",    "value"),
    Input("model-checklist",    "value"),
)
def update_kpis(price_range, fuel, brands, models):
    fdf = apply_filters(price_range, fuel, brands, models)
    if len(fdf) == 0:
        return "0", "—", "—", "0", "No data matches current filters"
    fuel_label = fuel if fuel and fuel != "All" else "All fuels"
    summary = f"{len(fdf):,} models · {fuel_label} · {fmt(price_range[0])}–{fmt(price_range[1])}"
    return (
        f"{len(fdf):,}",
        fmt(fdf["Price (INR)"].mean()),
        fdf["Brand"].value_counts().index[0],
        str(fdf["Brand"].nunique()),
        summary,
    )


@app.callback(
    Output("scatter-plot", "figure"),
    Input("price-range-slider", "value"),
    Input("fuel-dropdown",      "value"),
    Input("brand-checklist",    "value"),
    Input("model-checklist",    "value"),
)
def update_scatter(price_range, fuel, brands, models):
    return create_scatter(apply_filters(price_range, fuel, brands, models), brands)


@app.callback(
    Output("pie-chart", "figure"),
    Input("price-range-slider", "value"),
    Input("fuel-dropdown",      "value"),
    Input("brand-checklist",    "value"),
    Input("model-checklist",    "value"),
)
def update_pie(price_range, fuel, brands, models):
    return create_pie(apply_filters(price_range, fuel, brands, models))


@app.callback(
    Output("line-chart", "figure"),
    Input("price-range-slider", "value"),
    Input("fuel-dropdown",      "value"),
    Input("analysis-radio",     "value"),
    Input("brand-checklist",    "value"),
    Input("model-checklist",    "value"),
)
def update_line(price_range, fuel, perspective, brands, models):
    m = get_metrics(perspective)
    return create_trend(apply_filters(price_range, fuel, brands, models), m["trend"])


@app.callback(
    Output("fuel-bar-chart", "figure"),
    Input("price-range-slider", "value"),
    Input("fuel-dropdown",      "value"),
    Input("analysis-radio",     "value"),
    Input("brand-checklist",    "value"),
    Input("model-checklist",    "value"),
)
def update_fuel(price_range, fuel, perspective, brands, models):
    m = get_metrics(perspective)
    return create_fuel_bar(apply_filters(price_range, fuel, brands, models), m["fuel"])


@app.callback(
    Output("chart-description-content", "children"),
    Input("chart-description-tabs",  "active_tab"),
    Input("price-range-slider",       "value"),
    Input("fuel-dropdown",            "value"),
    Input("analysis-radio",           "value"),
    Input("brand-checklist",          "value"),
    Input("model-checklist",          "value"),
)
def update_analytics(tab, price_range, fuel, perspective, brands, models):
    fdf = apply_filters(price_range, fuel, brands, models)
    if tab == "market-summary":   return analytics_market_summary(fdf)
    if tab == "scatter-analysis": return analytics_scatter(fdf)
    if tab == "pie-analysis":     return analytics_pie(fdf)
    if tab == "line-analysis":    return analytics_line(fdf, perspective)
    if tab == "fuel-analysis":    return analytics_fuel(fdf)
    return html.P("Select a tab.", style={"fontSize": "12px"})


@app.callback(
    Output("scatter-modal", "is_open"),
    Output("zoomed-scatter-plot", "figure"),
    Input("zoom-scatter-btn", "n_clicks"),
    State("scatter-modal", "is_open"),
    State("scatter-plot", "figure"),
    prevent_initial_call=True,
)
def zoom_scatter(n, is_open, fig):
    if fig and not is_open:
        fig["layout"]["height"] = 600
    return not is_open, fig or {}


@app.callback(
    Output("pie-modal", "is_open"),
    Output("zoomed-pie-chart", "figure"),
    Input("zoom-pie-btn", "n_clicks"),
    State("pie-modal", "is_open"),
    State("pie-chart", "figure"),
    prevent_initial_call=True,
)
def zoom_pie(n, is_open, fig):
    if fig and not is_open:
        fig["layout"]["height"] = 600
    return not is_open, fig or {}


@app.callback(
    Output("line-modal", "is_open"),
    Output("zoomed-line-chart", "figure"),
    Input("zoom-line-btn", "n_clicks"),
    State("line-modal", "is_open"),
    State("line-chart", "figure"),
    prevent_initial_call=True,
)
def zoom_line(n, is_open, fig):
    if fig and not is_open:
        fig["layout"]["height"] = 600
    return not is_open, fig or {}


@app.callback(
    Output("fuel-modal", "is_open"),
    Output("zoomed-fuel-chart", "figure"),
    Input("zoom-fuel-btn", "n_clicks"),
    State("fuel-modal", "is_open"),
    State("fuel-bar-chart", "figure"),
    prevent_initial_call=True,
)
def zoom_fuel(n, is_open, fig):
    if fig and not is_open:
        fig["layout"]["height"] = 600
    return not is_open, fig or {}


# ── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(port=8061, debug=False)
