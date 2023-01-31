#!/usr/bin/env python
# coding: utf-8

# In[ ]:



from datetime import timedelta, date, datetime
import time
import pandas as pd
import numpy as np
import requests
import traceback
import logging
import threading
from threading import Thread
import asyncio
import nest_asyncio
import os
nest_asyncio.apply()

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)
bi_margin=20 # 1200/60
co_margin=200/10 #number request per second
no=20
ku_margin=15

bi_future=20 # 1200/60
co_future=200/10
ku_future=10

class ohlcvs():

    def binance_margin(self,timeframe,limit,i):
        pairs = pd.read_pickle("pairs_binance_margin.pkl")
        save_pairs=pairs.copy()

        try:

            tf =  {'1m':'1m','5m':'3m','5m':'5m',
                           '15m':'15m','30m':'30m','1h':'1h','2h':'2h','4h':'4h'
                          ,'6h':'6h','8h':'8h','12h':'12h','1d':'1d','3d':'3d','1w':'1w','1M':'1M'}
            duration =  tf[timeframe]
            url = 'https://api.binance.com/api/v1/klines'
            symbol = save_pairs.at[i,'pair']
            interval = tf[timeframe]
            par = {'symbol': symbol, 'interval': duration, 'limit': limit}

            headers = {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json',}
            df = pd.DataFrame((requests.get(url, params= par,headers=headers).json()))
            print('binance_margin:',i)
            df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume','close_time', 'qav', 'num_trades','taker_base_vol', 'taker_quote_vol', 'ignore']
            df['datetime'] = [datetime.fromtimestamp(x/1000.0) for x in df.datetime]
            df['date'] = df['datetime'].dt.strftime("%d/%m/%Y")
            df['time'] = df['datetime'].dt.strftime("%H:%M:%S")
            df.drop(['datetime','close_time', 'qav', 'num_trades','taker_base_vol', 'taker_quote_vol', 'ignore'], inplace=True, axis=1)
            df=df[["date", "time", "open", "high", "low", "close", "volume"]]
            df[["open", "high", "low", "close", "volume"]]=df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
            globals()["data_pairs_binance_margin_%s" % (timeframe)].at[i,'pair']=df
        except Exception as error:
            print(logging.error(traceback.format_exc()))
            result=requests.get(url, params= par,headers=headers)
            print(result.status_code)
            if result.status_code==429:
                globals()["data_pairs_binance_future_%s" % (timeframe)].at[i,'pair']='Too Many Requests'
        return 0

    def binance_future(self,timeframe,limit,i):
        pairs = pd.read_pickle("pairs_binance_future.pkl")
        save_pairs=pairs.copy()
        try:

            tf =  {'1m':'1m','5m':'3m','5m':'5m',
                           '15m':'15m','30m':'30m','1h':'1h','2h':'2h','4h':'4h'
                          ,'6h':'6h','8h':'8h','12h':'12h','1d':'1d','3d':'3d','1w':'1w','1M':'1M'}
            duration =  tf[timeframe]
            url = 'https://fapi.binance.com/fapi/v1/klines'
            symbol = save_pairs.at[i,'pair']
            interval = tf[timeframe]
            par = {'symbol': symbol, 'interval': duration, 'limit': limit}

            headers = {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json',}
            df = pd.DataFrame((requests.get(url, params= par,headers=headers).json()))
            print('binance_future:',i)
            df.columns = ['datetime', 'open', 'high', 'low', 'close', 'volume','close_time', 'qav', 'num_trades','taker_base_vol', 'taker_quote_vol', 'ignore']
#                 df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
            df['datetime'] = [datetime.fromtimestamp(x/1000.0) for x in df.datetime]
            df['date'] = df['datetime'].dt.strftime("%d/%m/%Y")
            df['time'] = df['datetime'].dt.strftime("%H:%M:%S")
            df.drop(['datetime','close_time', 'qav', 'num_trades','taker_base_vol', 'taker_quote_vol', 'ignore'], inplace=True, axis=1)
            df=df[["date", "time", "open", "high", "low", "close", "volume"]]
            df[["open", "high", "low", "close", "volume"]]=df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
            globals()["data_pairs_binance_future_%s" % (timeframe)].at[i,'pair']=df
        except Exception as error:
            print(logging.error(traceback.format_exc()))
            result=requests.get(url, params= par,headers=headers)
            print(result.status_code)
            if result.status_code==429:
                globals()["data_pairs_binance_future_%s" % (timeframe)].at[i,'pair']='Too Many Requests'
        return 0

    def coinex_margin(self,timeframe,limit,i):
        pairs = pd.read_pickle("pairs_coinex_margin.pkl")
        save_pairs=pairs.copy()
        try:
            symbol  =  save_pairs.at[i,'pair']
            tf = {'1m':'1min','5m':'5min',
                           '15m':'15min','30m':'30min','1h':'1hour','2h':'2hour','4h':'4hour'
                          ,'6h':'6hour','12h':'12hour','1d':'1day','3d':'3day','1w':'1week'}
            duration =  tf[timeframe]

            headers = {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json',}
            result = requests.get(
                'https://api.coinex.com/v1/market/kline?market={market}&type={timeframe}&limit={limit}'.format(
                    market=symbol,timeframe=duration,limit=limit),headers=headers)
            print(result.status_code)
            df = result.json()
            #print('coinex_margin:',i)
            df=pd.DataFrame(df["data"])
            df.columns = ['Timestamp', 'open', 'close', 'high', 'low', 'volume', 'value']
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
            df['date'] = df['Timestamp'].dt.strftime("%d/%m/%Y")
            df['time'] = df['Timestamp'].dt.strftime("%H:%M:%S")
            df.drop(['value','Timestamp'], inplace=True, axis=1)
            df=df[["date", "time", "open", "high", "low", "close", "volume"]]
            df[["open", "high", "low", "close", "volume"]]=df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
            globals()["data_pairs_coinex_margin_%s" % (timeframe)].at[i,'pair']=df
        except Exception as error:
            print(logging.error(traceback.format_exc()))
            print(result.status_code)
            if result.status_code==213:
                globals()["data_pairs_coinex_margin_%s" % (timeframe)].at[i,'pair']='Too Many Requests'
        return 0

    def coinex_future(self,timeframe,limit,i):
        pairs = pd.read_pickle("pairs_coinex_future.pkl")
        save_pairs=pairs.copy()
        try:

            symbol  =  save_pairs.at[i,'pair']
            tf =  {'1m':'1min','5m':'5min',
                           '15m':'15min','30m':'30min','1h':'1hour','2h':'2hour','4h':'4hour'
                          ,'6h':'6hour','12h':'12hour','1d':'1day','3d':'3day','1w':'1week'}
            duration =  tf[timeframe]                
            headers = {
                    'Content-Type': 'application/json; charset=utf-8',
                    'Accept': 'application/json',}
            result = requests.get(
                'https://api.coinex.com/perpetual/v1/market/kline?market={market}&type={timeframe}&limit={limit}'.format(
                    market=symbol,timeframe=duration,limit=limit
                ),
                headers=headers
            )

            df = result.json()
            print('coinex_future:',i)
            df=pd.DataFrame(df["data"])
            df.columns = ['Timestamp', 'open', 'close', 'high', 'low', 'volume', 'value']
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
            df['date'] = df['Timestamp'].dt.strftime("%d/%m/%Y")
            df['time'] = df['Timestamp'].dt.strftime("%H:%M:%S")
            df.drop(['value','Timestamp'], inplace=True, axis=1)
            df=df[["date", "time", "open", "high", "low", "close", "volume"]]
            df[["open", "high", "low", "close", "volume"]]=df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
            globals()["data_pairs_coinex_future_%s" % (timeframe)].at[i,'pair']=df
        except Exception as error:
            print(logging.error(traceback.format_exc()))
            print(result.status_code)
            if result.status_code==213:
                globals()["data_pairs_coinex_future_%s" % (timeframe)].at[i,'pair']='Too Many Requests'
        return 0

    def nobitex(self,timeframe,limit,i):
        pairs = pd.read_pickle("pairs_nobitex.pkl")
        save_pairs=pairs.copy()
        def number_candle(limit,timeframe):

            timeframes = (['1m',1,'minutes',limit*1],['3m',3,'minutes',limit*3],
                        ['5m',5,'minutes',limit*5],['15m',15,'minutes',limit*15],
                        ['30m',30,'minutes',limit*30],['1h',1,'hours',limit*1],
                        ['2h',2,'hours',limit*2],['4h',4,'hours',limit*4],
                        ['6h',6,'hours',limit*6],['8h',8,'hours',limit*8],
                        ['12h',12,'hours',limit*12],['1d',1,'days',limit*1],
                        ['3d',3,'days',limit*3],['1w',1,'weeks',limit*7])
            timeframes = pd.DataFrame(timeframes,columns=['timeframe' , 'time' , 'name_time' , 'limit'])
            timeframes.set_index('timeframe', inplace=True)

            timeframes['limit']  = timeframes['limit'].astype(np.float64)

            now = int(round(time.time() * 1000.0))
            if timeframes.loc[timeframe, 'name_time'] == 'minutes':
                from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(minutes=timeframes.loc[timeframe, 'limit'])

            if timeframes.loc[timeframe, 'name_time'] == 'hours':
                from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(hours=timeframes.loc[timeframe, 'limit'])

            if timeframes.loc[timeframe, 'name_time'] == 'days':
                from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(days=timeframes.loc[timeframe, 'limit'])

            if timeframes.loc[timeframe, 'name_time'] == 'weeks':
                from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(days=timeframes.loc[timeframe, 'limit'])

            from_datetime=datetime.strftime(from_datetime, '%Y-%m-%d %H:%M:%S')
            fromdate = from_datetime
            return fromdate



        try:
            symbol     =  save_pairs.at[i,'pair']
            tf         =  {'1h':'60','3h':'180','6h':'360','12h':'720','1d':'D','2d':'2D','3d':'3D'}
            duration   =  tf[timeframe]

            fromdate   =  datetime.strptime(number_candle(limit,timeframe),'%Y-%m-%d %H:%M:%S').strftime("%d/%m/%Y %H:%M:%S")
            fromdate   =  int(time.mktime(datetime.strptime(str(fromdate), "%d/%m/%Y %H:%M:%S").timetuple()))

            todate     =  int((time.mktime((datetime.now()).timetuple())))
            url = "https://api.nobitex.ir/market/udf/history?symbol=%s&resolution=%s&from=%s&to=%s" % (symbol,duration,fromdate,todate)

            payload={}
            headers = {}

            response = requests.request("GET", url, headers=headers, data=payload)

            df=response.json()
            print('nobitex:',i)

            t=df['t']
            df=pd.DataFrame(df)
            df.columns = ['s','dateTime','close','open','high','low', 'volume']
            df['dateTime'] = pd.to_datetime(df.dateTime, unit='s')
            df['date'] = df.dateTime.dt.strftime("%d/%m/%Y")
            df['time'] = df.dateTime.dt.strftime("%H:%M:%S")
            df.drop(['s','dateTime'], inplace=True, axis=1)

            column_names = ["date", "time", "open", "high", "low", "close", "volume"]
            df = df.reindex(columns=column_names)
            df=df.astype({'open': 'int64', 'high': 'int64', 'low': 'int64', 'close': 'int64', 'volume': 'float'})
            globals()["data_pairs_nobitex_%s" % (timeframe)].at[i,'pair']=df
        except Exception as error:
            print(logging.error(traceback.format_exc()))
            print(response.status_code)
            if response.status_code==400:
                globals()["data_pairs_nobitex_%s" % (timeframe)].at[i,'pair']='Too Many Requests'
        return 0

    def kucoin_margin(self,timeframe,limit,i):
        pairs = pd.read_pickle("pairs_kucoin_margin.pkl")
        save_pairs=pairs.copy()

        def number_candle(timeframe,limit):

            timeframes = (['1m',1,'minutes',limit*1],['3m',3,'minutes',limit*3],
                        ['5m',5,'minutes',limit*5],['15m',15,'minutes',limit*15],
                        ['30m',30,'minutes',limit*30],['1h',1,'hours',limit*1],
                        ['2h',2,'hours',limit*2],['4h',4,'hours',limit*4],
                        ['6h',6,'hours',limit*6],['8h',8,'hours',limit*8],
                        ['12h',12,'hours',limit*12],['1d',1,'days',limit*1],
                        ['3d',3,'days',limit*3],['1w',1,'weeks',limit*7])
            timeframes = pd.DataFrame(timeframes,columns=['timeframe' , 'time' , 'name_time' , 'limit'])
            timeframes.set_index('timeframe', inplace=True)

            timeframes['limit']  = timeframes['limit'].astype(np.float64)

            now = int(round(time.time() * 1000.0))
            if timeframes.loc[timeframe, 'name_time'] == 'minutes':
                from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(minutes=timeframes.loc[timeframe, 'limit'])

            if timeframes.loc[timeframe, 'name_time'] == 'hours':
                from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(hours=timeframes.loc[timeframe, 'limit'])

            if timeframes.loc[timeframe, 'name_time'] == 'days':
                from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(days=timeframes.loc[timeframe, 'limit'])



            from_datetime=datetime.strftime(from_datetime, '%Y-%m-%d %H:%M:%S')
            fromdate = from_datetime
            return fromdate


        try:
            symbol     =  save_pairs.at[i,'pair']
            tf         =  {'1m':'1min','3m':'3min','5m':'5min',
                           '15m':'15min','30m':'30min','1h':'1hour','2h':'2hour','4h':'4hour','6h':'6hour'
                          ,'8h':'8hour','12h':'12hour','1d':'1day','1w':'1week'}
            duration   =  tf[timeframe]
            fromdate   =  datetime.strptime(number_candle(timeframe,limit),'%Y-%m-%d %H:%M:%S').strftime("%d/%m/%Y %H:%M:%S")
            fromdate   =  int(time.mktime(datetime.strptime(str(fromdate), "%d/%m/%Y %H:%M:%S").timetuple()))

            todate     =  int((time.mktime((datetime.now()).timetuple())))

            url = "https://api.kucoin.com/api/v1/market/candles?type=%s&symbol=%s&startAt=%s&endAt=%s" % (duration,symbol,fromdate,todate)

            payload={}
            files={}
            headers ={}

            dff = requests.request("GET", url, headers=headers, data=payload, files=files)
            df=dff.json()
            print('kucoin_margin:',i)
            df=df['data']

            df=pd.DataFrame(df)
            df = df.rename({0:"Timestamp",1:"open",
                            2:"close",3:"high",4:"low",5:"volume",6:"value"}, axis='columns')
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='s')
            df['date'] = df['Timestamp'].dt.strftime("%d/%m/%Y")
            df['time'] = df['Timestamp'].dt.strftime("%H:%M:%S")
            df.drop(['value','Timestamp'], inplace=True, axis=1)
            df=df[["date", "time", "open", "high", "low", "close", "volume"]] 
            df =df[::-1]#reverse dataframe
            df.reset_index(drop=True,inplace=True)
            df[["open", "high", "low", "close", "volume"]]=df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
            globals()["data_pairs_kucoin_margin_%s" % (timeframe)].at[i,'pair']=df
        except Exception as error:
            print(dff.status_code)
            if dff.status_code==429:
                globals()["data_pairs_kucoin_margin_%s" % (timeframe)].at[i,'pair']='Too Many Requests'
            #print(logging.error(traceback.format_exc()))
        return 0

    def kucoin_future(self,timeframe,limit,j):
        pairs = pd.read_pickle("pairs_kucoin_future.pkl")
        save_pairs=pairs.copy()
        def number_candle(limit,timeframe):
            i=0
            list_date=[]
            now = int(round(time.time() * 1000.0))
            while True:
                    timeframes = (['1m',1,'minutes',limit*1],['3m',3,'minutes',limit*3],
                                  ['5m',5,'minutes',limit*5],['15m',15,'minutes',limit*15],
                                  ['30m',30,'minutes',limit*30],['1h',1,'hours',limit*1],
                                  ['2h',2,'hours',limit*2],['4h',4,'hours',limit*4],
                                  ['6h',6,'hours',limit*6],['8h',8,'hours',limit*8],
                                  ['12h',12,'hours',limit*12],['1d',1,'days',limit*1],
                                  ['3d',3,'days',limit*3],['1w',1,'weeks',limit*7])
                    timeframes = pd.DataFrame(timeframes,columns=['timeframe' , 'time' , 'name_time' , 'limit'])
                    timeframes.set_index('timeframe', inplace=True)

                    timeframes['limit']  = timeframes['limit'].astype(np.float64)

                    now = int(round(time.time() * 1000.0))
                    if timeframes.loc[timeframe, 'name_time'] == 'minutes':
                        from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(minutes=timeframes.loc[timeframe, 'limit'])

                    if timeframes.loc[timeframe, 'name_time'] == 'hours':
                        from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(hours=timeframes.loc[timeframe, 'limit'])

                    if timeframes.loc[timeframe, 'name_time'] == 'days':
                        from_datetime=datetime.fromtimestamp(now/1000.0) - timedelta(days=timeframes.loc[timeframe, 'limit'])

                    from_datetime=datetime.strftime(from_datetime, '%Y-%m-%d %H:%M:%S')
                    from_datetime=datetime.strptime(from_datetime,'%Y-%m-%d %H:%M:%S')
                    fromdate = from_datetime
                    fromdate =  int(from_datetime.timestamp() * 1000)
                    list_date.append(fromdate)
                    
                    if limit<200:
                        todate =  int(round(time.time() * 1000.0))
                        list_date.append(todate)
                        break
                    limit=limit-200
            return list_date


        try:
            i=0
            df=[]
            list_date=number_candle(limit,timeframe)
            
            while i<(len(list_date)-1):

                    symbol  =  save_pairs.loc[j,'pair']
                    tf =  {'1m':1,'5m':5,
                                   '15m':15,'30m':30,'1h':60,'2h':120,'4h':240
                                  ,'8h':480,'12h':720,'1d':1440,'1w':10080}
                    duration =  tf[timeframe]
                    fromdate = list_date[i]

                    todate = list_date[i+1]


                    url = "https://api-futures.kucoin.com/api/v1/kline/query?symbol=%s&granularity=%s&from=%s&to=%s"\
                    % (symbol,duration,fromdate,todate)

                    payload={}
                    files={}
                    headers ={}
                    x=1
                    while x==1:
                        try:
                            dfff = requests.request("GET", url, headers=headers, data=payload, files=files)
                            if dfff.status_code==200:
                                break
                            time.sleep(5)
                        except Exception as error:
                            print(error)
                    print(dfff)
                    dff=dfff.json()
                    dff=dff['data']
                    df.extend(dff)
                    i+=1
            print('get ohlcv')
            df=pd.DataFrame(df)
            df = df.rename({0:"Timestamp",1:"open",
                            2:"high",3:"low",4:"close",5:"volume"}, axis='columns')
#             df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit='ms')
            df['Timestamp'] = [datetime.fromtimestamp(x/1000.0) for x in df.Timestamp]
            df['date'] = df["Timestamp"].dt.strftime("%d/%m/%Y")
            df['time'] = df["Timestamp"].dt.strftime("%H:%M:%S")
            df.drop(['Timestamp'], inplace=True, axis=1)
            df=df[["date", "time", "open", "high", "low", "close", "volume"]]
            df[["open", "high", "low", "close", "volume"]]=df[["open", "high", "low", "close", "volume"]].apply(pd.to_numeric)
            globals()["data_pairs_kucoin_future_%s" % (timeframe)].at[j,'pair']=df
        except Exception as error:
            print(error)
            try:
                print(dfff.status_code)
                if dfff.status_code==429:
                    globals()["data_pairs_kucoin_future_%s" % (timeframe)].at[j,'pair']='Too Many Requests'
            except Exception as error:
                print('no data with funct kucoin_future')
        return 0

#----------------------------------------------------------------------------------------------------------------------

    async def run_binance_margin(self,timeframe,limit):
        pairs = pd.read_pickle("pairs_binance_margin.pkl")
        print('number of pairs in binance_margin: ',len(pairs))
        data_pairs=pairs.copy()
        data_pairs.to_pickle("data_pairs_binance_margin_%s.pkl" % (timeframe))
        globals()["data_pairs_binance_margin_%s" % (timeframe)] = pd.read_pickle("data_pairs_binance_margin_%s.pkl" % (timeframe))
        n=range(len(pairs))
        while True:
            async def run():
                threads=[]
                c=0
                for i in n:
                    thread=threading.Thread(target=self.binance_margin,args=(timeframe,limit,i))
                    thread.start()
                    threads.append(thread)
                    if c==bi_margin:
                        await asyncio.sleep(5)
                        c=0
                    c+=1
                for thread in threads:
                    thread.join()

                empt=[]
                for i in range(len(globals()["data_pairs_binance_margin_%s" % (timeframe)])):
                    if str(globals()["data_pairs_binance_margin_%s" % (timeframe)].loc[i,'pair'])=='Too Many Requests':
                        empt.append(i)
                return globals()["data_pairs_binance_margin_%s" % (timeframe)],empt
            data,empt=await run()

            if len(empt)==0:
                globals()["data_pairs_binance_margin_%s" % (timeframe)].to_pickle("data_pairs_binance_margin_%s.pkl" % (timeframe))
                break
            else:
                await asyncio.sleep(7)
                n=empt
                await run()
        return 0
    async def run_binance_future(self,timeframe,limit):
        pairs = pd.read_pickle("pairs_binance_future.pkl")
        print('number of pairs in binance_future: ',len(pairs))
        data_pairs=pairs.copy()
        data_pairs.to_pickle("data_pairs_binance_future_%s.pkl" % (timeframe))
        globals()["data_pairs_binance_future_%s" % (timeframe)] = pd.read_pickle("data_pairs_binance_future_%s.pkl" % (timeframe))        
        n=range(len(pairs))
        while True:
            async def run():
                threads=[]
                c=0
                for i in n:
                    thread=threading.Thread(target=self.binance_future,args=(timeframe,limit,i))
                    thread.start()
                    threads.append(thread)
                    if c==bi_future:
                        await asyncio.sleep(5)
                        c=0
                    c+=1
                for thread in threads:
                    thread.join()

                empt=[]
                for i in range(len(globals()["data_pairs_binance_future_%s" % (timeframe)])):
                    if str(globals()["data_pairs_binance_future_%s" % (timeframe)].loc[i,'pair'])=='Too Many Requests':
                        empt.append(i)
                return globals()["data_pairs_binance_future_%s" % (timeframe)],empt
            data,empt=await run()

            if len(empt)==0:
                globals()["data_pairs_binance_future_%s" % (timeframe)].to_pickle("data_pairs_binance_future_%s.pkl" % (timeframe))
                break
            else:
                await asyncio.sleep(7)
                n=empt
                await run()
        return 0
    async def run_coinex_margin(self,timeframe,limit):
        pairs = pd.read_pickle("pairs_coinex_margin.pkl")
        print('number of pairs in coinex_margin: ',len(pairs))
        data_pairs=pairs.copy()
        data_pairs.to_pickle("data_pairs_coinex_margin_%s.pkl" % (timeframe))
        globals()["data_pairs_coinex_margin_%s" % (timeframe)] = pd.read_pickle("data_pairs_coinex_margin_%s.pkl" % (timeframe))
        n=range(len(pairs))
        while True:
            async def run():
                threads=[]
                c=0
                for i in n:
                    thread=threading.Thread(target=self.coinex_margin,args=(timeframe,limit,i))
                    thread.start()
                    threads.append(thread)
                    if c==co_margin:
                        await asyncio.sleep(5)
                        c=0
                    c+=1
                for thread in threads:
                    thread.join()

                empt=[]
                for i in range(len(globals()["data_pairs_coinex_margin_%s" % (timeframe)])):
                    if str(globals()["data_pairs_coinex_margin_%s" % (timeframe)].loc[i,'pair'])=='Too Many Requests':
                        empt.append(i)
                return globals()["data_pairs_coinex_margin_%s" % (timeframe)],empt
            data,empt=await run()

            if len(empt)==0:
                globals()["data_pairs_coinex_margin_%s" % (timeframe)].to_pickle("data_pairs_coinex_margin_%s.pkl" % (timeframe))
                break
            else:
                await asyncio.sleep(7)
                n=empt
                await run()
        return 0
    async def run_coinex_future(self,timeframe,limit):
        pairs = pd.read_pickle("pairs_coinex_future.pkl")
        print('number of pairs in coinex_future: ',len(pairs))
        data_pairs=pairs.copy()
        data_pairs.to_pickle("data_pairs_coinex_future_%s.pkl" % (timeframe))
        globals()["data_pairs_coinex_future_%s" % (timeframe)] = pd.read_pickle("data_pairs_coinex_future_%s.pkl" % (timeframe))
        n=range(len(pairs))
        while True:
            async def run():
                threads=[]
                c=0
                for i in n:
                    thread=threading.Thread(target=self.coinex_future,args=(timeframe,limit,i))
                    thread.start()
                    threads.append(thread)
                    if c==co_future:
                        await asyncio.sleep(5)
                        c=0
                    c+=1
                for thread in threads:
                    thread.join()

                empt=[]
                for i in range(len(globals()["data_pairs_coinex_future_%s" % (timeframe)])):
                    if str(globals()["data_pairs_coinex_future_%s" % (timeframe)].loc[i,'pair'])=='Too Many Requests':
                        empt.append(i)
                return globals()["data_pairs_coinex_future_%s" % (timeframe)],empt
            data,empt=await run()

            if len(empt)==0:
                globals()["data_pairs_coinex_future_%s" % (timeframe)].to_pickle("data_pairs_coinex_future_%s.pkl" % (timeframe))
                break
            else:
                await asyncio.sleep(7)
                n=empt
                await run()
        return 0
    async def run_nobitex(self,timeframe,limit):
        pairs = pd.read_pickle("pairs_nobitex.pkl")
        print('number of pairs in nobitex: ',len(pairs))
        data_pairs=pairs.copy()
        data_pairs.to_pickle("data_pairs_nobitex_%s.pkl" % (timeframe))
        globals()["data_pairs_nobitex_%s" % (timeframe)] = pd.read_pickle("data_pairs_nobitex_%s.pkl" % (timeframe))
        n=range(len(pairs))
        while True:
            async def run():
                threads=[]
                c=0
                for i in n:
                    thread=threading.Thread(target=self.nobitex,args=(timeframe,limit,i))
                    thread.start()
                    threads.append(thread)
                    if c==no:
                        await asyncio.sleep(5)
                        c=0
                    c+=1
                for thread in threads:
                    thread.join()

                empt=[]
                for i in range(len(globals()["data_pairs_nobitex_%s" % (timeframe)])):
                    if str(globals()["data_pairs_nobitex_%s" % (timeframe)].loc[i,'pair'])=='Too Many Requests':
                        empt.append(i)
                return globals()["data_pairs_nobitex_%s" % (timeframe)],empt
            data,empt=await run()

            if len(empt)==0:
                globals()["data_pairs_nobitex_%s" % (timeframe)].to_pickle("data_pairs_nobitex_%s.pkl" % (timeframe))
                break
            else:
                await asyncio.sleep(7)
                n=empt
                await run()
        return 0
    async def run_kucoin_margin(self,timeframe,limit):
        pairs = pd.read_pickle("pairs_kucoin_margin.pkl")
        print('number of pairs in kucoin_margin: ',len(pairs))
        data_pairs=pairs.copy()
        data_pairs.to_pickle("data_pairs_kucoin_margin_%s.pkl" % (timeframe))
        globals()["data_pairs_kucoin_margin_%s" % (timeframe)] = pd.read_pickle("data_pairs_kucoin_margin_%s.pkl" % (timeframe))
        n=range(len(pairs))
        while True:
            async def run():
                print('\n******',n,'\n*******')
                threads=[]
                c=0
                for i in n:
                    thread=threading.Thread(target=self.kucoin_margin,args=(timeframe,limit,i))
                    thread.start()
                    threads.append(thread)
                    if c==ku_margin:
                        await asyncio.sleep(10)
                        c=0
                    c+=1
                for thread in threads:
                    thread.join()

                empt=[]
                for i in range(len(globals()["data_pairs_kucoin_margin_%s" % (timeframe)])):
                    if str(globals()["data_pairs_kucoin_margin_%s" % (timeframe)].loc[i,'pair'])=='Too Many Requests':
                        empt.append(i)
                return globals()["data_pairs_kucoin_margin_%s" % (timeframe)],empt
            data,empt=await run()

            if len(empt)==0:
                globals()["data_pairs_kucoin_margin_%s" % (timeframe)].to_pickle("data_pairs_kucoin_margin_%s.pkl" % (timeframe))
                break
            else:
                await asyncio.sleep(7)
                n=empt
                await run()
        return 0
    async def run_kucoin_future(self,timeframe,limit):
        pairs = pd.read_pickle("pairs_kucoin_future.pkl")
#         print('number of pairs in kucoin_future: ',len(pairs))
        data_pairs=pairs.copy()
        data_pairs.to_pickle("data_pairs_kucoin_future_%s.pkl" % (timeframe))
        globals()["data_pairs_kucoin_future_%s" % (timeframe)] = pd.read_pickle("data_pairs_kucoin_future_%s.pkl" % (timeframe))
        n=range(len(pairs))
        
        while True:
            try:
                async def run():
                    threads=[]
                    c=0
                    for i in n:
                        thread=threading.Thread(target=self.kucoin_future,args=(timeframe,limit,i))
                        thread.start()
                        threads.append(thread)
                        if c==ku_future:
                            await asyncio.sleep(10)
                            c=0
                        c+=1
                    for thread in threads:
                        thread.join()

                    empt=[]
                    for i in range(len(globals()["data_pairs_kucoin_future_%s" % (timeframe)])):
                        if str(globals()["data_pairs_kucoin_future_%s" % (timeframe)].loc[i,'pair'])=='Too Many Requests':
                            empt.append(i)
                    return globals()["data_pairs_kucoin_future_%s" % (timeframe)],empt
                data,empt=await run()

                if len(empt)==0:
                    globals()["data_pairs_kucoin_future_%s" % (timeframe)].to_pickle("data_pairs_kucoin_future_%s.pkl" % (timeframe))
                    break
                else:
                    await asyncio.sleep(7)
                    n=empt
                    await run()
            except Exception as error:
                print(error)
                break

        return 0


    def get_ohlcvs_margin(self,limit,list_timeframe,time_started):
        if (time_started[0]==0) or ((time.perf_counter()-time_started[0])>=9):
            print('***************************************15**************************************************')
            time_started[0]=time.perf_counter()
            self.run_binance_margin(list_timeframe[0],limit)
            self.run_coinex_margin(list_timeframe[0],limit)
            self.run_kucoin_margin(list_timeframe[0],limit)
            self.run_nobitex(list_timeframe[0],limit)


        if (time_started[1]==0) or ((time.perf_counter()-time_started[1])>=1800):
            print('*****************************************30************************************************')
            time_started[1]=time.perf_counter()
            self.run_binance_margin(list_timeframe[1],limit)
            self.run_coinex_margin(list_timeframe[1],limit)
            self.run_kucoin_margin(list_timeframe[1],limit)
            self.run_nobitex(list_timeframe[1],limit)


        if (time_started[2]==0) or ((time.perf_counter()-time_started[2])>=3600):
            print('*******************************************1h**********************************************')
            time_started[2]=time.perf_counter()
            self.run_binance_margin(list_timeframe[2],limit)
            self.run_coinex_margin(list_timeframe[2],limit)
            self.run_kucoin_margin(list_timeframe[2],limit)
            self.run_nobitex(list_timeframe[2],limit)
        if (time_started[3]==0) or ((time.perf_counter()-time_started[3])>=86400):
            print('******************************************1d***********************************************')
            time_started[3]=time.perf_counter()
            self.run_binance_margin(list_timeframe[3],limit)
            self.run_coinex_margin(list_timeframe[3],limit)
            self.run_kucoin_margin(list_timeframe[3],limit)
            self.run_nobitex(list_timeframe[3],limit)
        print('*****************************************************************************************')

        return list_timeframe,time_started
    
    
    
    async def main(self,limit,list_timeframe,time_started):
        if (time_started[0]==0) or ((time.perf_counter()-time_started[0])>=240):
            time_started[0]=time.perf_counter()
            t1=asyncio.create_task(self.run_binance_margin(list_timeframe[0],limit))
            t2=asyncio.create_task(self.run_kucoin_margin(list_timeframe[0],limit))
            t3=asyncio.create_task(self.run_coinex_margin(list_timeframe[0],limit))
            t4=asyncio.create_task(self.run_nobitex(list_timeframe[0],limit))
            await t1
            await t2
            await t3
            await t4
            print('***************************************15**************************************************')
        return list_timeframe,time_started

# d=ohlcvs()
# list_timeframe=['15m','30m','1h','1d']
# time_started=[0,0,0,0]
# while True:
#     list_timeframe,time_started =asyncio.run(d.main(400,list_timeframe,time_started))


# d=ohlcvs()
# asyncio.run(d.run_kucoin_future('1h',9700))
# asyncio.run(d.run_binance_margin('15m',400))

