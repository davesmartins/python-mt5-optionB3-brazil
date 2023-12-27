
import requests
from datetime import date, timedelta

# Definir a data de hoje e a data de 12 meses atrás
hoje = date.today().strftime('%d/%m/%Y')
doze_meses_atras = (date.today() - timedelta(days=365)).strftime('%d/%m/%Y')

# Definir a URL da API do Banco Central do Brasil
url = f'https://api.bcb.gov.br/dados/serie/bcdata.sgs.4447/dados?dataInicial={doze_meses_atras}&dataFinal={hoje}'

# Enviar a requisição para a API e obter os dados em formato JSON
r = requests.get(url)
dados = r.json()

# Obter o valor do IPCA como o último valor da lista de dados
ipca = dados[-1]['valor']

# Imprimir o valor do IPCA
print("Valor do IPCA:", ipca)
