import sys
import os
import json
sys.path.append("../..")
import db
import analyze_logs as al
from create_svg import plotDrags
from compare_conditions import getValidUserids
from incomplete_server import port,dbName

db.updateConnection('localhost:'+str(port),dbName)

logNames = ["initialState","dragEnd","targetsFoundList","foundButtonClick"]

def dumpLog(log,userid,logName,logPath):
  try:
    os.makedirs(os.path.join(logPath,"user_"+userid))
  except:
    pass
  with open(os.path.join(logPath,"user_"+userid,logName)+".json","w") as f:
    f.write(json.dumps(log))

#need: initialState, dragEnd, targetsFoundList, foundButtonClick
# studyEndButtonClick
def dumpUserData(userid):
  res = al.parseLog(userid)
  log = res["log"]
  parsedLog = res["parsedLog"]

  if "initialState" in parsedLog and "dragEnd" in parsedLog and "targetsFoundList" in parsedLog:
    if len(parsedLog["targetsFoundList"][0]["targetsFoundList"]) > 0: 
      params = parsedLog["initialState"][0]
      found = parsedLog["targetsFoundList"][0]["targetsFoundList"]
      delays = params["delays"]
      goodFirst = al.goodFoundFirst2(log,parsedLog)["goodFirst"]
      with open("../output.csv","a") as f:
        row = ",".join([userid,"incomplete",str(delays["slow"]),"1" if goodFirst else "0"])
        print row
        f.write(row+"\n")

      logPath = os.path.join("interactionLogs","incomplete","case_"+str(delays["slow"]))
      try:
        os.makedirs(logPath)
      except:
        pass
      for ln in logNames:
        dumpLog(parsedLog[ln],userid,ln,logPath)
    else:
      print "insufficient data for user:",userid
  else:
    print "insufficient data for user:",userid
  
def dumpUsers():
  validUserids = getValidUserids()
  print "total valid userids",len(validUserids)
  for userid in validUserids:
    dumpUserData(userid)

if __name__ == "__main__":
  dumpUsers()
