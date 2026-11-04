# Análise Financeira Pessoal

Esse projeto nasceu como uma forma simples de acompanhar o desempenho de uma ação e entender melhor o comportamento do mercado sem depender de ferramentas caras.

A ideia aqui é ser um ambiente de estudo e acompanhamento pessoal, com foco em:
- coleta de dados do mercado
- cálculo de retornos e volatilidade
- análise visual simples
- acompanhamento de ativos da carteira

## Objetivo prático
Usar a bolsa como laboratório de dados: observar tendências, comparar desempenho e aprender a transformar dados financeiros em indicadores úteis para tomada de decisão.

## Estrutura do projeto
- src/finance_analysis.py: script principal com coleta, indicadores e gráfico
- requirements.txt: bibliotecas usadas
- data/: pasta para salvar os gráficos gerados

## Como rodar
1. Crie o ambiente virtual
2. Instale as dependências
3. Execute o script principal ou o dashboard

### Script de análise básica
```bash
python3 src/finance_analysis.py --ticker PETR4.SA --period 1y
```

### Dashboard de carteira
```bash
streamlit run app.py
```

## Ativo usado no exemplo
O projeto usa PETR4.SA como referência inicial, mas o código pode ser adaptado para qualquer ativo da B3 ou do mercado internacional.

## Observação
Esse é um projeto pessoal de aprendizado, então a regra é manter o código simples, legível e fácil de evoluir conforme a análise vai ficando mais interessante.
