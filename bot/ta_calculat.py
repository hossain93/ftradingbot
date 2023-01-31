import pandas as pd
import numpy as np
import os
import talib as ta
from ohlcv import ohlcvs
import asyncio
import nest_asyncio
import threading
abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)

class calculate_ta():

        def __init__(self,df):
            self.data_pairs=df
            self.ADX_positions  =  pd.DataFrame(index=df.index,columns = ['trending_bullish','trending_bearish',
                                                             'best_positions','non_trending'])
            self.WMA_positions  =  pd.DataFrame(index=df.index,columns = ['WMA20_BUY','WMA20_SELL','WMA60_BUY',
                                                                 'WMA60_SELL','WMA100_BUY','WMA100_SELL','WMA200_BUY','WMA200_SELL'])

            self.MACD_positions =  pd.DataFrame(index=df.index,columns = ['trending_bearish_weak_BUY','trending_bullish_weak_SELL',
                                'trending_bearish_strong_SELL','trending_bullish_strong_BUY','cross_signal_BUY','cross_signal_SELL'])

            self.RSI_positions  =  pd.DataFrame(index=df.index,columns = ['cross_overbought_SELL','cross_oversold_BUY'])
            self.BB_positions   =  pd.DataFrame(index=df.index,columns = ['BB_BUY','BB_SELL'])
            self.OBV_positions  =  pd.DataFrame(index=df.index,columns = ['OBV_BUY','OBV_SELL'])
            
        def ADX(self):
                global pos
                self.data_pairs['ADX'] = ta.ADX(self.data_pairs['high'], self.data_pairs['low'], self.data_pairs['close'], timeperiod=14)
                DIplus = ta.PLUS_DI(self.data_pairs['high'], self.data_pairs['low'], self.data_pairs['close'], timeperiod=14)
                DIminus=ta.MINUS_DI(self.data_pairs['high'], self.data_pairs['low'], self.data_pairs['close'], timeperiod=14)

        #positions

                self.ADX_positions['trending_bullish'] = (self.data_pairs['ADX']>20) \
            & (DIplus > DIminus)
            
                self.ADX_positions['trending_bearish']  = (self.data_pairs['ADX']>20) \
                & (DIplus < DIminus)
                
                self.ADX_positions['best_positions']  = (self.data_pairs['ADX']>25) \
                & (self.data_pairs['ADX'] < DIplus) \
                & (self.data_pairs['ADX']>= DIminus) \
                | (self.data_pairs['ADX']>25)\
                & (self.data_pairs['ADX'] > DIplus) \
                & (self.data_pairs['ADX'] < DIminus)
                
                self.ADX_positions['non_trending']  = self.data_pairs['ADX']<20
                pos.at['adx','data']=self.ADX_positions
                return 

                #---------------------------------------------------------------------------------------------------------------------#

        def WMA(self):
            global pos
            WMA=pd.DataFrame()
            WMA20 = ta.WMA(self.data_pairs['close'], timeperiod=20)
            WMA60 = ta.WMA(self.data_pairs['close'], timeperiod=60)
            WMA100 = ta.WMA(self.data_pairs['close'], timeperiod=100)
            WMA200 = ta.WMA(self.data_pairs['close'], timeperiod=200)


    #positions

    # WMA20
            self.WMA_positions['WMA20_BUY'] =  (self.data_pairs['close'] > WMA20) & (self.data_pairs['close'].shift(1) <= WMA20)
            self.WMA_positions['WMA20_SELL'] = (self.data_pairs['close'] < WMA20) & (self.data_pairs['close'].shift(1) >= WMA20)

    # WMA60
            self.WMA_positions['WMA60_BUY'] =  (self.data_pairs['close'] > WMA60) & (self.data_pairs['close'].shift(1) <= WMA60)
            self.WMA_positions['WMA60_SELL'] = (self.data_pairs['close'] < WMA60) & (self.data_pairs['close'].shift(1) >= WMA60)

    # WMA100
            self.WMA_positions['WMA100_BUY'] =  (self.data_pairs['close'] > WMA100) & (self.data_pairs['close'].shift(1) <= WMA100)
            self.WMA_positions['WMA100_SELL'] = (self.data_pairs['close'] < WMA100) & (self.data_pairs['close'].shift(1) >= WMA100)

    # WMA200
            self.WMA_positions['WMA200_BUY'] =  (self.data_pairs['close'] > WMA200) & (self.data_pairs['close'].shift(1) <= WMA200)
            self.WMA_positions['WMA200_SELL'] = (self.data_pairs['close'] < WMA200) & (self.data_pairs['close'].shift(1) >= WMA200)
            for j in self.WMA_positions.columns:
                if j.split('_')[-1]=='SELL':
                    for i in range(len(self.WMA_positions)):
                        if self.WMA_positions.loc[i,j]==True:
                            self.WMA_positions.loc[i,j]=2
                elif j.split('_')[-1]=='BUY':
                    for i in range(len(self.WMA_positions)):
                        if self.WMA_positions.loc[i,j]==True:
                            self.WMA_positions.loc[i,j]=1
            pos.at['wma','data']=self.WMA_positions
            return 

            #---------------------------------------------------------------------------------------------------------------------#
            #MACD   

        def MACD(self):
            global pos
            EMA12 = ta.EMA(self.data_pairs['close'], timeperiod=12)
            EMA26 = ta.EMA(self.data_pairs['close'], timeperiod=26)
            macd, signal, histogram = ta.MACD(self.data_pairs['close'].values, fastperiod=12, slowperiod=26, signalperiod=9)

            macd = pd.DataFrame(macd)
            signal = pd.DataFrame(signal)
            histogram = pd.DataFrame(histogram)

    #positions

    #weak signal BUY and sell
            self.MACD_positions['trending_bearish_weak_BUY'] =  (macd > signal) & (macd.shift(1) <= signal)&(macd <= 0)
            self.MACD_positions['trending_bullish_weak_SELL'] = (macd < signal) & (macd.shift(1) >= signal)&(macd >= 0)

    #strong signal BUY and sell
            self.MACD_positions['trending_bearish_strong_SELL'] =  (macd < signal) & (macd.shift(1) >= signal)&(macd <= 0)
            self.MACD_positions['trending_bullish_strong_BUY'] = (macd > signal) & (macd.shift(1) <= signal)&(macd >= 0)


    #cross with zero line
            self.MACD_positions['cross_signal_BUY'] = (signal > 0) & (signal.shift(1) <= 0) #| (signal<=signal.shift()*0.05)
            self.MACD_positions['cross_signal_SELL'] = (signal < 0) & (signal.shift(1) >= 0)
            for j in self.MACD_positions.columns:
                if j.split('_')[-1]=='SELL':
                    for i in range(len(self.MACD_positions)):
                        if self.MACD_positions.loc[i,j]==True:
                            self.MACD_positions.loc[i,j]=2
                elif j.split('_')[-1]=='BUY':
                    for i in range(len(self.MACD_positions)):
                        if self.MACD_positions.loc[i,j]==True:
                            self.MACD_positions.loc[i,j]=1
            pos.at['macd','data']=self.MACD_positions
            return  

                #---------------------------------------------------------------------------------------------------------------------#

        def RSI(self):
            global pos
            RSI = ta.RSI(self.data_pairs['close'], timeperiod=14)

    #positions

            self.RSI_positions['cross_overbought_SELL'] = (RSI < 75) & (RSI.shift(1) >= 75)
            self.RSI_positions['cross_oversold_BUY'] =   (RSI > 30) & (RSI.shift(1) <= 30)
            for j in self.RSI_positions.columns:
                if j.split('_')[-1]=='SELL':
                    for i in range(len(self.RSI_positions)):
                        if self.RSI_positions.loc[i,j]==True:
                            self.RSI_positions.loc[i,j]=2
                elif j.split('_')[-1]=='BUY':
                    for i in range(len(self.RSI_positions)):
                        if self.RSI_positions.loc[i,j]==True:
                            self.RSI_positions.loc[i,j]=1
            pos.at['rsi','data']=self.RSI_positions
            return  

                #----------------------------------------------------------------------------------------------------------------#

        def BBANDS(self):
            global pos
            upper, mid, lower = ta.BBANDS(self.data_pairs['close'], nbdevup=2, nbdevdn=2, timeperiod=20)

            upper = pd.Series(upper)
            mid = pd.Series(mid)
            lower = pd.Series(lower)

            Percent_B = ((self.data_pairs['close']-lower)/(upper-lower))*100

    #positions

            self.BB_positions['BB_BUY'] =  Percent_B <= 0
            self.BB_positions['BB_SELL'] = Percent_B >= 100
            for j in self.BB_positions.columns:
                if j.split('_')[-1]=='SELL':
                    for i in range(len(self.BB_positions)):
                        if self.BB_positions.loc[i,j]==True:
                            self.BB_positions.loc[i,j]=2
                elif j.split('_')[-1]=='BUY':
                    for i in range(len(self.BB_positions)):
                        if self.BB_positions.loc[i,j]==True:
                            self.BB_positions.loc[i,j]=1
            pos.at['bbands','data']=self.BB_positions
            return  

                #----------------------------------------------------------------------------------------------------------------#            

        def OBV(self):
            global pos
            OBV = ta.OBV(self.data_pairs['close'], self.data_pairs['volume'])    
            EMA60 = ta.EMA(OBV, timeperiod=60)    
            self.OBV_positions['OBV_BUY']  = (OBV > EMA60) & (OBV.shift(1) <= EMA60)
            self.OBV_positions['OBV_SELL'] = (OBV < EMA60) & (OBV.shift(1) >= EMA60)
            for j in self.OBV_positions.columns:
                if j.split('_')[-1]=='SELL':
                    for i in range(len(self.OBV_positions)):
                        if self.OBV_positions.loc[i,j]==True:
                            self.OBV_positions.loc[i,j]=2
                elif j.split('_')[-1]=='BUY':
                    for i in range(len(self.OBV_positions)):
                        if self.OBV_positions.loc[i,j]==True:
                            self.OBV_positions.loc[i,j]=1
            pos.at['obv','data']=self.OBV_positions
            return 

        def position(self):
            threads=[]
            andicators=['ADX','WMA','MACD','RSI','BBANDS','OBV']
            for i in andicators:
                thread=threading.Thread(target=eval(f'self.{i}()'))
                thread.start()
            for i in threads:
                i.join()
            return
        
index = ['adx', 'wma', 'macd', 'rsi', 'bbands', 'obv']
pos = pd.DataFrame(columns = ['data'],index=index)

def runmain(timeframe='1m',limit=400):
    d=ohlcvs()
    xz=1
    while xz==1:
        try:
            asyncio.run(d.run_kucoin_future(timeframe,limit))
            df = pd.read_pickle("data_pairs_kucoin_future_%s.pkl" % (timeframe)).loc[0,'pair']
            if len(df)>=limit-100:
                break
            else:
                print('dont have enough lengh data ohlcv')
                break
        except Exception as error:
            print('errore in get ohlcv')
            break
#---------------------------------------------------------------    
    
    df['date'] = df['date'].astype(str) +' '+ df['time'].astype(str)
    df['date']= pd.to_datetime(df['date'], format='%d/%m/%Y %H:%M:%S')
    df.set_index('date', inplace=True)
    df.drop('time', axis=1,inplace=True)
    df.reset_index(drop=True, inplace=True)



#---------------------------------------------------------------     

    calculate_ta(df).position()

    sellorbuy=pd.DataFrame(index=pos.index,columns=['signal0','signal1','signal2','signal3','signal4'])
    p=pd.DataFrame()
    for i in pos.index:
        if i=='adx':
            continue
        j=0
        n=0
        while j < len(pos.loc[i,'data'].columns):
            p['sellorbuy']=pos.loc[i,'data'].iloc[:,j] + pos.loc[i,'data'].iloc[:,j+1]
            sellorbuy.at[i,'signal%s' % (n)]=p.copy()
            j+=2
            n+=1
    sellorbuy[sellorbuy.isna()]=0

    for i in sellorbuy.index:
        for j in sellorbuy.columns:
            if type(sellorbuy.loc[i,j])==int:
                continue
            sellorbuy.loc[i,j][sellorbuy.loc[i,j]==0]=np.nan
            sellorbuy.loc[i,j][sellorbuy.loc[i,j]==2]=0
    print('get sell or buy')
    return sellorbuy