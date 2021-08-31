import os
import sys

import sqlite3
from collections import defaultdict
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime

from helpers import error_maker, login_required, lookup, lookupBTC, priceFormatter, userCoinData, historyDataAdd, totalAssetDataAdd, totalAssetData, userHistoryData, COINS_LIST

########## TODO LIST ##########

# TODO: Add Modal for sell and buy operations to get second and last approvement from user
# TODO: Put api_key in database with hash version


# Configure the application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses are NOT cached
#@app.after.request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FLIE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure database:
connection_sqlite = sqlite3.connect("static/datas.db")
db = connection_sqlite.cursor()

# Make sure API key is set
#if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY_ not set")

@app.route("/",)
#@login_required
def index():
    """ Show user portfolio"""

    # check if user logged in
    try:
        if session["user_id"]:
            # Show user it's portfolio
            connection_sqlite = sqlite3.connect("static/datas.db")
            db = connection_sqlite.cursor()
            cursor = db.execute("SELECT cash FROM users WHERE userID=?", (session["user_id"],))
            row = cursor.fetchall()
            cash = float(row[0][0])
            #print(cash)
            
            cursor2 = db.execute("SELECT * FROM coins WHERE userID = ?", (session["user_id"],))
            rows2 = cursor2.fetchall()
            #print(rows2)

            data = defaultdict()
            
            data["Task"] = "None"
            data['Cash'] = cash
            totalAsset = cash
            priceBTC = lookupBTC()
            # buttons list to send to the html page
            buttons = []
            
            for row in rows2:
                
                symbol = row[1]
                amount = float(row[2])
                priceBought = row[3]
                
                if amount > 0:
                    # check live data for the coins that user has
                    if symbol == "BTC":
                        priceLive = priceBTC
                    else:
                        priceLive = lookup(symbol) * priceBTC
                else:
                    priceLive = 1

                changeAmount = round(((priceLive - priceBought)*amount),3)
                changePercentage = round((((priceLive - priceBought) / priceBought) * 100),3)
                
                # color adjustment and text arrangement
                if changePercentage >= 0:
                    changePercentage = "+%" + str(changePercentage)
                    changeAmount = "+$" + str(changeAmount)
                    textColor = 'green'
                else:
                    changePercentage = "%" + str(changePercentage)
                    changeAmount = "$" + str(changeAmount)
                    textColor = 'red'

                buttonsTuple = (symbol, changePercentage, changeAmount, amount, textColor)
                if amount > 0:
                    buttons.append(buttonsTuple)
                
                total = amount * priceLive
                
                # data dictionary for pie chart
                if total > 0:
                    data[symbol] = total
                # totalAsset for total asset line chart
                totalAsset += total
                
            totalAssetDataAdd(session["user_id"],totalAsset)
            
            lineChartData = totalAssetData(session["user_id"])
            lineChartData = dict(lineChartData)
            
            db.close()
            data = dict(data)
            print(data)

        
            
            cash, totalAsset = priceFormatter(cash), priceFormatter(totalAsset)

            return render_template("portfolio.html", data=data, cash=cash, totalAsset=totalAsset, buttons=buttons, lineChartData=lineChartData)
    except Exception as e:
        print("Excepion:",e)
        # if not logged in show main page
        return render_template("index.html")
     


@app.route("/login", methods=["GET", "POST"])
def login():
    """ LOG user in"""
    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()
    
    # Clean any userID
    session.clear()

    # When user reached via POST method
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return error_maker("Must Provide Username", 403)
        
        # Ensure password was submitted
        elif not request.form.get("password"):
            return error_maker("Must provide password", 403)
        
        # Query database for username
        db.execute("Select * FROM users WHERE username = ?", (request.form.get("username"),))
        rows = db.fetchall()
        #print(rows)
        # Ensure username exist and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            return error_maker("Invalid username and/or password", 403)
        
        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # redirect user to homepage
        return redirect("/")
    
    # Case which user reached login page via GET (by clicking a link or redirected)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """ Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()

    if request.method == "POST":

        # check if input blank or username already exist:
        if not request.form.get("username") or not request.form.get("password") or not request.form.get("confirmation"):
            return error_maker("Must provide username", 400)

        cursor = db.execute("SELECT * FROM users WHERE username = ?", (request.form.get("username"),))
        rows = cursor.fetchall()

        if len(rows) != 0:
            return error_maker("User already exist",400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return error_maker("Passwords do not mach",400)

        else:
            connection_sqlite = sqlite3.connect("static/datas.db")
            db = connection_sqlite.cursor()
            db.execute("INSERT INTO users (username,hash) VALUES(?,?)", (request.form.get("username"),generate_password_hash(request.form.get("password"),)))
            connection_sqlite.commit()
            db.close()
            
            return redirect("/")
            
    else:
        return render_template("register.html")



@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy crypto currencies"""

    if request.method == "POST":
        time = str(datetime.now())
        symbol = request.form.get("buySymbol")
        amount = float(request.form.get("buyAmount"))
        
        # If user wants to buy BTC:
        if symbol == "BTC":
            priceByUSD = lookupBTC()
        else:        
            # Check Btc current price and coin price by BTC
            priceByBTC = lookup(symbol)
            btcPrice = lookupBTC()
            
            # price needs to translated by USD
            priceByUSD = priceByBTC * btcPrice

        
        connection_sqlite = sqlite3.connect("static/datas.db")
        db = connection_sqlite.cursor()
        cursor = db.execute("SELECT cash FROM users WHERE userID=?", (session["user_id"],))
        row = cursor.fetchall()
        cashAvailable = float(row[0][0])

        if cashAvailable >= (priceByUSD * amount):
            # Case that buying process can be proceed
            
            # Check if user has already the coin
            cursor = db.execute("SELECT symbol,amount,price FROM coins WHERE userID = ?", (session['user_id'],))
            rows = cursor.fetchall()
            userCoins = []
            for row in rows:
                userCoins.append(row[0])
                if row[0] == symbol:
                    oldAmount = row[1]
                    oldPrice = row[2]

                    # Calculate the mean buy price including the old purchases
                    meanPrice = ((priceByUSD * amount) + (oldPrice * oldAmount)) / (amount + oldAmount)

                            
            if symbol in userCoins:
                # Case that user already have the same coin
                amount2 = amount + oldAmount
                valuesToInsert = (session["user_id"], symbol, amount2, meanPrice, time, session["user_id"], symbol)
                db.execute("UPDATE coins SET userID=?, symbol=?, amount=?, price=?, time=?  WHERE userID=? AND symbol=?",valuesToInsert)
                connection_sqlite.commit()
                
                
            else:
                valuesToInsert = (session["user_id"], symbol, amount, priceByUSD, time)
                db.execute("INSERT INTO coins  (userID, symbol, amount, price, time) VALUES (?,?,?,?,?) ",valuesToInsert)
                connection_sqlite.commit()

            # Reduce the cash
            db.execute("UPDATE users SET cash = ? WHERE userID=?",((cashAvailable - (priceByUSD*amount)),session["user_id"],))
            connection_sqlite.commit()

            db.close()

            # Update history table (type_ = 1 means Buy)
            historyDataAdd(symbol,amount,priceByUSD,1,session['user_id'])
            
            return redirect("/")
        else:
            return error_maker("Not enough money to buy coins")
        
    
    else:
        # Case that user reached the page via click, url etc.
        
        return render_template("buy.html",coinsList=COINS_LIST[:20])


@app.route("/sell", methods=['GET','POST'])
@login_required
def sell():
    """Sell coins"""

    # find the coins that user has
    connection_sqlite = sqlite3.connect("static/datas.db")
    db = connection_sqlite.cursor()
    cursor = db.execute("SELECT symbol, amount FROM coins WHERE userID = ?", (session["user_id"],))
    rows = cursor.fetchall()
    coinsList = []
    for row in rows:
        if row[1] > 0:
            coinsList.append(row[0])


    if request.method == "POST":
        symbol = request.form.get("sellSymbol")
        amount = float(request.form.get("sellAmount"))

        # check how many user has 
        cursor = db.execute("SELECT amount FROM coins WHERE userID = ? AND symbol=?", (session["user_id"],symbol))
        row = cursor.fetchone()
        userAmount = row[0]

        if amount > userAmount:
            return error_maker("Not enough coins to sell", 400)


        # Check Btc current price
        priceByBTC = lookup(symbol)
        btcPrice = lookupBTC()
        # price needs to translated by USD
        priceByUSD = priceByBTC * btcPrice * amount

        connection_sqlite = sqlite3.connect("static/datas.db")
        db = connection_sqlite.cursor()
        cursor = db.execute("UPDATE coins SET amount = amount - ?  WHERE userID = ? AND symbol=?", (amount, session["user_id"], symbol))
        connection_sqlite.commit()

        # update Cash
        cursor = db.execute("UPDATE users SET cash = cash + ?  WHERE userID = ?", (priceByUSD, session["user_id"]))
        connection_sqlite.commit()

        db.close()
        
        # Update history table (type_ = -1 means Sell)
        historyDataAdd(symbol,amount,priceByUSD,-1,session['user_id'])
         


        return redirect("/")
    
    else:
        # with GET method reached
        coinData = userCoinData(session["user_id"])

        return render_template("sell.html", coinsList=coinsList, coinData=coinData)

    

@app.route("/history")
@login_required
def history():
    historyData = userHistoryData(session["user_id"])
    return render_template("history.html", historyData=historyData)

@app.route("/information")
def information():
    return render_template("information.html")

if __name__ == '__main__':
    app.run()