"""
Economia, desenvolvimento humano e conflitos armados (1990-2018)
Gera 5 gráficos usando pandas, numpy, matplotlib, seaborn e cartopy.

Estrutura esperada do projeto:
    raiz/
    ├── src/analise_conflitos.py      <- este arquivo
    └── data/                         <- GEDEvent_v26_1.xlsx, WorldBank.xlsx, HDI.csv

Uso (a partir da raiz):  python src/analise_conflitos.py
Os PNGs são salvos em ./graficos (pasta atual de execução).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    TEM_CARTOPY = True
except ImportError:
    TEM_CARTOPY = False
    print("AVISO: cartopy não instalado; o mapa usará eixos simples (pip install cartopy).")

# Este arquivo fica em raiz/src/; os dados ficam em raiz/data/
RAIZ = Path(__file__).resolve().parent.parent
DATA_DIR = RAIZ / "data"
OUT_DIR = Path("graficos")
OUT_DIR.mkdir(exist_ok=True)
ANO_INI, ANO_FIM = 1990, 2018          # período em comum entre as 3 bases

sns.set_theme(style="whitegrid", context="notebook")

# ----------------------------------------------------------------------------
# 1. LEITURA E LIMPEZA (pandas)
# ----------------------------------------------------------------------------
# --- Banco Mundial -----------------------------------------------------------
wb_bruto = pd.read_excel(DATA_DIR / "WorldBank.xlsx")
wb = wb_bruto.rename(columns={
    "Country Name": "pais", "Country Code": "iso3", "Region": "regiao",
    "IncomeGroup": "renda", "Year": "ano",
    "GDP per capita (USD)": "pib_pc",
    "Infant mortality rate (per 1,000 live births)": "mort_infantil",
    "Life expectancy at birth (years)": "expec_vida",
    "Individuals using the Internet (% of population)": "internet",
    "Electric power consumption (kWh per capita)": "energia",
    "Unemployment (% of total labor force) (modeled ILO estimate)": "desemprego",
    "Population density (people per sq. km of land area)": "dens_pop",
})
wb = wb.drop_duplicates(subset=["iso3", "ano"])
wb = wb.dropna(subset=["regiao", "renda"])            # remove agregados (Mundo, regiões...)
wb = wb[wb["ano"].between(ANO_INI, ANO_FIM)]

indicadores = ["pib_pc", "mort_infantil", "expec_vida", "internet", "energia",
               "desemprego", "dens_pop"]
paises = (wb.groupby("iso3")
            .agg(pais=("pais", "first"), regiao=("regiao", "first"),
                 renda=("renda", "first"),
                 **{c: (c, "mean") for c in indicadores})   # média 1990-2018
            .reset_index())
# O Banco Mundial separa "renda alta" em OCDE / não-OCDE; aqui unificamos em um só grupo
paises["renda"] = paises["renda"].replace({"High income: OECD": "High income",
                                           "High income: nonOECD": "High income"})

# --- IDH (formato largo -> média 1990-2018) ---------------------------------
hdi = pd.read_csv(DATA_DIR / "HDI.csv")
cols_hdi = [f"hdi_{a}" for a in range(ANO_INI, ANO_FIM + 1) if f"hdi_{a}" in hdi.columns]
hdi = hdi.assign(idh=hdi[cols_hdi].mean(axis=1))
hdi = hdi[["iso3", "idh"]]

# --- GED: eventos de conflito -----------------------------------------------
cols_mortes = ["deaths_a", "deaths_b", "deaths_civilians", "deaths_unknown"]
ged = pd.read_excel(DATA_DIR / "GEDEvent_v26_1.xlsx",
                    usecols=["year", "country", "latitude", "longitude"] + cols_mortes)
ged = ged[ged["year"].between(ANO_INI, ANO_FIM)].copy()
ged["mortes"] = ged[cols_mortes].sum(axis=1)

# Nomes do GED que diferem dos do Banco Mundial -> código ISO3
DE_PARA_ISO = {
    "Bosnia-Herzegovina": "BIH", "Cambodia (Kampuchea)": "KHM", "Congo": "COG",
    "DR Congo (Zaire)": "COD", "Egypt": "EGY", "Gambia": "GMB", "Iran": "IRN",
    "Ivory Coast": "CIV", "Kingdom of eSwatini (Swaziland)": "SWZ",
    "Kyrgyzstan": "KGZ", "Laos": "LAO", "Madagascar (Malagasy)": "MDG",
    "Myanmar (Burma)": "MMR", "Russia (Soviet Union)": "RUS",
    "Serbia (Yugoslavia)": "SRB", "Syria": "SYR", "United States of America": "USA",
    "Venezuela": "VEN", "Yemen (North Yemen)": "YEM", "Zimbabwe (Rhodesia)": "ZWE",
}
nome_para_iso = wb_bruto.drop_duplicates("Country Name").set_index("Country Name")["Country Code"]
ged["iso3"] = ged["country"].map(DE_PARA_ISO).fillna(ged["country"].map(nome_para_iso))

sem_iso = ged.loc[ged["iso3"].isna(), "country"].unique()
if len(sem_iso):
    print("Países do GED sem correspondência no Banco Mundial:", list(sem_iso))

# Eventos e mortes por país (numpy/pandas)
ev = (ged.groupby("iso3").agg(eventos=("iso3", "size"), mortes=("mortes", "sum")).reset_index())

# --- Junção final: todos os países do Banco Mundial; sem conflito = 0 -------
base = (paises.merge(hdi, on="iso3", how="left")
              .merge(ev, on="iso3", how="left"))
base[["eventos", "mortes"]] = base[["eventos", "mortes"]].fillna(0)
base["teve_conflito"] = base["eventos"] > 0
print(f"{len(base)} países na base; {base['teve_conflito'].sum()} com ao menos 1 evento "
      f"({ANO_INI}-{ANO_FIM}).")

# Traduções para os rótulos
ORDEM_RENDA = ["Low income", "Lower middle income", "Upper middle income", "High income"]
RENDA_PT = {"Low income": "Renda baixa", "Lower middle income": "Renda média-baixa",
            "Upper middle income": "Renda média-alta", "High income": "Renda alta"}
REGIAO_PT = {
    "East Asia & Pacific": "Leste Asiático e Pacífico",
    "Europe & Central Asia": "Europa e Ásia Central",
    "Latin America & Caribbean": "América Latina e Caribe",
    "Middle East & North Africa": "Oriente Médio e Norte da África",
    "North America": "América do Norte", "South Asia": "Sul da Ásia",
    "Sub-Saharan Africa": "África Subsaariana",
}
PAIS_PT = {"Iraq": "Iraque", "Ukraine": "Ucrânia", "Colombia": "Colômbia",
           "Nigeria": "Nigéria", "Pakistan": "Paquistão", "India": "Índia",
           "Philippines": "Filipinas", "Mexico": "México", "Russian Federation": "Rússia",
           "Turkiye": "Turquia", "Turkey": "Turquia", "Ethiopia": "Etiópia",
           "Sudan": "Sudão", "Congo, Dem. Rep.": "RD Congo", "Yemen, Rep.": "Iêmen",
           "Afghanistan": "Afeganistão", "Syrian Arab Republic": "Síria",
           "Algeria": "Argélia", "Angola": "Angola", "Uganda": "Uganda",
           "Burundi": "Burundi", "Somalia": "Somália", "Libya": "Líbia",
           "Egypt, Arab Rep.": "Egito", "Israel": "Israel", "Brazil": "Brasil",
           "Indonesia": "Indonésia", "Nepal": "Nepal", "Lebanon": "Líbano",
           "Myanmar": "Mianmar", "Rwanda": "Ruanda", "Georgia": "Geórgia", "Bosnia and Herzegovina": "Bósnia"}
nome = lambda p: PAIS_PT.get(p, p)
base["regiao_pt"] = base["regiao"].map(REGIAO_PT).fillna(base["regiao"])
base["renda_pt"] = base["renda"].map(RENDA_PT)

# ----------------------------------------------------------------------------
# TABELAS - Top 4 países por mortes e por quantidade de conflitos (eventos)
# ----------------------------------------------------------------------------
def montar_top(df, criterio, n=4):
    """Retorna as n primeiras linhas ordenadas pelo critério, com colunas renomeadas."""
    top = df.nlargest(n, criterio)[["pais", "mortes", "eventos"]].copy()
    top["pais"] = top["pais"].map(nome)
    top[["mortes", "eventos"]] = top[["mortes", "eventos"]].astype(int)
    top.columns = ["País", "Mortes totais", "Quantidade de conflitos"]
    return top.reset_index(drop=True)


def formatar_pt(df):
    """Versão para exibição, com separador de milhar em português (1.234)."""
    out = df.copy()
    for c in ["Mortes totais", "Quantidade de conflitos"]:
        out[c] = out[c].map(lambda v: f"{v:,}".replace(",", "."))
    return out


top_mortes = montar_top(base, "mortes")
top_eventos = montar_top(base, "eventos")

print(f"\nTop 4 países com mais mortes em conflitos ({ANO_INI}-{ANO_FIM})")
print(formatar_pt(top_mortes).to_string(index=False))
print(f"\nTop 4 países com maior quantidade de conflitos ({ANO_INI}-{ANO_FIM})")
print(formatar_pt(top_eventos).to_string(index=False))

top_mortes.to_csv(OUT_DIR / "top4_mortes.csv", index=False)
top_eventos.to_csv(OUT_DIR / "top4_conflitos.csv", index=False)

# Tabela de apoio (útil para o relatório)
base.sort_values("eventos", ascending=False).to_csv(OUT_DIR / "base_por_pais.csv", index=False)
print("Concluído.")