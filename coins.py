#!/usr/bin/env python3

import urllib.request
import json
import time
import ssl
import sys
import requests

    # {
    #    "id": "bitcoin", 
    #    "name": "Bitcoin", 
    #    "symbol": "BTC", 
    #    "rank": "1", 
    #    "price_usd": "11453.3", 
    #    "price_btc": "1.0", 
    #    "24h_volume_usd": "11880100000.0", 
    #    "market_cap_usd": "192561755908", 
    #    "available_supply": "16812775.0", 
    #    "total_supply": "16812775.0", 
    #    "max_supply": "21000000.0", 
    #    "percent_change_1h": "0.02", 
    #    "percent_change_24h": "-2.57", 
    #    "percent_change_7d": "-17.64", 
    #    "last_updated": "1516389564"
    # }, 

do_verify = True

fields = [
    "rank",                   # field1
    "price_usd",              # field2
    "price_btc",              # field3
    "percent_change_1h",      # field4
    "percent_change_24h",     # field5
    "percent_change_7d",      # field6
    "market_cap_usd",         # field7
    "24h_volume_usd"          # field8
]

def get_coins():
    r = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit=0", verify=do_verify)
    array = json.loads(r.content.decode('utf-8'))
    return { entry['id']: entry for a, entry in zip(range(len(array)), array) }

def subscribe(key, subscribed_coins):
    print("=> Checking which channels that needs to be created...")
    existing_channels = []
    r = requests.get("https://api.thingspeak.com/channels.json?api_key=%s" % key, verify=do_verify)
    array = json.loads(r.content.decode('utf-8'))
    existing_channels = [ entry['name'] for entry in array ]

    for channel in subscribed_coins:
        if channel in existing_channels:
            print(" - Channel exists for %s" % channel)
        else:
            print(" - Creating channel for %s... " % channel, end='', flush=True)
            data = 'api_key=%s&name=%s' % (key, channel)
            r = requests.post("https://api.thingspeak.com/channels.json", verify=do_verify, data=data.encode('utf-8'))

    write_keys = {}
    r = requests.get("https://api.thingspeak.com/channels.json?api_key=%s" % key, verify=do_verify)
    array = json.loads(r.content.decode('utf-8'))
    for entry in array:
        # UPDATE FIELDS
        #payload = 'api_key=%s&field1=%s' % (key, "hello")
        #r = requests.put("http://api.thingspeak.com/channels/%s" % entry['id'], verify=do_verify, data=payload.encode('utf-8'))
        #print(r.content)

        write_keys[entry['name']] = entry
        for key in entry['api_keys']:
            if key['write_flag']:
                write_keys[entry['name']] = key['api_key']

    print("")
    print("=> Starting to send to ThingSpeak")

    while True:
        fetched_coins = get_coins()
        for subscribed_coin in subscribed_coins:
            print(" - Sending %s to ThingSpeak." % subscribed_coin)
            coin_values = fetched_coins[subscribed_coin]
            data = "&".join([ "%s=%s" % (k, coin_values[v]) for k, v in zip(map(lambda i: "field%d" % i, range(1,9)), fields)])
            url = "https://api.thingspeak.com/update?api_key=%s&%s" % (write_keys[subscribed_coin], data)
            r = requests.get(url, verify=do_verify)
            print("%d: %s" % (r.status_code, url))
        print("=> Done sending, wait for next round.")
        print("")
        time.sleep(15) # minimum time required to wait by ThingSpeak (for free accounts)

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == '-h':
        print("Usage: send_stats.py")
        print("")
        print(" coins.py -l")
        print("      Lists all crypto coins.") 
        print("")
        print(" coins.py -lv [VALUE]")
        print("      Lists a specific value for all coins.") 
        print("")
        print(" coins.py -g [COIN_ID]")
        print("      Details about one particular coin.") 
        print("")
        print(" coins.py -s [API_KEY] [COIN_ID] [COIN_ID] [COIN_ID] ...")
        print("      Subscribe to all coins specified in input.") 
        print("")
        print("      - API_KEY can be found on https://thingspeak.com/account/profile")
        print("")
        print(" coins.py -h")
        print("      Prints this") 
        print("")
        exit(0 if len(sys.argv) == 2 and sys.argv[1] == '-h' else 1)
    
    if sys.argv[1] == '-l':
        for id, coin in get_coins().items():
            print("%s: %s" % (coin['id'], coin['name']))

    if sys.argv[1] == '-lv' and len(sys.argv) == 3:
        for id, coin in get_coins().items():
            if coin[sys.argv[2]]:
                print("%s: %s (%s)" % (coin[sys.argv[2]], coin['id'], coin['name']))
    elif sys.argv[1] == '-lv':
        print("Need [VALUE] (you can see possible values with `-g`, such as `percent_change_7d`).")

    if sys.argv[1] == '-s':
        subscribe(sys.argv[2], sys.argv[3:])

    if sys.argv[1] == '-g' and len(sys.argv) == 3:
        d = get_coins()[sys.argv[2]]
        for k, v in sorted(d.items()):
            if "percent" in k:
                print("%s:%s%s%%" % (k, ' '*(28-len(k)), v))
            elif "usd" in k:
                print("%s:%s$%s" % (k, ' '*(28-len(k)), v))
            elif "btc" in k:
                print("%s:%s%s BTC" % (k, ' '*(28-len(k)), v))
            else:
                print("%s:%s%s" % (k, ' '*(28-len(k)), v))
    elif sys.argv[1] == '-g':
        print("Need [COIN_ID] (you can read the COIN_ID's if you do -l).")
    
    exit(0)