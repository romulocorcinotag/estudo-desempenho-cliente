import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import requests
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import os

warnings.filterwarnings("ignore")

_DIR = os.path.dirname(os.path.abspath(__file__))

st.set_page_config(
    page_title="TAG Investimentos — Estudo de Desempenho",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded",
)

# ── TAG Brand Colors ─────────────────────────────────────────────────────────
TAG_VERMELHO = "#630D24"
TAG_VERMELHO_LIGHT = "#8A1E3A"
TAG_OFFWHITE = "#F5F4F0"
TAG_LARANJA = "#FF8853"
TAG_AZUL_ESCURO = "#002A6E"
TAG_ROSA = "#ED5A6E"
TAG_ROXO = "#A485F2"
TAG_CINZA = "#6A6864"
TAG_BRANCO = "#FFFFFF"

CHART_COLORS = {
    "carteira": TAG_AZUL_ESCURO,
    "ibovespa": TAG_LARANJA,
    "cdi": TAG_ROXO,
    "bench67": TAG_ROSA,
}

_logo_path = os.path.join(_DIR, "tag_logo.png")

# ── CSS Profissional ─────────────────────────────────────────────────────────
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp {{
        background-color: {TAG_OFFWHITE};
        font-family: 'Inter', 'Tahoma', sans-serif;
    }}
    header[data-testid="stHeader"] {{
        background-color: {TAG_VERMELHO};
    }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {TAG_VERMELHO} 0%, {TAG_VERMELHO_LIGHT} 100%);
    }}
    section[data-testid="stSidebar"] * {{
        color: #F5F4F0 !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox > div > div {{
        background-color: rgba(255,255,255,0.1);
        border: 1px solid rgba(255,136,83,0.4);
        border-radius: 8px;
    }}

    /* Metric cards */
    div[data-testid="stMetric"] {{
        background-color: {TAG_BRANCO};
        border: 1px solid #E8E6DD;
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        border-left: 4px solid {TAG_VERMELHO};
        box-shadow: 0 2px 8px rgba(99,13,36,0.06);
        text-align: center;
    }}
    div[data-testid="stMetric"] label {{
        color: {TAG_CINZA} !important;
        font-weight: 600 !important;
        font-size: 0.72rem !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
        color: {TAG_AZUL_ESCURO} !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }}
    div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {{
        font-size: 0.82rem !important;
        justify-content: center;
    }}

    /* Section headers */
    .section-title {{
        color: {TAG_VERMELHO};
        font-size: 1.15rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding-bottom: 0.5rem;
        margin: 2rem 0 1rem 0;
        border-bottom: 2px solid {TAG_LARANJA};
    }}

    /* Charts container */
    .stPlotlyChart {{
        background-color: {TAG_BRANCO};
        border-radius: 12px;
        padding: 0.8rem;
        box-shadow: 0 2px 8px rgba(99,13,36,0.04);
        border: 1px solid #E8E6DD;
    }}

    /* Header banner */
    .tag-header {{
        background: linear-gradient(135deg, {TAG_VERMELHO} 0%, {TAG_VERMELHO_LIGHT} 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 0.5rem;
        box-shadow: 0 4px 16px rgba(99,13,36,0.15);
    }}
    .tag-header h1 {{
        color: #FFFFFF !important;
        font-size: 2rem !important;
        font-weight: 300 !important;
        letter-spacing: 0.08em;
        margin: 0.8rem 0 0 0 !important;
        padding: 0 !important;
        border: none !important;
    }}
    .tag-header .subtitle {{
        color: {TAG_LARANJA};
        font-size: 0.9rem;
        margin-top: 0.6rem;
        font-weight: 400;
        letter-spacing: 0.02em;
    }}
    .tag-header .divider {{
        width: 60px;
        height: 2px;
        background: {TAG_LARANJA};
        margin: 1rem auto 0 auto;
    }}

    /* Disclaimer */
    .disclaimer {{
        background: {TAG_BRANCO};
        border-left: 4px solid {TAG_LARANJA};
        border-radius: 0 12px 12px 0;
        padding: 1rem 1.5rem;
        margin-top: 2rem;
        font-size: 0.75rem;
        color: {TAG_CINZA};
        line-height: 1.6;
    }}

    /* Footer */
    .tag-footer {{
        background: linear-gradient(135deg, {TAG_VERMELHO} 0%, {TAG_VERMELHO_LIGHT} 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-top: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(99,13,36,0.1);
    }}
    .tag-footer p {{
        color: rgba(255,255,255,0.85) !important;
        font-size: 0.8rem !important;
        margin: 0 !important;
        line-height: 1.7;
    }}

    /* Hide streamlit defaults */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    .stMarkdown h2, .stMarkdown h3 {{
        display: none;
    }}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def section_title(text):
    st.markdown(f'<div class="section-title">{text}</div>', unsafe_allow_html=True)


@st.cache_data(ttl=86400)
def load_portfolio(path):
    if path.endswith(".csv"):
        data = pd.read_csv(path, parse_dates=["Date"])
    else:
        df = pd.read_excel(path, header=None)
        data = df.iloc[11:].copy()
        data = data[[1, 3, 8, 11, 15, 19, 21]].copy()
        data.columns = [
            "Date", "Entradas", "Saidas", "Patrimonio",
            "QtdCotas", "CotaFechamento", "CotaRendimento",
        ]
        data = data.dropna(subset=["Date"])
        data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
        data = data.dropna(subset=["Date"])
    for c in ["Patrimonio", "CotaRendimento", "Entradas", "Saidas"]:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    data = data.dropna(subset=["CotaRendimento"])
    data = data.sort_values("Date").reset_index(drop=True)
    first_valid = data[data["Patrimonio"] > 0].index[0]
    data = data.loc[first_valid:].reset_index(drop=True)
    # Suaviza patrimonio: interpola zeros e spikes isolados
    pat = data["Patrimonio"].copy()
    # 1) Substitui zeros/negativos por NaN e interpola
    pat[pat <= 0] = np.nan
    pat = pat.interpolate(method="linear").ffill().bfill()
    # 2) Remove V-shapes: variação >30% ida e volta
    for _ in range(3):  # multiplas passadas para pegar sequencias
        for i in range(1, len(pat) - 1):
            prev, cur, nxt = pat.iloc[i - 1], pat.iloc[i], pat.iloc[i + 1]
            if prev > 0 and nxt > 0:
                drop = abs(cur / prev - 1)
                recover = abs(nxt / cur - 1)
                if drop > 0.30 and recover > 0.30:
                    pat.iloc[i] = (prev + nxt) / 2
    data["Patrimonio"] = pat
    return data


@st.cache_data(ttl=86400)
def _load_ibov_bcb(start, end):
    chunks = []
    d = start
    while d <= end:
        d_end = min(d + timedelta(days=3650), end)
        di, df_str = d.strftime("%d/%m/%Y"), d_end.strftime("%d/%m/%Y")
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.7/dados?formato=json&dataInicial={di}&dataFinal={df_str}"
        try:
            r = requests.get(url, timeout=30, headers={"Accept": "application/json"})
            if r.status_code == 200:
                chunks.extend(r.json())
        except Exception:
            pass
        d = d_end + timedelta(days=1)
    if not chunks:
        return pd.DataFrame(columns=["Date", "Close"])
    df = pd.DataFrame(chunks)
    df["data"] = pd.to_datetime(df["data"], format="%d/%m/%Y")
    df["valor"] = df["valor"].astype(float)
    df = df.sort_values("data").drop_duplicates(subset="data").reset_index(drop=True)
    df.columns = ["Date", "Close"]
    return df


@st.cache_data(ttl=86400)
def load_ibov(start, end):
    try:
        ibov = yf.download("^BVSP", start=start, end=end + timedelta(days=5), progress=False)
        if not ibov.empty:
            if isinstance(ibov.columns, pd.MultiIndex):
                close = ibov[("Close", "^BVSP")].reset_index()
                close.columns = ["Date", "Close"]
            else:
                close = ibov[["Close"]].reset_index()
                close.columns = ["Date", "Close"]
            close["Date"] = pd.to_datetime(close["Date"])
            if close["Date"].dt.tz is not None:
                close["Date"] = close["Date"].dt.tz_localize(None)
            close = close.dropna(subset=["Close"])
            close = close.sort_values("Date").reset_index(drop=True)
            if len(close) > 10:
                return close
    except Exception:
        pass
    return _load_ibov_bcb(start, end)


@st.cache_data(ttl=86400)
def load_cdi(start, end):
    chunks = []
    d = start
    while d <= end:
        d_end = min(d + timedelta(days=3650), end)
        di, df_str = d.strftime("%d/%m/%Y"), d_end.strftime("%d/%m/%Y")
        url = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.12/dados?formato=json&dataInicial={di}&dataFinal={df_str}"
        try:
            r = requests.get(url, timeout=30, headers={"Accept": "application/json"})
            if r.status_code == 200:
                chunks.extend(r.json())
        except Exception:
            pass
        d = d_end + timedelta(days=1)
    if not chunks:
        return pd.DataFrame(columns=["Date", "CDI_pct"])
    cdi = pd.DataFrame(chunks)
    cdi["data"] = pd.to_datetime(cdi["data"], format="%d/%m/%Y")
    cdi["valor"] = cdi["valor"].astype(float)
    cdi = cdi.sort_values("data").drop_duplicates(subset="data").reset_index(drop=True)
    cdi.columns = ["Date", "CDI_pct"]
    return cdi


def calc_drawdown(s):
    return (s - s.cummax()) / s.cummax()


def rolling_return(s, w):
    return s / s.shift(w) - 1


def annualized_return(total_ret, days):
    if days <= 0 or np.isnan(total_ret):
        return 0.0
    return (1 + total_ret) ** (252 / days) - 1


def annualized_vol(rets):
    return rets.std() * np.sqrt(252)


def tag_chart_layout(fig, height=450, yaxis_title="", ticksuffix="%"):
    fig.update_layout(
        height=height,
        hovermode="x unified",
        yaxis_title=yaxis_title,
        yaxis_ticksuffix=ticksuffix,
        plot_bgcolor=TAG_BRANCO,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, Tahoma, sans-serif", size=12, color=TAG_AZUL_ESCURO),
        legend=dict(
            orientation="h", y=1.12, x=0.5, xanchor="center",
            font=dict(size=11, color=TAG_AZUL_ESCURO),
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#E8E6DD", borderwidth=1,
        ),
        xaxis=dict(gridcolor="#F0EEE8", showgrid=True, linecolor="#E0DDD5"),
        yaxis=dict(gridcolor="#F0EEE8", showgrid=True, linecolor="#E0DDD5"),
        margin=dict(l=60, r=20, t=40, b=40),
    )
    return fig


def style_table(df):
    html = '<div style="overflow-x:auto;border-radius:12px;border:1px solid #E8E6DD;box-shadow:0 2px 8px rgba(99,13,36,0.05);margin:0.5rem auto 1.5rem auto;max-width:900px;">'
    html += '<table style="width:100%;border-collapse:collapse;font-family:Inter,Tahoma,sans-serif;font-size:0.85rem;">'
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th style="background:{TAG_VERMELHO};color:#F5F4F0;padding:0.75rem 1rem;text-align:center;font-weight:600;font-size:0.75rem;letter-spacing:0.05em;text-transform:uppercase;border:none;">{col}</th>'
    html += '</tr></thead><tbody>'
    for i, (_, row) in enumerate(df.iterrows()):
        bg = TAG_BRANCO if i % 2 == 0 else "#FAFAF8"
        html += '<tr>'
        for j, val in enumerate(row):
            fw = "600" if j == 0 else "400"
            color = TAG_VERMELHO if j == 0 else TAG_AZUL_ESCURO
            html += f'<td style="background:{bg};color:{color};padding:0.6rem 1rem;text-align:center;font-weight:{fw};border-bottom:1px solid #F0EEE8;">{val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html


def build_merged(port_df, ibov_df, cdi_df):
    merged = port_df[["Date", "CotaRendimento", "Patrimonio"]].copy()
    if len(ibov_df) > 0:
        merged = merged.merge(ibov_df, on="Date", how="left")
    else:
        merged["Close"] = np.nan
    merged = merged.merge(cdi_df, on="Date", how="left")
    merged = merged.sort_values("Date").reset_index(drop=True)
    merged["Close"] = merged["Close"].ffill().bfill()
    merged["CDI_pct"] = merged["CDI_pct"].fillna(0)

    merged["Portfolio_cum"] = merged["CotaRendimento"] / merged["CotaRendimento"].iloc[0] - 1

    if merged["Close"].notna().any():
        merged["Ibov_cum"] = merged["Close"] / merged["Close"].iloc[0] - 1
    else:
        merged["Ibov_cum"] = np.nan

    merged["CDI_factor"] = (1 + merged["CDI_pct"] / 100).cumprod()
    merged["CDI_cum"] = merged["CDI_factor"] / merged["CDI_factor"].iloc[0] - 1

    ibov_norm = merged["Close"] / merged["Close"].iloc[0] if merged["Close"].notna().any() else pd.Series(np.nan, index=merged.index)
    cdi_norm = merged["CDI_factor"] / merged["CDI_factor"].iloc[0]
    merged["Ibov_daily_ret"] = ibov_norm.pct_change().fillna(0)
    merged["CDI_daily_ret"] = cdi_norm.pct_change().fillna(0)
    merged["Bench67_daily_ret"] = 0.67 * merged["Ibov_daily_ret"] + 0.33 * merged["CDI_daily_ret"]
    merged["Bench67_factor"] = (1 + merged["Bench67_daily_ret"]).cumprod()
    merged["Bench67_cum"] = merged["Bench67_factor"] - 1

    port_norm = 1 + merged["Portfolio_cum"]
    merged["Port_ret"] = port_norm.pct_change()
    merged["Ibov_ret"] = ibov_norm.pct_change()
    merged["CDI_ret"] = cdi_norm.pct_change()
    merged["Bench67_ret"] = merged["Bench67_factor"].pct_change()

    return merged


def fmt_pct(v):
    return f"{v:.2%}" if not np.isnan(v) else "\u2014"

def fmt_f(v):
    return f"{v:.2f}" if not np.isnan(v) else "\u2014"


# ── Load Data ────────────────────────────────────────────────────────────────

_CSV = os.path.join(_DIR, "portfolio_data.csv")
_XLS = r"C:\Users\romulo.corcino_tagin\Downloads\ReportHistoricoCota (3).xls"
DATA_PATH = _CSV if os.path.exists(_CSV) else _XLS

port_full = load_portfolio(DATA_PATH)
full_start = port_full["Date"].min()
full_end = port_full["Date"].max()

ibov_raw = load_ibov(full_start, full_end)
cdi_raw = load_cdi(full_start, full_end)

ibov_ok = len(ibov_raw) > 0 and ibov_raw["Close"].notna().any()


# ── Sidebar ──────────────────────────────────────────────────────────────────

if os.path.exists(_logo_path):
    st.sidebar.image(_logo_path, width=130)

st.sidebar.markdown("")
st.sidebar.markdown(f'<p style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:{TAG_LARANJA} !important;margin-bottom:0.3rem;font-weight:600;">Periodo de Analise</p>', unsafe_allow_html=True)

preset = st.sidebar.selectbox(
    "Periodo",
    ["Desde o Inicio", "YTD", "Ultimo Ano", "Ultimos 2 Anos", "Ultimos 3 Anos", "Ultimos 5 Anos", "Personalizado"],
    index=0,
    label_visibility="collapsed",
)

today_ref = full_end
if preset == "YTD":
    sel_start, sel_end = pd.Timestamp(today_ref.year, 1, 1), today_ref
elif preset == "Ultimo Ano":
    sel_start, sel_end = today_ref - pd.DateOffset(years=1), today_ref
elif preset == "Ultimos 2 Anos":
    sel_start, sel_end = today_ref - pd.DateOffset(years=2), today_ref
elif preset == "Ultimos 3 Anos":
    sel_start, sel_end = today_ref - pd.DateOffset(years=3), today_ref
elif preset == "Ultimos 5 Anos":
    sel_start, sel_end = today_ref - pd.DateOffset(years=5), today_ref
elif preset == "Personalizado":
    sel_start = pd.Timestamp(st.sidebar.date_input("Data Inicio", value=full_start.date(), min_value=full_start.date(), max_value=full_end.date()))
    sel_end = pd.Timestamp(st.sidebar.date_input("Data Fim", value=full_end.date(), min_value=full_start.date(), max_value=full_end.date()))
else:
    sel_start, sel_end = full_start, full_end

sel_start = max(sel_start, full_start)
sel_end = min(sel_end, full_end)

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="text-align:center;">
    <p style="font-size:0.65rem;color:rgba(245,244,240,0.5) !important;margin:0;">Dados atualizados ate</p>
    <p style="font-size:0.85rem;color:{TAG_LARANJA} !important;font-weight:600;margin:0.2rem 0 0 0;">{full_end.strftime('%d/%m/%Y')}</p>
</div>
""", unsafe_allow_html=True)

port_filtered = port_full[(port_full["Date"] >= sel_start) & (port_full["Date"] <= sel_end)].reset_index(drop=True)
if len(port_filtered) < 2:
    st.error("Periodo selecionado nao tem dados suficientes.")
    st.stop()

merged = build_merged(port_filtered, ibov_raw, cdi_raw)

start_date = merged["Date"].iloc[0]
end_date = merged["Date"].iloc[-1]
n_days = len(merged) - 1
total_days = (end_date - start_date).days


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""<div class="tag-header">
<h1>Estudo de Desempenho</h1>
<div class="subtitle">{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')} &nbsp;&bull;&nbsp; {total_days:,} dias corridos &nbsp;&bull;&nbsp; {n_days:,} dias uteis &nbsp;&bull;&nbsp; ~{total_days / 365:.1f} anos</div>
<div class="divider"></div>
</div>""", unsafe_allow_html=True)

if not ibov_ok:
    st.warning("Dados do Ibovespa indisponiveis. Exibindo apenas Carteira vs CDI.")


# ══════════════════════════════════════════════════════════════════════════════
# KPIs — RESUMO
# ══════════════════════════════════════════════════════════════════════════════

port_total = merged["Portfolio_cum"].iloc[-1]
ibov_total = merged["Ibov_cum"].iloc[-1] if ibov_ok else np.nan
cdi_total = merged["CDI_cum"].iloc[-1]
bench67_total = merged["Bench67_cum"].iloc[-1] if ibov_ok else np.nan

port_ann = annualized_return(port_total, total_days)
ibov_ann = annualized_return(ibov_total, total_days) if ibov_ok else np.nan
cdi_ann = annualized_return(cdi_total, total_days)
bench67_ann = annualized_return(bench67_total, total_days) if ibov_ok else np.nan

port_vol = annualized_vol(merged["Port_ret"].dropna())
ibov_vol = annualized_vol(merged["Ibov_ret"].dropna()) if ibov_ok else np.nan
bench67_vol = annualized_vol(merged["Bench67_ret"].dropna()) if ibov_ok else np.nan

cdi_daily_avg = merged["CDI_ret"].dropna().mean()
port_std = merged["Port_ret"].dropna().std()
ibov_std = merged["Ibov_ret"].dropna().std() if ibov_ok else 0
bench67_std = merged["Bench67_ret"].dropna().std() if ibov_ok else 0

port_sharpe = (merged["Port_ret"].dropna().mean() - cdi_daily_avg) / port_std * np.sqrt(252) if port_std > 0 else 0
ibov_sharpe = (merged["Ibov_ret"].dropna().mean() - cdi_daily_avg) / ibov_std * np.sqrt(252) if ibov_ok and ibov_std > 0 else np.nan
bench67_sharpe = (merged["Bench67_ret"].dropna().mean() - cdi_daily_avg) / bench67_std * np.sqrt(252) if ibov_ok and bench67_std > 0 else np.nan

port_dd = calc_drawdown(1 + merged["Portfolio_cum"])
ibov_dd = calc_drawdown(1 + merged["Ibov_cum"]) if ibov_ok else pd.Series(0, index=merged.index)
bench67_dd = calc_drawdown(1 + merged["Bench67_cum"]) if ibov_ok else pd.Series(0, index=merged.index)

section_title("Retorno Acumulado")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Carteira", fmt_pct(port_total), f"anual: {fmt_pct(port_ann)}")
c2.metric("Ibovespa", fmt_pct(ibov_total), f"anual: {fmt_pct(ibov_ann)}")
c3.metric("CDI", fmt_pct(cdi_total), f"anual: {fmt_pct(cdi_ann)}")
c4.metric("67% Ibov + 33% CDI", fmt_pct(bench67_total), f"anual: {fmt_pct(bench67_ann)}")

section_title("Risco")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Vol. Carteira", fmt_pct(port_vol))
c2.metric("Vol. Ibovespa", fmt_pct(ibov_vol))
c3.metric("Vol. CDI", "~0%")
c4.metric("Vol. Bench 67/33", fmt_pct(bench67_vol))

c1, c2, c3, c4 = st.columns(4)
c1.metric("Max DD Carteira", fmt_pct(port_dd.min()))
c2.metric("Max DD Ibovespa", fmt_pct(ibov_dd.min()) if ibov_ok else "\u2014")
c3.metric("Max DD CDI", "~0%")
c4.metric("Max DD Bench 67/33", fmt_pct(bench67_dd.min()) if ibov_ok else "\u2014")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Sharpe Carteira", fmt_f(port_sharpe))
c2.metric("Sharpe Ibovespa", fmt_f(ibov_sharpe))
c3.metric("Sharpe CDI", "\u2014")
c4.metric("Sharpe Bench 67/33", fmt_f(bench67_sharpe))


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 1 — Retorno Acumulado
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retorno Acumulado (%)")

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Portfolio_cum"] * 100, name="Carteira", line=dict(width=2.5, color=CHART_COLORS["carteira"])))
if ibov_ok:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Ibov_cum"] * 100, name="Ibovespa", line=dict(width=1.8, color=CHART_COLORS["ibovespa"])))
fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["CDI_cum"] * 100, name="CDI", line=dict(width=1.8, color=CHART_COLORS["cdi"], dash="dot")))
if ibov_ok:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench67_cum"] * 100, name="67% Ibov + 33% CDI", line=dict(width=1.8, color=CHART_COLORS["bench67"], dash="dash")))
tag_chart_layout(fig1, height=500, yaxis_title="Retorno Acumulado (%)")
st.plotly_chart(fig1, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 2 — Drawdown
# ══════════════════════════════════════════════════════════════════════════════

section_title("Drawdown")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=merged["Date"], y=port_dd * 100, name="Carteira", fill="tozeroy", line=dict(color=CHART_COLORS["carteira"]), fillcolor="rgba(0,42,110,0.10)"))
if ibov_ok:
    fig2.add_trace(go.Scatter(x=merged["Date"], y=ibov_dd * 100, name="Ibovespa", line=dict(color=CHART_COLORS["ibovespa"], width=1)))
    fig2.add_trace(go.Scatter(x=merged["Date"], y=bench67_dd * 100, name="67% Ibov + 33% CDI", line=dict(color=CHART_COLORS["bench67"], width=1, dash="dash")))
tag_chart_layout(fig2, height=350, yaxis_title="Drawdown (%)")
st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 3 — Retornos Anuais
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retornos Anuais")

merged["Year"] = merged["Date"].dt.year
yearly = merged.groupby("Year").agg(
    Port_start=("Portfolio_cum", lambda x: 1 + x.iloc[0]),
    Port_end=("Portfolio_cum", lambda x: 1 + x.iloc[-1]),
    Ibov_start=("Ibov_cum", lambda x: 1 + x.iloc[0]),
    Ibov_end=("Ibov_cum", lambda x: 1 + x.iloc[-1]),
    CDI_start=("CDI_cum", lambda x: 1 + x.iloc[0]),
    CDI_end=("CDI_cum", lambda x: 1 + x.iloc[-1]),
    Bench67_start=("Bench67_cum", lambda x: 1 + x.iloc[0]),
    Bench67_end=("Bench67_cum", lambda x: 1 + x.iloc[-1]),
).reset_index()

for prefix in ["Port", "Ibov", "CDI", "Bench67"]:
    yearly[f"{prefix}_ret"] = yearly[f"{prefix}_end"] / yearly[f"{prefix}_start"] - 1

fig3 = go.Figure()
fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Port_ret"] * 100, name="Carteira", marker_color=CHART_COLORS["carteira"]))
if ibov_ok:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Ibov_ret"] * 100, name="Ibovespa", marker_color=CHART_COLORS["ibovespa"]))
fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["CDI_ret"] * 100, name="CDI", marker_color=CHART_COLORS["cdi"]))
if ibov_ok:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Bench67_ret"] * 100, name="67% Ibov + 33% CDI", marker_color=CHART_COLORS["bench67"]))
tag_chart_layout(fig3, height=450, yaxis_title="Retorno (%)")
fig3.update_layout(barmode="group")
st.plotly_chart(fig3, use_container_width=True)

cols_display = ["Year", "Port_ret", "CDI_ret"]
col_names = ["Ano", "Carteira", "CDI"]
if ibov_ok:
    cols_display = ["Year", "Port_ret", "Ibov_ret", "CDI_ret", "Bench67_ret"]
    col_names = ["Ano", "Carteira", "Ibovespa", "CDI", "67% Ibov + 33% CDI"]
yearly_display = yearly[cols_display].copy()
yearly_display.columns = col_names
for c in col_names[1:]:
    yearly_display[c] = yearly_display[c].apply(lambda x: f"{x:.2%}" if not np.isnan(x) else "\u2014")
yearly_display["Ano"] = yearly_display["Ano"].astype(str)
st.markdown(style_table(yearly_display), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 4 — Rolling 12M
# ══════════════════════════════════════════════════════════════════════════════

rolling_windows = {"1 Ano": 252, "3 Anos": 756, "5 Anos": 1260}

for roll_label, roll_window in rolling_windows.items():
    if n_days >= roll_window:
        section_title(f"Retorno Rolling {roll_label}")

        port_roll = rolling_return(1 + merged["Portfolio_cum"], roll_window)
        cdi_roll = rolling_return(1 + merged["CDI_cum"], roll_window)

        fig_roll = go.Figure()
        fig_roll.add_trace(go.Scatter(x=merged["Date"], y=port_roll * 100, name="Carteira", line=dict(color=CHART_COLORS["carteira"], width=2)))
        if ibov_ok:
            ibov_roll = rolling_return(1 + merged["Ibov_cum"], roll_window)
            bench_roll = rolling_return(1 + merged["Bench67_cum"], roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=ibov_roll * 100, name="Ibovespa", line=dict(color=CHART_COLORS["ibovespa"], width=1.5)))
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=bench_roll * 100, name="67% Ibov + 33% CDI", line=dict(color=CHART_COLORS["bench67"], width=1.5, dash="dash")))
        fig_roll.add_trace(go.Scatter(x=merged["Date"], y=cdi_roll * 100, name="CDI", line=dict(color=CHART_COLORS["cdi"], width=1.5, dash="dot")))
        tag_chart_layout(fig_roll, height=400, yaxis_title=f"Retorno {roll_label} (%)")
        st.plotly_chart(fig_roll, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 5 — Excesso de Retorno
# ══════════════════════════════════════════════════════════════════════════════

section_title("Excesso de Retorno vs Benchmarks")

fig5 = go.Figure()
if ibov_ok:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["Ibov_cum"]) * 100, name="vs Ibovespa", line=dict(color=CHART_COLORS["ibovespa"], width=1.8)))
fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["CDI_cum"]) * 100, name="vs CDI", line=dict(color=CHART_COLORS["cdi"], width=1.8)))
if ibov_ok:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["Bench67_cum"]) * 100, name="vs 67% Ibov + 33% CDI", line=dict(color=CHART_COLORS["bench67"], width=1.8)))
fig5.add_hline(y=0, line_dash="dash", line_color=TAG_CINZA)
tag_chart_layout(fig5, height=400, yaxis_title="Excesso (p.p.)", ticksuffix=" p.p.")
st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 6 — Patrimonio
# ══════════════════════════════════════════════════════════════════════════════

section_title("Evolucao do Patrimonio (R$)")

fig6 = go.Figure()
fig6.add_trace(go.Scatter(x=merged["Date"], y=merged["Patrimonio"], name="Patrimonio", fill="tozeroy", line=dict(color=TAG_AZUL_ESCURO, width=2), fillcolor="rgba(0,42,110,0.08)"))
tag_chart_layout(fig6, height=350, yaxis_title="R$", ticksuffix="")
fig6.update_layout(yaxis_tickformat=",.0f", yaxis_tickprefix="R$ ")
st.plotly_chart(fig6, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABELA — Retornos por Periodo
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retornos por Periodo")

merged_full = build_merged(port_full, ibov_raw, cdi_raw)

def period_return_from_end(df, n):
    if len(df) < n + 1:
        return None
    idx = len(df) - 1 - n
    port_ret = (1 + df["Portfolio_cum"].iloc[-1]) / (1 + df["Portfolio_cum"].iloc[idx]) - 1
    ibov_ret = (1 + df["Ibov_cum"].iloc[-1]) / (1 + df["Ibov_cum"].iloc[idx]) - 1 if ibov_ok else np.nan
    cdi_ret = (1 + df["CDI_cum"].iloc[-1]) / (1 + df["CDI_cum"].iloc[idx]) - 1
    bench_ret = (1 + df["Bench67_cum"].iloc[-1]) / (1 + df["Bench67_cum"].iloc[idx]) - 1 if ibov_ok else np.nan
    return port_ret, ibov_ret, cdi_ret, bench_ret

def _period_row(label, subset):
    if len(subset) < 2:
        return None
    r = {"Periodo": label}
    r["Carteira"] = (1 + subset["Portfolio_cum"].iloc[-1]) / (1 + subset["Portfolio_cum"].iloc[0]) - 1
    r["Ibovespa"] = ((1 + subset["Ibov_cum"].iloc[-1]) / (1 + subset["Ibov_cum"].iloc[0]) - 1) if ibov_ok else np.nan
    r["CDI"] = (1 + subset["CDI_cum"].iloc[-1]) / (1 + subset["CDI_cum"].iloc[0]) - 1
    r["67% Ibov + 33% CDI"] = ((1 + subset["Bench67_cum"].iloc[-1]) / (1 + subset["Bench67_cum"].iloc[0]) - 1) if ibov_ok else np.nan
    return r

windows = {"1M": 21, "3M": 63, "6M": 126, "1A": 252, "2A": 504, "3A": 756, "5A": 1260, "Desde Inicio": len(merged_full) - 1}
rows = []

mtd_mask = merged_full["Date"] >= merged_full["Date"].iloc[-1].replace(day=1)
r = _period_row("MTD", merged_full[mtd_mask])
if r:
    rows.append(r)

ytd_mask = merged_full["Date"] >= merged_full["Date"].iloc[-1].replace(month=1, day=1)
r = _period_row("YTD", merged_full[ytd_mask])
if r:
    rows.append(r)

for label, window in windows.items():
    result = period_return_from_end(merged_full, window)
    if result:
        rows.append({"Periodo": label, "Carteira": result[0], "Ibovespa": result[1], "CDI": result[2], "67% Ibov + 33% CDI": result[3]})

period_df = pd.DataFrame(rows)
fmt_cols = ["Carteira", "CDI"]
if ibov_ok:
    fmt_cols = ["Carteira", "Ibovespa", "CDI", "67% Ibov + 33% CDI"]
else:
    period_df = period_df[["Periodo", "Carteira", "CDI"]]
for c in fmt_cols:
    period_df[c] = period_df[c].apply(lambda x: f"{x:.2%}" if not np.isnan(x) else "\u2014")

st.markdown(style_table(period_df), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 7 — Rolling Volatility
# ══════════════════════════════════════════════════════════════════════════════

if n_days >= 252:
    section_title("Volatilidade Rolling 12 Meses")

    merged["Port_vol12"] = merged["Port_ret"].rolling(252).std() * np.sqrt(252)

    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["Port_vol12"] * 100, name="Carteira", line=dict(color=CHART_COLORS["carteira"], width=2)))
    if ibov_ok:
        merged["Ibov_vol12"] = merged["Ibov_ret"].rolling(252).std() * np.sqrt(252)
        merged["Bench67_vol12"] = merged["Bench67_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["Ibov_vol12"] * 100, name="Ibovespa", line=dict(color=CHART_COLORS["ibovespa"], width=1.5)))
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench67_vol12"] * 100, name="67% Ibov + 33% CDI", line=dict(color=CHART_COLORS["bench67"], width=1.5, dash="dash")))
    tag_chart_layout(fig7, height=350, yaxis_title="Volatilidade (%)")
    st.plotly_chart(fig7, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# % do CDI
# ══════════════════════════════════════════════════════════════════════════════

section_title("Carteira como % do CDI")

yearly_pct_cdi = yearly[["Year"]].copy()
yearly_pct_cdi["% do CDI"] = np.where(
    yearly["CDI_ret"] > 0,
    (yearly["Port_ret"] / yearly["CDI_ret"] * 100).round(1),
    np.nan,
)
yearly_pct_cdi.columns = ["Ano", "% do CDI"]
total_pct_cdi = port_total / cdi_total * 100 if cdi_total > 0 else 0

c1, c2 = st.columns([1, 2])
with c1:
    st.metric("% do CDI (acumulado)", f"{total_pct_cdi:.1f}%")
    pct_display = yearly_pct_cdi.copy()
    pct_display["Ano"] = pct_display["Ano"].astype(str)
    pct_display["% do CDI"] = pct_display["% do CDI"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "\u2014")
    st.markdown(style_table(pct_display), unsafe_allow_html=True)
with c2:
    fig8 = go.Figure()
    colors = [TAG_AZUL_ESCURO if v >= 100 else TAG_ROSA for v in yearly_pct_cdi["% do CDI"].fillna(0)]
    fig8.add_trace(go.Bar(x=yearly_pct_cdi["Ano"], y=yearly_pct_cdi["% do CDI"], marker_color=colors))
    fig8.add_hline(y=100, line_dash="dash", line_color=TAG_VERMELHO, annotation_text="100% CDI", annotation_font_color=TAG_VERMELHO)
    tag_chart_layout(fig8, height=400, yaxis_title="% do CDI", ticksuffix="%")
    st.plotly_chart(fig8, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# DISCLAIMER & FOOTER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""<div class="disclaimer">
<strong>Aviso:</strong> Este material tem carater meramente informativo e nao constitui oferta, solicitacao de oferta ou recomendacao
de investimento. Rentabilidade passada nao representa garantia de rentabilidade futura. O benchmark ficticio (67% Ibovespa + 33% CDI)
e utilizado apenas para fins comparativos, refletindo a alocacao aproximada da carteira.
</div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="tag-footer">
<p>Dados: Cota de rendimento do cliente &bull; Ibovespa (BCB / Yahoo Finance) &bull; CDI (Banco Central)<br>
Benchmark = 67% Ibovespa + 33% CDI &bull; <strong>TAG Investimentos</strong></p>
</div>""", unsafe_allow_html=True)
