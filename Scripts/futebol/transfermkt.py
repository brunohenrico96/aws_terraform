import sys
import requests
import pandas as pd
import awswrangler as wr
from bs4 import BeautifulSoup
from awsglue.utils import getResolvedOptions

# 1. O Glue intercepta os parâmetros passados no Terraform
args = getResolvedOptions(sys.argv, ['selecao_id', 'database_name', 'output_bucket'])

id_da_selecao = args['selecao_id']
db_catalogo = args['database_name']
bucket_destino = args['output_bucket']

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

jogadores = []

# 2. Loop para iterar nas 5 páginas solicitadas
for pagina in range(1, 6):
    # URL dinâmica baseada no Terraform e na página do loop
    url = f"https://www.transfermarkt.com.br/brasilien/kader/verein/{id_da_selecao}/saison_id/2023/plus/1?page={pagina}"
    resposta = requests.get(url, headers=headers)

    sopa = BeautifulSoup(resposta.content, 'html.parser')

    # 3. Encontra a tabela principal
    tabela = sopa.find("table", class_="items")

    # Se a tabela não existir (ex: página vazia), interrompe o loop
    if not tabela:
        break

    # 4. Encontra todas as linhas de jogadores (classes odd e even)
    linhas = tabela.find("tbody").find_all("tr", class_=["odd", "even"])

    for linha in linhas:
        colunas = linha.find_all("td")

        # Extração defensiva: tenta buscar o texto, se falhar, retorna None
        try:
            # O nome geralmente fica dentro de uma tag <a> na classe 'hauptlink'
            nome = linha.find("td", class_="hauptlink").text.strip()

            # A idade e clube ficam em colunas centralizadas 'zentriert'
            idade = colunas[2].text.strip()

            # O clube atual geralmente é o atributo 'alt' da imagem do clube
            clube_img = colunas[3].find("img")
            clube = clube_img["alt"] if clube_img else "Sem clube"

            # O valor de mercado fica na coluna 'rechts hauptlink'
            valor_mercado = linha.find("td", class_="rechts hauptlink").text.strip()

            jogadores.append({
                "Nome": nome,
                "Idade": idade,
                "Clube_Atual": clube,
                "Valor_Mercado": valor_mercado
            })
        except Exception:
            # Ignora linhas que não sejam estruturadas como jogadores
            continue

# 5. Transformação: Converte a lista de dicionários para um DataFrame do Pandas
df_jogadores = pd.DataFrame(jogadores)

# 6. Carregamento: Salva no S3 e CRIA a tabela no Athena automaticamente ☁️
if not df_jogadores.empty:
    wr.s3.to_parquet(
        df=df_jogadores,
        path=f"s3://{bucket_destino}/jogadores/",
        dataset=True,
        database=db_catalogo,
        table="jogadores_selecao",
        mode="overwrite"  # Sobrescreve os dados a cada execução
    )
