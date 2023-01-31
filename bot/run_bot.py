
import requests
import json
import hmac
import hashlib
import base64
from urllib.parse import urlencode
import time
import uuid
import datetime
import threading
from websocket import create_connection
from ta_calculat import runmain
import pandas as pd
import re
import chime
import traceback
threads=[]
alive_positions=pd.DataFrame()
detail_accuonts=pd.DataFrame()
base_uri = 'https://api-futures.kucoin.com'
def creat_accuont(symbol):
    global detail_accuonts
    def accuo():
        # api_key = '62dff07d37a609000198b667'
        # api_secret = '37796955-d913-4499-9905-91327119ba3c'
        # api_passphrase = '09150286678'
        # base_uri = 'https://api-sandbox-futures.kucoin.com'
        # اگر یک کاربر مشخصات ای پی آی اون تغییر کرد باید راهی بزاریم که بگه اون کاربر قبلی هست و در ازای ای پی آی جدید یک مقدار کم بگیریم
        # معمولا ای پی آی پسفرض تغییر نمیکند و به عنوان تشخیص کاربر بزاریم

        api_key = '62e3e694054f1e0001127930'
        api_secret = 'a75605e8-aea9-4eb3-bc2a-d90c0c063a3f'
        api_passphrase = '92237302790'
        base_uri = 'https://api-futures.kucoin.com'
        user=[{'api_key':'62e3e694054f1e0001127930' , 'api_secret' : 'a75605e8-aea9-4eb3-bc2a-d90c0c063a3f',
        'api_passphrase' : '92237302790'}]


        ind=['availableBalance','calculated_size','type_ballance','api_key','api_passphrase','stop_trail',
             'api_secret','id','leverage','side','size_position','symbol','status','stopPrice_sl',
             'trailprice','actionprice','sl','st','status_sl','orderId_position','orderId_sl','last_time']
        column=[]
        for i in range(len(user)):
            column.append('user%s' % (i+1))
        detail_accuonts=pd.DataFrame(columns=column,index=ind)
        for i in range(len(user)):
            detail_accuonts.iloc[ind.index('api_key'),column.index('user%s' % (i+1))]=user[i]['api_key']
            detail_accuonts.iloc[ind.index('api_secret'),column.index('user%s' % (i+1))]=user[i]['api_secret']
            detail_accuonts.iloc[ind.index('api_passphrase'),column.index('user%s' % (i+1))]=user[i]['api_passphrase']
            detail_accuonts.iloc[ind.index('status'),column.index('user%s' % (i+1))]=0
            detail_accuonts.iloc[ind.index('status_sl'),column.index('user%s' % (i+1))]=0
            detail_accuonts.iloc[ind.index('type_ballance'),column.index('user%s' % (i+1))]=['XBT','USDT','XRP','ETH','DOT']
        detail_accuonts.loc['last_time',:]=datetime.datetime.utcnow()
        return detail_accuonts
    try:
        detail_accuonts=pd.read_pickle('detail_accuonts.pkl')
        print('exist position')
        multi_threading(func=check_exist_alive_position,accuonts=detail_accuonts.columns)
#         t=datetime.datetime.utcnow()
#         for i in detail_accuonts.columns:
#             minute=((t-detail_accuonts.loc['last_time',i])/60).seconds
#             if minute>60:
#                 detail_accuonts=accuo()
#                 response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=i)
#                 if len(response['data'])!=0:
#                     print('you have open position')
#                     time.sleep(2000)
    except Exception as error:
        detail_accuonts=accuo()
        

                
    return detail_accuonts

def runprice(symbol):
    global price
    global chprice
    url='https://api.kucoin.com/api/v1/bullet-public'
    token=json.loads(requests.post(url).text)['data']['token']
    ws=create_connection('wss://ws-api.kucoin.com/endpoint?token=%s&[connectId=%s]' % (token,uuid.uuid1()))

    msg = {"id":"%s" % (uuid.uuid1()),
        "type": "subscribe",
        "topic": "/contractMarket/ticker:%s" %(symbol),
        "response": True}
    msg=json.dumps(msg)
    ws.send(msg)
    i=0
    y=1
    while y==1:
        try:
            p = json.loads(ws.recv())#
            if "data" in p:
                if 'price' in p['data']:
                    price=p['data']['price']
                    chprice=price
#                     with open("price.txt", "w") as output:
#                         output.write(str(price)+'\n')

    #                 print(price)
            if i==3:
                msg = {"id":"%s" % (uuid.uuid1()),
            "type":"pong"
                      }
                msg=json.dumps(msg)
                ws.send(msg)
                i=0
            i+=1
        except Exception as error:
            print('break connection with websocket')
            thread=threading.Thread(target=runprice,args=(symbol,))
            thread.start()

            break

def time_sleep(timeframe):
    t=(datetime.datetime.utcnow() + datetime.timedelta(hours=+8)).strftime('%H:%M:%S.%f')
    tm=int(t[3:5])
    ts=int(t[6:8])
    for i in range(timeframe+1):
        if tm%timeframe==0:
            i=timeframe
            sleep=(i-1)*60 +(60-ts+5)
            time.sleep(sleep)
            break
        if (tm+i)%timeframe==0:
            sleep=(i-1)*60 +(60-ts+5)
            time.sleep(sleep)
            break
                

    return

def set_param_orders(leverage,side,size,stopPrice_sl=None,stopPrice_tp=None,maintrade=True,
                     symbol=None,sl_trade=True,tp_trade=True,close_position=False):
    listparams=[]  #   for main position  listparams=['main position','stop los', 'take profit']
    if maintrade==True:
        params ={'clientOid': str(uuid.uuid1()),
                'side': side,
                'symbol': symbol,
                'type': "market",
                'size': str(size),
                'leverage': str(leverage),
                'remark':'maintrade'}
        data_json = json.dumps(params)
        listparams.append(data_json)
    
    if side=='buy':

        if sl_trade==True:
            params ={'symbol':symbol,
                    'side':'sell',
                    'leverage':str(leverage),
                    'type': 'market',
                    'clientOid':str(uuid.uuid1()),
                    'size':str(size),
                    'stop':'down',
                    'stopPrice':str(stopPrice_sl),
                    'stopPriceType':'MP',
                    'closeOrder':'true'}
            data_json = json.dumps(params)
            listparams.append(data_json)

        if tp_trade==True:
            params ={'symbol':symbol,
                    'side':'sell',
                    'leverage':str(leverage),
                    'type': 'market',
                    'clientOid':str(uuid.uuid1()),
                    'size':str(size),
                    'stop':'up',
                    'stopPrice':str(stopPrice_tp),
                    'stopPriceType':'MP',
                    'closeOrder':'true'}
            data_json = json.dumps(params)
            listparams.append(data_json)
        
        if close_position==True:
            params ={'symbol':symbol,
                    'side':'sell',
                    'leverage':str(leverage),
                    'type': 'market',
                    'clientOid':str(uuid.uuid1()),
                    'size':str(size),
                    'stopPriceType':'MP',
                    'closeOrder':'true'}
            data_json = json.dumps(params)
            listparams.append(data_json)
    
    elif side=='sell':

        if sl_trade==True:
            params ={'symbol':symbol,
                    'side':'buy',
                    'leverage':str(leverage),
                    'type': 'market',
                    'clientOid':str(uuid.uuid1()),
                    'size':str(size),
                    'stop':'up',
                    'stopPrice':str(stopPrice_sl),
                    'stopPriceType':'MP',
                    'closeOrder':'true'}
            data_json = json.dumps(params)
            listparams.append(data_json)

        if tp_trade==True:
            params ={'symbol':symbol,
                    'side':'sell',
                    'leverage':str(leverage),
                    'type': 'market',
                    'clientOid':str(uuid.uuid1()),
                    'size':str(size),
                    'stop':'down',
                    'stopPrice':str(stopPrice_tp),
                    'stopPriceType':'MP',
                    'closeOrder':'true'}
            data_json = json.dumps(params)
            listparams.append(data_json)
        
        if close_position==True:
            params ={'symbol':symbol,
                    'side':'buy',
                    'leverage':str(leverage),
                    'type': 'market',
                    'clientOid':str(uuid.uuid1()),
                    'size':str(size),
                    'stopPriceType':'MP',
                    'closeOrder':'true'}
            data_json = json.dumps(params)
            listparams.append(data_json)
        
    return listparams

def get_headers(method,endpoint,parameters,user=None):
    api_key=detail_accuonts.loc['api_key',user]
    api_secret=detail_accuonts.loc['api_secret',user]
    api_passphrase=detail_accuonts.loc['api_passphrase',user]
    now = int(time.time() * 1000)
    if parameters=='':
        str_to_sign = str(now) + method + endpoint
    else:
        str_to_sign = str(now) + method + endpoint + parameters
    signature = base64.b64encode(hmac.new(api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest()).decode()
    passphrase = base64.b64encode(hmac.new(api_secret.encode('utf-8'), api_passphrase.encode('utf-8'), hashlib.sha256).digest()).decode()
    return {'KC-API-SIGN': signature,
            'KC-API-TIMESTAMP': str(now),
            'KC-API-KEY': api_key,
            'KC-API-PASSPHRASE': passphrase,
            'KC-API-KEY-VERSION': '2',
            'Content-Type': 'application/json'}

def request_order(meth,num,addendpoint,base_uri=base_uri,parameters=None,user=None):
    global detail_accuonts
    getmethod={'GET':{'1':'account-overview?currency=','2':'transaction-history','3':'deposit-address','4':'deposit-list',
    '5':'withdrawals/quotas','6':'withdrawal-list','7':'orders?status=done','8':'stopOrders?symbol=','9':'recentDoneOrders',
    '10':'fills','11':'recentFills','12':'openOrderStatistics','13':'positions?symbol=','14':'position?symbol=',
    '15':'contracts/risk-limit/','16':'funding-history?symbol=','method':'GET'},

    'POST':{'1':'orders','2':'position/margin/auto-deposit-status','3':'position/margin/deposit-margin',
    '4':'position/risk-limit-level/change','method':'POST'},

    'DELETE':{'1':'orders/','2':'orders?symbol=','3':'stopOrders?symbol=','method':'DELETE' }}

    method = getmethod[meth]['method']
    if addendpoint=='':
        endpoint = '/api/v1/%s' % (getmethod[method][num])
    else:
        endpoint = '/api/v1/%s' % (getmethod[method][num]) + addendpoint
        print(endpoint)
    re=''
    x=1
    while x==1:
        try:
            response = requests.request(method, base_uri+endpoint,
                headers=get_headers(method,endpoint,parameters,user=user), data=parameters)
            print(response.status_code)
            if response.status_code==200:
                break
            elif response.status_code==300003:
                print('no enough money')
                break
            elif response.status_code==429:
                print('Too Many Requests')
            elif response.status_code==200002:
                print('time sleep 10')
                time.sleep(11)
            elif response.status_code!=429 or response.status_code!=200002 :
                print(response.status_code ,' : ', response.json()['msg'])
                break
        except Exception as error:
            re='request_order'
            print(re)
            print(error)
            break
    
    return response.json() , re , response.status_code

def open_position(user,symbol,leverage,side,stopPrice_sl):
    # باید یک حالتی بزارم که اگه پوزیشن ها باز شد ولی استاپ گذاشته نشد باید دوباره اقدام کنه یا پیام بزاره و صدا داشته باشه چون خیلی مهم است استاپ لاس
    # باید قیمت باز شدن را برای همه پوزیشنها در نظر بگیرم چون که همه در یک قیمت باز نمیشن
    global detail_accuonts
    global price
    
    one_lot=10 #xrp
    cost=leverage*detail_accuonts.loc['availableBalance',user]
    size=int(cost/(one_lot*price))
    detail_accuonts.loc['calculated_size',user]=size


    if detail_accuonts.loc['status',user]==0:
        if side=='sell':
            print('sell-open_position')
            listparams=set_param_orders(symbol=symbol,leverage=leverage,side=side,size=size,
            stopPrice_sl=stopPrice_sl,tp_trade=False)
            for parameters in listparams:
                response,re,statusCode=request_order(num='1',parameters=parameters,meth='POST',addendpoint='',user=user)
                if listparams.index(parameters)==0:
                    if statusCode==200:
                        detail_accuonts.loc['status',user]=1
                        detail_accuonts.loc['orderId_position',user]=response['data']['orderId']
                    else:
                        break
                if listparams.index(parameters)==1:
                    if statusCode==200:
                        detail_accuonts.loc['status_sl',user]=1
                        detail_accuonts.loc['orderId_sl',user]=response['data']['orderId']

        if side=='buy':
            print('buy-open_position')
            listparams=set_param_orders(symbol=symbol,leverage=leverage,side=side,size=size,
            stopPrice_sl=stopPrice_sl,tp_trade=False)
            for parameters in listparams:
                response , re , statusCode=request_order(parameters=parameters,meth='POST',num='1',addendpoint='',user=user)
                if listparams.index(parameters)==0:
                    if statusCode==200:
                        detail_accuonts.loc['status',user]=1
                        detail_accuonts.loc['orderId_position',user]=response['data']['orderId']
                    else:
                        break
                if listparams.index(parameters)==1:
                    if statusCode==200:
                        detail_accuonts.loc['status_sl',user]=1
                        detail_accuonts.loc['orderId_sl',user]=response['data']['orderId']

    if detail_accuonts.loc['status',user]==1:
        detail_accuonts.loc['side',user]=side
        detail_accuonts.loc['size_position',user]=size
        detail_accuonts.loc['leverage',user]=leverage
        detail_accuonts.loc['symbol',user]=symbol
        x=1
        i=0
        while x==1:
#             try:
            response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=user)
            if statusCode==200 and len(response['data'])!=0:  # این باید 200 بشه و باید اینقدر تلاش کنه که جواب بگیره مگرنه باید پوزیشن را ببنده و اینو باید بعد از باز کردن پوزیشن تو قسمت اپن اردر بزارم و چک کنم که اونهایی که  اکشن پرایس و تریل پرایس ندارن بسته بشن یعنی یک تابع مخصوص کلوز بزارم
                entryprice=response['data'][0]['avgEntryPrice']
                detail_accuonts.loc['id',user]=response['data'][0]['id']
                detail_accuonts.loc['trailprice',user]=entryprice
                detail_accuonts.loc['actionprice',user]=entryprice
                break
            if  len(response['data'])==0:
                i+=1
            if i==2:
                entryprice=price
                detail_accuonts.loc['trailprice',user]=entryprice
                detail_accuonts.loc['actionprice',user]=entryprice
                break
#             except Exception as error:
#                 print(response , 'open position')
#                 print(error)
#                 traceback.print_exc()
            
    detail_accuonts.to_pickle('detail_accuonts.pkl')
                #  اگر بعد یه مقدار تکرار فرجی نشد اوردر یا پوزیشن را ببند چون ممکنه گاهی اورد تبدیل به پوزیشن نشه
    return

def control_sl(user,symbol,leverage,side):
    global detail_accuonts
    global alive_positions
    
    if detail_accuonts.loc['status',user]==1:
        parameters=''
        x=1
        c=0
        size=detail_accuonts.loc['calculated_size',user]
        if side=='buy':
            print('buy-control_sl')
            while x==1:
                if c>=3:
                    listparams=set_param_orders(symbol=symbol,leverage=leverage,side=side,size=size,
                    stopPrice_sl=stopPrice_sl,stopPrice_tp=stopPrice_tp,maintrade=False,sl_trade=False,
                                                tp_trade=False,close_position=True)
                    response,re,statusCode=request_order(parameters=listparams[0],meth='POST',num='1',addendpoint=symbol,user=user)
                    if statusCode==200:
                        alive_positions.drop(user, axis=1, inplace=True)
                    statusCode=0
                    response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=user)

                    if statusCode==200:
                        if len(response['data'])==0:
                            response,re,statusCode=request_order(parameters='',meth='DELETE',num='3',addendpoint=symbol,user=user)
                            detail_accuonts.loc['status',user]=0
                        break

                response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=user)
                if statusCode==200:
                    if len(response['data'])==0:
                        alive_positions.drop(user, axis=1, inplace=True)
                        request_order(parameters='',meth='DELETE',num='3',addendpoint=symbol,user=user)
                        detail_accuonts.loc['status',user]=0
                        break

                c+=1

        if side=='sell':
            print('sell-control_sl')
            while x==1:

                if c>=3:
                    listparams=set_param_orders(symbol=symbol,leverage=leverage,side=side,size=size,
                    maintrade=False,sl_trade=False,tp_trade=False,close_position=True)
                    request_order(parameters=listparams[0],meth='POST',num='1',addendpoint=symbol,user=user)
                    if statusCode==200:
                        alive_positions.drop(user, axis=1, inplace=True)
                    statusCode=0
                    response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=user)

                    if statusCode==200:
                        if len(response['data'])==0:
                            request_order(parameters='',meth='DELETE',num='3',addendpoint=symbol,user=user)
                            detail_accuonts.loc['status',user]=0
                        break

                response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=user)
                if statusCode==200:
                    if len(response['data'])==0:
                        alive_positions.drop(user, axis=1, inplace=True)
                        request_order(parameters='',meth='DELETE',num='3',addendpoint=symbol,user=user)
                        detail_accuonts.loc['status',user]=0
                        break

                c+=1
    
    return 

def control_stoptrail(user,symbol,leverage,side,stopPrice_sl,stop_trail,trailprice):
    global detail_accuonts
    global alive_positions
    global price

    size=detail_accuonts.loc['calculated_size',user]

    if detail_accuonts.loc['status',user]==1:

        if side=='buy':
            print('buy-control_stoptrail')
            # اینجا باید محاسبه کنم که حد ضررم از روی پرایس تریل محاسبه بشه            
            listparams=set_param_orders(symbol=symbol,leverage=leverage,side=side,size=size,
            stopPrice_sl=stopPrice_sl,maintrade=False,sl_trade=True,tp_trade=False)

            response,re,statusCode=request_order(parameters=listparams[0],meth='POST',num='1',addendpoint='',user=user)
            if statusCode==200:
                detail_accuonts.loc['stopPrice_sl',user]=stopPrice_sl
                detail_accuonts.loc['trailprice',user]=trailprice
                detail_accuonts.loc['stop_trail',user]=stop_trail
                    
        if side=='sell':
            print('sell-control_stoptrail')
            # اینجا باید محاسبه کنم که حد ضررم از روی پرایس تریل محاسبه بشه
            listparams=set_param_orders(symbol=symbol,leverage=leverage,side=side,size=size,
            stopPrice_sl=stopPrice_sl,maintrade=False,sl_trade=True,tp_trade=False)

            response,re,statusCode=request_order(parameters=listparams[0],meth='POST',num='1',addendpoint='',user=user)
            if statusCode==200:
                detail_accuonts.loc['stopPrice_sl',user]=stopPrice_sl
                detail_accuonts.loc['trailprice',user]=trailprice
                detail_accuonts.loc['stop_trail',user]=stop_trail
    
    detail_accuonts.to_pickle('detail_accuonts.pkl')

def first_control(user,kwargs=None):
    global detail_accuonts
    if detail_accuonts.loc['status',user]==1:
        response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=user)
        if len(response['data'])!=0:
            response,re,statusCode=request_order(parameters='',meth='GET',num='7',addendpoint='',user=user)
            i=1
            while i < len(response['data']['items']):
                if response['data']['items'][-i]['remark']=='maintrade':
                    side=response['data']['items'][-i]['remark']
                    symbol=response['data']['items'][-i]['symbol']
                    size=respons.json()['data']['items'][-i]['size']
                    leverage=response['data']['items'][-i]['leverage']
                    break
            listparams=set_param_orders(symbol=symbol,leverage=leverage,side=side,size=size,
            maintrade=False,sl_trade=False,tp_trade=False,close_position=True)

            request_order(parameters=listparams[0],meth='POST',num='1',addendpoint=symbol,user=user)
            request_order(parameters='',meth='DELETE',num='3',addendpoint=symbol,user=user)

        if len(response['data'])==0:
            request_order(parameters='',meth='DELETE',num='3',addendpoint=symbol,user=user)
    return

def check_exist_alive_position(user,kwargs=None):
    global detail_accuonts
    x=1
    while x==1:
        response,re,statusCode=request_order(parameters='',meth='GET',num='13',addendpoint=symbol,user=user)
        if len(response['data'])==0 and statusCode==200:
            multi_threading(func=reset_users,accuonts=detail_accuonts.columns)
            print('seccful reset detail accuont')
            break

def multi_threading(func,accuonts,**kwargs):
    global threads
    threads=[]
    if len(kwargs)==0:
        kwargs=None
    for i in accuonts:
        user=i
        thread=threading.Thread(target=func,args=(user,kwargs,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    return

def account_overview(user,kwargs=None):
    print('#####')
    global detail_accuonts
    print(detail_accuonts.loc['type_ballance',user][1])
    response,re,statusCode=request_order(parameters='',meth='GET',num='1',addendpoint=detail_accuonts.loc['type_ballance',user][1],user=user)
    detail_accuonts.loc['availableBalance',user]=response['data']['availableBalance']
    return

def reset_users(user,kwargs=None):
    print('*****')
    global detail_accuonts
    zero=['availableBalance','calculated_size','id','leverage','side','size_position',
          'symbol','status','symbol','stopPrice_sl','stop_trail','trailprice','actionprice','sl','st',
          'status_sl','orderId_position','orderId_sl']
    for i in zero:
        detail_accuonts.loc[i,user] = 0
    detail_accuonts.to_pickle('detail_accuonts.pkl')
    return

def get_signal(timeframe,limit):
    global detail_accuonts
    global alive_positions
    address='F:/ارز دیجیتال-فارکس/Python Scripts/ccxt/module/bot/آنالیز دیتا'
        
    detail={'andicator':'','signal':'','st':'','leverage':'','sl':''}
    filltred_strategy = pd.read_pickle('%s/filltred_strategy.pkl'% (address))
    order_details={}
    j=0
    for i in filltred_strategy.index:
        if j==0:
            detail['andicator']=i.split('*')[0]
            detail['signal']=i.split('*')[1]
            detail['st']=float(i.split('*')[2].split('-')[2])
            detail['leverage']=float(i.split('*')[2].split('-')[1])
            detail['sl']=float(i.split('*')[2].split('-')[0])
            order_details[i.split('*')[0]]=detail.copy()
        j+=1
        if i.split('*')[0]!=detail['andicator']:
            detail['andicator']=i.split('*')[0]
            detail['signal']=i.split('*')[1]
            detail['st']=float(i.split('*')[2].split('-')[2])
            detail['leverage']=int(i.split('*')[2].split('-')[1])
            detail['sl']=float(i.split('*')[2].split('-')[0])
            order_details[i.split('*')[0]]=detail.copy()
            print(order_details)
            break

    x=1
    while x==1:
        action=None
        sellorbuy=runmain(timeframe,limit)
        sellorbuy.to_pickle('sellorbuy.pkl')
        for i in order_details.keys():
#             print(sellorbuy.loc[order_details[i]['andicator'],order_details[i]['signal']].iloc[-10::])
            
            if sellorbuy.loc[order_details[i]['andicator'],order_details[i]['signal']].iloc[-1,0]==0:
                print('find a signal')
                action=0
            elif sellorbuy.loc[order_details[i]['andicator'],order_details[i]['signal']].iloc[-1,0]==1:
                print('find a signal')
                action=1
        if action!=None:

            andicator=order_details[i]['andicator']
            signal=order_details[i]['signal']
            detail_accuonts.loc['st',:]=order_details[i]['st']
            detail_accuonts.loc['leverage',:]=order_details[i]['leverage']
            detail_accuonts.loc['sl',:]=order_details[i]['sl']
            detail_accuonts.to_pickle('detail_accuonts.pkl')
            chime.theme('material')
            chime.success()
            break
        else:
            print('no order',end='-')
        time_sleep(int(re.findall(r'\d+', timeframe)[0]))

# -----------------------------------------------------------------------
        
                # open position
    return andicator , signal , sellorbuy

def open_order(symbol,timeframe,limit):
    global detail_accuonts
    global alive_positions
    global price
    global commission
    if detail_accuonts.loc['status',:].sum()==0: # if one status was 1 is not trigger
        andicator , signal , sellorbuy = get_signal(timeframe,limit)
        print('\n new order\n in ' ,andicator+signal,'\n')
        x=1
        while x==1:
            detail_accuonts.loc['symbol',:]=symbol
            p=price
            threads_op=[]
            if sellorbuy.loc[andicator,signal].iloc[-1,0]==0:
                detail_accuonts.loc['side',:]='sell'

                for i in detail_accuonts.columns:
                    detail_accuonts.loc['stopPrice_sl',i]=(1+(detail_accuonts.loc['sl',i]/detail_accuonts.loc['leverage',i]))\
                    *p - p*commission

                for i in detail_accuonts.columns:
                    user=i
                    thread=threading.Thread(target=open_position,args=(i,detail_accuonts.loc['symbol',i],
                    detail_accuonts.loc['leverage',i],detail_accuonts.loc['side',i],detail_accuonts.loc['stopPrice_sl',i],))
                    thread.start()
                    threads_op.append(thread)
                for thread in threads_op:
                    thread.join()
                    threads_op.remove(thread)


            if sellorbuy.loc[andicator,signal].iloc[-1,0]==1:
                detail_accuonts.loc['side',:]='buy'
                for i in detail_accuonts.columns:
                    detail_accuonts.loc['stopPrice_sl',i]=(1-(detail_accuonts.loc['sl',i]/detail_accuonts.loc['leverage',i]))\
                    *p + p*commission

                for i in detail_accuonts.columns:
                    user=i
                    thread=threading.Thread(target=open_position,args=(i,detail_accuonts.loc['symbol',i],
                    detail_accuonts.loc['leverage',i],detail_accuonts.loc['side',i],detail_accuonts.loc['stopPrice_sl',i],))
                    thread.start()
                    threads_op.append(thread)
                for thread in threads_op:
                    thread.join()
                    threads_op.remove(thread)

            if len(threads_op)==0:
                break
    return

def control_position_buy():
    global threads
    global accuonts
    global detail_accuonts
    global alive_positions
    global touched_st
    global touched_sl
    global tou_st
    global price
    global commission
    
    x=1
    while x==1:
        detail_accuonts.loc['last_time',:]=datetime.datetime.utcnow()

        alive_positions.loc['stop_trail',:]=(1+(alive_positions.loc['st',:]/alive_positions.loc['leverage',:]))\
        *alive_positions.loc['trailprice',:] + alive_positions.loc['actionprice',:]*commission

        touched_sl=list(alive_positions.loc[:,alive_positions.loc['stopPrice_sl',:]>=price].columns).copy()
        if len(touched_sl)>0:

            # باید لیست اونایی که ذخیره میشه با  اجرای مالتی تریدین هم زمان اجرا بشه که اگه هر کدومشون به لیست اضافه شد بلافاصله بری داخل مالتی تریدینگ

            print('touch sl')
            def touch_sl():
                global price
                global touched_sl
                global alive_positions
                t_sl=touched_sl.copy()
                x=1
                while x==1:
                    tr=list(alive_positions.loc[:,alive_positions.loc['stopPrice_sl',:]>=price].columns)
                    c=list(set(tr) ^ set(t_sl)) # پیدا کردن عضو های نامشابه
                    for i in c:
                        if i in t_sl:
                            c.remove(i)
                    touched_sl.extend(c)
                    t_sl.extend(c)
                    touched_sl=list(set(touched_sl)) # remove duplicated
            thre=threading.Thread(target=touch_sl)
            thre.start()

            while x==1:
                if len(touched_sl)>0:
                    threads_sl=[]
                    for i in touched_sl:
                        touched_sl.remove(i)
                        user=i
                        thread=threading.Thread(target=control_sl,args=(i,alive_positions.loc['symbol',i],
                                                        alive_positions.loc['leverage',i],alive_positions.loc['side',i],))
                        thread.start()
                        threads_sl.append(thread)
                    for thread in threads_sl:
                        thread.join()
                else:
                    thre.join()
                    break


        touched_st=list(alive_positions.loc[:,alive_positions.loc['stop_trail',:]<=price].columns).copy()
        tou_st=touched_st.copy()
        if len(touched_st)>0:

            print('touch st')
            for i in touched_st:
                alive_positions.loc['stopPrice_sl',i]=(1-(alive_positions.loc['sl',i]/alive_positions.loc['leverage',i]))\
                *price + alive_positions.loc['actionprice',i]*commission
            def touch_st():
                global commission
                global price
                global touched_st
                global alive_positions
                global tou_st
                t_st=touched_st.copy()
                x=1
                while x==1:
                    tr=list(alive_positions.loc[:,alive_positions.loc['stop_trail',:]<=price].columns)
                    c=list(set(tr) ^ set(t_st)) # پیدا کردن عضوهای نامشابه
                    for i in c:
                        if i in t_st:
                            c.remove(i)
                    touched_st.extend(c)
                    t_st.extend(c)
                    tou_st.extend(c)
                    for i in c:
                        alive_positions.loc['stopPrice_sl',i]=(1-(alive_positions.loc['sl',i]/alive_positions.loc['leverage',i]))\
                        *price + alive_positions.loc['actionprice',i]*commission
            thre=threading.Thread(target=touch_st)
            thre.start()

            while x==1:
                if len(touched_st)>0:
                    threads_st=[]
                    for i in touched_st:
                        touched_st.remove(i)
                        user=i
                        thread=threading.Thread(target=control_stoptrail,args=(i,alive_positions.loc['symbol',i],
                                                    alive_positions.loc['leverage',i],alive_positions.loc['side',i],
                        alive_positions.loc['stopPrice_sl',i],alive_positions.loc['stop_trail',i],price,))
                        thread.start()
                        threads_st.append(thread)
                    for thread in threads_st:
                        thread.join()
                else:
                    thre.join()
                    break
            # شرط گذاشتم که اگه ریسپانس 200 داشت بیاد ذخیره کنه مقدار جدید را
            for i in tou_st:
                if alive_positions.loc['stopPrice_sl',i]==detail_accuonts.loc['stopPrice_sl',i]:
                    alive_positions.loc['trailprice',i]=detail_accuonts.loc['trailprice',i]

                #اگر هم زمان دو تا یوزر اومدن داخل شرط از کجا بفهمیم که تریل پرایس مال کدوم است

        if len(alive_positions.columns)==0:
            break
    return

def control_position_sell():
    global threads
    global accuonts
    global detail_accuonts
    global alive_positions
    global touched_st
    global touched_sl
    global tou_st
    global price
    global commission
    
    x=1
    while x==1:
        detail_accuonts.loc['last_time',:]=datetime.datetime.utcnow()

        alive_positions.loc['stop_trail',:]=(1-(alive_positions.loc['st',:]/alive_positions.loc['leverage',:]))\
        *alive_positions.loc['trailprice',:] - alive_positions.loc['actionprice',:]*commission

        touched_sl=list(alive_positions.loc[:,alive_positions.loc['stopPrice_sl',:]<=price].columns).copy()

        if len(touched_sl)>0:

            print('touch sl')


            def touch_sl():
                global price
                global touched_sl
                global alive_positions
                t_sl=touched_sl.copy()
                x=1
                while x==1:
                    tr=list(alive_positions.loc[:,alive_positions.loc['stopPrice_sl',:]<=price].columns)
                    c=list(set(tr) ^ set(t_sl)) # پیدا کردن عضو های نامشابه
                    for i in c:
                        if i in t_sl:
                            c.remove(i)
                    touched_sl.extend(c)
                    t_sl.extend(c)
                    touched_sl=list(set(touched_sl)) # remove duplicated
            thre=threading.Thread(target=touch_sl)
            thre.start()
#             time.sleep(1000)
            while x==1:
                if len(touched_sl)>0:
                    threads_sl=[]
                    for i in touched_sl:
                        touched_sl.remove(i)
                        user=i
                        thread=threading.Thread(target=control_sl,args=(i,alive_positions.loc['symbol',i],
                                                        alive_positions.loc['leverage',i],alive_positions.loc['side',i],))
                        thread.start()
                        threads_sl.append(thread)
                    for thread in threads_sl:
                        thread.join()
                else:
                    thre.join()
                    break

        touched_st=list(alive_positions.loc[:,alive_positions.loc['stop_trail',:]>=price].columns).copy()

        tou_st=touched_st.copy()
        if len(touched_st)>0:
            print('touch st')
            for i in touched_st:
                alive_positions.loc['stopPrice_sl',i]=(1+(alive_positions.loc['sl',i]/alive_positions.loc['leverage',i]))\
                *price - alive_positions.loc['actionprice',i]*commission
            def touch_st():
                global commission
                global price
                global touched_st
                global alive_positions
                global tou_st
                t_st=touched_st.copy()
                x=1
                while x==1:
                    tr=list(alive_positions.loc[:,alive_positions.loc['stop_trail',:]>=price].columns)
                    c=list(set(tr) ^ set(t_st)) # پیدا کردن عضوهای نامشابه
                    for i in c:
                        if i in t_st:
                            c.remove(i)
                    touched_st.extend(c)
                    t_st.extend(c)
                    tou_st.extend(c)
                    for i in c:
                        alive_positions.loc['stopPrice_sl',i]=(1+(alive_positions.loc['sl',i]/alive_positions.loc['leverage',i]))\
                        *price - alive_positions.loc['actionprice',i]*commission
            thre=threading.Thread(target=touch_st)
            thre.start()
#             time.sleep(1000)

            while x==1:
                if len(touched_st)>0:
                    threads_st=[]
                    for i in touched_st:
                        touched_st.remove(i)
                        user=i
                        thread=threading.Thread(target=control_stoptrail,args=(i,alive_positions.loc['symbol',i],
                                                alive_positions.loc['leverage',i],alive_positions.loc['side',i],
                        alive_positions.loc['stopPrice_sl',i],alive_positions.loc['stop_trail',i],price,))
                        thread.start()
                        threads_st.append(thread)
                    for thread in threads_st:
                        thread.join()
                else:
                    thre.join()
                    break
            # شرط گذاشتم که اگه ریسپانس 200 داشت بیاد ذخیره کنه مقدار جدید را
            for i in tou_st:
                if alive_positions.loc['stopPrice_sl',i]==detail_accuonts.loc['stopPrice_sl',i]:
                    alive_positions.loc['trailprice',i]=detail_accuonts.loc['trailprice',i]

        if len(alive_positions.columns)==0:
            break
    return

def control_position(symbol,timeframe,limit):
    global price
    global detail_accuonts
    global alive_positions
    display(detail_accuonts)
    thread=threading.Thread(target=runprice,args=(symbol,))
    thread.start()

    x=1
    while x==1:

# -----------------------------------------------------------------------

        if detail_accuonts.loc['status',:].sum()==0: # if one status was 1 is not trigger
            multi_threading(func=account_overview,accuonts=detail_accuonts.columns)
            
# -----------------------------------------------------------------------
        # open position
        open_order(symbol,timeframe,limit)
# -----------------------------------------------------------------------
        #control position        
        if detail_accuonts.loc['status',:].sum()>0:
            alive_positions=detail_accuonts.loc[:,detail_accuonts.loc['status',:]==1]
            for i in alive_positions.columns:
                if alive_positions.loc['side',i]=='buy':
                    side='buy'
                    break
                elif alive_positions.loc['side',i]=='sell':
                    side='sell'
                    break


            while x==1:
                if price==0:
                    time.sleep(5)
                else:
                    break
            if side=='buy':
                control_position_buy()

            elif side=='sell':
                control_position_sell()

# -----------------------------------------------------------------------
        multi_threading(func=reset_users,accuonts=detail_accuonts.columns)

            
    return

symbol='XRPUSDTM'
timeframe='5m'
limit=540
commission=0.001
price=0

detail_accuonts=creat_accuont(symbol)
control_position(symbol=symbol,timeframe=timeframe,limit=limit)
# مقدار لات باید خودم بهش بدم
#size is lot size
# account_overview('user1')
# creat_accuont(symbol)