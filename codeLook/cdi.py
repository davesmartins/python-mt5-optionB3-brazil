import requests
from datetime import date, timedelta

# Definir a data de hoje e a data de ontem
hoje = date.today().strftime('%d/%m/%Y')
ontem = (date.today() - timedelta(days=30)).strftime('%d/%m/%Y')

# Definir a URL da API do Banco Central do Brasil
url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?dataInicial={ontem}&dataFinal={hoje}'

# Enviar a requisição para a API e obter os dados em formato JSON
r = requests.get(url)
dados = r.json()
print(dados)

# Obter o valor do CDI como o último valor da lista de dados
cdi = dados[-1]['valor']

# Imprimir o valor do CDI
print("Valor do CDI:", cdi)
