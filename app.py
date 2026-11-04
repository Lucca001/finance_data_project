from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf


DEFAULT_TICKERS = ["AAPL", "MSFT", "NVDA", "AMZN"]
VALID_PERIODS = ["1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
BENCHMARKS = ["SPY", "QQQ", "^BVSP"]
SECTOR_MAP = {
    "AAPL": "Tecnologia",
    "MSFT": "Tecnologia",
    "NVDA": "Semicondutores",
    "AMZN": "Consumo",
    "PETR4.SA": "Energia",
    "VALE3.SA": "Mineração",
    "ITUB4.SA": "Financeiro",
    "B3SA3.SA": "Financeiro",
    "GOOGL": "Tecnologia",
    "META": "Tecnologia",
    "TSLA": "Automotivo",
    "NFLX": "Entretenimento",
    "QQQ": "ETF",
    "SPY": "ETF",
    "^BVSP": "Índice",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.to_flat_index()

    df = df.reset_index()
    df.columns = [
        str(col).strip().lower().replace(" ", "_")
        if not isinstance(col, tuple)
        else str(col[0]).strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    if "date" not in df.columns and "datetime" in df.columns:
        df = df.rename(columns={"datetime": "date"})

    return df


@st.cache_data
def fetch_ticker_data(ticker: str, period: str) -> pd.DataFrame:
    ticker = ticker.strip().upper()
    data = yf.download(ticker, period=period, auto_adjust=False, progress=False, threads=True)
    if data.empty:
        raise ValueError(f"Nenhum dado encontrado para {ticker} no período {period}.")

    data = normalize_columns(data)
    data["ticker"] = ticker
    data["date"] = pd.to_datetime(data["date"])
    return data


@st.cache_data
def fetch_benchmark_data(symbol: str, period: str) -> pd.DataFrame:
    symbol = symbol.strip().upper()
    data = yf.download(symbol, period=period, auto_adjust=False, progress=False, threads=True)
    if data.empty:
        raise ValueError(f"Benchmark {symbol} não foi encontrado.")
    data = normalize_columns(data)
    data["ticker"] = symbol
    data["date"] = pd.to_datetime(data["date"])
    return data


def build_portfolio_frame(tickers: Iterable[str], period: str) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for ticker in tickers:
        try:
            data = fetch_ticker_data(ticker, period)
            frames.append(data)
        except Exception as exc:
            st.warning(f"Não foi possível carregar {ticker}: {exc}")

    if not frames:
        raise ValueError("Nenhum ativo válido foi carregado. Verifique os tickers informados.")

    portfolio = pd.concat(frames, ignore_index=True)
    if "close" not in portfolio.columns:
        raise ValueError("Os dados carregados não possuem coluna close.")

    portfolio = portfolio.sort_values(["ticker", "date"]).reset_index(drop=True)
    return portfolio


def get_sector(ticker: str) -> str:
    return SECTOR_MAP.get(ticker.strip().upper(), "Diversificado")


def add_technical_indicators(portfolio: pd.DataFrame) -> pd.DataFrame:
    portfolio = portfolio.sort_values(["ticker", "date"]).copy()
    portfolio["return"] = portfolio.groupby("ticker")["close"].pct_change().fillna(0)
    portfolio["sma_7"] = portfolio.groupby("ticker")["close"].transform(lambda s: s.rolling(7).mean())
    portfolio["sma_20"] = portfolio.groupby("ticker")["close"].transform(lambda s: s.rolling(20).mean())

    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi_value = 100 - (100 / (1 + rs))
        return rsi_value.fillna(50)

    portfolio["rsi_14"] = portfolio.groupby("ticker")["close"].transform(rsi)

    ema_12 = portfolio.groupby("ticker")["close"].transform(lambda s: s.ewm(span=12, adjust=False).mean())
    ema_26 = portfolio.groupby("ticker")["close"].transform(lambda s: s.ewm(span=26, adjust=False).mean())
    portfolio["macd"] = ema_12 - ema_26
    signal = portfolio.groupby("ticker")["macd"].transform(lambda s: s.ewm(span=9, adjust=False).mean())
    portfolio["signal_line"] = signal

    return portfolio


def compute_summary(portfolio: pd.DataFrame) -> pd.DataFrame:
    summary = []
    for ticker, group in portfolio.groupby("ticker"):
        group = group.sort_values("date")
        first_price = group["close"].iloc[0]
        last_price = group["close"].iloc[-1]
        total_return = (last_price / first_price - 1) * 100 if first_price else 0.0
        daily_return = group["return"].fillna(0)
        volatility = daily_return.std() * 100
        rsi_last = float(group["rsi_14"].iloc[-1])
        summary.append(
            {
                "ticker": ticker,
                "setor": get_sector(ticker),
                "preco_inicial": round(float(first_price), 2),
                "preco_final": round(float(last_price), 2),
                "retorno_total_pct": round(total_return, 2),
                "volatilidade_diaria_pct": round(volatility, 2),
                "rsi_14": round(rsi_last, 2),
                "ultima_data": group["date"].max(),
            }
        )

    if not summary:
        return pd.DataFrame(columns=["ticker", "setor", "preco_inicial", "preco_final", "retorno_total_pct", "volatilidade_diaria_pct", "rsi_14", "ultima_data"])

    return pd.DataFrame(summary).sort_values("retorno_total_pct", ascending=False).reset_index(drop=True)


def compute_risk_return(portfolio: pd.DataFrame, weights: dict[str, float]) -> tuple[float, float, float]:
    price_pivot = portfolio.pivot_table(index="date", columns="ticker", values="close", aggfunc="last")
    returns = price_pivot.pct_change().dropna()

    valid_tickers = [t for t in weights if t in returns.columns]
    if not valid_tickers:
        raise ValueError("Nenhum ticker válido para cálculo de carteira.")

    vector = pd.Series({ticker: weights[ticker] for ticker in valid_tickers})
    vector = vector / vector.sum()
    port_returns = returns[valid_tickers].dot(vector)

    expected_return = float(port_returns.mean() * 252 * 100)
    volatility = float(port_returns.std() * (252 ** 0.5) * 100)
    sharpe = float((expected_return / 100 - 0.03) / (volatility / 100)) if volatility else 0.0
    return expected_return, volatility, sharpe


def parse_weights(tickers: list[str], weights_input: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    if not weights_input.strip():
        for ticker in tickers:
            weights[ticker] = 100 / len(tickers)
        return weights

    items = [part.strip() for part in weights_input.split(",") if part.strip()]
    if len(items) != len(tickers):
        raise ValueError("A quantidade de pesos precisa combinar com a quantidade de ativos.")

    for item, ticker in zip(items, tickers):
        value = float(item.replace("%", ""))
        if value <= 0:
            raise ValueError("Cada peso deve ser maior que zero.")
        weights[ticker] = value

    total = sum(weights.values())
    if total == 0:
        raise ValueError("A soma dos pesos não pode ser zero.")

    return {ticker: value / total * 100 for ticker, value in weights.items()}


def build_allocation(raw_tickers: list[str], weights: dict[str, float], total_value: float) -> pd.DataFrame:
    allocation = pd.DataFrame({
        "ticker": raw_tickers,
        "setor": [get_sector(ticker) for ticker in raw_tickers],
        "peso_pct": [weights.get(ticker, 0.0) for ticker in raw_tickers],
    })
    allocation["valor_investido"] = (allocation["peso_pct"] / 100) * total_value
    return allocation


def compute_sector_summary(allocation: pd.DataFrame) -> pd.DataFrame:
    sector_summary = allocation.groupby("setor", as_index=False).agg(
        peso_pct=("peso_pct", "sum"),
        valor_investido=("valor_investido", "sum"),
        ativos=("ticker", "count"),
    )
    return sector_summary.sort_values("peso_pct", ascending=False).reset_index(drop=True)


def build_relative_return(df: pd.DataFrame, target_col: str) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=float)

    series = df.sort_values("date").set_index("date")[target_col]
    start_value = series.iloc[0]
    return ((series / start_value) - 1) * 100


st.set_page_config(page_title="Carteira Financeira", page_icon="📈", layout="wide")

st.markdown(
    """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%);
            color: #0f172a;
        }
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stDataFrame"] {
            border-radius: 12px;
            border: 1px solid #dfe7f1;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Carteira Financeira")
st.caption("Painel profissional para análise de ativos, risco, retorno, setor e indicadores técnicos.")

with st.sidebar:
    st.header("Configuração da carteira")

    tickers_input = st.text_input(
        "Ativos",
        value=", ".join(DEFAULT_TICKERS),
        help="Digite os tickers separados por vírgula. Ex.: AAPL, MSFT, NVDA, AMZN",
    )
    weights_input = st.text_input(
        "Pesos (%)",
        value="25, 25, 25, 25",
        help="Informe os pesos na mesma ordem dos ativos.",
    )
    invest_value = st.number_input("Valor investido (R$)", min_value=100.0, value=10000.0, step=100.0)
    benchmark = st.selectbox("Benchmark", BENCHMARKS, index=0)
    period = st.selectbox("Período", VALID_PERIODS, index=3)

raw_tickers = [item.strip().upper() for item in tickers_input.split(",") if item.strip()]
if not raw_tickers:
    raw_tickers = DEFAULT_TICKERS

try:
    weights = parse_weights(raw_tickers, weights_input)
    allocation = build_allocation(raw_tickers, weights, float(invest_value))
    portfolio = build_portfolio_frame(raw_tickers, period)
    portfolio = add_technical_indicators(portfolio)
    summary = compute_summary(portfolio)
    expected_return, volatility, sharpe = compute_risk_return(portfolio, weights)
    sector_summary = compute_sector_summary(allocation)

    st.subheader("Resumo executivo")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Retorno esperado", f"{expected_return:.2f}%")
    col2.metric("Volatilidade", f"{volatility:.2f}%")
    col3.metric("Sharpe", f"{sharpe:.2f}")
    col4.metric("Capital investido", f"R$ {invest_value:,.2f}")

    st.subheader("Distribuição da carteira")
    col_a, col_b = st.columns(2)
    with col_a:
        st.dataframe(allocation[["ticker", "setor", "peso_pct", "valor_investido"]].sort_values("peso_pct", ascending=False), width="stretch")
    with col_b:
        st.bar_chart(allocation.set_index("ticker")["peso_pct"])

    st.subheader("Comparação dos ativos")
    comparison = summary[["ticker", "setor", "retorno_total_pct", "volatilidade_diaria_pct", "rsi_14"]].copy()
    comparison = comparison.rename(columns={
        "retorno_total_pct": "Retorno total %",
        "volatilidade_diaria_pct": "Volatilidade diária %",
        "rsi_14": "RSI (14)",
    })
    st.dataframe(comparison, width="stretch")

    st.subheader("Risco x retorno")
    scatter_data = summary[["ticker", "retorno_total_pct", "volatilidade_diaria_pct"]].set_index("ticker")
    st.scatter_chart(scatter_data)

    st.subheader("Setores da carteira")
    sector_chart = sector_summary.set_index("setor")[["peso_pct"]]
    st.bar_chart(sector_chart)
    st.dataframe(sector_summary, width="stretch")

    st.subheader("Evolução do preço")
    price_chart = portfolio.pivot_table(index="date", columns="ticker", values="close", aggfunc="last").sort_index()
    st.line_chart(price_chart)

    st.subheader("Retorno acumulado")
    normalized = portfolio.groupby(["ticker", "date"])["close"].last().unstack(fill_value=None)
    normalized = normalized / normalized.iloc[0]
    st.line_chart(normalized)

    st.subheader("Indicadores técnicos")
    selected_ticker = st.selectbox("Ativo para análise técnica", raw_tickers)
    tech = portfolio[portfolio["ticker"] == selected_ticker].sort_values("date")
    col_a, col_b = st.columns(2)
    with col_a:
        st.line_chart(tech.set_index("date")[["close", "sma_7", "sma_20"]])
    with col_b:
        st.line_chart(tech.set_index("date")[["rsi_14"]])

    st.subheader("Benchmark vs carteira")
    benchmark_data = fetch_benchmark_data(benchmark, period)
    if not benchmark_data.empty:
        bench_relative = build_relative_return(benchmark_data, "close")
        benchmark_df = pd.DataFrame({"date": bench_relative.index, "benchmark": bench_relative.values})
        selected_series = portfolio[portfolio["ticker"] == selected_ticker].sort_values("date")
        selected_relative = build_relative_return(selected_series, "close")
        selected_df = pd.DataFrame({"date": selected_relative.index, selected_ticker: selected_relative.values})
        compare_df = benchmark_df.merge(selected_df, on="date", how="inner")
        if not compare_df.empty:
            compare_df = compare_df.set_index("date")
            st.line_chart(compare_df)

    st.subheader("Detalhes por ativo")
    for ticker in summary["ticker"].tolist():
        group = portfolio[portfolio["ticker"] == ticker].sort_values("date")
        with st.expander(f"{ticker}"):
            st.dataframe(group[["date", "open", "high", "low", "close", "volume", "sma_7", "sma_20", "rsi_14", "macd"]].tail(10), width="stretch")

except ValueError as exc:
    st.error(f"Erro ao carregar os dados: {exc}")
