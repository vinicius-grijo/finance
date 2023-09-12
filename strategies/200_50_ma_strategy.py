import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf

def calculate_return( df, column_thr, column_var ):
    data = df.copy()

    column_variable = data[f'{column_var}']
    column_threshold = data[f'{column_thr}']

    # Definindo a posição
    data.loc[ column_variable >= column_threshold, 'Signal' ] = 1
    data.loc[ column_variable < column_threshold, 'Signal'] = -1

    # Definindo a ordem, com base na alteração da posição
    data['Order'] = data.Signal.diff()/2
    data['Order'] = data['Order'].fillna( data.Signal.iloc[0] )

    trades = data[ data.Order != 0 ].dropna()
    if len(trades) % 2 != 0:
        trades = trades[:-1]

    # Abertura de posição
    trades_start = trades.iloc[::2]

    # Fechamento de posição
    trades_end = trades.iloc[1::2]

    completed_trades = pd.DataFrame()
    # Calcule a diferença entre as linhas pares e ímpares, obtendo o saldo da negociação completa
    if trades.Order.iloc[0] > 0:
        completed_trades['Buy_price'] = trades_start.reset_index(drop=True).Close
        completed_trades['Sell_price'] = trades_end.reset_index(drop=True).Close
        completed_trades['Return'] = completed_trades.Sell_price - completed_trades.Buy_price
        position = 'Long'
    else:
        completed_trades['Sell_price'] = trades_start.reset_index(drop=True).Close
        completed_trades['Buy_price'] = trades_end.reset_index(drop=True).Close
        completed_trades['Return'] = completed_trades.Sell_price - completed_trades.Buy_price
        position = 'Short'

    completed_trades.index = completed_trades.index + 1
    completed_trades.index.name = 'n_operation'
    
    # profit = completed_trades.Return.sum()
    profit = f"{ np.round( completed_trades.Return.sum() / trades['Close'].iloc[0], 2)}%"

    info = { 'Profit': profit, 'Trades':completed_trades, 'Summary': completed_trades.Return.describe(), 'Position':position, 'Trades_full':trades }
    
    return info

def main():
    print(pd.__version__)
    ticker = 'PETR4.SA'
    print('Iniciando o download.')
    data = yf.download(ticker, start='2020-01-01', end='2023-01-01', progress=False)
    print('Download concluído.')

    # Calcule a média móvel dos 200 e dos 50 fechamentos anteriores
    data['200_MA'] = data['Close'].rolling(window=200).mean()
    data['50_MA'] = data['Close'].rolling(window=50).mean()
    data = data.dropna()

    # Aplica e analisa a estratégia
    r = calculate_return( df=data, column_thr='200_MA', column_var='50_MA')
    print()
    print(f"O retorno da estratégia 200_MA foi de { r['Profit'] }. ")
    print(f"O retorno de Buy and Hold seria de { np.round( (data['Close'].iloc[-1] - data['Close'].iloc[0])/data['Close'].iloc[0] ,2)}%.")
    print()
    print( r['Trades'].to_markdown() )
    print()

    # Cria um gráfico com os preços de fechamento e a média móvel
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data['Close'], label='Preço de Fechamento')
    plt.plot(data.index, data['200_MA'], label='Média Móvel de 200 Dias')
    plt.plot(data.index, data['50_MA'], label='Média Móvel de 50 Dias', color='red')
    plt.xlabel('Data')
    plt.ylabel('Preço')
    plt.title(f'Gráfico de Preço de Fechamento para {ticker}')
    plt.legend()
    plt.grid()
    plt.show()

if __name__=='__main__':
    main()