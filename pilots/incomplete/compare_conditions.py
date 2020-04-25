import sys
import os
import json
import math
import numpy as np
sys.path.append("../..")
import db
import analyze_logs as al
#from create_svg import plotDrags
from incomplete_server import port,dbName
#from incomplete_server import dbName
#port = 5020

db.updateConnection('localhost:'+str(port),dbName)
logLocation = "/Users/leibatt/vis/code/search-study-data/inthint-pilot/logs"
toIgnore=[
"c01bd926-126f-11e7-be64-d4ae5273e5cf",
"c73075ec-126e-11e7-a2db-d4ae5273e5cf",
"f6ba2a54-1275-11e7-baa0-d4ae5273e5cf"
]
'''
toIgnore = [
"1a103f54-0f5e-11e7-b8cf-d4ae5273e5cf",
"e544df0e-0f8b-11e7-9935-d4ae5273e5cf",
"de0ad0b0-0f8e-11e7-a1aa-d4ae5273e5cf",
"2697b34c-0f8b-11e7-802a-d4ae5273e5cf",
"ce56b72a-0f74-11e7-abf3-d4ae5273e5cf"
"894d6abc-0f4b-11e7-b749-d4ae5273e5cf",
"4064f5cc-0f8c-11e7-b383-d4ae5273e5cf",
"d39fcb92-0f8b-11e7-a1aa-d4ae5273e5cf",
"6783be7c-0f8c-11e7-9935-d4ae5273e5cf",
"2a44bd5c-0f98-11e7-a1aa-d4ae5273e5cf",
"7252dd5c-0f95-11e7-94a7-d4ae5273e5cf",
"ab641962-0f40-11e7-802a-d4ae5273e5cf",
"abbff17c-0f97-11e7-b383-d4ae5273e5cf",
"c8b8116c-0f8b-11e7-8e96-d4ae5273e5cf",
"b07d0cca-0f44-11e7-802a-d4ae5273e5cf",
"a4c14262-0f48-11e7-b097-d4ae5273e5cf",
"65a7a422-0f43-11e7-b8cf-d4ae5273e5cf",
"d103bd94-0f8b-11e7-b383-d4ae5273e5cf",
"b166e45c-0f40-11e7-88ae-d4ae5273e5cf"
]
'''

def makeDelaysString(delays):
  return "_".join([str(delays["fast"]),str(delays["quick"]),str(delays["med"]),str(delays["slow"])])

def getRawLogDataFromFile(userid,formName):
  logName = formName+"_"+userid+".txt"
  with open(os.path.join(logLocation,userid,logName),"r") as f:
    return f.read()
  return None

def getValidUserids():
  completed = db.getCompleted()
  print len(completed)
  confirmed = db.getConfirmed()
  return [userid for userid in confirmed if userid in completed and userid is not None and userid not in toIgnore]

'''
def renderTest():
  validUserids = getValidUserids()
  for userid in validUserids:
    res = al.parseLog(userid)
    log = res["log"]
    parsedLog = res["parsedLog"]  
    if "dragEnd" not in parsedLog:
      continue
    #if len(parsedLog["targetsFoundList"][0]["targetsFoundList"]) == 0:
    #  continue
    params = parsedLog["initialState"][0]
    delays = params["delays"]
    center_loc = params["center_loc"]
    good_loc = params["good_loc"]
    bad_loc = params["bad_loc"]
    ds = makeDelaysString(delays)
    center_loc = {}
    center_loc["x"] = params["starting_pos"]["x"]*params["imwidth"]+params["svgwidth"]/2.0
    center_loc["y"] = params["starting_pos"]["y"]*params["imheight"]+params["svgheight"]/2.0
    #spatialGrade = getSpatialGrade(userid)

    #plotDrags(userid,ds,"images",parsedLog["dragEnd"],parsedLog["foundButtonClick"],center_loc,spatialGrade)
    fbc = []
    if "foundButtonClick" in parsedLog:
      fbc = parsedLog["foundButtonClick"]
    plotDrags(userid,ds,"images/puzzle/"+ds+"/",parsedLog["dragEnd"],fbc,center_loc,good_loc,bad_loc,0)
'''

def evaluateValidUsers():
  validUserids = getValidUserids()
  results = {}
  totals = {}
  print "total valid userids",len(validUserids)
  totalTargetsFound = {}
  imatch = {}
  total = 0.0
  totalGoodFirst = 0.0
  _testData = []
  completed = 0
  all_users = 0
  for userid in validUserids:
    res = al.parseLog(userid)
    log = res["log"]
    parsedLog = res["parsedLog"]
    #spatialGrade = getSpatialGrade(userid)
    sts= al.matchOctantStrict(log,parsedLog)
    #sts= al.matchOctantFlexible(log,parsedLog)
    if sts is not None and "initialState" in parsedLog:
      params = parsedLog["initialState"][0]
      delays = params["delays"]
      #print "params:",params.keys()
      #print "good_pos:",params["good_pos"]
      ds = makeDelaysString(delays)
      if ds not in imatch:
        imatch[ds] = {"badInteractions":0,"goodInteractions":0,"goodVBad":[]}
      case = "firstStats"
      if sts[case]["total"] > 0:
        imt = (sts[case]["matchBad"]+sts[case]["matchGood"])
        if imt > 0:
          imatch[ds]["badInteractions"] += sts[case]["matchBad"] * 1.0 / imt
          imatch[ds]["goodInteractions"] += sts[case]["matchGood"] * 1.0 / imt
        imatch[ds]["goodVBad"].append(sts[case]["matchGood"] * 1.0 / max(sts[case]["matchBad"],1))

    if "initialState" in parsedLog:
      params = parsedLog["initialState"][0]
      delays = params["delays"]
      ds = makeDelaysString(delays)
      if ds not in totalTargetsFound:
        totalTargetsFound[ds] = {}
      ttf = 0
      if "targetsFoundList" in parsedLog:
        ttf = len(parsedLog["targetsFoundList"][0]["targetsFoundList"])
        #print "targets found:",ttf,parsedLog["targetsFoundList"]
      if ttf not in totalTargetsFound[ds]:
        totalTargetsFound[ds][ttf] = 1
      else:
        totalTargetsFound[ds][ttf] += 1

    if "dragEnd" in parsedLog:
      all_users += 1
      print userid,len(parsedLog["dragEnd"]), params["delays"]["slow"]

    if "dragEnd" in parsedLog and "targetsFoundList" in parsedLog and "initialState" in parsedLog:
      if len(parsedLog["targetsFoundList"][0]["targetsFoundList"]) > 0: 
        completed += 1
        params = parsedLog["initialState"][0]
        #print parsedLog["dragEnd"][0]
        found = parsedLog["targetsFoundList"][0]["targetsFoundList"]
        
        goodFirst = al.goodFoundFirst2(log,parsedLog)["goodFirst"]
	_testData.append({"userid":userid,"totalInteractions":len(parsedLog["dragEnd"]),"foundFastTargetFirst":goodFirst,"maxLatency":params["delays"]["slow"],"positionOfTarget": "West" if params["good_pos"]["x"] == 2 else "East"})
	total += 1
        delays = params["delays"]
	#print "\t",userid,len(parsedLog["dragEnd"]), delays["slow"],goodFirst
        ds = makeDelaysString(delays)
        if ds not in results:
          results[ds] = 0
          totals[ds] = 1
        else:
          totals[ds] += 1
        if goodFirst:
          results[ds] += 1
	  totalGoodFirst += 1
      else:
        print "insufficient data for user:",userid
    else:
      print "insufficient data for user:",userid
  print totalGoodFirst,"found good first, out of",total,", fraction: ",1.0 * totalGoodFirst/total
  for d in _testData:
    print json.dumps(d)+","
  print "\n\n"
  print "userid,condition,maxLatency,positionOfTarget,foundFastTargetFirst"
  for d in _testData:
    if d["foundFastTargetFirst"] is not None:
      print ",".join([d["userid"],"incomplete",str(d["maxLatency"]),str(d["positionOfTarget"]),str(int(d["foundFastTargetFirst"]))])

  print "good found first:",results
  print "everyone:",totals
  print "completed:",completed,", all participants:",all_users
  print "total people that found 0, 1, or 2 targets:",totalTargetsFound
'''
  for ds in imatch:
    print "case:",ds
    print "\tmedian('good' interactions / 'bad' interactions):",np.median(imatch[ds]["goodVBad"])
    print "\tmean('good' interactions / 'bad' interactions):",np.mean(imatch[ds]["goodVBad"])
    print "\tstdev('good' interactions / 'bad' interactions):",np.std(imatch[ds]["goodVBad"])
    print "\t'good' interactions / 'bad' interactions:",sorted(imatch[ds]["goodVBad"])
'''
'''
    print userid
    print "delays: ",params["delays"]
    found = parsedLog["targetsFoundList"][0]["targetsFoundList"]
    print "foundList:",found
    if "foundButtonClick" in parsedLog:
      print "foundButtonClick: ",parsedLog["foundButtonClick"]
    else:
      print "foundButtonClick: ",[]
    if "dragEnd" in parsedLog:
      print "\t"+str(len(parsedLog["dragEnd"]))
    else:
      print "\t0"
    #print al.goodFoundFirst2(log,parsedLog)
'''

if __name__ == "__main__":
  if len(sys.argv) == 2:
    logLocation = sys.argv[1]
  #gradeObj = evaluateSpatialScores()
  #evaluateValidUsersTraining()
  evaluateValidUsers()
  #renderTest()
  #renderTestTraining()
