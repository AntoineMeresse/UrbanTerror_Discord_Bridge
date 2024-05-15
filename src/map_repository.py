import glob
import os
from random import choice

def getMapPath(mapfile, mapfolder):
    if (not ".pk3" in mapfile):
        mapfile+=".pk3"
    return f"{mapfolder}/{mapfile}"

def getAllMaps(mapfolder):
    path = f"{mapfolder}/*.pk3"
    maps = [os.path.basename(urtmap) for urtmap in glob.glob(path)]
    maps.sort()
    return maps

def getRandomMap(mapfolder):
    maps = getAllMaps(mapfolder)
    return choice(maps)

def getMapsWithPattern(pattern, mapfolder):
    return [x.replace(".pk3", "") for x in getAllMaps(mapfolder) if pattern in x]