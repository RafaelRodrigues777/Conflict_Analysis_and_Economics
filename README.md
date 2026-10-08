# Conflict_Analysis_and_Economics

Conflict Analysis and Economics — análise da relação entre a economia, o desenvolvimento humano e a quantidade de conflitos armados nos países (1990–2018).

(SENAI CIC · Turma Bosch, 2026).

# Equipe

Artur Oliveira · Diego Schapieski · Guilherme Padilha · Rafael Rodrigues

# Perguntas

1. Países com menor PIB per capita e menor IDH concentram mais eventos de conflito?
2. Como o número de conflitos e a economia de um país evoluem ao longo do tempo?
3. Onde no mundo ocorrem os conflitos e a que grupo de renda pertencem esses países?

# Dados

- [UCDP Georeferenced Event Dataset (GED) v26.1](https://ucdp.uu.se/downloads/) · Uppsala Conflict Data Program — eventos de violência organizada, com localização e número de mortes
- [World Bank Indicators](https://mavenanalytics.io/data-playground/world-economic-indicators) · Banco Mundial — PIB per capita, mortalidade infantil, expectativa de vida, internet, energia, desemprego, densidade populacional e grupo de renda
- [Human Development Index (HDI)](https://mavenanalytics.io/data-playground/world-economic-indicators) · PNUD — IDH e componentes

Os arquivos devem ficar na pasta `data/`:

```
data/
├── GEDEvent_v26_1.xlsx
├── WorldBank.xlsx
└── HDI.csv
```

# Estrutura do projeto

```
raiz/
├── data/                      # bases de dados (fontes)
├── notebooks                  # notebooks para testes e criação de alguns gráficos
├── src/
│   └── analise_conflitos.py   # limpeza, junção das bases e geração dos gráficos
├── graficos/                  # PNGs gerados pelo script
├── docs/                      # documentação técnica e slides
└── requirements.txt
```

# Como executar

Instale as dependências (Python 3.10 ou superior recomendado):

```
pip install -r requirements.txt
```

Com os dados na pasta `data/`, execute a partir da raiz do projeto:

```
python src/analise_conflitos.py
```

Os 5 gráficos e a tabela de apoio `base_por_pais.csv` serão salvos na pasta `graficos/`.

> **Observação:** o `cartopy` baixa os contornos dos países (Natural Earth) na primeira execução, então é necessário ter acesso à internet nesse momento.

# Metodologia

- **Período:** 1990–2018, que é o intervalo em comum entre as três bases.
- **Junção:** as bases são unidas pelo código ISO3 do país. Os nomes do GED que diferem dos do Banco Mundial (por exemplo, "Syria" e "DR Congo (Zaire)") foram corrigidos por um dicionário de correspondência no script.
- **Países sem conflito:** o GED só registra países com ao menos um evento. Os demais países do Banco Mundial entram na análise com 0 eventos.
- **Indicadores:** valores médios do período 1990–2018, por país. O IDH, que vem em formato largo (uma coluna por ano), também é reduzido à média do período.
- **Correlação:** usa-se o coeficiente de Spearman, mais adequado que o de Pearson por causa da forte assimetria e dos valores extremos.
- **Grupos de renda:** "renda alta (OCDE)" e "renda alta (não-OCDE)" foram unificados em um único grupo.

# Gráficos

Os gráficos estão exibidos na pasta images e alguns estão no notebook Projeto.

# Documentação

[Documentação técnica](docs/documentacao.pdf).