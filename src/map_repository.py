import glob
import os

def getMapPath(mapfile, mapfolder):
    if (not ".pk3" in mapfile):
        mapfile+=".pk3"
    return f"{mapfolder}/{mapfile}"

def getAllMaps(mapfolder):
    path = f"{mapfolder}/*.pk3"
    maps = [os.path.basename(urtmap) for urtmap in glob.glob(path)]
    maps.sort()
    return maps