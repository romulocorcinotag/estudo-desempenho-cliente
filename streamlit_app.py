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

    /* Captions */
    .stCaption, div[data-testid="stCaptionContainer"] {{
        text-align: left !important;
        color: {TAG_CINZA} !important;
        font-size: 0.78rem !important;
        margin: -0.3rem 0 0.8rem 0 !important;
        line-height: 1.6;
        font-style: italic;
    }}

    /* Sidebar image centered */
    section[data-testid="stSidebar"] div[data-testid="stImage"] {{
        display: flex;
        justify-content: center;
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
    # Suaviza patrimonio: interpola somente dados claramente errados
    pat = data["Patrimonio"].copy()
    # 1) Zeros/negativos sao erros de report -> marca como NaN
    pat[pat <= 0] = np.nan
    # 2) Detecta valores que caem >50% E voltam >50% em ate 5 dias (erro,
    #    nao resgate real — resgates reais nao voltam)
    vals = pat.values.copy()
    i = 0
    while i < len(vals):
        if np.isnan(vals[i]):
            i += 1
            continue
        # Encontra proximo valor valido anterior
        if i == 0:
            i += 1
            continue
        prev = vals[i - 1] if not np.isnan(vals[i - 1]) else None
        if prev is None:
            i += 1
            continue
        change = vals[i] / prev - 1
        # Queda brusca >50%? Verifica se e temporaria (volta em ate 5 dias)
        if change < -0.50:
            # Procura recuperacao nos proximos 5 dias
            recovered = False
            for j in range(i + 1, min(i + 6, len(vals))):
                if not np.isnan(vals[j]) and vals[j] > 0:
                    if vals[j] / prev > 0.70:  # Voltou a pelo menos 70% do anterior
                        # Marca todos de i ate j-1 como NaN (dados errados)
                        for k in range(i, j):
                            vals[k] = np.nan
                        recovered = True
                        i = j
                        break
            if not recovered:
                i += 1
        else:
            i += 1
    pat = pd.Series(vals, index=pat.index)
    # 3) Interpola NaNs
    pat = pat.interpolate(method="linear").ffill().bfill()
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


def annualized_return(total_ret, cal_days):
    """Retorno anualizado usando dias corridos (calendario)."""
    if cal_days <= 0 or np.isnan(total_ret):
        return 0.0
    return (1 + total_ret) ** (365.25 / cal_days) - 1


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


def style_table(df, highlight_best=False):
    html = '<div style="overflow-x:auto;border-radius:12px;border:1px solid #E8E6DD;box-shadow:0 2px 8px rgba(99,13,36,0.05);margin:0.5rem auto 1.5rem auto;max-width:960px;">'
    html += '<table style="width:100%;border-collapse:collapse;font-family:Inter,Tahoma,sans-serif;font-size:0.85rem;">'
    html += '<thead><tr>'
    for col in df.columns:
        html += f'<th style="background:{TAG_VERMELHO};color:#F5F4F0;padding:0.75rem 1rem;text-align:center;font-weight:600;font-size:0.75rem;letter-spacing:0.05em;text-transform:uppercase;border:none;">{col}</th>'
    html += '</tr></thead><tbody>'
    for i, (_, row) in enumerate(df.iterrows()):
        bg = TAG_BRANCO if i % 2 == 0 else "#FAFAF8"
        # Find best value in this row (for highlight)
        best_col = -1
        if highlight_best and len(row) > 1:
            numeric_vals = []
            for j, val in enumerate(row):
                if j == 0:
                    numeric_vals.append(None)
                    continue
                try:
                    v = str(val).replace("%", "").replace(",", ".").replace("\u2014", "")
                    numeric_vals.append(float(v) if v.strip() else None)
                except (ValueError, AttributeError):
                    numeric_vals.append(None)
            valid = [(j, v) for j, v in enumerate(numeric_vals) if v is not None]
            if valid:
                best_col = max(valid, key=lambda x: x[1])[0]
        html += '<tr>'
        for j, val in enumerate(row):
            fw = "600" if j == 0 else "400"
            color = TAG_VERMELHO if j == 0 else TAG_AZUL_ESCURO
            cell_bg = bg
            if j == best_col and highlight_best:
                cell_bg = "#E8F5E9"
                fw = "700"
            html += f'<td style="background:{cell_bg};color:{color};padding:0.6rem 1rem;text-align:center;font-weight:{fw};border-bottom:1px solid #F0EEE8;">{val}</td>'
        html += '</tr>'
    html += '</tbody></table></div>'
    return html


def insight_box(text, icon=""):
    """Caixa de destaque para insights."""
    st.markdown(f"""<div style="background:linear-gradient(135deg,{TAG_AZUL_ESCURO}08,{TAG_VERMELHO}06);
    border:1px solid {TAG_AZUL_ESCURO}20;border-radius:12px;padding:1rem 1.5rem;margin:0.5rem 0 1.5rem 0;
    font-size:0.88rem;color:{TAG_AZUL_ESCURO};line-height:1.6;">
    {icon} {text}
    </div>""", unsafe_allow_html=True)


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
    st.sidebar.markdown('<div style="text-align:center;padding:1rem 0;">', unsafe_allow_html=True)
    st.sidebar.image(_logo_path, width=140)
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown(f'<div style="border-top:1px solid rgba(255,136,83,0.3);margin:0.5rem 0 1rem 0;"></div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<p style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:{TAG_LARANJA} !important;margin-bottom:0.3rem;font-weight:600;text-align:center;">Período de Análise</p>', unsafe_allow_html=True)

preset = st.sidebar.selectbox(
    "Período",
    ["Desde o Início", "YTD", "Último Ano", "Últimos 2 Anos", "Últimos 3 Anos", "Últimos 5 Anos", "Personalizado"],
    index=0,
    label_visibility="collapsed",
)

today_ref = full_end
if preset == "YTD":
    sel_start, sel_end = pd.Timestamp(today_ref.year, 1, 1), today_ref
elif preset == "Último Ano":
    sel_start, sel_end = today_ref - pd.DateOffset(years=1), today_ref
elif preset == "Últimos 2 Anos":
    sel_start, sel_end = today_ref - pd.DateOffset(years=2), today_ref
elif preset == "Últimos 3 Anos":
    sel_start, sel_end = today_ref - pd.DateOffset(years=3), today_ref
elif preset == "Últimos 5 Anos":
    sel_start, sel_end = today_ref - pd.DateOffset(years=5), today_ref
elif preset == "Personalizado":
    sel_start = pd.Timestamp(st.sidebar.date_input("Data Início", value=full_start.date(), min_value=full_start.date(), max_value=full_end.date()))
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
    st.error("Período selecionado não tem dados suficientes.")
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
    st.warning("Dados do Ibovespa indisponíveis. Exibindo apenas Carteira vs CDI.")


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

# ── Painel de Destaques ──
total_pct_cdi_quick = port_total / cdi_total * 100 if cdi_total > 0 else 0
excess_vs_ibov = (port_total - ibov_total) * 100 if ibov_ok and not np.isnan(ibov_total) else 0
excess_vs_cdi = (port_total - cdi_total) * 100

insights = []
insights.append(f"<b>Retorno acumulado da carteira: {fmt_pct(port_total)}</b> ({fmt_pct(port_ann)} a.a.) em ~{total_days / 365:.0f} anos")
if ibov_ok and excess_vs_ibov > 0:
    insights.append(f"Carteira superou o Ibovespa em <b>{excess_vs_ibov:+.1f} p.p.</b> acumulados")
if excess_vs_cdi > 0:
    insights.append(f"Carteira entregou <b>{total_pct_cdi_quick:.0f}% do CDI</b> no período")
insight_box(" &nbsp;|&nbsp; ".join(insights))

# ── Tabela Comparativa ──
section_title("Painel Comparativo")
st.caption("Melhor resultado de cada métrica destacado em verde.")

summary_data = {
    "": ["Retorno Acumulado", "Retorno Anual", "Volatilidade", "Max Drawdown", "Sharpe"],
    "Carteira": [fmt_pct(port_total), fmt_pct(port_ann), fmt_pct(port_vol), fmt_pct(port_dd.min()), fmt_f(port_sharpe)],
    "Ibovespa": [fmt_pct(ibov_total), fmt_pct(ibov_ann), fmt_pct(ibov_vol), fmt_pct(ibov_dd.min()) if ibov_ok else "\u2014", fmt_f(ibov_sharpe)],
    "CDI": [fmt_pct(cdi_total), fmt_pct(cdi_ann), "~0%", "~0%", "\u2014"],
    "67% Ibov + 33% CDI": [fmt_pct(bench67_total), fmt_pct(bench67_ann), fmt_pct(bench67_vol), fmt_pct(bench67_dd.min()) if ibov_ok else "\u2014", fmt_f(bench67_sharpe)],
}
summary_df = pd.DataFrame(summary_data)
st.markdown(style_table(summary_df, highlight_best=True), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 1 — Retorno Acumulado
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retorno Acumulado (%)")
st.caption("Evolução do retorno acumulado da carteira comparado aos benchmarks, com base na cota de rendimento (descontando aportes e resgates).")

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
st.caption("Queda percentual em relação ao pico histórico. Quanto menor (mais negativo), maior foi a perda temporária no período.")

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
st.caption("Retorno de cada ativo dentro de cada ano-calendário. Permite comparar o desempenho relativo ano a ano.")

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
st.markdown(style_table(yearly_display, highlight_best=True), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 4 — Rolling 12M
# ══════════════════════════════════════════════════════════════════════════════

rolling_windows = {"1 Ano": 252, "3 Anos": 756, "5 Anos": 1260}

for roll_label, roll_window in rolling_windows.items():
    if n_days >= roll_window:
        section_title(f"Retorno Rolling {roll_label}")
        st.caption(f"Cada ponto mostra o retorno nos últimos {roll_window} d.u. O retorno médio representa a experiência média do cotista que permaneceu investido por {roll_label.lower()}.")

        port_roll = rolling_return(1 + merged["Portfolio_cum"], roll_window)
        cdi_roll = rolling_return(1 + merged["CDI_cum"], roll_window)

        # Calcula retornos medios
        avg_port = port_roll.dropna().mean()
        avg_cdi = cdi_roll.dropna().mean()

        fig_roll = go.Figure()
        fig_roll.add_trace(go.Scatter(x=merged["Date"], y=port_roll * 100, name=f"Carteira (media: {avg_port:.1%})", line=dict(color=CHART_COLORS["carteira"], width=2)))
        # Linha media carteira
        fig_roll.add_hline(y=avg_port * 100, line_dash="dot", line_color=CHART_COLORS["carteira"], line_width=1,
                           annotation_text=f"Media Carteira: {avg_port:.1%}", annotation_font_color=CHART_COLORS["carteira"],
                           annotation_position="top left", annotation_font_size=10)

        if ibov_ok:
            ibov_roll = rolling_return(1 + merged["Ibov_cum"], roll_window)
            bench_roll = rolling_return(1 + merged["Bench67_cum"], roll_window)
            avg_ibov = ibov_roll.dropna().mean()
            avg_bench = bench_roll.dropna().mean()
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=ibov_roll * 100, name=f"Ibovespa (media: {avg_ibov:.1%})", line=dict(color=CHART_COLORS["ibovespa"], width=1.5)))
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=bench_roll * 100, name=f"67% Ibov + 33% CDI (media: {avg_bench:.1%})", line=dict(color=CHART_COLORS["bench67"], width=1.5, dash="dash")))

        avg_cdi_val = avg_cdi
        fig_roll.add_trace(go.Scatter(x=merged["Date"], y=cdi_roll * 100, name=f"CDI (media: {avg_cdi_val:.1%})", line=dict(color=CHART_COLORS["cdi"], width=1.5, dash="dot")))

        tag_chart_layout(fig_roll, height=430, yaxis_title=f"Retorno {roll_label} (%)")
        st.plotly_chart(fig_roll, use_container_width=True)

        # Tabela resumo dos retornos medios
        avg_data = {"": [f"Retorno médio {roll_label}"], "Carteira": [f"{avg_port:.2%}"], "CDI": [f"{avg_cdi_val:.2%}"]}
        if ibov_ok:
            avg_data["Ibovespa"] = [f"{avg_ibov:.2%}"]
            avg_data["67% Ibov + 33% CDI"] = [f"{avg_bench:.2%}"]
        avg_df = pd.DataFrame(avg_data)
        st.markdown(style_table(avg_df), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 5 — Excesso de Retorno
# ══════════════════════════════════════════════════════════════════════════════

section_title("Excesso de Retorno vs Benchmarks")
st.caption("Diferença acumulada entre o retorno da carteira e cada benchmark. Valores positivos indicam que a carteira superou o benchmark.")

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

section_title("Evolução do Patrimônio (R$)")
st.caption("Patrimônio total ao longo do tempo, incluindo efeito de aportes, resgates e valorização. Aportes e resgates significativos podem causar saltos no gráfico.")

fig6 = go.Figure()
fig6.add_trace(go.Scatter(x=merged["Date"], y=merged["Patrimonio"], name="Patrimonio", fill="tozeroy", line=dict(color=TAG_AZUL_ESCURO, width=2), fillcolor="rgba(0,42,110,0.08)"))
tag_chart_layout(fig6, height=350, yaxis_title="R$", ticksuffix="")
fig6.update_layout(yaxis_tickformat=",.0f", yaxis_tickprefix="R$ ")
st.plotly_chart(fig6, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABELA — Retornos por Periodo
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retornos por Período")
st.caption("Retorno da carteira e benchmarks em diferentes horizontes de tempo.")

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
    r = {"Período": label}
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
        rows.append({"Período": label, "Carteira": result[0], "Ibovespa": result[1], "CDI": result[2], "67% Ibov + 33% CDI": result[3]})

period_df = pd.DataFrame(rows)
fmt_cols = ["Carteira", "CDI"]
if ibov_ok:
    fmt_cols = ["Carteira", "Ibovespa", "CDI", "67% Ibov + 33% CDI"]
else:
    period_df = period_df[["Período", "Carteira", "CDI"]]
for c in fmt_cols:
    period_df[c] = period_df[c].apply(lambda x: f"{x:.2%}" if not np.isnan(x) else "\u2014")

st.markdown(style_table(period_df, highlight_best=True), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 7 — Rolling Volatility
# ══════════════════════════════════════════════════════════════════════════════

if n_days >= 252:
    section_title("Volatilidade Rolling 12 Meses")
    st.caption("Volatilidade anualizada calculada sobre os últimos 252 dias úteis. Mede a oscilação dos retornos — quanto maior, mais risco.")

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
st.caption("Percentual do CDI entregue pela carteira em cada ano. Acima de 100% significa que a carteira superou o CDI no período.")

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
<strong>Aviso:</strong> Este material tem caráter meramente informativo e não constitui oferta, solicitação de oferta ou recomendação
de investimento. Rentabilidade passada não representa garantia de rentabilidade futura. O benchmark fictício (67% Ibovespa + 33% CDI)
é utilizado apenas para fins comparativos, refletindo a alocação aproximada da carteira.
</div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="tag-footer">
<p>Dados: Cota de rendimento do cliente &bull; Ibovespa (BCB / Yahoo Finance) &bull; CDI (Banco Central)<br>
Benchmark = 67% Ibovespa + 33% CDI &bull; <strong>TAG Investimentos</strong></p>
</div>""", unsafe_allow_html=True)
