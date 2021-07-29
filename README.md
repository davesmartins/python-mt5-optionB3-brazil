## MetaTrader 5 Option Tick a Tick B3 Brazil

### O que é?

Esse é um projeto criado com o objetivo de utilizando a Api do Python do MetaTrader 5, para realizar a consulta dos valores de ASK,BID,Last e Volume. 
Esse projeto não contempla ainda pegar os valores históricos das opções.

1. Acessar um arquivo com todas as opções da B3
2. Filtrar os ativos compostos dentro do índice IBX100, pegando as opções que tem uma certa liquidez.
3. Usando **Asynchronous Execution** com **threads** usando **ThreadPoolExecutor** usando a Biblioteca do MetaTrader para pegar de **bid, ask, Last e Volume** das opções da lista filtrada.
4. Após percorrer toda a lista, é chamado uma função com os valores finais, e colocado em um banco de dados **PostGres** para serem as devidas analises.

O passo 3 em um servidor Xeon com 2 cpus, demora cerca de 15 segundos para realizar a consulta em todos os ativos. O passo 4 demora uma média de 2 segundos.

1. O processo fica em loop até o horário das 17:00, atualizando o banco de dados. Como o processo de update apaga a Table e cria uma nova, é necessário criar uma Function dentro do banco de dados para tratar esse detalhe.

### Como Usar?
1 . Instalar as dependencias do projeto:

```
    pip install -r requirements.txt
```
2. Atualizar a carteira do IBX 100 , baixando no link abaixo e ao finalizar o download excluir a primeira e as duas ultimas linhas do arquivo csv, essas colunas mostram a data do arquivo baixo, e  a quantidade teorica total
```
http://www.b3.com.br/pt_br/market-data-e-indices/indices/indices-amplos/indice-brasil-100-ibrx-100-composicao-da-carteira.htm
```
3. Atualizar a grade de opções listadas na B3, baixando atraves do link abaixo. E antes de usar, apagar a primeira linha do arquivo.
```
http://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/consultas/mercado-a-vista/opcoes/series-autorizadas/
```
4. rodar o script atraves do comando.
```
    python mt5-option.py
```

### Proximos passos do projeto

1. Fazer um webscrapping para que as series autorizadas e a composiçāo da carteira do IBX100, sejam atualizadas automaticamente.
2. Achar uma maneira perfomatica para puxar também os dados historicos e adicionar no banco de dados.
3. Criar um conteiner docker com wine+python, para rodar o MT5 num server linux sem dificuldades.
