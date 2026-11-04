# Finance Data Project

Dashboard e análise de carteira focados em dados financeiros, risco, retorno e indicadores técnicos.

## Visão geral
Este projeto foi pensado como uma base sólida para acompanhar desempenho de ativos, comparar carteira, entender setor de exposição e validar ideias de análise quantitativa com dados reais do mercado.

### Funcionalidades principais
- coleta de dados via yfinance
- cálculo de retorno total, volatilidade e Sharpe
- distribuição por pesos e valor investido
- comparação por ativo e setor
- indicadores técnicos: SMA, RSI e MACD
- benchmark para contextualizar desempenho
- interface em Streamlit com visualização profissional

## Estrutura do projeto
- app.py: dashboard principal da carteira
- src/finance_analysis.py: script complementar para análise de ativos
- tests/test_finance_analysis.py: testes de validação de entradas
- requirements.txt: dependências do projeto
- data/: pasta para artefatos e gráficos
- .streamlit/config.toml: configurações do Streamlit para execução sem prompts extras

## Requisitos
- Python 3.10+
- pip

## Setup local
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Como executar
### Dashboard
```bash
streamlit run app.py
```

### Script de análise básica
```bash
python src/finance_analysis.py --ticker AAPL --period 1y
```

## Exemplos de uso
- comparar carteira com 4 ações americanas
- ajustar pesos na sidebar
- testar benchmark SPY ou QQQ
- trocar ativos e período conforme interesse

## Observações
O projeto é pensado para uso pessoal e aprendizado prático em finanças quantitativas, com foco em clareza, robustez e fácil expansão.

## Licença
Este projeto está licenciado sob a MIT License.
