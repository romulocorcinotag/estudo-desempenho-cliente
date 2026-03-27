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
    "carteira":    "#002A6E",   # azul marinho
    "consolidada": "#0891B2",   # ciano/azul-piscina
    "ibovespa":    "#FF6600",   # laranja vivo
    "cdi":         "#7C3AED",   # violeta
    "bench67":     "#DC2626",   # vermelho
    "bench55":     "#E11D48",   # rosa escuro
    "fia":         "#16A34A",   # verde
    "bench67fia":  "#E8590C",   # laranja escuro
    "bench55fia":  "#059669",   # verde escuro
    "hybrid":      "#6D28D9",   # roxo escuro
    "cm":          "#D97706",   # amarelo/âmbar escuro
}

# All available benchmark keys (label -> internal key)
ALL_BENCHMARKS = {
    "Ibovespa":             "ibovespa",
    "CDI":                  "cdi",
    "67% Ibov + 33% CDI":   "bench67",
    "55% Ibov + 45% CDI":   "bench55",
    "Média FIA*":           "fia",
    "67% Média FIAs + 33% CDI*":   "bench67fia",
    "55% Média FIAs + 45% CDI*":   "bench55fia",
    "Carteira Modelo":              "cm",
}

# ── Carteira Modelo: assets, proxies, and default weights ────────────────────
# Proxy types: "ibov" (Ibovespa), "fia" (Média FIA), "cdi" (CDI)
CM_ASSETS = [
    {"key": "tag_pe",        "name": "TAG Private Equity",  "proxy": "cdi",  "pct": 4.18,  "estrategia": "ALT PRIVATE EQUITY"},
    {"key": "tag_ventures",  "name": "TAG Ventures",        "proxy": "cdi",  "pct": 2.78,  "estrategia": "ALT VENTURE CAPITAL"},
    {"key": "lc_iii",        "name": "LC III FIDC",         "proxy": "cdi",  "pct": 2.22,  "estrategia": "ALTERNATIVOS PRECATÓRIOS"},
    {"key": "ntnb",          "name": "NTN-B IPCA+6%",       "proxy": "imab", "pct": 9.48,  "estrategia": "RF TPF NTNB OU TESOURO INFLAÇÃO"},
    {"key": "bova11",        "name": "BOVA11",              "proxy": "ibov", "pct": 31.66, "estrategia": "RV ETFs INDEXADOS BOVESPA"},
    {"key": "regio",         "name": "Régio FIA",           "proxy": "fia",  "pct": 6.94,  "estrategia": "RV FUNDOS CLUB DEAL"},
    {"key": "algido",        "name": "Algido FIA",          "proxy": "fia",  "pct": 1.01,  "estrategia": "RV FUNDOS CLUB DEAL"},
    {"key": "tarpon",        "name": "Tarpon GT FIA",       "proxy": "fia",  "pct": 4.82,  "estrategia": "RV FUNDOS SMALL CAPS"},
    {"key": "kiron",         "name": "Kiron FIA",           "proxy": "fia",  "pct": 5.00,  "estrategia": "RV FUNDOS VALOR"},
    {"key": "real_investor", "name": "Real Investor FIA",   "proxy": "fia",  "pct": 10.00, "estrategia": "RV FUNDOS VALOR"},
    {"key": "atmos",         "name": "TB Atmos FIA",        "proxy": "fia",  "pct": 16.91, "estrategia": "RV FUNDOS VALOR"},
    {"key": "cdi_cash",      "name": "CDI (Caixa)",         "proxy": "cdi",  "pct": 5.00,  "estrategia": "CAIXA"},
]

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
        display: flex !important;
        justify-content: center !important;
        margin: 0 auto !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stImage"] img {{
        margin: 0 auto !important;
        display: block !important;
    }}

    /* Carteira Modelo expander — compact inputs */
    section[data-testid="stSidebar"] div[data-testid="stExpander"] {{
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,136,83,0.25);
        border-radius: 10px;
    }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] p {{
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        color: {TAG_LARANJA} !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] label {{
        font-size: 0.68rem !important;
        margin-bottom: 0 !important;
        color: rgba(245,244,240,0.8) !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] .stNumberInput {{
        margin-bottom: 0.2rem !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] input {{
        background: rgba(255,255,255,0.9) !important;
        color: {TAG_VERMELHO} !important;
        border: 1px solid rgba(255,136,83,0.3) !important;
        border-radius: 6px !important;
        font-size: 0.78rem !important;
        padding: 0.25rem 0.4rem !important;
        height: 2rem !important;
    }}
    section[data-testid="stSidebar"] div[data-testid="stExpander"] button[data-testid="stNumberInputStepUp"],
    section[data-testid="stSidebar"] div[data-testid="stExpander"] button[data-testid="stNumberInputStepDown"] {{
        height: 1rem !important;
        width: 1.5rem !important;
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
def load_ibov(start, end):
    # Primary: local CSV (pre-downloaded, always available)
    _ibov_csv = os.path.join(_DIR, "ibov_data.csv")
    if os.path.exists(_ibov_csv):
        close = pd.read_csv(_ibov_csv, parse_dates=["Date"])
        close["Date"] = pd.to_datetime(close["Date"]).dt.tz_localize(None)
        close = close[(close["Date"] >= start) & (close["Date"] <= end + timedelta(days=5))]
        close = close.dropna(subset=["Close"]).sort_values("Date").reset_index(drop=True)
        if len(close) > 10:
            return close
    # Fallback: yfinance
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
    return pd.DataFrame(columns=["Date", "Close"])


@st.cache_data(ttl=86400)
def load_cdi(start, end):
    chunks = []
    d = start
    while d <= end:
        d_end = min(d + timedelta(days=365), end)
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
    cdi.rename(columns={"data": "Date", "valor": "CDI_pct"}, inplace=True)
    cdi["Date"] = pd.to_datetime(cdi["Date"], format="%d/%m/%Y")
    cdi["CDI_pct"] = cdi["CDI_pct"].astype(float)
    cdi = cdi.sort_values("Date").drop_duplicates(subset="Date").reset_index(drop=True)
    return cdi


@st.cache_data(ttl=3600)
def load_fia_benchmark():
    """Carrega benchmark médio da indústria de FIA (dados pré-calculados)."""
    path = os.path.join(_DIR, "fia_benchmark.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Date", "ret_fia"])
    df = pd.read_csv(path, parse_dates=["Date"])
    return df.sort_values("Date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_imab5p():
    """Carrega IMA-B 5+ (proxy NTN-B longa) de CSV pré-baixado."""
    path = os.path.join(_DIR, "imab5p_data.csv")
    if not os.path.exists(path):
        return pd.DataFrame(columns=["Date", "ret_imab"])
    df = pd.read_csv(path, parse_dates=["Date"])
    df["ret_imab"] = pd.to_numeric(df["ret_imab"], errors="coerce")
    return df.dropna(subset=["ret_imab"]).sort_values("Date").reset_index(drop=True)


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


def build_merged(port_df, ibov_df, cdi_df, fia_df=None, imab_df=None):
    merged = port_df[["Date", "CotaRendimento", "Patrimonio"]].copy()
    if len(ibov_df) > 0:
        merged = merged.merge(ibov_df, on="Date", how="left")
    else:
        merged["Close"] = np.nan
    merged = merged.merge(cdi_df, on="Date", how="left")
    if fia_df is not None and len(fia_df) > 0:
        merged = merged.merge(fia_df, on="Date", how="left")
    else:
        merged["ret_fia"] = np.nan
    if imab_df is not None and len(imab_df) > 0:
        merged = merged.merge(imab_df[["Date", "ret_imab"]], on="Date", how="left")
    else:
        merged["ret_imab"] = np.nan
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
    # Composite benchmarks: Ibov + CDI
    merged["Bench67_daily_ret"] = 0.67 * merged["Ibov_daily_ret"] + 0.33 * merged["CDI_daily_ret"]
    merged["Bench67_factor"] = (1 + merged["Bench67_daily_ret"]).cumprod()
    merged["Bench67_cum"] = merged["Bench67_factor"] - 1

    merged["Bench55_daily_ret"] = 0.55 * merged["Ibov_daily_ret"] + 0.45 * merged["CDI_daily_ret"]
    merged["Bench55_factor"] = (1 + merged["Bench55_daily_ret"]).cumprod()
    merged["Bench55_cum"] = merged["Bench55_factor"] - 1

    # FIA benchmark: equal-weighted average of active FIA funds
    first_fia = merged["ret_fia"].first_valid_index()
    if first_fia is not None:
        merged["FIA_factor"] = np.nan
        merged.loc[first_fia:, "FIA_factor"] = (1 + merged.loc[first_fia:, "ret_fia"].fillna(0)).cumprod()
        ref = merged.loc[first_fia, "FIA_factor"]
        merged["FIA_cum"] = merged["FIA_factor"] / ref - 1
    else:
        merged["FIA_factor"] = np.nan
        merged["FIA_cum"] = np.nan

    # Composite benchmarks: FIA + CDI
    fia_daily = merged["ret_fia"].fillna(0)
    merged["Bench67FIA_daily_ret"] = 0.67 * fia_daily + 0.33 * merged["CDI_daily_ret"]
    merged["Bench67FIA_factor"] = (1 + merged["Bench67FIA_daily_ret"]).cumprod()
    merged["Bench67FIA_cum"] = merged["Bench67FIA_factor"] - 1

    merged["Bench55FIA_daily_ret"] = 0.55 * fia_daily + 0.45 * merged["CDI_daily_ret"]
    merged["Bench55FIA_factor"] = (1 + merged["Bench55FIA_daily_ret"]).cumprod()
    merged["Bench55FIA_cum"] = merged["Bench55FIA_factor"] - 1

    port_norm = 1 + merged["Portfolio_cum"]
    merged["Port_ret"] = port_norm.pct_change()
    merged["Ibov_ret"] = ibov_norm.pct_change()
    merged["CDI_ret"] = cdi_norm.pct_change()
    merged["Bench67_ret"] = merged["Bench67_factor"].pct_change()
    merged["Bench55_ret"] = merged["Bench55_factor"].pct_change()
    merged["FIA_ret"] = merged["ret_fia"]
    merged["Bench67FIA_ret"] = merged["Bench67FIA_factor"].pct_change()
    merged["Bench55FIA_ret"] = merged["Bench55FIA_factor"].pct_change()

    return merged


def fmt_pct(v):
    return f"{v:.2%}" if not np.isnan(v) else "\u2014"

def fmt_f(v):
    return f"{v:.2f}" if not np.isnan(v) else "\u2014"


# ── Load Data ────────────────────────────────────────────────────────────────

_CSV = os.path.join(_DIR, "portfolio_data.csv")
_XLS = r"C:\Users\romulo.corcino_tagin\Downloads\ReportHistoricoCota (3).xls"
DATA_PATH = _CSV if os.path.exists(_CSV) else _XLS

_CONSOL_CSV = os.path.join(_DIR, "consolidada_data.csv")
consol_available = os.path.exists(_CONSOL_CSV)

port_full = load_portfolio(DATA_PATH)
consol_full = load_portfolio(_CONSOL_CSV) if consol_available else None

# ── Carteira + Consolidada (hybrid) ──────────────────────────────────────────
# Uses Carteira data from its start until the day before Consolidada begins,
# then switches to Consolidada data from that point forward.
# CotaRendimento is re-chained so cumulative return is continuous.
hybrid_full = None
if consol_available and consol_full is not None and len(consol_full) > 0:
    _consol_start = consol_full["Date"].min()
    # Part 1: Carteira before Consolidada
    _part1 = port_full[port_full["Date"] < _consol_start].copy()
    # Part 2: Consolidada from its start
    _part2 = consol_full.copy()
    if len(_part1) > 0 and len(_part2) > 0:
        # Re-chain: last cota of part1 * (consol cota / consol first cota)
        _last_cota1 = _part1["CotaRendimento"].iloc[-1]
        _first_cota2 = _part2["CotaRendimento"].iloc[0]
        _part2["CotaRendimento"] = _last_cota1 * (_part2["CotaRendimento"] / _first_cota2)
        # For patrimonio, use part2 as-is (consolidada patrimonio)
        hybrid_full = pd.concat([_part1, _part2], ignore_index=True)
        hybrid_full = hybrid_full.sort_values("Date").reset_index(drop=True)

full_start = port_full["Date"].min()
full_end = port_full["Date"].max()

ibov_raw = load_ibov(full_start, full_end)
cdi_raw = load_cdi(full_start, full_end)
fia_raw = load_fia_benchmark()
imab_raw = load_imab5p()

ibov_ok = len(ibov_raw) > 0 and ibov_raw["Close"].notna().any()
fia_ok = len(fia_raw) > 0



# ── Sidebar ──────────────────────────────────────────────────────────────────

if os.path.exists(_logo_path):
    st.sidebar.image(_logo_path, use_container_width=False, width=200)

st.sidebar.markdown(f'<div style="border-top:1px solid rgba(255,136,83,0.3);margin:0.5rem 0 1rem 0;"></div>', unsafe_allow_html=True)

# ── Portfolio selector ──
if consol_available:
    st.sidebar.markdown(f'<p style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:{TAG_LARANJA} !important;margin-bottom:0.3rem;font-weight:600;text-align:center;">Carteira</p>', unsafe_allow_html=True)
    _view_options = ["Individual (834)", "Consolidada (840)", "Carteira + Consolidada", "Comparativo"]
    portfolio_view = st.sidebar.selectbox(
        "Carteira",
        _view_options,
        index=0,
        label_visibility="collapsed",
    )
    show_consol = portfolio_view in ("Consolidada (840)", "Comparativo")
    show_individual = portfolio_view in ("Individual (834)", "Comparativo")
    show_hybrid = portfolio_view == "Carteira + Consolidada"
    compare_mode = portfolio_view == "Comparativo"
else:
    portfolio_view = "Individual (834)"
    show_consol = False
    show_individual = True
    show_hybrid = False
    compare_mode = False

st.sidebar.markdown(f'<p style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:{TAG_LARANJA} !important;margin-bottom:0.3rem;font-weight:600;text-align:center;">Período de Análise</p>', unsafe_allow_html=True)

# Determine effective data range based on portfolio selection
if show_hybrid and hybrid_full is not None:
    _eff_start = hybrid_full["Date"].min()
    _eff_end = hybrid_full["Date"].max()
elif show_consol and not show_individual:
    _eff_start = consol_full["Date"].min()
    _eff_end = consol_full["Date"].max()
elif compare_mode:
    # In compare mode, use intersection of dates (consolidada starts later)
    _eff_start = consol_full["Date"].min()
    _eff_end = min(port_full["Date"].max(), consol_full["Date"].max())
else:
    _eff_start = full_start
    _eff_end = full_end

preset = st.sidebar.selectbox(
    "Período",
    ["Desde o Início", "YTD", "Último Ano", "Últimos 2 Anos", "Últimos 3 Anos", "Últimos 5 Anos", "Personalizado"],
    index=0,
    label_visibility="collapsed",
)

today_ref = _eff_end
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
    sel_start = pd.Timestamp(st.sidebar.date_input("Data Início", value=_eff_start.date(), min_value=_eff_start.date(), max_value=_eff_end.date()))
    sel_end = pd.Timestamp(st.sidebar.date_input("Data Fim", value=_eff_end.date(), min_value=_eff_start.date(), max_value=_eff_end.date()))
else:
    sel_start, sel_end = _eff_start, _eff_end

sel_start = max(sel_start, _eff_start)
sel_end = min(sel_end, _eff_end)

st.sidebar.markdown(f'<div style="border-top:1px solid rgba(255,136,83,0.3);margin:0.8rem 0 0.5rem 0;"></div>', unsafe_allow_html=True)
st.sidebar.markdown(f'<p style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;color:{TAG_LARANJA} !important;margin-bottom:0.3rem;font-weight:600;text-align:center;">Benchmarks</p>', unsafe_allow_html=True)

_bench_options = list(ALL_BENCHMARKS.keys())
_bench_defaults = ["Ibovespa", "CDI", "67% Ibov + 33% CDI", "Média FIA*", "Carteira Modelo"]
selected_benchmarks = st.sidebar.multiselect(
    "Benchmarks",
    options=_bench_options,
    default=_bench_defaults,
    label_visibility="collapsed",
)
# Convert to set of internal keys for quick lookup
_sel_bench = {ALL_BENCHMARKS[b] for b in selected_benchmarks}

# Convenience flags
show_ibov = "ibovespa" in _sel_bench and ibov_ok
show_cdi = "cdi" in _sel_bench
show_bench67 = "bench67" in _sel_bench and ibov_ok
show_bench55 = "bench55" in _sel_bench and ibov_ok
show_fia = "fia" in _sel_bench and fia_ok
show_bench67fia = "bench67fia" in _sel_bench and fia_ok
show_bench55fia = "bench55fia" in _sel_bench and fia_ok
show_cm = "cm" in _sel_bench

# ── Carteira Modelo weights editor ──
if show_cm:
    st.sidebar.markdown(f'<div style="border-top:1px solid rgba(255,136,83,0.3);margin:0.5rem 0;"></div>', unsafe_allow_html=True)
    with st.sidebar.expander("📊 Pesos Carteira Modelo", expanded=False):
        _cm_cols = st.columns(2)
        cm_weights = {}
        for i, asset in enumerate(CM_ASSETS):
            with _cm_cols[i % 2]:
                cm_weights[asset["key"]] = st.number_input(
                    asset["name"],
                    min_value=0.0, max_value=100.0,
                    value=asset["pct"],
                    step=0.5,
                    format="%.2f",
                    key=f"cm_{asset['key']}",
                    label_visibility="visible",
                )
        _cm_total = sum(cm_weights.values())
        if abs(_cm_total - 100.0) > 0.1:
            st.warning(f"⚠️ Soma: {_cm_total:.2f}% (deveria ser 100%)")
        else:
            st.success(f"✅ Total: {_cm_total:.2f}%")
else:
    cm_weights = {a["key"]: a["pct"] for a in CM_ASSETS}

st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="text-align:center;">
    <p style="font-size:0.65rem;color:rgba(245,244,240,0.5) !important;margin:0;">Dados atualizados até</p>
    <p style="font-size:0.85rem;color:{TAG_LARANJA} !important;font-weight:600;margin:0.2rem 0 0 0;">{_eff_end.strftime('%d/%m/%Y')}</p>
</div>
""", unsafe_allow_html=True)

# ── Filter portfolios ──
if show_hybrid and hybrid_full is not None:
    active_port = hybrid_full
    port_label = "Carteira + Consolidada"
elif show_consol and not show_individual:
    # Consolidada only
    active_port = consol_full
    port_label = "Consolidada"
elif compare_mode:
    active_port = port_full
    port_label = "Individual"
else:
    active_port = port_full
    port_label = "Carteira"

port_filtered = active_port[(active_port["Date"] >= sel_start) & (active_port["Date"] <= sel_end)].reset_index(drop=True)
if len(port_filtered) < 2:
    st.error("Período selecionado não tem dados suficientes.")
    st.stop()

if compare_mode:
    consol_filtered = consol_full[(consol_full["Date"] >= sel_start) & (consol_full["Date"] <= sel_end)].reset_index(drop=True)
    if len(consol_filtered) < 2:
        st.error("Período selecionado não tem dados suficientes para a carteira consolidada.")
        st.stop()
    consol_merged = build_merged(consol_filtered, ibov_raw, cdi_raw, fia_raw, imab_raw)

merged = build_merged(port_filtered, ibov_raw, cdi_raw, fia_raw, imab_raw)

# ── Carteira Modelo: compute composite returns ──
if show_cm:
    _proxy_map = {"ibov": "Ibov_daily_ret", "fia": "ret_fia", "cdi": "CDI_daily_ret", "imab": "ret_imab"}
    _cm_daily = pd.Series(0.0, index=merged.index)
    for asset in CM_ASSETS:
        w = cm_weights[asset["key"]] / 100.0
        if w > 0:
            proxy_col = _proxy_map[asset["proxy"]]
            _cm_daily += w * merged[proxy_col].fillna(0)
    merged["CM_factor"] = (1 + _cm_daily).cumprod()
    merged["CM_cum"] = merged["CM_factor"] - 1
    merged["CM_ret"] = merged["CM_factor"].pct_change()

start_date = merged["Date"].iloc[0]
end_date = merged["Date"].iloc[-1]
n_days = len(merged) - 1
total_days = (end_date - start_date).days


# ══════════════════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════════════════

_view_label = {"Individual (834)": "Carteira Individual (834)", "Consolidada (840)": "Carteira Consolidada (840)", "Carteira + Consolidada": "Carteira + Consolidada (834 → 840)", "Comparativo": "Comparativo Individual vs Consolidada"}.get(portfolio_view, "Carteira")
st.markdown(f"""<div class="tag-header">
<h1>Estudo de Desempenho</h1>
<div class="subtitle">{_view_label} &nbsp;&bull;&nbsp; {start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')} &nbsp;&bull;&nbsp; {total_days:,} dias corridos &nbsp;&bull;&nbsp; {n_days:,} dias uteis &nbsp;&bull;&nbsp; ~{total_days / 365:.1f} anos</div>
<div class="divider"></div>
</div>""", unsafe_allow_html=True)

if show_hybrid and hybrid_full is not None:
    _consol_start_str = consol_full["Date"].min().strftime('%d/%m/%Y')
    st.info(f"📌 **Carteira + Consolidada**: utiliza os dados da Carteira Individual (834) até {_consol_start_str}, e a partir dessa data utiliza a Carteira Consolidada (840). O retorno acumulado é encadeado de forma contínua.")

if not ibov_ok:
    st.warning("Dados do Ibovespa indisponíveis. Exibindo apenas Carteira vs CDI.")


# ══════════════════════════════════════════════════════════════════════════════
# KPIs — RESUMO
# ══════════════════════════════════════════════════════════════════════════════

# ── Compute all benchmark stats (always compute, display controlled by flags) ──
port_total = merged["Portfolio_cum"].iloc[-1]
consol_total = consol_merged["Portfolio_cum"].iloc[-1] if compare_mode else np.nan
ibov_total = merged["Ibov_cum"].iloc[-1] if ibov_ok else np.nan
cdi_total = merged["CDI_cum"].iloc[-1]
bench67_total = merged["Bench67_cum"].iloc[-1] if ibov_ok else np.nan
bench55_total = merged["Bench55_cum"].iloc[-1] if ibov_ok else np.nan
fia_total = merged["FIA_cum"].dropna().iloc[-1] if fia_ok and merged["FIA_cum"].notna().any() else np.nan
fia_days = int((merged.loc[merged["FIA_cum"].notna(), "Date"].iloc[-1] - merged.loc[merged["FIA_cum"].notna(), "Date"].iloc[0]).days) if not np.isnan(fia_total) else 0
bench67fia_total = merged["Bench67FIA_cum"].iloc[-1] if fia_ok else np.nan
bench55fia_total = merged["Bench55FIA_cum"].iloc[-1] if fia_ok else np.nan

port_ann = annualized_return(port_total, total_days)
consol_ann = annualized_return(consol_total, total_days) if compare_mode else np.nan
ibov_ann = annualized_return(ibov_total, total_days) if ibov_ok else np.nan
cdi_ann = annualized_return(cdi_total, total_days)
bench67_ann = annualized_return(bench67_total, total_days) if ibov_ok else np.nan
bench55_ann = annualized_return(bench55_total, total_days) if ibov_ok else np.nan
fia_ann = annualized_return(fia_total, fia_days) if not np.isnan(fia_total) and fia_days > 0 else np.nan
bench67fia_ann = annualized_return(bench67fia_total, total_days) if fia_ok else np.nan
bench55fia_ann = annualized_return(bench55fia_total, total_days) if fia_ok else np.nan

port_vol = annualized_vol(merged["Port_ret"].dropna())
consol_vol = annualized_vol(consol_merged["Port_ret"].dropna()) if compare_mode else np.nan
ibov_vol = annualized_vol(merged["Ibov_ret"].dropna()) if ibov_ok else np.nan
bench67_vol = annualized_vol(merged["Bench67_ret"].dropna()) if ibov_ok else np.nan
bench55_vol = annualized_vol(merged["Bench55_ret"].dropna()) if ibov_ok else np.nan
fia_vol = annualized_vol(merged["FIA_ret"].dropna()) if fia_ok else np.nan
bench67fia_vol = annualized_vol(merged["Bench67FIA_ret"].dropna()) if fia_ok else np.nan
bench55fia_vol = annualized_vol(merged["Bench55FIA_ret"].dropna()) if fia_ok else np.nan

cdi_daily_avg = merged["CDI_ret"].dropna().mean()

def _sharpe(ret_col):
    s = ret_col.dropna()
    std = s.std()
    return (s.mean() - cdi_daily_avg) / std * np.sqrt(252) if std > 0 else np.nan

port_sharpe = _sharpe(merged["Port_ret"])
consol_sharpe = _sharpe(consol_merged["Port_ret"]) if compare_mode else np.nan
ibov_sharpe = _sharpe(merged["Ibov_ret"]) if ibov_ok else np.nan
bench67_sharpe = _sharpe(merged["Bench67_ret"]) if ibov_ok else np.nan
bench55_sharpe = _sharpe(merged["Bench55_ret"]) if ibov_ok else np.nan
fia_sharpe = _sharpe(merged["FIA_ret"]) if fia_ok else np.nan
bench67fia_sharpe = _sharpe(merged["Bench67FIA_ret"]) if fia_ok else np.nan
bench55fia_sharpe = _sharpe(merged["Bench55FIA_ret"]) if fia_ok else np.nan

cm_total = merged["CM_cum"].iloc[-1] if show_cm else np.nan
cm_ann = annualized_return(cm_total, total_days) if show_cm else np.nan
cm_vol = annualized_vol(merged["CM_ret"].dropna()) if show_cm else np.nan
cm_sharpe = _sharpe(merged["CM_ret"]) if show_cm else np.nan

port_dd = calc_drawdown(1 + merged["Portfolio_cum"])
consol_dd = calc_drawdown(1 + consol_merged["Portfolio_cum"]) if compare_mode else pd.Series(np.nan, index=merged.index)
ibov_dd = calc_drawdown(1 + merged["Ibov_cum"]) if ibov_ok else pd.Series(0, index=merged.index)
bench67_dd = calc_drawdown(1 + merged["Bench67_cum"]) if ibov_ok else pd.Series(0, index=merged.index)
bench55_dd = calc_drawdown(1 + merged["Bench55_cum"]) if ibov_ok else pd.Series(0, index=merged.index)
fia_dd = calc_drawdown(1 + merged["FIA_cum"].ffill()) if fia_ok and merged["FIA_cum"].notna().any() else pd.Series(np.nan, index=merged.index)
bench67fia_dd = calc_drawdown(1 + merged["Bench67FIA_cum"]) if fia_ok else pd.Series(np.nan, index=merged.index)
bench55fia_dd = calc_drawdown(1 + merged["Bench55FIA_cum"]) if fia_ok else pd.Series(np.nan, index=merged.index)
cm_dd = calc_drawdown(1 + merged["CM_cum"]) if show_cm else pd.Series(np.nan, index=merged.index)

# ── Painel de Destaques ──
total_pct_cdi_quick = port_total / cdi_total * 100 if cdi_total > 0 else 0
excess_vs_ibov = (port_total - ibov_total) * 100 if ibov_ok and not np.isnan(ibov_total) else 0
excess_vs_cdi = (port_total - cdi_total) * 100

insights = []
insights.append(f"<b>Retorno acumulado {port_label}: {fmt_pct(port_total)}</b> ({fmt_pct(port_ann)} a.a.) em ~{total_days / 365:.0f} anos")
if compare_mode:
    insights.append(f"<b>Consolidada: {fmt_pct(consol_total)}</b> ({fmt_pct(consol_ann)} a.a.)")
if ibov_ok and excess_vs_ibov > 0:
    insights.append(f"{port_label} superou o Ibovespa em <b>{excess_vs_ibov:+.1f} p.p.</b> acumulados")
if excess_vs_cdi > 0:
    insights.append(f"{port_label} entregou <b>{total_pct_cdi_quick:.0f}% do CDI</b> no período")
insight_box(" &nbsp;|&nbsp; ".join(insights))

# ── Tabela Comparativa ──
section_title("Painel Comparativo")
st.caption("Melhor resultado de cada métrica destacado em verde.")

summary_data = {
    "": ["Retorno Acumulado", "Retorno Anual", "Volatilidade", "Max Drawdown", "Sharpe"],
    port_label: [fmt_pct(port_total), fmt_pct(port_ann), fmt_pct(port_vol), fmt_pct(port_dd.min()), fmt_f(port_sharpe)],
}
if compare_mode:
    _cdd = consol_dd.dropna().min() if consol_dd.notna().any() else np.nan
    summary_data["Consolidada"] = [fmt_pct(consol_total), fmt_pct(consol_ann), fmt_pct(consol_vol), fmt_pct(_cdd), fmt_f(consol_sharpe)]
if show_ibov:
    summary_data["Ibovespa"] = [fmt_pct(ibov_total), fmt_pct(ibov_ann), fmt_pct(ibov_vol), fmt_pct(ibov_dd.min()), fmt_f(ibov_sharpe)]
if show_cdi:
    summary_data["CDI"] = [fmt_pct(cdi_total), fmt_pct(cdi_ann), "~0%", "~0%", "\u2014"]
if show_bench67:
    summary_data["67% Ibov + 33% CDI"] = [fmt_pct(bench67_total), fmt_pct(bench67_ann), fmt_pct(bench67_vol), fmt_pct(bench67_dd.min()), fmt_f(bench67_sharpe)]
if show_bench55:
    summary_data["55% Ibov + 45% CDI"] = [fmt_pct(bench55_total), fmt_pct(bench55_ann), fmt_pct(bench55_vol), fmt_pct(bench55_dd.min()), fmt_f(bench55_sharpe)]
if show_fia:
    _fdd = fia_dd.dropna().min() if fia_dd.notna().any() else np.nan
    summary_data["Média FIA*"] = [fmt_pct(fia_total), fmt_pct(fia_ann), fmt_pct(fia_vol), fmt_pct(_fdd), fmt_f(fia_sharpe)]
if show_bench67fia:
    _b67dd = bench67fia_dd.dropna().min() if bench67fia_dd.notna().any() else np.nan
    summary_data["67% Média FIAs + 33% CDI*"] = [fmt_pct(bench67fia_total), fmt_pct(bench67fia_ann), fmt_pct(bench67fia_vol), fmt_pct(_b67dd), fmt_f(bench67fia_sharpe)]
if show_bench55fia:
    _b55dd = bench55fia_dd.dropna().min() if bench55fia_dd.notna().any() else np.nan
    summary_data["55% Média FIAs + 45% CDI*"] = [fmt_pct(bench55fia_total), fmt_pct(bench55fia_ann), fmt_pct(bench55fia_vol), fmt_pct(_b55dd), fmt_f(bench55fia_sharpe)]
if show_cm:
    _cmdd = cm_dd.dropna().min() if cm_dd.notna().any() else np.nan
    summary_data["Carteira Modelo"] = [fmt_pct(cm_total), fmt_pct(cm_ann), fmt_pct(cm_vol), fmt_pct(_cmdd), fmt_f(cm_sharpe)]
summary_df = pd.DataFrame(summary_data)
st.markdown(style_table(summary_df, highlight_best=True), unsafe_allow_html=True)
if fia_ok:
    st.caption("* Média FIA: média ponderada igualmente de 245 fundos de ações (categorias: Livre, Valor/Crescimento e Small Caps) que existiam no início da carteira, incluindo os que fecharam ao longo do tempo — sem viés de sobrevivência. Fonte: CVM/Inf. Diário.")


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 1 — Retorno Acumulado
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retorno Acumulado (%)")
st.caption("Evolução do retorno acumulado da carteira comparado aos benchmarks, com base na cota de rendimento (descontando aportes e resgates).")

_port_color = CHART_COLORS["hybrid"] if show_hybrid else CHART_COLORS["carteira"]

fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Portfolio_cum"] * 100, name=port_label, line=dict(width=2.5, color=_port_color)))
if compare_mode:
    fig1.add_trace(go.Scatter(x=consol_merged["Date"], y=consol_merged["Portfolio_cum"] * 100, name="Consolidada", line=dict(width=2.5, color=CHART_COLORS["consolidada"])))
if show_ibov:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Ibov_cum"] * 100, name="Ibovespa", line=dict(width=1.8, color=CHART_COLORS["ibovespa"])))
if show_cdi:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["CDI_cum"] * 100, name="CDI", line=dict(width=1.8, color=CHART_COLORS["cdi"], dash="dot")))
if show_bench67:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench67_cum"] * 100, name="67% Ibov + 33% CDI", line=dict(width=1.8, color=CHART_COLORS["bench67"], dash="dash")))
if show_bench55:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench55_cum"] * 100, name="55% Ibov + 45% CDI", line=dict(width=1.8, color=CHART_COLORS["bench55"], dash="dash")))
if show_fia and merged["FIA_cum"].notna().any():
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["FIA_cum"] * 100, name="Média FIA*", line=dict(width=1.8, color=CHART_COLORS["fia"], dash="longdash")))
if show_bench67fia:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench67FIA_cum"] * 100, name="67% Média FIAs + 33% CDI*", line=dict(width=1.8, color=CHART_COLORS["bench67fia"], dash="dashdot")))
if show_bench55fia:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench55FIA_cum"] * 100, name="55% Média FIAs + 45% CDI*", line=dict(width=1.8, color=CHART_COLORS["bench55fia"], dash="dashdot")))
if show_cm:
    fig1.add_trace(go.Scatter(x=merged["Date"], y=merged["CM_cum"] * 100, name="Carteira Modelo", line=dict(width=2.5, color=CHART_COLORS["cm"])))
tag_chart_layout(fig1, height=500, yaxis_title="Retorno Acumulado (%)")
st.plotly_chart(fig1, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 2 — Drawdown
# ══════════════════════════════════════════════════════════════════════════════

section_title("Drawdown")
st.caption("Queda percentual em relação ao pico histórico. Quanto menor (mais negativo), maior foi a perda temporária no período.")

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=merged["Date"], y=port_dd * 100, name=port_label, fill="tozeroy", line=dict(color=_port_color), fillcolor="rgba(0,42,110,0.10)"))
if compare_mode:
    fig2.add_trace(go.Scatter(x=consol_merged["Date"], y=consol_dd * 100, name="Consolidada", line=dict(color=CHART_COLORS["consolidada"], width=2)))
if show_ibov:
    fig2.add_trace(go.Scatter(x=merged["Date"], y=ibov_dd * 100, name="Ibovespa", line=dict(color=CHART_COLORS["ibovespa"], width=1)))
if show_bench67:
    fig2.add_trace(go.Scatter(x=merged["Date"], y=bench67_dd * 100, name="67% Ibov + 33% CDI", line=dict(color=CHART_COLORS["bench67"], width=1, dash="dash")))
if show_bench55:
    fig2.add_trace(go.Scatter(x=merged["Date"], y=bench55_dd * 100, name="55% Ibov + 45% CDI", line=dict(color=CHART_COLORS["bench55"], width=1, dash="dash")))
if show_fia and fia_dd.notna().any():
    fig2.add_trace(go.Scatter(x=merged["Date"], y=fia_dd * 100, name="Média FIA*", line=dict(color=CHART_COLORS["fia"], width=1, dash="longdash")))
if show_bench67fia and bench67fia_dd.notna().any():
    fig2.add_trace(go.Scatter(x=merged["Date"], y=bench67fia_dd * 100, name="67% Média FIAs + 33% CDI*", line=dict(color=CHART_COLORS["bench67fia"], width=1, dash="dashdot")))
if show_bench55fia and bench55fia_dd.notna().any():
    fig2.add_trace(go.Scatter(x=merged["Date"], y=bench55fia_dd * 100, name="55% Média FIAs + 45% CDI*", line=dict(color=CHART_COLORS["bench55fia"], width=1, dash="dashdot")))
if show_cm and cm_dd.notna().any():
    fig2.add_trace(go.Scatter(x=merged["Date"], y=cm_dd * 100, name="Carteira Modelo", line=dict(color=CHART_COLORS["cm"], width=2)))
tag_chart_layout(fig2, height=350, yaxis_title="Drawdown (%)")
st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 3 — Retornos Anuais
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retornos Anuais")
st.caption("Retorno de cada ativo dentro de cada ano-calendário. Permite comparar o desempenho relativo ano a ano.")

merged["Year"] = merged["Date"].dt.year

def _fia_year_ret(g):
    vals = g.dropna()
    if len(vals) < 2:
        return np.nan
    return (1 + vals.iloc[-1]) / (1 + vals.iloc[0]) - 1

yearly = merged.groupby("Year").agg(
    Port_start=("Portfolio_cum", lambda x: 1 + x.iloc[0]),
    Port_end=("Portfolio_cum", lambda x: 1 + x.iloc[-1]),
    Ibov_start=("Ibov_cum", lambda x: 1 + x.iloc[0]),
    Ibov_end=("Ibov_cum", lambda x: 1 + x.iloc[-1]),
    CDI_start=("CDI_cum", lambda x: 1 + x.iloc[0]),
    CDI_end=("CDI_cum", lambda x: 1 + x.iloc[-1]),
    Bench67_start=("Bench67_cum", lambda x: 1 + x.iloc[0]),
    Bench67_end=("Bench67_cum", lambda x: 1 + x.iloc[-1]),
    Bench55_start=("Bench55_cum", lambda x: 1 + x.iloc[0]),
    Bench55_end=("Bench55_cum", lambda x: 1 + x.iloc[-1]),
    B67FIA_start=("Bench67FIA_cum", lambda x: 1 + x.iloc[0]),
    B67FIA_end=("Bench67FIA_cum",  lambda x: 1 + x.iloc[-1]),
    B55FIA_start=("Bench55FIA_cum", lambda x: 1 + x.iloc[0]),
    B55FIA_end=("Bench55FIA_cum",  lambda x: 1 + x.iloc[-1]),
    **({} if not show_cm else {"CM_start": ("CM_cum", lambda x: 1 + x.iloc[0]), "CM_end": ("CM_cum", lambda x: 1 + x.iloc[-1])}),
).reset_index()

_yr_prefixes = ["Port", "Ibov", "CDI", "Bench67", "Bench55", "B67FIA", "B55FIA"]
if show_cm:
    _yr_prefixes.append("CM")
for prefix in _yr_prefixes:
    yearly[f"{prefix}_ret"] = yearly[f"{prefix}_end"] / yearly[f"{prefix}_start"] - 1

# FIA yearly returns — only for years where we have data
yearly["FIA_ret"] = merged.groupby("Year")["FIA_cum"].apply(_fia_year_ret).values

# Consolidada yearly returns (if compare mode)
if compare_mode:
    consol_merged["Year"] = consol_merged["Date"].dt.year
    consol_yearly = consol_merged.groupby("Year").agg(
        Consol_start=("Portfolio_cum", lambda x: 1 + x.iloc[0]),
        Consol_end=("Portfolio_cum", lambda x: 1 + x.iloc[-1]),
    ).reset_index()
    consol_yearly["Consol_ret"] = consol_yearly["Consol_end"] / consol_yearly["Consol_start"] - 1
    yearly = yearly.merge(consol_yearly[["Year", "Consol_ret"]], on="Year", how="left")

# Build bars and table columns dynamically based on selected benchmarks
fig3 = go.Figure()
fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Port_ret"] * 100, name=port_label, marker_color=_port_color))

# Dynamic columns for table
_yr_cols = [("Year", "Ano"), ("Port_ret", port_label)]
if compare_mode and "Consol_ret" in yearly.columns:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Consol_ret"] * 100, name="Consolidada", marker_color=CHART_COLORS["consolidada"]))
    _yr_cols.append(("Consol_ret", "Consolidada"))
if show_ibov:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Ibov_ret"] * 100, name="Ibovespa", marker_color=CHART_COLORS["ibovespa"]))
    _yr_cols.append(("Ibov_ret", "Ibovespa"))
if show_cdi:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["CDI_ret"] * 100, name="CDI", marker_color=CHART_COLORS["cdi"]))
    _yr_cols.append(("CDI_ret", "CDI"))
if show_bench67:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Bench67_ret"] * 100, name="67% Ibov + 33% CDI", marker_color=CHART_COLORS["bench67"]))
    _yr_cols.append(("Bench67_ret", "67% Ibov + 33% CDI"))
if show_bench55:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["Bench55_ret"] * 100, name="55% Ibov + 45% CDI", marker_color=CHART_COLORS["bench55"]))
    _yr_cols.append(("Bench55_ret", "55% Ibov + 45% CDI"))
if show_fia:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["FIA_ret"] * 100, name="Média FIA*", marker_color=CHART_COLORS["fia"]))
    _yr_cols.append(("FIA_ret", "Média FIA*"))
if show_bench67fia:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["B67FIA_ret"] * 100, name="67% Média FIAs + 33% CDI*", marker_color=CHART_COLORS["bench67fia"]))
    _yr_cols.append(("B67FIA_ret", "67% Média FIAs + 33% CDI*"))
if show_bench55fia:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["B55FIA_ret"] * 100, name="55% Média FIAs + 45% CDI*", marker_color=CHART_COLORS["bench55fia"]))
    _yr_cols.append(("B55FIA_ret", "55% Média FIAs + 45% CDI*"))
if show_cm:
    fig3.add_trace(go.Bar(x=yearly["Year"], y=yearly["CM_ret"] * 100, name="Carteira Modelo", marker_color=CHART_COLORS["cm"]))
    _yr_cols.append(("CM_ret", "Carteira Modelo"))

tag_chart_layout(fig3, height=450, yaxis_title="Retorno (%)")
fig3.update_layout(barmode="group")
st.plotly_chart(fig3, use_container_width=True)

cols_display = [c[0] for c in _yr_cols]
col_names = [c[1] for c in _yr_cols]
yearly_display = yearly[cols_display].copy()
yearly_display.columns = col_names
for c in col_names[1:]:
    yearly_display[c] = yearly_display[c].apply(lambda x: f"{x:.2%}" if pd.notna(x) and not np.isnan(x) else "\u2014")
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
        fig_roll.add_trace(go.Scatter(x=merged["Date"], y=port_roll * 100, name=f"{port_label} (media: {avg_port:.1%})", line=dict(color=_port_color, width=2)))
        # Linha media carteira
        fig_roll.add_hline(y=avg_port * 100, line_dash="dot", line_color=_port_color, line_width=1,
                           annotation_text=f"Media {port_label}: {avg_port:.1%}", annotation_font_color=_port_color,
                           annotation_position="top left", annotation_font_size=10)

        if compare_mode and len(consol_merged) > roll_window:
            consol_roll = rolling_return(1 + consol_merged["Portfolio_cum"], roll_window)
            avg_consol = consol_roll.dropna().mean()
            fig_roll.add_trace(go.Scatter(x=consol_merged["Date"], y=consol_roll * 100, name=f"Consolidada (media: {avg_consol:.1%})", line=dict(color=CHART_COLORS["consolidada"], width=2)))

        if show_ibov:
            ibov_roll = rolling_return(1 + merged["Ibov_cum"], roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=ibov_roll * 100, name=f"Ibovespa (media: {ibov_roll.dropna().mean():.1%})", line=dict(color=CHART_COLORS["ibovespa"], width=1.5)))
        if show_cdi:
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=cdi_roll * 100, name=f"CDI (media: {avg_cdi:.1%})", line=dict(color=CHART_COLORS["cdi"], width=1.5, dash="dot")))
        if show_bench67:
            bench67_roll = rolling_return(1 + merged["Bench67_cum"], roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=bench67_roll * 100, name=f"67% Ibov + 33% CDI (media: {bench67_roll.dropna().mean():.1%})", line=dict(color=CHART_COLORS["bench67"], width=1.5, dash="dash")))
        if show_bench55:
            bench55_roll = rolling_return(1 + merged["Bench55_cum"], roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=bench55_roll * 100, name=f"55% Ibov + 45% CDI (media: {bench55_roll.dropna().mean():.1%})", line=dict(color=CHART_COLORS["bench55"], width=1.5, dash="dash")))
        if show_fia and merged["FIA_cum"].notna().sum() > roll_window:
            fia_roll = rolling_return(1 + merged["FIA_cum"].ffill(), roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=fia_roll * 100, name=f"Média FIA* (media: {fia_roll.dropna().mean():.1%})", line=dict(color=CHART_COLORS["fia"], width=1.5, dash="longdash")))
        if show_bench67fia and merged["FIA_cum"].notna().sum() > roll_window:
            b67fia_roll = rolling_return(1 + merged["Bench67FIA_cum"], roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=b67fia_roll * 100, name=f"67% Média FIAs + 33% CDI* (media: {b67fia_roll.dropna().mean():.1%})", line=dict(color=CHART_COLORS["bench67fia"], width=1.5, dash="dashdot")))
        if show_bench55fia and merged["FIA_cum"].notna().sum() > roll_window:
            b55fia_roll = rolling_return(1 + merged["Bench55FIA_cum"], roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=b55fia_roll * 100, name=f"55% Média FIAs + 45% CDI* (media: {b55fia_roll.dropna().mean():.1%})", line=dict(color=CHART_COLORS["bench55fia"], width=1.5, dash="dashdot")))
        if show_cm:
            cm_roll = rolling_return(1 + merged["CM_cum"], roll_window)
            fig_roll.add_trace(go.Scatter(x=merged["Date"], y=cm_roll * 100, name=f"Carteira Modelo (media: {cm_roll.dropna().mean():.1%})", line=dict(color=CHART_COLORS["cm"], width=2)))

        tag_chart_layout(fig_roll, height=430, yaxis_title=f"Retorno {roll_label} (%)")
        st.plotly_chart(fig_roll, use_container_width=True)

        # Tabela resumo dos retornos medios
        avg_data = {"": [f"Retorno médio {roll_label}"], port_label: [f"{avg_port:.2%}"]}
        if show_cdi:
            avg_data["CDI"] = [f"{avg_cdi:.2%}"]
        avg_df = pd.DataFrame(avg_data)
        st.markdown(style_table(avg_df), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 5 — Excesso de Retorno
# ══════════════════════════════════════════════════════════════════════════════

section_title("Excesso de Retorno vs Benchmarks")
st.caption("Diferença acumulada entre o retorno da carteira e cada benchmark. Valores positivos indicam que a carteira superou o benchmark.")

fig5 = go.Figure()
if compare_mode:
    # In compare mode, show individual vs consolidada excess (align by date)
    _exc = merged[["Date", "Portfolio_cum"]].merge(
        consol_merged[["Date", "Portfolio_cum"]].rename(columns={"Portfolio_cum": "Consol_cum"}),
        on="Date", how="inner",
    )
    fig5.add_trace(go.Scatter(x=_exc["Date"], y=(_exc["Portfolio_cum"] - _exc["Consol_cum"]) * 100, name=f"{port_label} vs Consolidada", line=dict(color=CHART_COLORS["consolidada"], width=2.5)))
if show_ibov:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["Ibov_cum"]) * 100, name=f"{port_label} vs Ibovespa", line=dict(color=CHART_COLORS["ibovespa"], width=1.8)))
if show_cdi:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["CDI_cum"]) * 100, name=f"{port_label} vs CDI", line=dict(color=CHART_COLORS["cdi"], width=1.8)))
if show_bench67:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["Bench67_cum"]) * 100, name=f"{port_label} vs 67% Ibov + 33% CDI", line=dict(color=CHART_COLORS["bench67"], width=1.8)))
if show_bench55:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["Bench55_cum"]) * 100, name=f"{port_label} vs 55% Ibov + 45% CDI", line=dict(color=CHART_COLORS["bench55"], width=1.8)))
if show_fia and merged["FIA_cum"].notna().any():
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["FIA_cum"]) * 100, name=f"{port_label} vs Média FIA*", line=dict(color=CHART_COLORS["fia"], width=1.8, dash="longdash")))
if show_bench67fia:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["Bench67FIA_cum"]) * 100, name=f"{port_label} vs 67% Média FIAs + 33% CDI*", line=dict(color=CHART_COLORS["bench67fia"], width=1.8, dash="dashdot")))
if show_bench55fia:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["Bench55FIA_cum"]) * 100, name=f"{port_label} vs 55% Média FIAs + 45% CDI*", line=dict(color=CHART_COLORS["bench55fia"], width=1.8, dash="dashdot")))
if show_cm:
    fig5.add_trace(go.Scatter(x=merged["Date"], y=(merged["Portfolio_cum"] - merged["CM_cum"]) * 100, name=f"{port_label} vs Carteira Modelo", line=dict(color=CHART_COLORS["cm"], width=2)))
fig5.add_hline(y=0, line_dash="dash", line_color=TAG_CINZA)
tag_chart_layout(fig5, height=400, yaxis_title="Excesso (p.p.)", ticksuffix=" p.p.")
st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 6 — Patrimonio
# ══════════════════════════════════════════════════════════════════════════════

section_title("Evolução do Patrimônio (R$)")
st.caption("Patrimônio total ao longo do tempo, incluindo efeito de aportes, resgates e valorização. Aportes e resgates significativos podem causar saltos no gráfico.")

fig6 = go.Figure()
fig6.add_trace(go.Scatter(x=merged["Date"], y=merged["Patrimonio"], name=f"Patrimonio {port_label}", fill="tozeroy", line=dict(color=TAG_AZUL_ESCURO, width=2), fillcolor="rgba(0,42,110,0.08)"))
if compare_mode:
    fig6.add_trace(go.Scatter(x=consol_merged["Date"], y=consol_merged["Patrimonio"], name="Patrimonio Consolidada", line=dict(color=CHART_COLORS["consolidada"], width=2)))
tag_chart_layout(fig6, height=350, yaxis_title="R$", ticksuffix="")
fig6.update_layout(yaxis_tickformat=",.0f", yaxis_tickprefix="R$ ")
st.plotly_chart(fig6, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TABELA — Retornos por Periodo
# ══════════════════════════════════════════════════════════════════════════════

section_title("Retornos por Período")
st.caption("Retorno da carteira e benchmarks em diferentes horizontes de tempo.")

merged_full = build_merged(port_full, ibov_raw, cdi_raw, fia_raw, imab_raw)

# Carteira Modelo on merged_full
if show_cm:
    _proxy_map_f = {"ibov": "Ibov_daily_ret", "fia": "ret_fia", "cdi": "CDI_daily_ret", "imab": "ret_imab"}
    _cm_daily_f = pd.Series(0.0, index=merged_full.index)
    for asset in CM_ASSETS:
        w = cm_weights[asset["key"]] / 100.0
        if w > 0:
            _cm_daily_f += w * merged_full[_proxy_map_f[asset["proxy"]]].fillna(0)
    merged_full["CM_factor"] = (1 + _cm_daily_f).cumprod()
    merged_full["CM_cum"] = merged_full["CM_factor"] - 1

def _fia_period_ret(subset):
    """Return FIA cumulative return for a subset, or NaN if no data."""
    vals = subset["FIA_cum"].dropna()
    if len(vals) < 2:
        return np.nan
    return (1 + vals.iloc[-1]) / (1 + vals.iloc[0]) - 1

def _cum_ret(s, i0, i1):
    return (1 + s.iloc[i1]) / (1 + s.iloc[i0]) - 1

def _period_row(label, subset):
    if len(subset) < 2:
        return None
    r = {"Período": label}
    r[port_label] = _cum_ret(subset["Portfolio_cum"], 0, -1)
    if show_ibov: r["Ibovespa"] = _cum_ret(subset["Ibov_cum"], 0, -1)
    if show_cdi: r["CDI"] = _cum_ret(subset["CDI_cum"], 0, -1)
    if show_bench67: r["67% Ibov + 33% CDI"] = _cum_ret(subset["Bench67_cum"], 0, -1)
    if show_bench55: r["55% Ibov + 45% CDI"] = _cum_ret(subset["Bench55_cum"], 0, -1)
    if show_fia: r["Média FIA*"] = _fia_period_ret(subset)
    if show_bench67fia: r["67% Média FIAs + 33% CDI*"] = _cum_ret(subset["Bench67FIA_cum"], 0, -1)
    if show_bench55fia: r["55% Média FIAs + 45% CDI*"] = _cum_ret(subset["Bench55FIA_cum"], 0, -1)
    if show_cm: r["Carteira Modelo"] = _cum_ret(subset["CM_cum"], 0, -1)
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
    if len(merged_full) >= window + 1:
        subset = merged_full.iloc[len(merged_full) - 1 - window:]
        r = _period_row(label, subset)
        if r:
            rows.append(r)

period_df = pd.DataFrame(rows)
fmt_cols = [c for c in period_df.columns if c != "Período"]
for c in fmt_cols:
    period_df[c] = period_df[c].apply(lambda x: f"{x:.2%}" if pd.notna(x) and not np.isnan(x) else "\u2014")

st.markdown(style_table(period_df, highlight_best=True), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# GRAFICO 7 — Rolling Volatility
# ══════════════════════════════════════════════════════════════════════════════

if n_days >= 252:
    section_title("Volatilidade Rolling 12 Meses")
    st.caption("Volatilidade anualizada calculada sobre os últimos 252 dias úteis. Mede a oscilação dos retornos — quanto maior, mais risco.")

    merged["Port_vol12"] = merged["Port_ret"].rolling(252).std() * np.sqrt(252)

    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["Port_vol12"] * 100, name=port_label, line=dict(color=_port_color, width=2)))
    if compare_mode and len(consol_merged) > 252:
        consol_merged["Port_vol12"] = consol_merged["Port_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=consol_merged["Date"], y=consol_merged["Port_vol12"] * 100, name="Consolidada", line=dict(color=CHART_COLORS["consolidada"], width=2)))
    if show_ibov:
        merged["Ibov_vol12"] = merged["Ibov_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["Ibov_vol12"] * 100, name="Ibovespa", line=dict(color=CHART_COLORS["ibovespa"], width=1.5)))
    if show_bench67:
        merged["Bench67_vol12"] = merged["Bench67_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench67_vol12"] * 100, name="67% Ibov + 33% CDI", line=dict(color=CHART_COLORS["bench67"], width=1.5, dash="dash")))
    if show_bench55:
        merged["Bench55_vol12"] = merged["Bench55_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["Bench55_vol12"] * 100, name="55% Ibov + 45% CDI", line=dict(color=CHART_COLORS["bench55"], width=1.5, dash="dash")))
    if show_fia:
        merged["FIA_vol12"] = merged["FIA_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["FIA_vol12"] * 100, name="Média FIA*", line=dict(color=CHART_COLORS["fia"], width=1.5, dash="longdash")))
    if show_bench67fia:
        merged["B67FIA_vol12"] = merged["Bench67FIA_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["B67FIA_vol12"] * 100, name="67% Média FIAs + 33% CDI*", line=dict(color=CHART_COLORS["bench67fia"], width=1.5, dash="dashdot")))
    if show_bench55fia:
        merged["B55FIA_vol12"] = merged["Bench55FIA_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["B55FIA_vol12"] * 100, name="55% Média FIAs + 45% CDI*", line=dict(color=CHART_COLORS["bench55fia"], width=1.5, dash="dashdot")))
    if show_cm:
        merged["CM_vol12"] = merged["CM_ret"].rolling(252).std() * np.sqrt(252)
        fig7.add_trace(go.Scatter(x=merged["Date"], y=merged["CM_vol12"] * 100, name="Carteira Modelo", line=dict(color=CHART_COLORS["cm"], width=2)))
    tag_chart_layout(fig7, height=380, yaxis_title="Volatilidade (%)")
    st.plotly_chart(fig7, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# % do CDI
# ══════════════════════════════════════════════════════════════════════════════

section_title(f"{port_label} como % do CDI")
st.caption("Percentual do CDI entregue pela carteira em cada ano. Acima de 100% significa que a carteira superou o CDI no período.")

yearly_pct_cdi = yearly[["Year"]].copy()
yearly_pct_cdi[f"% CDI {port_label}"] = np.where(
    yearly["CDI_ret"] > 0,
    (yearly["Port_ret"] / yearly["CDI_ret"] * 100).round(1),
    np.nan,
)
if compare_mode and "Consol_ret" in yearly.columns:
    yearly_pct_cdi["% CDI Consolidada"] = np.where(
        yearly["CDI_ret"] > 0,
        (yearly["Consol_ret"] / yearly["CDI_ret"] * 100).round(1),
        np.nan,
    )
if show_cm and "CM_ret" in yearly.columns:
    yearly_pct_cdi["% CDI Cart. Modelo"] = np.where(
        yearly["CDI_ret"] > 0,
        (yearly["CM_ret"] / yearly["CDI_ret"] * 100).round(1),
        np.nan,
    )
total_pct_cdi = port_total / cdi_total * 100 if cdi_total > 0 else 0

c1, c2 = st.columns([1, 2])
with c1:
    st.metric(f"% do CDI {port_label}", f"{total_pct_cdi:.1f}%")
    if compare_mode:
        consol_pct_cdi = consol_total / cdi_total * 100 if cdi_total > 0 else 0
        st.metric("% do CDI Consolidada", f"{consol_pct_cdi:.1f}%")
    if show_cm:
        cm_pct_cdi = cm_total / cdi_total * 100 if cdi_total > 0 else 0
        st.metric("% do CDI Cart. Modelo", f"{cm_pct_cdi:.1f}%")
    pct_display = yearly_pct_cdi.copy()
    pct_display["Year"] = pct_display["Year"].astype(str)
    pct_display.rename(columns={"Year": "Ano"}, inplace=True)
    for c in pct_display.columns[1:]:
        pct_display[c] = pct_display[c].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "\u2014")
    st.markdown(style_table(pct_display), unsafe_allow_html=True)
with c2:
    fig8 = go.Figure()
    pct_vals = yearly_pct_cdi[f"% CDI {port_label}"].fillna(0)
    colors = [TAG_AZUL_ESCURO if v >= 100 else TAG_ROSA for v in pct_vals]
    fig8.add_trace(go.Bar(x=yearly_pct_cdi["Year"], y=yearly_pct_cdi[f"% CDI {port_label}"], name=port_label, marker_color=colors))
    if compare_mode and "% CDI Consolidada" in yearly_pct_cdi.columns:
        fig8.add_trace(go.Bar(x=yearly_pct_cdi["Year"], y=yearly_pct_cdi["% CDI Consolidada"], name="Consolidada", marker_color=CHART_COLORS["consolidada"]))
    if show_cm and "% CDI Cart. Modelo" in yearly_pct_cdi.columns:
        fig8.add_trace(go.Bar(x=yearly_pct_cdi["Year"], y=yearly_pct_cdi["% CDI Cart. Modelo"], name="Carteira Modelo", marker_color=CHART_COLORS["cm"]))
    if compare_mode or show_cm:
        fig8.update_layout(barmode="group")
    fig8.add_hline(y=100, line_dash="dash", line_color=TAG_VERMELHO, annotation_text="100% CDI", annotation_font_color=TAG_VERMELHO)
    tag_chart_layout(fig8, height=400, yaxis_title="% do CDI", ticksuffix="%")
    st.plotly_chart(fig8, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# 9) COMPOSIÇÃO: CARTEIRA ATUAL vs CARTEIRA MODELO
# ══════════════════════════════════════════════════════════════════════════════

_carteira_atual_path = os.path.join(_DIR, "carteira_atual.csv")
if os.path.exists(_carteira_atual_path):
    st.markdown("---")
    st.markdown(f'<p class="section-title">Composição: Carteira Atual vs Carteira Modelo</p>', unsafe_allow_html=True)

    _ca = pd.read_csv(_carteira_atual_path)
    _cm_dict = {a["key"]: a for a in CM_ASSETS}
    _cm_weights_lookup = {a["key"]: cm_weights.get(a["key"], a["pct"]) for a in CM_ASSETS}

    # ── Helper: build HTML table ──
    def _build_comparison_table(df, label_col, title):
        """Render a professional HTML comparison table."""
        def _diff_cell(val):
            """Green = modelo > atual (precisa aumentar), Red = modelo < atual (precisa reduzir)."""
            sign = "+" if val > 0 else ""
            txt = f"{sign}{val:.2f}"
            if val < -0.01:
                # Atual > Modelo → precisa reduzir → vermelho
                return f"""<div style="display:inline-flex;align-items:center;gap:4px;background:rgba(220,38,38,0.08);
                    border-radius:6px;padding:3px 10px;">
                    <span style="color:#dc2626;font-size:0.7rem;">&#9660;</span>
                    <span style="color:#dc2626;font-weight:700;font-size:0.84rem;">{txt}</span></div>"""
            elif val > 0.01:
                # Atual < Modelo → precisa aumentar → verde
                return f"""<div style="display:inline-flex;align-items:center;gap:4px;background:rgba(22,163,74,0.08);
                    border-radius:6px;padding:3px 10px;">
                    <span style="color:#16a34a;font-size:0.7rem;">&#9650;</span>
                    <span style="color:#16a34a;font-weight:700;font-size:0.84rem;">{txt}</span></div>"""
            return f'<span style="color:#a3a3a3;font-weight:500;font-size:0.84rem;">0.00</span>'

        def _bar_html(atual, modelo, max_val):
            """Mini horizontal bar comparing atual vs modelo."""
            w_atual = (atual / max_val * 100) if max_val > 0 else 0
            w_modelo = (modelo / max_val * 100) if max_val > 0 else 0
            return f"""<div style="position:relative;height:6px;background:#ede9e3;border-radius:3px;width:100%;min-width:60px;">
                <div style="position:absolute;top:0;left:0;height:100%;width:{w_modelo:.1f}%;background:rgba(99,13,36,0.18);border-radius:3px;"></div>
                <div style="position:absolute;top:0;left:0;height:100%;width:{w_atual:.1f}%;background:{TAG_VERMELHO};border-radius:3px;opacity:0.7;"></div>
            </div>"""

        max_val = max(df["Atual (%)"].max(), df["Modelo (%)"].max(), 1)
        rows_html = ""
        for i, row in df.iterrows():
            bg = "#fafaf8" if i % 2 == 0 else "#ffffff"
            diff_val = row["Modelo (%)"] - row["Atual (%)"]
            rows_html += f"""<tr style="background-color:{bg};transition:background 0.15s;" onmouseover="this.style.backgroundColor='#f0ede6'" onmouseout="this.style.backgroundColor='{bg}'">
                <td style="padding:11px 16px;border-bottom:1px solid #ede9e3;text-align:left;font-size:0.84rem;color:#1a1a1a;font-weight:500;">{row[label_col]}</td>
                <td style="padding:11px 16px;border-bottom:1px solid #ede9e3;text-align:center;font-size:0.84rem;font-weight:700;color:{TAG_AZUL_ESCURO};">{row['Atual (%)']:.2f}%</td>
                <td style="padding:11px 16px;border-bottom:1px solid #ede9e3;text-align:center;font-size:0.84rem;color:#6a6864;font-weight:500;">{row['Modelo (%)']:.2f}%</td>
                <td style="padding:11px 16px;border-bottom:1px solid #ede9e3;text-align:center;">{_diff_cell(diff_val)}</td>
                <td style="padding:11px 12px;border-bottom:1px solid #ede9e3;vertical-align:middle;">{_bar_html(row['Atual (%)'], row['Modelo (%)'], max_val)}</td>
            </tr>"""

        # Totals row
        tot_atual = df["Atual (%)"].sum()
        tot_modelo = df["Modelo (%)"].sum()
        tot_diff = tot_modelo - tot_atual
        rows_html += f"""<tr style="background-color:#f0efeb;">
            <td style="padding:12px 16px;font-weight:700;font-size:0.85rem;color:{TAG_VERMELHO};border-top:2px solid {TAG_VERMELHO};">TOTAL</td>
            <td style="padding:12px 16px;text-align:center;font-weight:700;font-size:0.85rem;color:{TAG_AZUL_ESCURO};border-top:2px solid {TAG_VERMELHO};">{tot_atual:.2f}%</td>
            <td style="padding:12px 16px;text-align:center;font-weight:700;font-size:0.85rem;color:#6a6864;border-top:2px solid {TAG_VERMELHO};">{tot_modelo:.2f}%</td>
            <td style="padding:12px 16px;text-align:center;border-top:2px solid {TAG_VERMELHO};">{_diff_cell(tot_diff)}</td>
            <td style="border-top:2px solid {TAG_VERMELHO};"></td>
        </tr>"""

        html = f"""
        <div style="background:{TAG_BRANCO};border-radius:14px;overflow:hidden;box-shadow:0 4px 20px rgba(99,13,36,0.10);border:1px solid #e8e6dd;margin-bottom:2rem;">
            <div style="background:linear-gradient(135deg, {TAG_VERMELHO} 0%, {TAG_VERMELHO_LIGHT} 100%);padding:14px 20px;display:flex;align-items:center;gap:10px;">
                <span style="color:rgba(255,255,255,0.85);font-size:1.1rem;">&#9632;</span>
                <span style="color:#ffffff;font-weight:700;font-size:0.95rem;letter-spacing:0.05em;text-transform:uppercase;">{title}</span>
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="background-color:#f5f4f0;">
                        <th style="padding:11px 16px;text-align:left;font-size:0.72rem;font-weight:700;color:{TAG_CINZA};text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #e0ddd5;">{label_col}</th>
                        <th style="padding:11px 16px;text-align:center;font-size:0.72rem;font-weight:700;color:{TAG_CINZA};text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #e0ddd5;">Atual</th>
                        <th style="padding:11px 16px;text-align:center;font-size:0.72rem;font-weight:700;color:{TAG_CINZA};text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #e0ddd5;">Modelo</th>
                        <th style="padding:11px 16px;text-align:center;font-size:0.72rem;font-weight:700;color:{TAG_CINZA};text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #e0ddd5;">Diferença</th>
                        <th style="padding:11px 12px;text-align:center;font-size:0.72rem;font-weight:700;color:{TAG_CINZA};text-transform:uppercase;letter-spacing:0.07em;border-bottom:2px solid #e0ddd5;min-width:80px;"></th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>"""
        return html

    # ── Table 1: By Ativo ──
    _rows_ativo = []
    _used_cm_keys = set()
    for _, row in _ca.iterrows():
        cm_key = row["cm_key"] if pd.notna(row["cm_key"]) and row["cm_key"] != "" else None
        modelo_pct = _cm_weights_lookup.get(cm_key, 0.0) if cm_key else 0.0
        diff = row["pct_pl"] - modelo_pct
        _rows_ativo.append({
            "Ativo": row["ativo"],
            "Atual (%)": row["pct_pl"],
            "Modelo (%)": modelo_pct,
            "Diferença (p.p.)": diff,
        })
        if cm_key:
            _used_cm_keys.add(cm_key)
    for a in CM_ASSETS:
        if a["key"] not in _used_cm_keys:
            modelo_pct = _cm_weights_lookup.get(a["key"], a["pct"])
            _rows_ativo.append({
                "Ativo": a["name"],
                "Atual (%)": 0.0,
                "Modelo (%)": modelo_pct,
                "Diferença (p.p.)": -modelo_pct,
            })
    df_ativo = pd.DataFrame(_rows_ativo)
    st.markdown(_build_comparison_table(df_ativo, "Ativo", "Alocação por Ativo"), unsafe_allow_html=True)

    # ── Table 2: By Estratégia ──
    _ca_strat = _ca.groupby("estrategia")["pct_pl"].sum().reset_index()
    _ca_strat.columns = ["Estratégia", "Atual (%)"]
    _cm_strat_data = []
    for a in CM_ASSETS:
        _cm_strat_data.append({"estrategia": a["estrategia"], "modelo_pct": _cm_weights_lookup.get(a["key"], a["pct"])})
    _cm_strat = pd.DataFrame(_cm_strat_data).groupby("estrategia")["modelo_pct"].sum().reset_index()
    _cm_strat.columns = ["Estratégia", "Modelo (%)"]
    df_strat = _ca_strat.merge(_cm_strat, on="Estratégia", how="outer").fillna(0.0)
    df_strat["Diferença (p.p.)"] = df_strat["Atual (%)"] - df_strat["Modelo (%)"]
    df_strat = df_strat.sort_values("Atual (%)", ascending=False).reset_index(drop=True)
    st.markdown(_build_comparison_table(df_strat, "Estratégia", "Alocação por Estratégia"), unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# DISCLAIMER & FOOTER
# ══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""<div class="disclaimer">
<strong>Aviso:</strong> Este material tem caráter meramente informativo e não constitui oferta, solicitação de oferta ou recomendação
de investimento. Rentabilidade passada não representa garantia de rentabilidade futura. Os benchmarks compostos
são utilizados apenas para fins comparativos. A Carteira Modelo usa proxies por classe de ativo:
BOVA11 → Ibovespa, Fundos de Ações → Média FIA*, NTN-B → IMA-B 5+ (BCB/IMAB11), Crédito/CDI → CDI.
</div>""", unsafe_allow_html=True)

st.markdown(f"""<div class="tag-footer">
<p>Dados: Cota de rendimento do cliente &bull; Ibovespa (BCB / Yahoo Finance) &bull; CDI (Banco Central)<br>
Benchmark = 67% Ibovespa + 33% CDI &bull; <strong>TAG Investimentos</strong></p>
</div>""", unsafe_allow_html=True)
