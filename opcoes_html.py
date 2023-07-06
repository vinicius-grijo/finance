# -*- coding: utf-8 -*-
"""opcoes_html.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1eoVf9lYVjToIC1BAHabIv6W-bQwRAB2q

# Libraries
"""

pip install scienceplots

import pandas as pd
import numpy as np
from scipy.stats import norm
from datetime import datetime
import matplotlib.pyplot as plt
import yfinance as yf
from datetime import datetime, timedelta
import scienceplots

plt.style.use([ 'notebook', 'grid','bright'])

"""# Analysing the Stock"""

petr4 = yf.download("PETR4.SA", start="2021-06-16", end='2023-06-17', progress=False)
petr4

plt.figure(figsize=(18,6))
plt.plot( petr4.index, petr4.Close )
plt.xlabel('Time')
plt.ylabel('Stock Price')
plt.title('Stock Price as a Function of Time')
plt.show();

def historical_volatility( stock_series, start_date_str = '2022-06-16', end_date_str='2023-06-16', days=365 ):
  date = datetime.strptime(start_date_str, '%Y-%m-%d')
  end_date = datetime.strptime(end_date_str,'%Y-%m-%d')
  volatility={}
  while date <= end_date:
    year_hist = stock_series.loc[date - timedelta(days=days): date,]
    sample = np.log(year_hist).diff(periods=1).dropna()
    volatility[ f'{date}' ] = sample.std()*np.sqrt(252)
    date += timedelta(days=1)
  volatility_series = pd.Series( volatility )
  volatility_series.index = pd.to_datetime( volatility_series.index )
  return volatility_series

petr4['Volatility'] = historical_volatility( petr4.Close, days=365 )
petr4 = petr4[ petr4.Volatility > 0 ]
petr4 = petr4[ ['Close', 'Volatility'] ]
petr4

plt.figure(figsize=(18,6))
plt.plot( petr4.index, petr4.Volatility)
plt.xlabel('Time')
plt.ylabel('Historical Volatility')
plt.title('Historical Volatility as a Function of Time')
plt.show();

"""# Analysing the Option

## HTML
"""

df = pd.read_html('https://opcoes.net.br/PETRF463')[0]
df

"""## CSV"""

# df = pd.read_csv('PETRF463.csv', header=[0,1], index_col=0)
# df

"""## Cleaning the Data"""

strike = 25.18
maturity = datetime.strptime( '16/06/2023', '%d/%m/%Y')

date = df.iloc[0:-2].loc[:, 'Unnamed: 0_level_0'].rename( columns={ 'Unnamed: 0_level_1' : 'Date' } )
date['Date'] = pd.to_datetime(date['Date'], format= '%d/%m/%Y')
option = df.iloc[0:-2].loc[:,'PETRF463 - Cotação não ajustada'].rename( columns={ 'Min':'Min', 'Pri':'Open', 'Med':'Mean', 'Ult':'Close',  'Max':'Max', 'Negócios':'Vol', 'Vol. Fin.':'Fin_Vol'} )
option.loc[:,['Min','Open','Mean','Close','Max']] = option.loc[:,['Min','Open','Mean','Close','Max']]*0.01
option.index = date.Date
imp_vol = df.iloc[0:-2].loc[:,'PETRF463 - Volatilidade implícita'].rename( columns={ 'Min':'Min', 'Pri':'Open', 'Med':'Mean', 'Ult':'Close',  'Max':'Max'} )
imp_vol = imp_vol*0.0001
imp_vol.index = date.Date
imp_vol = imp_vol[ imp_vol.index < maturity ]
stock = df.iloc[0:-2].loc[:, 'PETR4 - Cotação não ajustada'].rename( columns={ 'Min':'Min', 'Abe':'Open', 'Med':'Mean', 'Ult':'Close',  'Max':'Max'} )
stock = stock*0.01
stock.index=date.Date

print(option)
print()
print(imp_vol)
print()
print(stock)

"""## Black-Scholes Function"""

def BS( strike, stock, volatility, maturity, r=0.1375, increment_days=0):

  first_day = maturity - timedelta(days=365)
  first_day_to_maturity = np.busday_count( first_day.date(), maturity.date() )

  # present_date = datetime.strptime( str(stock.index.date[0]), '%Y-%m-%d')
  # present_to_maturity = np.busday_count( present_date.date(), maturity.date() )

  pre_time = []
  for indice in stock.index:
    present_date = datetime.strptime( str(indice.date() ), '%Y-%m-%d')
    present_to_maturity = np.busday_count( present_date.date()+timedelta(days=increment_days), maturity.date() )
    pre_time += [
      {f'Date': indice,
    'present_to_maturity': present_to_maturity,
      }
      ]

  time = pd.DataFrame(pre_time)
  time.set_index('Date',inplace=True)
  time.index = pd.DatetimeIndex(time.index)

  time['time_left'] = time.present_to_maturity/first_day_to_maturity

  d_1 = ( np.log( stock/strike ) + (r + (volatility**2)/2)*( time.time_left ) )/( volatility*np.sqrt( time.time_left ) )
  d_2 = d_1 - volatility*np.sqrt( time.time_left )
  price = norm.cdf( d_1 )*stock - norm.cdf( d_2 )*strike*np.exp( -r*time.time_left )

  return price

option = pd.DataFrame(option.Close)
option['Implied_volatility'] = imp_vol.Close
BS_price = pd.DataFrame( BS(strike=strike, stock=petr4.Close, volatility=petr4.Volatility, maturity=maturity), columns=['BS_price'] ).dropna()
option = pd.concat( [BS_price, option], axis=1 ).fillna(method='ffill')
option['Strike'] = strike
option['Maturity'] = maturity
option

"""# Analysing the Greeks

## Delta and Gamma
"""

date = '2023-06-12'

pre_df_delta = []
for stock_price in np.arange(0.01, 2*strike, 0.01):
  dic={}
  reduced_petr4 = petr4[ petr4.index== date ].copy()
  reduced_petr4['Stock_price'] = stock_price
  option_price = BS( strike=strike, stock=reduced_petr4.Stock_price, volatility=reduced_petr4.Volatility, maturity=maturity )
  dic['Stock_price'] = stock_price
  dic['Option_price'] = option_price.values[0]
  pre_df_delta.append( dic )

df_delta = pd.DataFrame( pre_df_delta )
df_delta['Date'] = reduced_petr4.index.values[0]
df_delta.set_index( "Date", inplace=True)

df_delta['Diff_stock_price'] = df_delta.Stock_price.diff()
df_delta['Diff_option_price'] = df_delta.Option_price.diff()
df_delta['Delta'] = df_delta.Diff_option_price/df_delta.Diff_stock_price
df_delta['Delta_whole'] = 100*df_delta.Delta

df_delta['Diff_delta'] = df_delta.Delta.diff()
df_delta['Gamma'] = df_delta.Delta.diff()/df_delta.Diff_stock_price

plt.figure(figsize=(18,6))
plt.plot( df_delta.Stock_price, df_delta.Option_price)
plt.xlabel('Stock Price')
plt.ylabel('Option Price')
plt.title("Option's Theoretical Price as a Function of the Stock Price")
plt.show()

plt.figure(figsize=(18,6))
plt.plot( df_delta.Stock_price, df_delta.Delta_whole )
plt.xlabel('Stock Price')
plt.ylabel('Delta')
plt.title('Delta as a Function of the Stock Price')
plt.show()

plt.figure(figsize=(18,6))
plt.plot( df_delta.Stock_price, df_delta.Gamma )
plt.xlabel('Stock Price')
plt.ylabel('Gamma')
plt.title('Gamma as a Function of the Stock Price')
plt.show()

df_delta[ (25 < df_delta.Stock_price) & (df_delta.Stock_price < 26) ]

"""## Vega"""

date= '2023-06-12'

pre_df_vega = []
for volatility in np.arange(0, 2.01, 0.01):
  dic={}
  reduced_petr4 = petr4[ petr4.index== date ].copy()
  reduced_petr4['Volatility'] = volatility
  option_price = BS( strike=strike, stock=reduced_petr4.Close, volatility=reduced_petr4.Volatility, maturity=maturity )
  dic['Volatility'] = volatility
  dic['Option_price'] = option_price.values[0]
  pre_df_vega.append( dic )

df_vega = pd.DataFrame( pre_df_vega )
df_vega['Date'] = reduced_petr4.index.values[0]
df_vega.set_index('Date', inplace=True)

df_vega['Diff_volatility'] = df_vega.Volatility.diff()
df_vega['Diff_option_price'] = df_vega.Option_price.diff()
df_vega['Vega'] = df_vega.Diff_option_price/df_vega.Diff_volatility

plt.figure(figsize=(18,6))
plt.plot( df_vega.Volatility, df_vega.Option_price)
plt.xlabel('Volatility')
plt.ylabel('Stock Price')
plt.title("Option's Theoretical Price as a Function of Volatility ")
plt.show()

plt.figure(figsize=(18,6))
plt.plot( df_vega.Volatility, df_vega.Vega )
plt.xlabel('Volatility')
plt.ylabel('Vega')
plt.title('Vega as a Function of Volatility')
plt.show()

df_vega

"""## Theta"""

date= '2023-05-15'

pre_df_theta = []
#for day in range( (maturity - petr4.index[-5] ).days ):
for day in range( (maturity - petr4[ petr4.index == date ].index[0] ).days ):
  dic={}
  reduced_petr4 = petr4[ petr4.index== date ].copy()
  reduced_petr4.index = reduced_petr4.index + timedelta(day)
  option_price = BS( strike=strike, stock=reduced_petr4.Close, volatility=reduced_petr4.Volatility, maturity=maturity )
  dic['Date'] = reduced_petr4.index.values[0]
  dic['Option_price'] = option_price.values[0]
  pre_df_theta.append( dic )

df_theta = pd.DataFrame( pre_df_theta )
df_theta.set_index('Date', inplace=True )

df_theta['Stock_price'] = reduced_petr4.Close.values[0]
df_theta['Diff_option_price'] = df_theta.Option_price.diff()
df_theta['Theta'] = df_theta.Diff_option_price

plt.figure(figsize=(18,6))
plt.plot( df_theta.index, df_theta.Option_price)
plt.xlabel('Time')
plt.ylabel('Option Price')
plt.title("Option's Theoretical Price as Maturity Approaches")
plt.show()

plt.figure(figsize=(18,6))
plt.plot( df_theta.index, df_theta.Theta )
plt.xlabel('Time')
plt.ylabel('Theta')
plt.title('Theta')
plt.show()

df_theta

"""## Rho"""

date = '2023-06-12'

pre_df_rho = []
for interest_rate in np.arange(0, 1, 0.001):
  dic={}
  reduced_petr4 = petr4[ petr4.index== date ].copy()
  reduced_petr4['Interest_rate'] = interest_rate
  option_price = BS( strike=strike, stock=reduced_petr4.Close, volatility=reduced_petr4.Volatility, maturity=maturity, r = interest_rate )
  dic['Interest_rate'] = reduced_petr4.Interest_rate.values[0]
  dic['Option_price'] = option_price.values[0]
  pre_df_rho.append( dic )

df_rho = pd.DataFrame( pre_df_rho )
df_rho['Date'] = reduced_petr4.index.values[0]
df_rho.index = df_rho.Date

df_rho['Diff_option_price'] = df_rho.Option_price.diff()
df_rho['Diff_interest_rate'] = df_rho.Interest_rate.diff()
df_rho['Rho'] = df_rho.Diff_option_price/df_rho.Diff_interest_rate

plt.figure(figsize=(18,6))
plt.plot( df_rho.Interest_rate, df_rho.Option_price)
plt.xlabel('Interest Rate')
plt.ylabel('Option Price')
plt.title("Option's Theoretical Price as a Function of the Interest Rate")
plt.show()

plt.figure(figsize=(18,6))
plt.plot( df_rho.Interest_rate, df_rho.Rho )
plt.xlabel('Interest Rate')
plt.ylabel('Rho')
plt.title('Rho as a Function of the Interest Rate')
plt.show()

df_rho

"""# The End"""

imp_vol

petr4_final_df = petr4.copy()
petr4_final_df['Close'] = np.round(petr4_final_df.Close, decimals=2)
petr4_final_df['Volatility'] = np.round(petr4_final_df.Volatility, decimals=4)



option['Delta'] = np.round(
                          ( BS( strike, petr4_final_df.Close+0.01, petr4_final_df.Volatility, maturity=maturity )
                          - BS( strike, petr4_final_df.Close, petr4_final_df.Volatility, maturity=maturity ) )/0.01,
                          decimals=2)

option['Gamma'] = np.round(
                          ( BS( strike, petr4_final_df.Close+0.02, petr4_final_df.Volatility, maturity=maturity )
                          - 2*BS( strike, petr4_final_df.Close+0.01, petr4_final_df.Volatility, maturity=maturity )
                          + BS( strike, petr4_final_df.Close, petr4_final_df.Volatility, maturity=maturity ) )/( 0.01**2 ),
                          decimals=2)

option['Vega'] = np.round(
                        ( BS( strike, petr4_final_df.Close, petr4_final_df.Volatility+0.0001, maturity=maturity )
                        - BS( strike, petr4_final_df.Close, petr4_final_df.Volatility, maturity=maturity ) )/0.0001,
                        decimals=4)

option['Theta'] = np.round(
                        ( BS( strike, petr4_final_df.Close, petr4_final_df.Volatility, maturity=maturity, increment_days=1)
                        - BS( strike, petr4_final_df.Close, petr4_final_df.Volatility, maturity=maturity ) ),
                        decimals=2)

option['Rho'] = np.round(
                        ( BS( strike, petr4_final_df.Close, petr4_final_df.Volatility, maturity=maturity, r=0.1375+0.0001)
                        - BS( strike, petr4_final_df.Close, petr4_final_df.Volatility, maturity=maturity ) )/0.0001,
                        decimals=2)

petr4_final_df = pd.concat( {'PETR4':petr4_final_df}, axis=1, names=['TICKER', "Metrics"])
petr4_final_df

option_final_df = pd.concat({"PETRF463": option}, axis=1, names=["TICKER", "Metrics"])
option_final_df

final_df = pd.concat( [petr4_final_df, option_final_df], axis=1 )
final_df = final_df[::-1]
final_df

final_df.to_csv('PETRF463_BS.csv')

plt.figure(figsize=(18,6))
plt.plot( final_df.index, final_df.PETRF463.BS_price, label='Theoretical Price')
plt.plot( final_df.index, final_df.PETRF463.Close, label='Market Price')
plt.xlabel('Time')
plt.ylabel('Option Prices')
plt.title("Theorical Price Against Market Price")
plt.legend()
plt.show();