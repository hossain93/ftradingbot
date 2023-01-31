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
# from ta_calculat import runmain
import pandas as pd
import re
import chime
import traceback
import numpy as np
# users={'hossain1993':{'api_key':'62e3e694054f1e0001127930' , 'api_secret' : 'a75605e8-aea9-4eb3-bc2a-d90c0c063a3f',
#     'api_passphrase' : '92237302790','balance_trade':100,'username_trader':'hossain1993',
#                       'username_user':'hossain1993','trader_code':1,'bot_code':1,'proxy':None}}
# این مقدارها را کاربر وارد میکند و همچنین تریدرشو خودش انتخاب میکنه، یا خودش هست یا کس دیگه ای
# اولین کسی که به عنوان یوزرها هست خودمم و استارتش از خودم زده میشه
# json.dump(users, open('users.json','w'))

# new_user={"api_key": "", "api_secret": "", "api_passphrase": "",
#            "balance_trade": None,'username_trader':'','username_user':'','trader_code':1,'bot_code':1,'proxy':None}

proxy_list=[]
json.dump(proxy_list, open('proxy_list.json', 'w'))

class trader():

    def __init__(self,rond=None,commission=None,symbol=None,one_lot=None,timeframe=None,limit=None,username=None):

        self.detail_accuonts =pd.DataFrame()
        self.price =0
        self.rond =rond
        self.runpricetr =None
        self.ws =0
        self.alive_positions =pd.DataFrame()
        self.commission =commission
        self.touched_sl =0
        self.sl_tp =None
        self.base_uri = 'https://api-futures.kucoin.com'
        self.symbol=symbol
        self.touched_st =0
        self.timeframe =timeframe
        self.limit =limit
        self.one_lot=one_lot
        self.api_correct=[]
        self.username=username
        self.pnl_users={} #{'user1':{'actionprice':'','lastprice':self.price}}
        self.check_newuser=None
        self.proxy_user=10
        try:
            entry_trader=json.load(open("entry_trader_%s.json" %(self.username)))
        except Exception as error:
            entry_trader={"st": 0, "leverage": 0, "sl": 0, "sellorbuy": None,'stopPrice_sl':0,'stop_trail':0,
                          "propertise_trader":{"sl":0.03,"number_user":10 ,"state":1}}
            json.dump(entry_trader, open('entry_trader_%s.json' %(self.username), 'w'))
        user=json.load(open('users.json'))
        entry_trader["propertise_trader"]["state"]=user[self.username]['trader_code']
        entry_trader['sellorbuy']=None
        entry_trader['st']=0
#         entry_trader["propertise_trader"]['sl']=0 # این توسط ادمین گذاشته میشه
        entry_trader['leverage']=0
        json.dump(entry_trader, open('entry_trader_%s.json' %(self.username), 'w'))
        self.exit_trader=entry_trader["propertise_trader"]["state"]


    def creat_accuont(self):
        def accuo():

            self.base_uri = 'https://api-futures.kucoin.com'
            try:
                user=json.load(open('users.json'))
            except Exception as error:
                pass
            
            ind=['availableBalance','calculated_size','type_ballance','api_key','api_passphrase','stop_trail',
                 'api_secret','id','leverage','side','size_position','symbol','status','stopPrice_sl','lastprice',
                 'trailprice','actionprice','sl','st','status_sl','orderId_position','orderId_sl','last_time',
                 'proxy','username_trader','PNL','balance_trade']
            column=[]
            for i in [*user]:
                if (user[i]['username_trader']==self.username) and (user[i]['bot_code']==1):
                    column.append(i)
            
            if len(column)>0:
                self.set_proxy()
                user=json.load(open('users.json'))
                ind_key = {key: 0 for key in ind}
                self.detail_accuonts = {key: ind_key for key in column}

                for i in column:
                    self.detail_accuonts[i]['api_key']=user[i]['api_key']
                    self.detail_accuonts[i]['api_secret']=user[i]['api_secret']
                    self.detail_accuonts[i]['api_passphrase']=user[i]['api_passphrase']
                    self.detail_accuonts[i]['status']=0
                    self.detail_accuonts[i]['status_sl']=0
                    self.detail_accuonts[i]['type_ballance']=['XBT','USDT','XRP','ETH','DOT']
                    self.detail_accuonts[i]['last_time']=str(datetime.datetime.utcnow())
                    self.detail_accuonts[i]['balance_trade']=user[i]['balance_trade']
                    self.detail_accuonts[i]['proxy']=user[i]['proxy']
            else:
                self.exit_trader=0
            
            return self.detail_accuonts

        try:
            self.detail_accuonts=json.load(open('detail_accuonts_%s.json' % (self.username)))
            print('exist position')
            self.multi_threading(func=self.check_exist_alive_position,accuonts=[*self.detail_accuonts])
            check=0
            for i in [*self.detail_accuonts]:
                if self.detail_accuonts[i]['status']>0:
                    check=1
                    break
            if check==0:
                self.detail_accuonts=accuo()
        except Exception as error:
            print(error)
            self.detail_accuonts=accuo()
            self.multi_threading(func=self.check_exist_alive_position,accuonts=[*self.detail_accuonts])
        if len([*self.detail_accuonts])>0:

            print(self.detail_accuonts)
            json.dump(self.detail_accuonts, open('detail_accuonts_%s.json' % (self.username), 'w'))
        return self.detail_accuonts

    def new_user(self):
        try:
            user=json.load(open('users.json'))
            entry_trader=json.load(open("entry_trader_%s.json" %(self.username)))
        except Exception as error:
            pass

        
        self.check_newuser=entry_trader["propertise_trader"]['number_user']
        ind=['availableBalance','calculated_size','type_ballance','api_key','api_passphrase','stop_trail',
             'api_secret','id','leverage','side','size_position','symbol','status','stopPrice_sl','lastprice',
             'trailprice','actionprice','sl','st','status_sl','orderId_position','orderId_sl','last_time',
             'proxy','username_trader','PNL','balance_trade']
        if (len(user)>0) and (len(user)>self.check_newuser):
            self.check_newuser=len(user)
            column=[]
            for i in [*user]:
                if (user[i]['username_trader']==self.username) and (user[i]['bot_code']==1):
                    column.append(i)

            if len(column)>0:
                self.set_proxy()
                user=json.load(open('users.json'))
                ind_key = {key: 0 for key in ind}
                new_detail_accuonts = {key: ind_key for key in column}

                self.detail_accuonts.update(new_detail_accuonts)
                for i in column:
                    self.detail_accuonts[i]['api_key']=user[i]['api_key']
                    self.detail_accuonts[i]['api_secret']=user[i]['api_secret']
                    self.detail_accuonts[i]['api_passphrase']=user[i]['api_passphrase']
                    self.detail_accuonts[i]['status']=0
                    self.detail_accuonts[i]['status_sl']=0
                    self.detail_accuonts[i]['type_ballance']=['XBT','USDT','XRP','ETH','DOT']
                    self.detail_accuonts[i]['last_time']=str(datetime.datetime.utcnow())
                    self.detail_accuonts[i]['balance_trade']=user[i]['balance_trade']
                    self.detail_accuonts[i]['proxy']=user[i]['proxy']
                json.dump(self.detail_accuonts, open('detail_accuonts_%s.json' % (self.username), 'w'))

    def set_proxy(self):

        colmn=[*self.detail_accuonts]
        try:
            user=json.load(open('users.json'))
            proxy_list=json.load(open('proxy_list.json'))
            used_proxy=json.load(open('used_proxy.json'))
        except Exception as error:
            proxy_list=[]

        maxmin={'now':0 , 'max':self.proxy_user}

        for i in proxy_list:
            if i not in [*used_proxy]:
                used_proxy[i]=maxmin.copy()
                
        def find_empty_proxy():
            global used_proxy
            global proxy_list

            pro=0
            n=0
            if len(proxy_list)>0:
                for i in proxy_list:
                    if used_proxy[i]['now']<used_proxy[i]['max']:
                        n=used_proxy[i]['now']
                        pro=i
                        break
            return pro , n
        pro,n=find_empty_proxy()

        if len(proxy_list)>0:
            for i in [*user]:
                if user[i]['proxy']==None:
                    n+=1
                    user[i]['proxy']=pro
                    if n==used_proxy[pro]['max']:
                        used_proxy[pro]['now']=n
                        pro,n=find_empty_proxy()
                        if (pro==0) or (n==0):
                            json.dump(used_proxy, open('used_proxy.json', 'w'))
                            json.dump(user, open('used_proxy.json', 'w'))
                            break

    def runprice(self):

        url='https://api.kucoin.com/api/v1/bullet-public'
        token=json.loads(requests.post(url).text)['data']['token']
        self.ws=create_connection('wss://ws-api.kucoin.com/endpoint?token=%s&[connectId=%s]' % (token,uuid.uuid1()))

        msg = {"id":"%s" % (uuid.uuid1()),
            "type": "subscribe",
            "topic": "/contractMarket/ticker:%s" %(self.symbol),
            "response": True}
        msg=json.dumps(msg)
        self.ws.send(msg)
        i=0
        self.runpricetr=1
        while self.runpricetr==1:
            if self.exit_trader==0:
                self.runpricetr=0
            try:
                p = json.loads(self.ws.recv())#
                if "data" in p:
                    if 'price' in p['data']:
                        self.price=p['data']['price']
    #                     rond=len(str(price).split(".")[1])
#                         print(self.price,end='-')

                if i==3:
                    msg = {"id":"%s" % (uuid.uuid1()),
                "type":"pong"
                          }
                    msg=json.dumps(msg)
                    self.ws.send(msg)
                    i=0
                i+=1
            except Exception as error:
    #             print('break connection with websocket')
#                 print('.',end='-')
                thread=threading.Thread(target=self.runprice)
                thread.start()
                break

    def refresh_runprice(self) :
        
        pr=0
        prr=1
        x=1
        while x==1:
            if self.exit_trader==0:
                x=0
            pr=self.price    
            time.sleep(5)
            prr=self.price
            if pr==prr:
                self.ws.close()
                self.runpricetr=0
                thread=threading.Thread(target=self.runprice)
                thread.start()
        return

    def time_sleep(self,timeframe):
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

    def set_param_orders(self,leverage,side,size,stopPrice_sl=None,stopPrice_tp=None,maintrade=True,
                         sl_trade=True,tp_trade=True,close_position=False):
        listparams=[]  #   for main position  listparams=['main position','stop los', 'take profit']
        if maintrade==True:
            params ={'clientOid': str(uuid.uuid1()),
                    'side': side,
                    'symbol': self.symbol,
                    'type': "market",
                    'size': str(size),
                    'leverage': str(leverage),
                    'remark':'maintrade'}
            data_json = json.dumps(params)
            listparams.append(data_json)

        if side=='buy':

            if sl_trade==True:
                params ={'symbol':self.symbol,
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
                params ={'symbol':self.symbol,
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
                params ={'symbol':self.symbol,
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
                params ={'symbol':self.symbol,
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
                params ={'symbol':self.symbol,
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
                params ={'symbol':self.symbol,
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

    def get_headers(self,method,endpoint,parameters,user=None):
        api_key=self.detail_accuonts[user]['api_key']
        api_secret=self.detail_accuonts[user]['api_secret']
        api_passphrase=self.detail_accuonts[user]['api_passphrase']
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

    def request_order(self,meth,num,addendpoint,parameters=None,user=None):
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
                if self.detail_accuonts[user]['proxy']==None:
                    response = requests.request(method, self.base_uri+endpoint,
                        headers=self.get_headers(method,endpoint,parameters,user=user), data=parameters)
                else:
                    proxies = {
                               'http': 'http://%s' % (self.detail_accuonts[user]['proxy']),
                               'https': 'http://%s' % (self.detail_accuonts[user]['proxy']),}
                    response = requests.request(method, self.base_uri+endpoint,
                        headers=self.get_headers(method,endpoint,parameters,user=user), data=parameters ,proxies=proxies)
                print(response.status_code)
                if response.status_code==200:
                    if user in self.api_correct:
                        self.api_correct.remove(user)
                    break
                elif response.status_code==300003:
                    print('no enough money')
                    break
                elif response.status_code==429:
                    print('Too Many Requests')
                elif response.status_code==200002:
                    print('time sleep 10')
                    time.sleep(11)
                elif (response.status_code==400001) and (response.status_code==400002) and (response.status_code==400003)\
                and (response.status_code==400004):
                    self.api_correct.append(user)
                    print('self.api_correct=0 for trader %s and user %s' % (self.username , user))
                    break
                 
                elif response.status_code!=429 or response.status_code!=200002 :
                    print(response.status_code ,' : ', response.json()['msg'])
                    break
            except Exception as error:
                re='request_order'
                print(re)
                print(error)
                break
            
        return response.json() , re , response.status_code

    def open_position(self,user,leverage,side,stopPrice_sl):
        # باید یک حالتی بزارم که اگه پوزیشن ها باز شد ولی استاپ گذاشته نشد باید دوباره اقدام کنه یا پیام بزاره و صدا داشته باشه چون خیلی مهم است استاپ لاس
        # باید قیمت باز شدن را برای همه پوزیشنها در نظر بگیرم چون که همه در یک قیمت باز نمیشن

        self.one_lot=10 #xrp
        cost=leverage*(self.detail_accuonts[user]['availableBalance']*(self.detail_accuonts[user]['balance_trade']/100))
        size=int(cost/(self.one_lot*self.price))
        self.detail_accuonts[user]['calculated_size']=size
        no_enough_money=1
        if size<1:
            no_enough_money=0
#         print(cost ,'\n',size)
#         print(self.detail_accuonts)
#         print(self.detail_accuonts[user]['status'],'\n',no_enough_money,'\n',self.api_correct)

        if (self.detail_accuonts[user]['status']==0) and (no_enough_money==1) and (user not in self.api_correct):
            if side=='sell':
                print('sell-open_position')
                listparams=self.set_param_orders(leverage=leverage,side=side,size=size,
                stopPrice_sl=stopPrice_sl,tp_trade=False)
                for parameters in listparams:
                    response,re,statusCode=self.request_order(num='1',parameters=parameters,meth='POST',addendpoint='',user=user)
                    if listparams.index(parameters)==0:
                        if statusCode==200:
                            self.detail_accuonts[user]['status']=1
                            self.detail_accuonts[user]['orderId_position']=response['data']['orderId']
                        else:
                            break
                    if listparams.index(parameters)==1:
                        if statusCode==200:
                            self.detail_accuonts[user]['status_sl']=1
                            self.detail_accuonts[user]['orderId_sl']=response['data']['orderId']

            if side=='buy':
                print('buy-open_position')
                listparams=self.set_param_orders(leverage=leverage,side=side,size=size,
                stopPrice_sl=stopPrice_sl,tp_trade=False)
                for parameters in listparams:
                    response , re , statusCode=self.request_order(parameters=parameters,meth='POST',num='1',addendpoint='',user=user)
                    if listparams.index(parameters)==0:
                        if statusCode==200:
                            self.detail_accuonts[user]['status']=1
                            self.detail_accuonts[user]['orderId_position']=response['data']['orderId']
                        else:
                            break
                    if listparams.index(parameters)==1:
                        if statusCode==200:
                            self.detail_accuonts[user]['status_sl']=1
                            self.detail_accuonts[user]['orderId_sl']=response['data']['orderId']

        if self.detail_accuonts[user]['status']==1:
            self.detail_accuonts[user]['side']=side
            self.detail_accuonts[user]['size_position']=size
            self.detail_accuonts[user]['leverage']=leverage
            self.detail_accuonts[user]['symbol']=self.symbol
            x=1
            i=0
            while x==1:
    #             try:
                response,re,statusCode=self.request_order(parameters='',meth='GET',num='13',addendpoint=self.symbol,user=user)
                if statusCode==200 and len(response['data'])!=0:  # این باید 200 بشه و باید اینقدر تلاش کنه که جواب بگیره مگرنه باید پوزیشن را ببنده و اینو باید بعد از باز کردن پوزیشن تو قسمت اپن اردر بزارم و چک کنم که اونهایی که  اکشن پرایس و تریل پرایس ندارن بسته بشن یعنی یک تابع مخصوص کلوز بزارم
                    entryprice=response['data'][0]['avgEntryPrice']
                    self.detail_accuonts[user]['id']=response['data'][0]['id']
                    self.detail_accuonts[user]['trailprice']=entryprice
                    self.detail_accuonts[user]['actionprice']=entryprice
                    break
                if  len(response['data'])==0:
                    i+=1
                if i==2:
                    entryprice=self.price
                    self.detail_accuonts[user]['trailprice']=entryprice
                    self.detail_accuonts[user]['actionprice']=entryprice
                    break
    #             except Exception as error:
    #                 print(response , 'open position')
    #                 print(error)
    #                 traceback.print_exc()

        json.dump(self.detail_accuonts, open('detail_accuonts_%s.json' % (self.username), 'w'))
                    #  اگر بعد یه مقدار تکرار فرجی نشد اوردر یا پوزیشن را ببند چون ممکنه گاهی اورد تبدیل به پوزیشن نشه
        return

    def control_sl(self,user,leverage,side):
        

        if self.detail_accuonts[user]['status']==1:
            parameters=''
            x=1
            c=0
            size=self.detail_accuonts[user]['calculated_size']
            if side=='buy':
                print('buy-control_sl')
                while x==1:
                    response,re,statusCode=self.request_order(parameters='',meth='GET',num='13',addendpoint=self.symbol,user=user)
                    if c>=1:
                        listparams=self.set_param_orders(leverage=leverage,side=side,size=size,
                        maintrade=False,sl_trade=False,tp_trade=False,close_position=True)
                        response,re,statusCode=self.request_order(parameters=listparams[0],meth='POST',num='1',addendpoint='',user=user)
                        print(8)
                        if statusCode==200:
                            print(2)
                            statusCode=0
                            response,re,statusCode=self.request_order(parameters='',meth='GET',num='13',addendpoint=self.symbol,user=user)

                            if (statusCode==200) and (len(response['data'])==0):
                                print(1)
                                self.alive_positions.pop(user)
                                response,re,statusCode=self.request_order(parameters='',meth='DELETE',num='3',addendpoint=self.symbol,user=user)
                                self.detail_accuonts[user]['status']=0
                                break

                    elif (statusCode==200) and (len(response['data'])==0):
                        print(3)
                        self.alive_positions.pop(user)
                        self.request_order(parameters='',meth='DELETE',num='3',addendpoint=self.symbol,user=user)
                        self.detail_accuonts[user]['status']=0
                        break

                    c+=1

            if side=='sell':
                print('sell-control_sl')
                while x==1:

                    response,re,statusCode=self.request_order(parameters='',meth='GET',num='13',addendpoint=self.symbol,user=user)
                    if c>=1:
                        listparams=self.set_param_orders(leverage=leverage,side=side,size=size,
                        maintrade=False,sl_trade=False,tp_trade=False,close_position=True)
                        response,re,statusCode=self.request_order(parameters=listparams[0],meth='POST',num='1',addendpoint='',user=user)

                        print(7)
                        if statusCode==200:
                            print(5)
                            statusCode=0
                            response,re,statusCode=self.request_order(parameters='',meth='GET',num='13',addendpoint=self.symbol,user=user)

                            if (statusCode==200) and (len(response['data'])==0):
                                print(4)
                                self.alive_positions.pop(user)
                                response,re,statusCode=self.request_order(parameters='',meth='DELETE',num='3',addendpoint=self.symbol,user=user)
                                self.detail_accuonts[user]['status']=0
                                break

                    elif (statusCode==200) and (len(response['data'])==0):
                        print(6)
                        self.alive_positions.pop(user)
                        self.request_order(parameters='',meth='DELETE',num='3',addendpoint=self.symbol,user=user)
                        self.detail_accuonts[user]['status']=0
                        break

                    c+=1

        return 

    def control_stoptrail(self,user,stopPrice_sl):

#         print('stop_trail= ',self.stop_trail , '  ' ,'stopPrice_sl= ',stopPrice_sl )
        size=self.detail_accuonts[user]['calculated_size']
        leverage=self.alive_positions[user]['leverage']
        side=self.alive_positions[user]['side']

        if side=='buy':
            print('buy-control_stoptrail')
            x=1
            while x==1:
                listparams=self.set_param_orders(leverage=leverage,side=side,size=size,
                stopPrice_sl=stopPrice_sl,maintrade=False,sl_trade=True,tp_trade=False)

                response,re,statusCode=self.request_order(parameters=listparams[0],meth='POST',num='1',addendpoint='',user=user)
                if statusCode==200:
                    self.detail_accuonts[user]['stopPrice_sl']=stopPrice_sl
                    break

        if side=='sell':
            print('sell-control_stoptrail')
            x=1
            while x==1:
                listparams=self.set_param_orders(leverage=leverage,side=side,size=size,
                stopPrice_sl=stopPrice_sl,maintrade=False,sl_trade=True,tp_trade=False)

                response,re,statusCode=self.request_order(parameters=listparams[0],meth='POST',num='1',addendpoint='',user=user)
                if statusCode==200:
                    self.detail_accuonts[user]['stopPrice_sl']=stopPrice_sl
                    break
        self.detail_accuonts[user]['trailprice']=self.price
        return

    def first_control(self,user,kwargs=None):

        if self.detail_accuonts.loc['status',user]==1:
            response,re,statusCode=self.request_order(parameters='',meth='GET',num='13',addendpoint=self.symbol,user=user)
            if len(response['data'])!=0:
                response,re,statusCode=self.request_order(parameters='',meth='GET',num='7',addendpoint='',user=user)
                i=1
                while i < len(response['data']['items']):
                    if response['data']['items'][-i]['remark']=='maintrade':
                        side=response['data']['items'][-i]['remark']
                        self.symbol=response['data']['items'][-i]['symbol']
                        size=respons.json()['data']['items'][-i]['size']
                        leverage=response['data']['items'][-i]['leverage']
                        break
                listparams=self.set_param_orders(leverage=leverage,side=side,size=size,
                maintrade=False,sl_trade=False,tp_trade=False,close_position=True)

                self.request_order(parameters=listparams[0],meth='POST',num='1',addendpoint=self.symbol,user=user)
                self.request_order(parameters='',meth='DELETE',num='3',addendpoint=self.symbol,user=user)

            if len(response['data'])==0:
                self.request_order(parameters='',meth='DELETE',num='3',addendpoint=self.symbol,user=user)
        return

    def check_exist_alive_position(self,user,kwargs=None):

        x=1
        while x==1:
            response,re,statusCode=self.request_order(parameters='',meth='GET',num='13',addendpoint=self.symbol,user=user)
            if (len(response['data'])==0) and (statusCode==200):
                self.multi_threading(func=self.reset_users,accuonts=[*self.detail_accuonts])
                self.request_order(parameters='',meth='DELETE',num='3',addendpoint=self.symbol,user=user)
                print('seccful reset detail accuont')
                break
            elif (len(response['data'])!=0) and (statusCode==200):
                break

    def multi_threading(self,func,accuonts,**kwargs):

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

    def account_overview(self,user,kwargs=None):
        print('#####')

        print(self.detail_accuonts[user]['type_ballance'][1])
        response,re,statusCode=self.request_order(parameters='',meth='GET',num='1',addendpoint=self.detail_accuonts[user]['type_ballance'][1],user=user)
        self.detail_accuonts[user]['availableBalance']=response['data']['availableBalance']
        return

    def reset_users(self,user,kwargs=None):
        print('*****')

        zero=['availableBalance','calculated_size','id','leverage','side','size_position',
              'symbol','status','symbol','stopPrice_sl','stop_trail','trailprice','actionprice','sl','st',
              'status_sl','orderId_position','orderId_sl']
        for i in zero:
            self.detail_accuonts[user][i] = 0
        json.dump(self.detail_accuonts, open('detail_accuonts_%s.json' % (self.username), 'w'))
        return

    def get_signal(self):

        print('enter a signal')
        tstart=time.perf_counter()
        x=1
        while x==1:
            try:
                detail = json.load( open( "entry_trader_%s.json" %(self.username) ) ) # detail={'st':'','leverage':'','sl':'' ,'sellorbuy':None}
            except Exception as error:
                pass
            if (type(detail['st'])==float) and (type(detail['leverage'])==int) \
            and (type(detail["propertise_trader"]['sl'])==float) and (type(detail['sellorbuy'])==int):

                if detail["propertise_trader"]['sl']>=0 and detail["propertise_trader"]['sl']<=0.05:
                    if (detail['sellorbuy']==1) or (detail['sellorbuy']==0):
                        for i in [*self.detail_accuonts]:

                            self.detail_accuonts[i]['st']=detail['st']
                            self.detail_accuonts[i]['leverage']=detail['leverage']
                            self.detail_accuonts[i]['sl']=detail["propertise_trader"]['sl']
                            json.dump(self.detail_accuonts, open('detail_accuonts_%s.json' % (self.username), 'w'))

                        detail_copy=detail.copy()
                        detail_copy['sellorbuy']=None
                        detail_copy['st']=0
#                         detail_copy["propertise_trader"]['sl']=0
                        detail_copy['leverage']=0
                        chime.theme('material')
                        chime.success()
                        json.dump(detail_copy, open('entry_trader_%s.json' %(self.username), 'w'))
                        break
            elif (time.perf_counter()-tstart)>3600:
                self.exit_trader=0

        return detail

    def open_order(self):

        detail = self.get_signal()
        x=1
        while x==1:

            if self.price==0:
                time.sleep(5)
            else:
                break
        print('\n new order\n in ' ,detail,'\n')
        print('action price= ',self.price)
        print('self.exit_trader:',self.exit_trader)
        if self.exit_trader==1:
            for i in [*self.detail_accuonts]:
                self.detail_accuonts[i]['symbol']=self.symbol
            p=self.price
            threads_op=[]
            if detail['sellorbuy']==0:
                for i in [*self.detail_accuonts]:
                    self.detail_accuonts[i]['side']='sell'
                print('sell position')
                for i in [*self.detail_accuonts]:
                    self.detail_accuonts[i]['stopPrice_sl']=(1+(self.detail_accuonts[i]['sl']/self.detail_accuonts[i]['leverage']))\
                    *p - p*self.commission
                    self.detail_accuonts[i]['stop_trail']=(1-(self.detail_accuonts[i]['st']/self.detail_accuonts[i]['leverage']))\
                    *p - p*self.commission

                print(self.detail_accuonts)
                print(self.price)
#                 while x==1:
#                     x=1
                for i in [*self.detail_accuonts]:
                    thread=threading.Thread(target=self.open_position,args=(i,
                    self.detail_accuonts[i]['leverage'],self.detail_accuonts[i]['side'],round(self.detail_accuonts[i]['stopPrice_sl'],self.rond),))
                    thread.start()
                    threads_op.append(thread)
                for thread in threads_op:
                    thread.join()
                    threads_op.remove(thread)

            if detail['sellorbuy']==1:
                for i in [*self.detail_accuonts]:
                    self.detail_accuonts[i]['side']='buy'
                print('buy position')
                for i in [*self.detail_accuonts]:
                    self.detail_accuonts[i]['stopPrice_sl']=(1-(self.detail_accuonts[i]['sl']/self.detail_accuonts[i]['leverage']))\
                    *p + p*self.commission
                    self.detail_accuonts[i]['stop_trail']=(1+(self.detail_accuonts[i]['st']/self.detail_accuonts[i]['leverage']))\
                    *p + p*self.commission
                    
                print(self.detail_accuonts)
                print(self.price)
#                 while x==1:
#                     x=1
                for i in [*self.detail_accuonts]:
                    thread=threading.Thread(target=self.open_position,args=(i,
                    self.detail_accuonts[i]['leverage'],self.detail_accuonts[i]['side'],round(self.detail_accuonts[i]['stopPrice_sl'],self.rond),))
                    thread.start()
                    threads_op.append(thread)
                for thread in threads_op:
                    thread.join()
                    threads_op.remove(thread)
        return

    def control_position_buy(self):
        
        self.touched_st=[]
        self.touched_sl=[]
        self.sl_tp={'stop_trail':0,'stopPrice_sl':0}
        print('control buy')
        
        x=1
        while x==1:
            try:
                sp= json.load(open("entry_trader_%s.json" %(self.username)))
            except Exception as error:
                pass
            if (type(sp['stop_trail'])==int) and (type(sp['stopPrice_sl'])==int):
                if (sp['stop_trail']>0) or (sp['stopPrice_sl']>0):
                    self.sl_tp=sp
            for i in [*self.alive_positions]:
                self.detail_accuonts[i]['last_time']=str(datetime.datetime.utcnow())
            for i in [*self.alive_positions]:
                self.alive_positions[i]['stop_trail']=(1+(self.alive_positions[i]['st']/self.alive_positions[i]['leverage']))\
                *self.alive_positions[i]['trailprice'] + self.alive_positions[i]['actionprice']*self.commission

#                 self.alive_positions [i]["stopPrice_sl"]= np.trunc(10**self.rond* self.alive_positions.T["stopPrice_sl"]) / 10**self.rond
#                 self.alive_positions [i]["stop_trail"]= np.trunc(10**self.rond* self.alive_positions.T["stop_trail"]) / 10**self.rond

            self.touched_sl=[*{key:value for key,value in self.alive_positions.items() if value['stopPrice_sl']>=self.price}]
            self.touched_st=[*{key:value for key,value in self.alive_positions.items() if value['stop_trail']<=self.price}]

            if (len(self.touched_sl)>0) or (self.sl_tp['stopPrice_sl']>0):
#                 print('real=',self.price,'  calculated_sl=',self.alive_positions.loc['stopPrice_sl',:])
                

                # باید لیست اونایی که ذخیره میشه با  اجرای مالتی تریدین هم زمان اجرا بشه که اگه هر کدومشون به لیست اضافه شد بلافاصله بری داخل مالتی تریدینگ
                self.touched_sl=[*self.alive_positions]
                print('touch sl')
                
                for i in self.touched_sl:
                    self.alive_positions[i]['lastprice']=self.price
                    self.alive_positions[i]['PNL']= ((self.alive_positions[i]['lastprice']-self.alive_positions[i]['actionprice'])\
                    /self.alive_positions[i]['actionprice'])*100
                try:
                    pnl_traders=json.load(open("pnl_traders.json"))
                except Exception as error:
                    pnl_traders={}
                    json.dump(pnl_traders, open('pnl_traders.json', 'w'))

                if self.username in pnl_traders:
                    l=len(pnl_traders[self.username])
                    pnl_traders[self.username]['%s'%(l+1)]=self.alive_positions
                else:
                    pnl_traders[self.username]={}
                    l=len(pnl_traders[self.username])
                    pnl_traders[self.username]['%s'%(l+1)]=self.alive_positions
                json.dump(pnl_traders, open('pnl_traders.json', 'w'))
                
#                 print(self.alive_positions)
#                 break
                threads_sl=[]
                for i in self.touched_sl:
                    self.touched_sl.remove(i)
                    user=i
                    thread=threading.Thread(target=self.control_sl,args=(i,
                    self.alive_positions[i]['leverage'],self.alive_positions[i]['side'],))
                    thread.start()
                    threads_sl.append(thread)
                for thread in threads_sl:
                    thread.join()
                self.sl_tp=json.load(open("entry_trader_%s.json" %(self.username)))
                self.sl_tp['stopPrice_sl']=0
                self.sl_tp['stop_trail']=0
                json.dump(self.sl_tp, open('entry_trader_%s.json' %(self.username), 'w'))
                print(12)

            elif len([*self.alive_positions])==0:
                print(16)
                break

            elif (len(self.touched_st)>0) or (self.sl_tp['stop_trail']>0):
#                 print('real=',self.price,'  calculated_st=',self.alive_positions[i]['stop_trail'])


                self.touched_st=[*self.alive_positions]
                print('touch st')
                for i in self.touched_st:
                    self.alive_positions[i]['stopPrice_sl']=(1-(self.alive_positions[i]['sl']/self.alive_positions[i]['leverage']))\
                    *self.price + self.alive_positions[i]['actionprice']*self.commission
#                 self.alive_positions [i]["stopPrice_sl"]= np.trunc(10**self.rond* self.alive_positions.T["stopPrice_sl"]) / 10**self.rond
#                 self.alive_positions [i]["stop_trail"]= np.trunc(10**self.rond* self.alive_positions.T["stop_trail"]) / 10**self.rond
                
                threads_st=[]
                for i in self.touched_st:
                    self.touched_st.remove(i)
                    user=i
                    thread=threading.Thread(target=self.control_stoptrail,args=(i,
                    round(self.alive_positions[i]['stopPrice_sl'],self.rond),))
                    
                    thread.start()
                    threads_st.append(thread)
                for thread in threads_st:
                    thread.join()
                

                self.alive_positions={key:value for key,value in self.detail_accuonts.items() if value['status']==1}
                json.dump(self.detail_accuonts, open('detail_accuonts_%s.json' % (self.username), 'w'))
                self.sl_tp=json.load(open("entry_trader_%s.json" %(self.username)))
                self.sl_tp['stopPrice_sl']=0
                self.sl_tp['stop_trail']=0
                json.dump(self.sl_tp, open('entry_trader_%s.json' %(self.username), 'w'))

        return

    def control_position_sell(self):
        
        self.touched_st=[]
        self.touched_sl=[]
        self.sl_tp={'stop_trail':0,'stopPrice_sl':0}

        print('control sell')
        x=1
        while x==1:
            
            try:
                sp= json.load(open("entry_trader_%s.json" %(self.username)))
            except Exception as error:
                pass
            if (type(sp['stop_trail'])==int) and (type(sp['stopPrice_sl'])==int):
                if (sp['stop_trail']>0) or (sp['stopPrice_sl']>0):
                    self.sl_tp=sp
            for i in [*self.alive_positions]:
                self.detail_accuonts[i]['last_time']=str(datetime.datetime.utcnow())
            
            for i in [*self.alive_positions]:
                self.alive_positions[i]['stop_trail']=(1-(self.alive_positions[i]['st']/self.alive_positions[i]['leverage']))\
                *self.alive_positions[i]['trailprice'] - self.alive_positions[i]['actionprice']*self.commission

            self.touched_sl=[*{key:value for key,value in self.alive_positions.items() if value['stopPrice_sl']<=self.price}]
            self.touched_st=[*{key:value for key,value in self.alive_positions.items() if value['stop_trail']>=self.price}]

            if (len(self.touched_sl)>0) or (self.sl_tp['stopPrice_sl']>0):


                print('touch sl')

                self.touched_sl=[*self.alive_positions]

                for i in self.touched_sl:
                    self.alive_positions[i]['lastprice']=self.price
                    self.alive_positions[i]['PNL']= ((self.alive_positions[i]['actionprice']-self.alive_positions[i]['lastprice'])\
                    /self.alive_positions[i]['actionprice'])*100
                try:
                    pnl_traders=json.load(open("pnl_traders.json"))
                except Exception as error:
                    pnl_traders={}
                    json.dump(pnl_traders, open('pnl_traders.json', 'w'))

                if self.username in pnl_traders:
                    l=len(pnl_traders[self.username])
                    pnl_traders[self.username]['%s'%(l+1)]=self.alive_positions
                else:
                    pnl_traders[self.username]={}
                    l=len(pnl_traders[self.username])
                    pnl_traders[self.username]['%s'%(l+1)]=self.alive_positions
                json.dump(pnl_traders, open('pnl_traders.json', 'w'))

#                 print(self.alive_positions)
#                 break
                threads_sl=[]
                for i in self.touched_sl:
                    self.touched_sl.remove(i)
                    user=i
                    thread=threading.Thread(target=self.control_sl,args=(i,
                    self.alive_positions[i]['leverage'],self.alive_positions[i]['side'],))
                    thread.start()
                    threads_sl.append(thread)
                for thread in threads_sl:
                    print(21)
                    thread.join()

                self.sl_tp=json.load(open("entry_trader_%s.json" %(self.username)))
                self.sl_tp['stopPrice_sl']=0
                self.sl_tp['stop_trail']=0
                json.dump(self.sl_tp, open('entry_trader_%s.json' %(self.username), 'w'))
                print(19)

            elif len([*self.alive_positions])==0:
                print(20)
                break

            elif (len(self.touched_st)>0) or (self.sl_tp['stop_trail']>0):
#                 print('real=',self.price,'  calculated_st=',self.alive_positions[i]['stop_trail'])
                print('touch st')
                self.touched_st=[*self.alive_positions]
                for i in self.touched_st:
                    self.alive_positions[i]['stopPrice_sl']=(1+(self.alive_positions[i]['sl']/self.alive_positions[i]['leverage']))\
                    *self.price - self.alive_positions[i]['actionprice']*self.commission
#                     self.alive_positions [i]["stopPrice_sl"]= np.trunc(10**self.rond* self.alive_positions.T["stopPrice_sl"]) / 10**self.rond
#                     self.alive_positions [i]["stop_trail"]= np.trunc(10**self.rond* self.alive_positions.T["stop_trail"]) / 10**self.rond

                threads_st=[]
                for i in self.touched_st:
                    self.touched_st.remove(i)
                    user=i
                    thread=threading.Thread(target=self.control_stoptrail,args=(i,
                    round(self.alive_positions[i]['stopPrice_sl'],self.rond),))
                    thread.start()
                    threads_st.append(thread)
                for thread in threads_st:
                    thread.join()

                self.alive_positions={key:value for key,value in self.detail_accuonts.items() if value['status']==1}
                json.dump(self.detail_accuonts, open('detail_accuonts_%s.json' % (self.username), 'w'))
                
                self.sl_tp=json.load(open("entry_trader_%s.json" %(self.username)))
                self.sl_tp['stopPrice_sl']=0
                self.sl_tp['stop_trail']=0
                json.dump(self.sl_tp, open('entry_trader_%s.json' %(self.username), 'w'))
                print(23)
        return

    def control_position(self):
        
        if self.exit_trader==1:
            x=1
            self.detail_accuonts=self.creat_accuont()
            display(self.detail_accuonts)

            thread=threading.Thread(target=self.runprice)
            thread.start()

            thread=threading.Thread(target=self.refresh_runprice)
            thread.start()
        else:
            x=0

        while x==1:
            if self.exit_trader==0:
                x=0
    # -----------------------------------------------------------------------
            
            if (len([*{key:value for key,value in self.detail_accuonts.items() if value['status']>0}])==0)\
            and (self.exit_trader==1): # if one status was 1 is not trigger
                self.multi_threading(func=self.account_overview,accuonts=[*self.detail_accuonts])

    # -----------------------------------------------------------------------
            # open position

            if (len([*{key:value for key,value in self.detail_accuonts.items() if value['status']>0}])==0)\
            and (self.exit_trader==1):
                self.open_order()
    # -----------------------------------------------------------------------
            #control position

            if (len([*{key:value for key,value in self.detail_accuonts.items() if value['status']>0}])>0):
                print ('start control position')
                self.alive_positions={key:value for key,value in self.detail_accuonts.items() if value['status']>0}

                for i in [*self.alive_positions]:
                    if self.alive_positions[i]['side']=='buy':
                        side='buy'
                        break
                    elif self.alive_positions[i]['side']=='sell':
                        side='sell'
                        break


                while x==1:
                    if self.price==0:
                        time.sleep(5)
                    else:
                        break
                if side=='buy':
                    self.control_position_buy()

                elif side=='sell':
                    self.control_position_sell()

    # -----------------------------------------------------------------------
            self.multi_threading(func=self.check_exist_alive_position,accuonts=[*self.detail_accuonts])

            self.new_user()
            if len([*self.detail_accuonts])>self.check_newuser:
                self.set_proxy()

        return

# one_lot=10 # xrp
# symbol='XRPUSDTM'
# timeframe='5m'
# limit=540
# commission=0.001
# rond=4
# trade=trader( rond=rond , commission=commission , symbol=symbol , one_lot=one_lot , limit=limit , timeframe=timeframe , username='hossain1993')

# trade.control_position()
# مقدار لات باید خودم بهش بدم
#size is lot size
# account_overview('user1')
# creat_accuont(symbol)