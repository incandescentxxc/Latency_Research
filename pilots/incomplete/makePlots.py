import sys
import os
import json
import math
import numpy as np
sys.path.append("../..")
import db
import analyze_logs as al
from create_svg import plotDrags
from incomplete_server import port,dbName

db.updateConnection('localhost:'+str(port),dbName)
logLocation = "/Users/leibatt/vis/code/search-study-data/cclusters-pilot/logs"
toIgnore=[
"c01bd926-126f-11e7-be64-d4ae5273e5cf",
"c73075ec-126e-11e7-a2db-d4ae5273e5cf",
"f6ba2a54-1275-11e7-baa0-d4ae5273e5cf"
]

def makeDelaysString(delays):
  return "_".join([str(int(delays["fast"])),str(int(delays["quick"])),str(int(delays["med"])),str(int(delays["slow"]))])

def getRawLogDataFromFile(userid,formName):
  logName = formName+"_"+userid+".txt"
  with open(os.path.join(logLocation,userid,logName),"r") as f:
    return f.read()
  return None

def getValidUserids():
  completed = db.getCompleted()
  confirmed = db.getConfirmed()
  return [userid for userid in confirmed if userid in completed and userid is not None and userid not in toIgnore]

def renderTest():
  validUserids = getValidUserids()
  for userid in validUserids:
    res = al.parseLog(userid)
    log = res["log"]
    parsedLog = res["parsedLog"]  
    if "dragEnd" not in parsedLog:
      continue
    if len(parsedLog["targetsFoundList"][0]["targetsFoundList"]) == 0:
      continue
    if "initialState" not in parsedLog:
      continue
    params = parsedLog["initialState"][0]
    delays = params["delays"]
    center_loc = params["center_loc"]
    ds = makeDelaysString(delays)
    center_loc = {}
    center_loc["x"] = params["starting_pos"]["x"]*params["imwidth"]+params["svgwidth"]/2.0
    center_loc["y"] = params["starting_pos"]["y"]*params["imheight"]+params["svgheight"]/2.0
    good_loc = parsedLog["initialState"][0]["good_loc"]
    bad_loc = parsedLog["initialState"][0]["bad_loc"]

    plotDrags(userid,ds,os.path.join("images","_".join(["condition","incomplete","latency",ds,"userid",userid])+".png"),parsedLog["dragEnd"],parsedLog["foundButtonClick"],center_loc,good_loc,bad_loc,None)

if __name__ == "__main__":
  renderTest()
