"""
Economia, desenvolvimento humano e conflitos armados (1990-2018)
Gera 5 gráficos usando pandas, numpy, matplotlib, seaborn e cartopy.

Estrutura esperada do projeto:
    raiz/
    ├── src/analise_conflitos.py      <- este arquivo
    └── data/                         <- GEDEvent_v26_1.xlsx, WorldBank.xlsx, HDI.csv

Uso (a partir da raiz):  python src/analise_conflitos.py
Os PNGs são salvos em ./images (pasta atual de execução).
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
OUT_DIR = Path("images")
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
           "Myanmar": "Mianmar", "Georgia": "Geórgia", "Bosnia and Herzegovina": "Bósnia"}
nome = lambda p: PAIS_PT.get(p, p)
base["regiao_pt"] = base["regiao"].map(REGIAO_PT).fillna(base["regiao"])
base["renda_pt"] = base["renda"].map(RENDA_PT)


def salvar(fig, arquivo):
    fig.savefig(OUT_DIR / arquivo, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("salvo:", OUT_DIR / arquivo)


# ----------------------------------------------------------------------------
# GRÁFICO 1 - Dispersão: PIB per capita x nº de eventos (matplotlib + numpy)
# ----------------------------------------------------------------------------
d = base.dropna(subset=["pib_pc"]).copy()
rho = d[["pib_pc", "eventos"]].corr(method="spearman").iloc[0, 1]

fig, ax = plt.subplots(figsize=(12, 7.5))
paleta = dict(zip(sorted(d["regiao_pt"].unique()), sns.color_palette("tab10", d["regiao_pt"].nunique())))
for reg, sub in d.groupby("regiao_pt"):
    tamanho = 25 + 700 * np.sqrt(sub["mortes"] / d["mortes"].max())
    ax.scatter(sub["pib_pc"], sub["eventos"] + 1, s=tamanho, color=paleta[reg],
               alpha=0.65, edgecolor="white", linewidth=0.6, label=reg)
ax.set_xscale("log"); ax.set_yscale("log")
for _, r in d.nlargest(10, "eventos").iterrows():
    ax.annotate(nome(r["pais"]), (r["pib_pc"], r["eventos"] + 1), xytext=(6, 5),
                textcoords="offset points", fontsize=9)
ax.set_xlabel("PIB per capita médio, 1990-2018 (US$, escala log)")
ax.set_ylabel("Nº de eventos de conflito + 1 (escala log)")
ax.set_title("Países mais pobres concentram mais conflitos?\n"
             "PIB per capita × eventos de conflito (tamanho da bolha = mortes totais)",
             fontsize=14, fontweight="bold", loc="left")
ax.text(0.015, 0.04, f"Correlação de Spearman (ρ) = {rho:.2f}\nn = {len(d)} países",
        transform=ax.transAxes, fontsize=11, bbox=dict(boxstyle="round", fc="white", ec="grey"))
leg = ax.legend(title="Região", loc="upper right", fontsize=9, markerscale=0.6, frameon=True)
for h in leg.legend_handles: h.set_sizes([60])
fig.text(0.01, -0.01, "Fontes: UCDP GED v26.1; Banco Mundial. Países sem conflito aparecem com 0 eventos (y = 1).",
         fontsize=8, color="grey")
salvar(fig, "g1_dispersao_pib_eventos.png")

# ----------------------------------------------------------------------------
# GRÁFICO 2 - Boxplot por grupo de renda (seaborn)
# ----------------------------------------------------------------------------
d = base.copy()
d["log_eventos"] = np.log10(d["eventos"] + 1)
ordem_pt = [RENDA_PT[o] for o in ORDEM_RENDA]
resumo = d.groupby("renda_pt").agg(n=("iso3", "size"), pct=("teve_conflito", "mean"))
rotulos = [f"{g}\n(n={int(resumo.loc[g, 'n'])}; {resumo.loc[g, 'pct']*100:.0f}% com conflito)" for g in ordem_pt]

fig, ax = plt.subplots(figsize=(11, 7))
cores_box = dict(zip(ordem_pt, ["#bd0026", "#f03b20", "#fd8d3c", "#fecc5c"]))  # renda baixa = mais escuro
sns.boxplot(data=d, x="renda_pt", y="log_eventos", order=ordem_pt, hue="renda_pt",
            hue_order=ordem_pt, palette=cores_box, legend=False, showfliers=False, width=0.55, ax=ax)
sns.stripplot(data=d, x="renda_pt", y="log_eventos", order=ordem_pt, color="black",
              alpha=0.35, size=3.5, jitter=0.22, ax=ax)
ax.set_xticks(range(4)); ax.set_xticklabels(rotulos)
ax.set_yticks([0, 1, 2, 3, 4]); ax.set_yticklabels(["0", "~10", "~100", "~1.000", "~10.000"])
ax.set_xlabel(""); ax.set_ylabel("Nº de eventos por país, 1990-2018 (escala log)")
ax.set_title("Distribuição de eventos de conflito por grupo de renda",
             fontsize=14, fontweight="bold", loc="left")
fig.text(0.01, -0.01, "Cada ponto é um país. Fontes: UCDP GED v26.1; Banco Mundial (grupos de renda).",
         fontsize=8, color="grey")
salvar(fig, "g2_boxplot_renda.png")

# ----------------------------------------------------------------------------
# GRÁFICO 3 - Mapa de calor de correlação de Spearman (seaborn)
# ----------------------------------------------------------------------------
ROTULOS = {"eventos": "Nº de eventos", "mortes": "Mortes totais", "pib_pc": "PIB per capita",
           "idh": "IDH", "expec_vida": "Expectativa de vida", "mort_infantil": "Mortalidade infantil",
           "internet": "Uso de internet (%)", "energia": "Consumo de energia",
           "desemprego": "Desemprego (%)", "dens_pop": "Densidade populacional"}
corr = base[list(ROTULOS)].corr(method="spearman").rename(index=ROTULOS, columns=ROTULOS)
mascara = np.triu(np.ones_like(corr, dtype=bool), k=1)

fig, ax = plt.subplots(figsize=(11, 8.5))
sns.heatmap(corr, mask=mascara, annot=True, fmt=".2f", cmap="RdBu_r", vmin=-1, vmax=1,
            center=0, square=True, linewidths=0.5, cbar_kws={"label": "ρ de Spearman", "shrink": 0.8}, ax=ax)
ax.set_title("Correlação entre conflitos e indicadores econômicos e sociais\n(médias 1990-2018, por país)",
             fontsize=14, fontweight="bold", loc="left")
plt.setp(ax.get_xticklabels(), rotation=40, ha="right")
ax.grid(False)
fig.text(0.01, -0.12, "Correlação não implica causalidade. Fontes: UCDP GED v26.1; Banco Mundial; PNUD (IDH).",
         fontsize=8, color="grey")
salvar(fig, "g3_heatmap_correlacao.png")

# ----------------------------------------------------------------------------
# GRÁFICO 4 - Séries temporais: eventos x PIB per capita em países-chave
# ----------------------------------------------------------------------------
anos = np.arange(ANO_INI, ANO_FIM + 1)
pib_ano = wb.pivot(index="ano", columns="iso3", values="pib_pc").reindex(anos)
ev_ano = ged.groupby(["iso3", "year"]).size().unstack(fill_value=0).reindex(columns=anos, fill_value=0)

# 6 países com mais eventos que tenham >= 20 anos de PIB per capita
validos = pib_ano.columns[pib_ano.notna().sum() >= 20]
top = ev[ev["iso3"].isin(validos)].nlargest(6, "eventos")["iso3"].tolist()
nomes = base.set_index("iso3")["pais"]

fig, axs = plt.subplots(2, 3, figsize=(15, 8), sharex=True)
for ax, iso in zip(axs.ravel(), top):
    ax.bar(anos, ev_ano.loc[iso], color="#d6604d", alpha=0.75, label="Eventos de conflito")
    ax.set_ylabel("Eventos", color="#b2182b")
    ax2 = ax.twinx()
    ax2.plot(anos, pib_ano[iso], color="#2166ac", linewidth=2.2, marker="o", markersize=3,
             label="PIB per capita")
    ax2.set_ylabel("PIB per capita (US$)", color="#2166ac")
    ax2.grid(False)
    ax.set_title(nome(nomes[iso]), fontsize=12, fontweight="bold")
fig.suptitle("Conflito e economia ao longo do tempo: eventos anuais × PIB per capita",
             fontsize=15, fontweight="bold", x=0.01, ha="left")
h1 = plt.Rectangle((0, 0), 1, 1, color="#d6604d", alpha=0.75)
h2 = plt.Line2D([0], [0], color="#2166ac", linewidth=2.2)
fig.legend([h1, h2], ["Eventos de conflito (UCDP GED)", "PIB per capita (Banco Mundial)"],
           loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(rect=(0, 0.03, 1, 0.95))
salvar(fig, "g4_series_temporais.png")

# ----------------------------------------------------------------------------
# GRÁFICO 5 - Mapa (cartopy): localização dos eventos por grupo de renda
# ----------------------------------------------------------------------------
pts = ged.merge(base[["iso3", "renda"]], on="iso3", how="left")
pts = pts.dropna(subset=["latitude", "longitude"])
CORES = {"Low income": "#b2182b", "Lower middle income": "#ef8a62",
         "Upper middle income": "#67a9cf", "High income": "#2166ac"}

if TEM_CARTOPY:
    fig = plt.figure(figsize=(15, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_extent([-125, 155, -38, 60], crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.OCEAN, facecolor="#e8f1f8")
    ax.add_feature(cfeature.LAND, facecolor="#f4f1ea")
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, edgecolor="grey")
    ax.add_feature(cfeature.COASTLINE, linewidth=0.4)
    kw = dict(transform=ccrs.PlateCarree())
else:
    fig, ax = plt.subplots(figsize=(15, 8))
    ax.set_xlim(-125, 155); ax.set_ylim(-38, 60); ax.set_aspect("equal")
    kw = {}

# renda alta por último (menos eventos), para não esconder os pontos de renda baixa
for g in ["High income", "Upper middle income", "Lower middle income", "Low income"]:
    s = pts[pts["renda"] == g]
    ax.scatter(s["longitude"], s["latitude"], s=3, color=CORES[g], alpha=0.35,
               linewidths=0, zorder=3, **kw)
sem = pts[pts["renda"].isna()]
ax.scatter(sem["longitude"], sem["latitude"], s=3, color="grey", alpha=0.35,
           linewidths=0, zorder=3, **kw)

handles = [plt.Line2D([0], [0], marker="o", ls="", color=CORES[g], markersize=8, label=RENDA_PT[g])
           for g in ORDEM_RENDA]
handles.append(plt.Line2D([0], [0], marker="o", ls="", color="grey", markersize=8, label="Sem classificação"))
ax.legend(handles=handles, title="Grupo de renda do país", loc="lower left", frameon=True)
n_pts = f"{len(pts):,}".replace(",", ".")
ax.set_title(f"Onde ocorrem os conflitos? Eventos violentos georreferenciados, {ANO_INI}-{ANO_FIM} "
             f"({n_pts} eventos)", fontsize=14, fontweight="bold", loc="left")
fig.text(0.01, 0.04, "Fontes: UCDP GED v26.1; Banco Mundial. Cada ponto é um evento.",
         fontsize=8, color="grey")
salvar(fig, "g5_mapa_eventos.png")

# Tabela de apoio (útil para o relatório)
base.sort_values("eventos", ascending=False).to_csv(OUT_DIR / "base_por_pais.csv", index=False)
print("Concluído.")