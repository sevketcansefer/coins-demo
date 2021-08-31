import os
import requests
import sqlite3
import urllib.parse
import json
from datetime import datetime
from collections import defaultdict

from flask import redirect, render_template, request, session
from functools import wraps

def error_maker(message, code=400):
    
    return render_template("errorPage.html",message=message, code=code)

def priceFormatter(price):
    price = float(price)
    price = round(price, 2)
    result = "$" + str(price)
    
    return result

def historyDataAdd(symbol,amount,price,type_,userID):
    """Update history table with every buy, sale, portfoy view"""
    timeNow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Change the datetime object if operation type is portfolio view
    if type_ == 0:
        timeNow = datetime.now.strftime("%Y-%m-%d %H")
    updateValues = (userID,symbol,amount,price,type_,timeNow)

    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()
    db.execute("INSERT INTO history (userID,symbol,amount,price,type,time) VALUES(?,?,?,?,?,?)",updateValues)
    connection_sqlite.commit()
    db.close()

    return None

def totalAssetDataAdd(userID,totalAsset):
    """Update totalasset table with every portfoy view"""
    timeNow = datetime.now().strftime("%Y-%m-%d %H")
    updateValues = (userID,totalAsset,timeNow)

    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()
    cursor = db.execute("SELECT time FROM totalAsset WHERE userID=?",(userID,))
    rows = cursor.fetchall()

    for row in rows:
        if row[0] == timeNow:
            print(timeNow, row[0])
            return None
        
    db.execute("INSERT INTO totalAsset (userID,total_asset,time) VALUES(?,?,?)",updateValues)
    connection_sqlite.commit()
    db.close()

    return None


     
def totalAssetData(userID):
    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()
    cursor = db.execute("SELECT total_asset, time FROM totalAsset WHERE userID=?",(userID,))
    rows = cursor.fetchall()

    data = defaultdict()
    data["Date"] = "Asset"
    
    for row in rows:
        data[str(row[1][5:])] = float(row[0])

    return data

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def lookup(name):
    """ Get the details of the coin """

    if name == "BTC":
        return lookupBTC()
    # get the price data according to btc
    # (it is used coin-btc pricing because in 
    # this way there are more coins can be find) 
    name = name.upper() + "BTC"
    
    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        #searchSymbol = urllib.parse.quote_plus(name)
        url = f"https://cloud.iexapis.com/stable/crypto/{name}/price?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except :
        return None
    
    result = response.json()
    result = float(result['price'])
    return result

def lookupBTC():
    """Checks BTC price by USD"""
    try:
        api_key = os.environ.get("API_KEY")
        #searchSymbol = urllib.parse.quote_plus(name)
        url = f"https://cloud.iexapis.com/stable/crypto/BTCUSD/price?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except request.RequestException:
        return None

    result = response.json()
    result = float(result['price'])

    return result

def userCoinData(userID):
    coinData = []
    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()
    cursor = db.execute("SELECT symbol,amount,price FROM coins WHERE userID=?",(userID,))
    rows = cursor.fetchall()
    
    for row in rows:
        if row[1] > 0:
            price = priceFormatter(row[2])
            coinData.append((row[0], row[1], price))

    return coinData

def userHistoryData(userID):
    historyData = []
    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()
    cursor = db.execute("SELECT symbol,amount,price,time,type FROM history WHERE userID=? ORDER BY time DESC",(userID,))
    rows = cursor.fetchall()

    for row in rows:
        price = priceFormatter(row[2])

        if row[-1] == -1:
            historyData.append((row[0], row[1], price, row[3], "SELL"))
        else:
            historyData.append((row[0], row[1], price, row[3], "BUY"))

    return historyData




########################################################################################################################
def supportedDatas():
    """One time function that created for clean supported crypto coins by IEX"""
    file = open("static/supported_symbols.txt")
    data = json.load(file)

    newDatabase = []

    for i in data:
        if "BTC" in i["symbol"] or "USD" in i["symbol"]:
            symbol = i["symbol"]
            name = str(i["name"])
            fromName, toName = name.split("to")
            #fromName = fromName.strip()
            #toName = toName.strip() 

            eleman = {"symbol": symbol, "from": fromName.strip(), "to": toName.strip()}
            newDatabase.append(eleman) 

    file.close()

    with open("newData", "w") as outfile:
        for element in newDatabase:
            json.dump(element, outfile)
            outfile.write('\n')


    with open("toBTC.txt", "w") as out:
        for element in newDatabase:
            if element["to"] == "BTC" or element["to"] == "Bitcoin":
                json.dump(element,out)
                out.write('\n')



COINS_LIST=['BTC','ETH', 'XRP', 'XLM','ZEC', 'TRX', 'BCH', 'LTC', 'BNB', 'DOT', 'NEO', 'BCC', 'GAS', 'HSR', 'MCO', 'WTC',
    'LRC', 'QTUM', 'YOYO', 'OMG', 'ZRX', 'STRAT', 'SNGLS', 'BQX', 'KNC', 'FUN', 'SNM', 'IOTA', 'LINK', 'XVG', 'SALT',
    'MDA', 'MTL', 'SUB', 'EOS', 'SNT', 'ETC', 'MTH', 'ENG', 'DNT', 'BNT', 'AST', 'DASH', 'OAX', 'ICN', 'BTG', 'EVX',
    'REQ', 'VIB',  'POWR', 'ARK', 'MOD', 'ENJ', 'STORJ', 'VEN', 'KMD', 'RCN', 'NULS', 'RDN', 'XMR',
    'DLT', 'AMB', 'BAT', 'BCPT', 'ARN', 'GVT', 'CDT', 'GXS', 'POE', 'QSP', 'BTS', 'XZC', 'LSK', 'TNT', 'FUEL',
    'MANA', 'BCD', 'DGD', 'ADX', 'ADA', 'PPT', 'CMT', 'CND', 'LEND', 'WABI', 'TNB', 'WAVES', 'GTO', 'ICX',
    'OST', 'ELF', 'AION', 'NEBL', 'BRD', 'EDO', 'WINGS', 'NAV', 'LUN', 'TRIG', 'APPC', 'VIBE', 'RLC', 'INS',
    'PIVX', 'IOST', 'CHAT', 'STEEM', 'NANO', 'VIA', 'BLZ', 'AE', 'RPX', 'NCASH', 'POA', 'ZIL', 'ONT', 'STORM',
    'XEM', 'WAN', 'WPR', 'QLC', 'SYS', 'GRS', 'CLOAK', 'GNT', 'LOOM', 'BCN', 'REP', 'TUSD', 'ZEN', 'SKY', 'CVC',
    'THETA', 'IOTX', 'QKC', 'AGI', 'NXS', 'DATA', 'SC', 'NPXS', 'KEY', 'NAS', 'MFT', 'DENT', 'ARDR', 'HOT', 'VET', 'DOCK', 'POLY', 'PHX', 'HC', 'GO', 'PAX', 'RVN', 'DCR', 'MITH', 'BCHABC', 'BCHSV', 'REN', 'BTT', 'ONG', 'FET', 'CELR', 'MATIC', 'ATOM', 'PHB', 'TFUEL', 'ONE', 'FTM', 'BTCB', 'ALGO', 'ERD', 'DOGE', 'DUSK', 'ANKR', 'WIN', 'COS', 'COCOS', 'TOMO', 'PERL', 'CHZ', 'BAND', 'BEAM', 'XTZ', 'HBAR', 'NKN', 'STX', 'KAVA', 'ARPA', 'CTXC', 'TROY', 'VITE', 'FTT', 'OGN', 'DREP', 'TCT', 'WRX', 'LTO', 'MBL', 'COTI', 'STPT', 'SOL', 'CTSI', 'HIVE', 'CHR', 'MDT', 'STMX', 'PNT', 'DGB', 'COMP', 'SXP', 'SNX', 'IRIS', 'MKR', 'DAI', 'RUNE', 'FIO', 'AVA', 'BAL', 'YFI', 'JST', 'SRM', 'ANT', 'CRV', 'SAND', 'OCEAN', 'NMR', 'LUNA', 'IDEX', 'RSR', 'PAXG', 'WNXM', 'TRB', 'BZRX', 'WBTC', 'SUSHI', 'YFII', 'KSM', 'EGLD', 'DIA', 'UMA', 'BEL', 'WING', 'UNI', 'NBS', 'OXT', 'SUN', 'AVAX', 'HNT', 'FLM', 'SCRT', 'ORN', 'UTK', 'XVS', 'ALPHA', 'VIDT', 'AAVE', 'NEAR', 'FIL', 'INJ', 'AERGO', 'AUDIO', 'CTK', 'BOT', 'AKRO', 'AXS', 'HARD', 'RENBTC', 'STRAX', 'FOR', 'UNFI', 'ROSE', 'SKL', 'SUSD', 'GLM', 'GRT', 'JUV', 'PSG', '1INCH', 'REEF', 'OG', 'ATM', 'ASR', 'CELO', 'RIF', 'BTCST', 
    'TRU', 'CKB', 'TWT', 'FIRO', 'LIT', 'SFP', 'FXS', 'DODO', 'FRONT', 'EASY', 'CAKE', 'ACM', 'AUCTION', 'PHA',
    'TVK', 'BADGER', 'FIS', 'OM', 'POND', 'DEGO', 'ALICE', 'LINA', 'PERP', 'RAMP', 'SUPER', 'CFX', 'EPS', 'AUTO']






