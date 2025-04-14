import json

with open('changedpayload.json') as f:
    jsondata = json.load(f)

    for productView in jsondata['data']['productSearch']['items'][0]:
        print(productView)
    
    #print(jsondata['data']['productSearch']['items']