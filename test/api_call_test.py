import random
from time import sleep
import requests

address =  "toDefine"

def messageTest():
    port = ["27960","27961"]
    team = [None, "[spec]", "[game]"]

    for i in range(100):
        json = {
            "message" : f"Test {i}",
            "serverAddress" : f"{address}:{random.choice(port)}",
            "team" : random.choice(team)
        }
        requests.post(f"http://localhost:5000/message", json=json)

def demoTest():
    port = ["27960","27961"]

    for i in range(10):
        json = {
            "serverAddress" : f"{address}:{random.choice(port)}",
            "msg" : f"Message Test {i}",
            "path" : "/home/antoine/dev/UrbanTerror_Discord_Bridge/test/fakedemofile.txt",
            "name" : f"tmp_downloaded_{i}.txt",
            "chatMessage" : f"Chat Message : Link to demo"
        }
        requests.post(f"http://localhost:5000/demo", json=json)
        sleep(1)

def download():
    for i in range (50):
        r = requests.get("http://localhost:5000/q3ut4/ut4_testulben.pk3")
        print(f"Status ({i+1}) : {r.status_code}")
        sleep(0.1)

# download()
# messageTest()
# demoTest()