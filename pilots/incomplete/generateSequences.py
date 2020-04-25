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
from compare_conditions import getValidUserids

db.updateConnection('localhost:'+str(port),dbName)
logLocation = "/Users/leibatt/vis/code/search-study-data/inthint-pilot/logs"
toIgnore = [
]

def getGBString(parsedLog):
  if "initialState" not in parsedLog or "dragEnd" not in parsedLog:
    return None
  goodp = parsedLog["initialState"][0]["good_loc"]
  badp = parsedLog["initialState"][0]["bad_loc"]
  sequence = []
  for r in parsedLog["dragEnd"]:
    res = al.matchOctantPerRecord(r,goodp,badp)
    if res["o"] == "C":
      #print "skipping C"
      continue
    if res["o"] == res["goodo"]:
      sequence.append("G")
    elif res["o"] == res["bado"]:
      sequence.append("B")
    else:
      sequence.append("N")
  return sequence

def generateGBSequence(log,parsedLog):
  seq = getGBString(parsedLog)
  if seq is None:
    return None
  params = parsedLog["initialState"][0]
  delays = params["delays"]
  goodFirst = al.goodFoundFirst2(log,parsedLog)["goodFirst"]
  res = ["incomplete",str(delays["slow"]),str(goodFirst)]
        
  res.extend(seq)
  return res

def generateGBSequences():
  validUserids = getValidUserids()
  sequences = []
  for userid in validUserids:
    res = al.parseLog(userid)
    log = res["log"]
    parsedLog = res["parsedLog"]
    if "dragEnd" in parsedLog and "targetsFoundList" in parsedLog:
      if len(parsedLog["targetsFoundList"][0]["targetsFoundList"]) > 0:
        seq = generateGBSequence(log,parsedLog)
        if seq is None:
          continue
        sequences.append(seq)
  return sequences

def writeSequenceFile():
  sequences = generateGBSequences()
  with open("incomplete.csv","w") as f:
    for seq in sequences:
      if len(seq) > 0:
        s = ",".join(seq)
        f.write(s+"\n")

if __name__ == "__main__":
  writeSequenceFile()
