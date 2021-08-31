import json

def supportedDatas():
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

            eleman = {"symbol":symbol,"from":fromName.strip(),"to":toName.strip()}
            newDatabase.append(eleman) 

    file.close()

    with open("newData", "w") as outfile:
        for element in newDatabase:
            json.dump(element, outfile)
            outfile.write('\n')

    coinsList = []    
    with open("toBTC.txt", "w") as out:
        
        for element in newDatabase:
            if element["to"] == "BTC" or element["to"] == "Bitcoin":
                json.dump(element,out)
                out.write('\n')
                coinsList.append(element["from"])

    return coinsList

asd = supportedDatas()

print(asd)
