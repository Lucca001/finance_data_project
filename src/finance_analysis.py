from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

"""Projeto pessoal de análise financeira.

A ideia aqui é acompanhar o desempenho de ações de forma simples,
visual e didática, usando dados reais do mercado.
"""

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}


def normalize_ticker(ticker: str) -> str:
    """Valida e padroniza o código do ativo."""
    if not isinstance(ticker, str):
        raise TypeError("Ticker deve ser uma string.")

    normalized = ticker.strip().upper().replace(" ", "")
    if not normalized:
        raise ValueError("Ticker não pode estar vazio.")
    return normalized


def validate_period(period: str) -> str:
    """Valida a granularidade de tempo do dado."""
    if not isinstance(period, str):
        raise TypeError("Período deve ser uma string.")

    normalized = period.strip().lower()
    if not normalized:
        raise ValueError("Período não pode estar vazio.")
    if normalized not in VALID_PERIODS:
        valid_values = ", ".join(sorted(VALID_PERIODS))
        raise ValueError(f"Período inválido: {period}. Use um dos valores: {valid_values}.")
    return normalized


def fetch_data(ticker: str = "PETR4.SA", period: str = "1y") -> pd.DataFrame:
    """Busca os dados históricos do ativo escolhido."""
    normalized_ticker = normalize_ticker(ticker)
    validated_period = validate_period(period)

    try:
        data = yf.download(
            normalized_ticker,
            period=validated_period,
            auto_adjust=False,
            progress=False,
            threads=True,
        )
    except Exception as exc:
        raise RuntimeError(f"Erro ao buscar dados para {normalized_ticker}: {exc}") from exc

    if data.empty:
        raise ValueError(f"Nenhum dado encontrado para {normalized_ticker} no período {validated_period}.")

    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.to_flat_index()

    data = data.reset_index()
    data.columns = [
        str(col).strip().lower().replace(" ", "_")
        if not isinstance(col, tuple)
        else str(col[0]).strip().lower().replace(" ", "_")
        for col in data.columns
    ]

    if "date" not in data.columns and "datetime" in data.columns:
        data = data.rename(columns={"datetime": "date"})

    return data


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona indicadores básicos para acompanhamento do preço."""
    df = df.copy()
    df["daily_return"] = df["close"].pct_change().fillna(0)
    df["moving_average_7"] = df["close"].rolling(window=7).mean()
    df["moving_average_30"] = df["close"].rolling(window=30).mean()
    return df


def print_summary(df: pd.DataFrame, ticker: str) -> None:
    """Exibe um resumo rápido do desempenho do ativo."""
    if df.empty:
        print(f"Sem dados para {ticker}.")
        return

    total_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
    volatility = df["daily_return"].std() * 100

    print(f"Resumo para {ticker}")
    print(f"Primeiro preço: R$ {df['close'].iloc[0]:.2f}")
    print(f"Último preço: R$ {df['close'].iloc[-1]:.2f}")
    print(f"Retorno total: {total_return:.2f}%")
    print(f"Volatilidade diária: {volatility:.2f}%")
    print(f"Máximo histórico: R$ {df['close'].max():.2f}")
    print(f"Mínimo histórico: R$ {df['close'].min():.2f}")


def plot_prices(df: pd.DataFrame, ticker: str) -> None:
    """Gera o gráfico do ativo e salva em arquivo de imagem."""
    plt.figure(figsize=(12, 6))
    plt.plot(df["date"], df["close"], label="Preço de fechamento", color="navy")
    plt.plot(df["date"], df["moving_average_7"], label="Média móvel 7d", linestyle="--")
    plt.plot(df["date"], df["moving_average_30"], label="Média móvel 30d", linestyle="-.")
    plt.title(f"Preço e médias móveis - {ticker}")
    plt.xlabel("Data")
    plt.ylabel("Preço (R$)")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(DATA_DIR / f"{ticker}_price_analysis.png", dpi=150)
    plt.close()


def parse_args() -> argparse.Namespace:
    """Lê opções do usuário pela linha de comando."""
    parser = argparse.ArgumentParser(description="Análise financeira simples com dados reais do mercado.")
    parser.add_argument("--ticker", type=str, default="PETR4.SA", help="Ticker do ativo, ex.: PETR4.SA, VALE3.SA, AAPL")
    parser.add_argument("--period", type=str, default="1y", help="Período dos dados, ex.: 1mo, 6mo, 1y, 5y")
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada do projeto pessoal de análise financeira."""
    args = parse_args()

    try:
        ticker = normalize_ticker(args.ticker)
        period = validate_period(args.period)
        data = fetch_data(ticker=ticker, period=period)
        data = calculate_indicators(data)
        print_summary(data, ticker)
        plot_prices(data, ticker)
    except (TypeError, ValueError, RuntimeError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
