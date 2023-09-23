from RequestObjects import PlayerPenInfos
import datetime
import os

def createDirIfNotExists(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def getTodayData(filename : str) -> list:
    if os.path.isfile(filename):
        print("print load data")
    else:
        print("create list")
        return dict()
    
def writeTodayData(filename : str, datas : list) -> None:
    pass

def addPen(penInfos : PlayerPenInfos, path : str = "pen_datas") -> str:
    createDirIfNotExists(path)
    date = datetime.date.today()
    today_file = f"{path}/pen_{date}.json"
    data = getTodayData(today_file)
    qkey = penInfos.qkey
    if penInfos.qkey in data:
        return "Already in"
    else:
        data[qkey] = [penInfos.name, penInfos.size]
        print(data)


#addPen(PlayerPenInfos(qkey="1234", name="Fliro", size=12.89))
