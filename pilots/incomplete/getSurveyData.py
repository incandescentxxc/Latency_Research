import sys
import os
import json
sys.path.append("../..")
import analyze_logs as al
import db
from incomplete_server import port,dbName

db.updateConnection('localhost:'+str(port),dbName)
logLocation = "logs"
toIgnore=[
"c01bd926-126f-11e7-be64-d4ae5273e5cf",
"c73075ec-126e-11e7-a2db-d4ae5273e5cf",
"f6ba2a54-1275-11e7-baa0-d4ae5273e5cf"
]

def makeDelaysString(delays):
  return "_".join([str(delays["fast"]),str(delays["quick"]),str(delays["med"]),str(delays["slow"])])

def getRawLogDataFromFile(userid,formName):
  logName = formName+"_"+userid+".txt"
  with open(os.path.join(logLocation,userid,logName),"r") as f:
    return f.read()
  return None

def getPreTestData(userid):
  #pre-test_01e031a4-40f9-11e9-8ed1-e4434b0071f4.txt
  data = None
  try:
    raw = getRawLogDataFromFile(userid,"pre-test")
    data = json.loads(raw)
    toRemove = ["id","pTime1","pTime2","image_id","devices"]
    for tr in toRemove:
      if tr in data:
        del data[tr]
    for k in data.keys():
      data[k] = data[k][0]
  except:
    pass
  return data

def getPostTestData(userid):
  #post-test_01e031a4-40f9-11e9-8ed1-e4434b0071f4.txt
  data = None
  try:
    raw = getRawLogDataFromFile(userid,"post-test")
    data = json.loads(raw)
  except:
    pass
  return data

def getValidUserids():
  completed = db.getCompleted()
  print len(completed)
  confirmed = db.getConfirmed()
  return [userid for userid in confirmed if userid in completed and userid is not None and userid not in toIgnore]

def evaluateValidUsers():
  validUserids = getValidUserids()
  results = {}
  totals = {}
  print "total valid userids",len(validUserids)
  totalTargetsFound = {}
  total = 0.0
  totalGoodFirst = 0.0
  _testData = []
  for userid in validUserids:
    res = al.parseLog(userid)
    log = res["log"]
    parsedLog = res["parsedLog"]

    if "initialState" in parsedLog:
      params = parsedLog["initialState"][0]
      delays = params["delays"]

    #if "dragEnd" in parsedLog:
    #  print userid,len(parsedLog["dragEnd"]), params["delays"]["slow"]

    if "dragEnd" in parsedLog and "targetsFoundList" in parsedLog and "initialState" in parsedLog:
      if len(parsedLog["targetsFoundList"][0]["targetsFoundList"]) > 0: 
        params = parsedLog["initialState"][0]
        found = parsedLog["targetsFoundList"][0]["targetsFoundList"]
        
        goodFirst = al.goodFoundFirst2(log,parsedLog)["goodFirst"]
        record = {
          "condition":"incomplete",
          "userid":userid,
          "totalInteractions":len(parsedLog["dragEnd"]),
          "foundFastTargetFirst":goodFirst,
          "maxLatency":params["delays"]["slow"],
          "positionOfTarget": "West" if params["good_pos"]["x"] == 2 else "East"
        }
        preTestData = getPreTestData(userid)
        record.update(preTestData)
        _testData.append(record)
        total += 1
        delays = params["delays"]

        # do something in here
        if goodFirst:
          totalGoodFirst += 1
        else:
          #print "insufficient data for user:",userid
          pass
      else:
        #print "insufficient data for user:",userid
        pass
  print totalGoodFirst,"found good first, out of",total,", fraction: ",1.0 * totalGoodFirst/total
  for d in _testData:
    print json.dumps(d)+","
  print "\n\n"
  keys = sorted(_testData[0].keys())
  print ",".join([str(k) for k in keys])
  for d in _testData:
    if d["foundFastTargetFirst"] is not None:
      print ",".join([str(d[k]) if k in d else "" for k in keys])

if __name__ == "__main__":
  if len(sys.argv) == 2:
    logLocation = sys.argv[1]
  evaluateValidUsers()
