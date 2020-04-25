import sys
import json
import math
import db

db.updateConnection('localhost:5002','search_study_database')
width = 700
height = 700
# log record types
recordTypeList = [
  # stores the state of all initial parameters for the study
  u'initialState',

  # tracks the beginning, middle, and end of every user drag interaction
  u'dragStart',
  u'dragMid',
  u'dragEnd', # has both drag start and drag end point

  # tracks the position of the center of the viewport throughout 
  # the start, middle, and end of every drag interaction
  u'visPosition',

  # tracks the paths from the center of the viewport
  # to both the good location and to the bad location.
  # includes the shifted paths used to calculate swaths.
  # used to calculate path-based delays
  u'delayPaths',

  # records every tile that gets added to the visualization, and when
  u'tileAddition',

  # records every tile that gets removed from the visualization, and when
  u'tileRemoval',

  # records when the user hit the found button, and center of viewport
  u'foundButtonClick',
  #records when and where the user clicked the mouse, and the current
  # position of the viewport, after the user hit the found button
  u'answerMouseClick',

  # records when the user finished the study, and center of viewport
  u'studyEndButtonClick',

  # the explicit list of targets found by the participant, in grid positions
  u'targetsFoundList'
]

# given a log from mongodb parse the log, separating the records by log type
# also track the original log order, so we can use it for time analysis
def parseTrainingLog(userid):
  parsedLog = {}
  log = db.getOrderedTrainingLog(userid)
  for record in log:
    recordType = record["recordType"]
    if recordType not in parsedLog:
      parsedLog[recordType] = []
    parsedLog[recordType].append(record)
  #print parsedLog.keys()
  return {"log":log,"parsedLog":parsedLog}

# given a log from mongodb parse the log, separating the records by log type
# also track the original log order, so we can use it for time analysis
def parseLog(userid):
  parsedLog = {}
  log = db.getOrderedLog(userid)
  for record in log:
    recordType = record["recordType"]
    if recordType not in parsedLog:
      parsedLog[recordType] = []
    parsedLog[recordType].append(record)
  #print parsedLog.keys()
  return {"log":log,"parsedLog":parsedLog}

# returns a list of the good and bad positions found by the user, based solely on found button clicks
def calculateAnswerPositionsFromFoundClicks(log,parsedLog):
  if "initialState" not in parsedLog or "foundButtonClick" not in parsedLog:
    return None
  gbp = getGoodBadPos(log,parsedLog)
  if gbp is None:
    return None
  params = parsedLog["initialState"][0]
  svgwidth = params["svgwidth"]
  svgheight = params["svgheight"]
  imwidth = params["imwidth"]
  imheight = params["imheight"]
  gridxlen = len(params["pixelOrdersX"])
  gridylen = len(params["pixelOrdersY"][0])
  #{"userid":userid,"recordType":"foundButtonClick","svgwidth":width,"svgheight":height,"stagingLoc":{"x":staging_loc.x,"y":staging_loc.y}
  found = []
  # for each found button click
  for record in parsedLog["foundButtonClick"]:
    stagingLoc = record["stagingLoc"]
    print stagingLoc
    x = stagingLoc["x"]
    y = stagingLoc["y"]
    minp ={
      "x":x-svgwidth/2.0,
      "y":y-svgheight/2.0
    }
    maxp ={
      "x":x+svgwidth/2.0,
      "y":y+svgheight/2.0
    }
    minxpos = int(max(math.floor(minp["x"] / imwidth),0.0))
    minypos = int(max(math.floor(minp["y"] / imheight),0.0))
    maxxpos = int(min(math.floor(maxp["x"] / imwidth),gridxlen))
    maxypos = int(min(math.floor(maxp["y"] / imheight),gridylen))
    print minxpos,maxxpos,minypos,maxypos
    # iterate over all grid positions
    for i in range(minxpos,maxxpos+1):
      if i != gbp["goodPos"]["x"] and i != gbp["badPos"]["x"]:
        continue
      for j in range(minypos,maxypos+1):
        if j != gbp["goodPos"]["y"] and j != gbp["badPos"]["y"]:
          continue
        # matches good pos
        if i == gbp["goodPos"]["x"] and j == gbp["goodPos"]["y"]:
          found.append({"gb":"good","gridx":i,"gridy":j})
        if i == gbp["badPos"]["x"] and j == gbp["badPos"]["y"]:
          found.append({"gb":"bad","gridx":i,"gridy":j})
    print gbp
    print found
    # if the user didn't find both pictures, or found the same picture twice
    if len(found) != 2 or found[0]["gb"] == found[1]["gb"]:
      return []
    return found

# for this log, did the user find the good position first?
def goodFoundFirst2(log,parsedLog):
  gbp = getGoodBadPos(log,parsedLog)
  found = parsedLog["targetsFoundList"][0]["targetsFoundList"]
  if gbp is None:
    return None
  return {"goodFirst":len(found) > 0 and found[0]["x"] == gbp["goodPos"]["x"] and found[0]["y"] == gbp["goodPos"]["y"],
    "completeAnswers":len(found)>0}

# NOTE: this is old, do not use this function. It is broken.
# for this log, did the user find the good position first?
def goodFoundFirst(log,parsedLog):
  found = calculateAnswerPositionsFromFoundClicks(log,parsedLog)
  return {"goodFirst":len(found) > 0 and found[0]["gb"] == "good","completeAnswers":len(found)>0}

# calculate how long the participant took to complete the study
def calculateStudyDuration(log,parsedLog):
  if "initialState" not in parsedLog or "studyEndButtonClick" not in parsedLog or \
    "dragStart" not in parsedLog or "dragEnd" not in parsedLog or \
    len(parsedLog["initialState"][0]) == 0 or \
    len(parsedLog["studyEndButtonClick"]) == 0 or len(parsedLog["dragStart"]) == 0 or \
    len(parsedLog["dragEnd"][-1]) == 0:
    return None
  initialTimestamp = parsedLog["initialState"][0]["timestamp"]
  studyEndTimestamp = parsedLog["studyEndButtonClick"][-1]["timestamp"]
  initialInteractionTimestamp = parsedLog["dragStart"][0]["timestamp"]
  finalInteractionTimestamp = parsedLog["dragEnd"][-1]["timestamp"]
  return {
    "outer-duration":studyEndTimestamp-initialTimestamp,
    "inner-duration":finalInteractionTimestamp-initialInteractionTimestamp
  }

# find the grid positions and pixel positions of the good answer and bad answer
def getGoodBadPos(log,parsedLog):
  if "initialState" not in parsedLog:
    return None
  goodPos = parsedLog["initialState"][0]["good_pos"]
  goodLoc = parsedLog["initialState"][0]["good_loc"]
  badPos = parsedLog["initialState"][0]["bad_pos"]
  badLoc = parsedLog["initialState"][0]["bad_loc"]
  return {
    "goodPos":goodPos,
    "goodLoc":goodLoc,
    "badPos":badPos,
    "badLoc":badLoc
  }

def halfLineStatsPerRecord(dragEndRecord,halfLine,goodp,badp):
  startStagingLoc = dragEndRecord["prevStagingLoc"]
  endStagingLoc = dragEndRecord["stagingLoc"]
  return {
  "startGoodHalf": pointSameSideOfHalfLine(halfLine["a"],halfLine["b"],
    goodp,startStagingLoc),
  "endGoodHalf": pointSameSideOfHalfLine(halfLine["a"],halfLine["b"],
    goodp,endStagingLoc),
  "startBadHalf": pointSameSideOfHalfLine(halfLine["a"],halfLine["b"],
    badp,startStagingLoc),
  "endBadHalf": pointSameSideOfHalfLine(halfLine["a"],halfLine["b"],
    badp,endStagingLoc)
  }

def halfLineStats(log,parsedLog):
  goodp = parsedLog["initialState"][0]["good_loc"]
  badp = parsedLog["initialState"][0]["bad_loc"]
  halfLine = parsedLog["initialState"][0]["halfLine"]
  baseStats = {
    "onGoodSide": 0,
    "onBadSide": 0,
    "goodToBad": 0,
    "badToGood": 0,
    "goodToNeutral": 0,
    "badToNeutral": 0,
    "neutralToGood": 0,
    "neutralToBad": 0,
    "neutral": 0
  }
  firstStats = baseStats.copy() # copies actual values for primitives
  secondStats = baseStats.copy() # copies actual values for primitives
  endStats = baseStats.copy() # copies actual values for primitives
  firstFound = parsedLog["foundButtonClick"][0]["timestamp"]
  secondFound = parsedLog["foundButtonClick"][1]["timestamp"]
  # for each record
  for r in parsedLog["dragEnd"]:
    stats = None
    if r["timestamp"] < firstFound:
      stats = firstStats
    elif r["timestamp"] < secondFound:
      stats = secondStats
    else:
      stats = endStats
    res = halfLineStatsPerRecord(r,halfLine,goodp,badp)
    if res["startGoodHalf"] and res["endGoodHalf"]:
      stats["onGoodSide"] += 1
    elif res["startBadHalf"] and res["endBadHalf"]:
      stats["onBadSide"] += 1
    elif res["startGoodHalf"] and res["endBadHalf"]:
      stats["goodToBad"] += 1
    elif res["startBadHalf"] and res["endGoodHalf"]:
      stats["badToGood"] += 1
    elif res["startGoodHalf"]:
      stats["goodToNeutral"] += 1
    elif res["startBadHalf"]:
      stats["badToNeutral"] += 1
    elif res["endGoodHalf"]:
      stats["neutralToGood"] += 1
    elif res["endBadHalf"]:
      stats["neutralToBad"] += 1
    else:
      neutral += 1
  return {
    "firstStats":firstStats,
    "secondStats":secondStats,
    "endStats":endStats
  }

def matchOctantPerRecord(dragEndRecord,goodp,badp):
  startStagingLoc = dragEndRecord["prevStagingLoc"]
  endStagingLoc = dragEndRecord["stagingLoc"]
  o = getOctant(startStagingLoc,endStagingLoc)
  goodo = getOctant(startStagingLoc,goodp)
  bado = getOctant(startStagingLoc,badp)
  return {"o":o,"goodo":goodo,"bado":bado}

def matchOctantStrict(log,parsedLog):
  if "initialState" not in parsedLog or "dragEnd" not in parsedLog:
    return None
  goodp = parsedLog["initialState"][0]["good_loc"]
  badp = parsedLog["initialState"][0]["bad_loc"]
  baseStats = {
    "matchGood": 0,
    "matchBad": 0,
    "total": 0
  }
  firstStats = baseStats.copy() # copies actual values for primitives
  secondStats = baseStats.copy() # copies actual values for primitives
  endStats = baseStats.copy() # copies actual values for primitives
  firstFound = -1
  secondFound = -1
  if "foundButtonClick" in parsedLog:
    firstFound = parsedLog["foundButtonClick"][0]["timestamp"]
    secondFound = firstFound + 1
    if len(parsedLog["foundButtonClick"]) == 2:
      secondFound = parsedLog["foundButtonClick"][1]["timestamp"]
  if firstFound < 0:
    if 'studyEndButtonClick' in parsedLog:
      firstFound = parsedLog["studyEndButtonClick"][0]["timestamp"]
      secondFound = firstFound + 1
    else: # no valid data
      return None

  for r in parsedLog["dragEnd"]:
    stats = None
    if r["timestamp"] < firstFound:
      stats = firstStats
    elif r["timestamp"] < secondFound:
      stats = secondStats
    else:
      stats = endStats
    res = matchOctantPerRecord(r,goodp,badp)
    if res["o"] == "C":
      #print "skipping C"
      continue
    if res["o"] == res["goodo"]:
      stats["matchGood"] += 1
    elif res["o"] == res["bado"]:
      stats["matchBad"] += 1
    stats["total"] +=1
  return {
    "firstStats":firstStats,
    "secondStats":secondStats,
    "endStats":endStats
  }

def matchOctantFlexible(log,parsedLog):
  if "initialState" not in parsedLog or "dragEnd" not in parsedLog:
    return None
  goodp = parsedLog["initialState"][0]["good_loc"]
  badp = parsedLog["initialState"][0]["bad_loc"]
  baseStats = {
    "matchGood": 0,
    "matchBad": 0,
    "both":0,
    "total": 0
  }
  firstStats = baseStats.copy() # copies actual values for primitives
  secondStats = baseStats.copy() # copies actual values for primitives
  endStats = baseStats.copy() # copies actual values for primitives
  firstFound = -1
  secondFound = -1
  if "foundButtonClick" in parsedLog:
    firstFound = parsedLog["foundButtonClick"][0]["timestamp"]
    secondFound = firstFound + 1
    if len(parsedLog["foundButtonClick"]) == 2:
      secondFound = parsedLog["foundButtonClick"][1]["timestamp"]
  if firstFound < 0:
    if 'studyEndButtonClick' in parsedLog:
      firstFound = parsedLog["studyEndButtonClick"][0]["timestamp"]
      secondFound = firstFound + 1
    else: # no valid data
      return None

  for r in parsedLog["dragEnd"]:
    stats = None
    if r["timestamp"] < firstFound:
      stats = firstStats
    elif r["timestamp"] < secondFound:
      stats = secondStats
    else:
      stats = endStats
    res = matchOctantPerRecord(r,goodp,badp)
    if res["o"] == "C":
      continue
    odirs = getDirs(res["o"])
    gdirs = getDirs(res["goodo"])
    bdirs = getDirs(res["bado"])
    found = False
    for d in odirs:
      if d in gdirs:
        found = True
        break
    for d in odirs:
      if d in bdirs:
        if found:
          stats["both"] += 1
          found = False
        else:
          stats["matchBad"] += 1
        break
    if found:
      stats["matchGood"] += 1
    stats["total"] +=1
  return {
    "firstStats":firstStats,
    "secondStats":secondStats,
    "endStats":endStats
  }

# tells you whether the target (good/bad) and the regular point
# are on the same side of the given line
def pointSameSideOfHalfLine(l1,l2,t,p):
  def F(x,y): return (l2["y"]-l1["y"])*x + \
    (l1["x"]-l2["x"])*y + (l2["x"]*l1["y"] - l1["x"]*l2["y"])
  # target tracker
  gtzt = 0; ltzt = 0; eqzt = 0
  # regular tracker
  gtz = 0; ltz = 0; eqz = 0
  val = F(t["x"],t["y"])
  if val > 0:
    gtzt += 1
  elif val < 0:
    ltzt += 1
  else:
    eqzt += 1 # should never happen!
    console.log("reached invalid state")

  val = F(p["x"],p["y"]);
  if(val > 0):
    gtz += 1
  elif val < 0:
    ltz += 1
  else:
    eqz += 1

  # all points of the polygon are on the same side as the target
  # any points that are not on the same side means that the polygon intersects the line
  return (gtzt > 0) and (gtz > 0) \
    or (ltzt > 0) and (ltz > 0)

def getOctant(dragStart,dragEnd):
  newDragStart = getNormalizedDragStart(dragStart,dragEnd)
  part = getPartition(newDragStart)
  if part is None:
    print "partition not found for pan action:",state
    return None
  return part

# lays out additional directions to check
def getDirs(o):
  if o in ["N","S","E","W"]:
    return o
  elif o == "NE":
    return ["NE","N","E"]
  elif o == "NW":
    return ["NW","N","W"]
  elif o == "SE":
    return ["SE","S","E"]
  else:
    return ["SW","S","W"]
  
###################################################
####### Repurposed ForeCache Analysis Code ########
lines = {
'a': (lambda x: x*50.0/(width / 2.0)),
'b': (lambda x: x*-50.0/(width / 2.0)),
'c': (lambda x: x* -1.0* (height / 2.0) / 50.0),
'd': (lambda x: x * (height / 2.0) / 50.0)
}
boundaries = {
'E':(lambda x,y: (x > 0) and (y >= lines['b'](x)) and (y <= lines['a'](x))),
'W':(lambda x,y: (x < 0) and (y >= lines['a'](x)) and (y <= lines['b'](x))),
'N':(lambda x,y: (y > 0) and (y >= lines['c'](x)) and (y >= lines['d'](x))),
'S':(lambda x,y: (y < 0) and (y <= lines['c'](x)) and (y <= lines['d'](x))),
'NE':(lambda x,y: (y > 0) and (x > 0) and (y >= lines['a'](x)) and (y <= lines['d'](x))),
'SW':(lambda x,y: (y < 0) and (x < 0) and (y <= lines['a'](x)) and (y >= lines['d'](x))),
'SE':(lambda x,y: (y < 0) and (x > 0) and (y >= lines['c'](x)) and (y <= lines['b'](x))),
'NW':(lambda x,y: (y > 0) and (x < 0) and (y >= lines['b'](x)) and (y <= lines['c'](x)))
}

def inPartE(x,y):
  return (x > 0) and (y >= lines['b'](x)) and (y <= lines['a'](x))

def inPartW(x,y):
  return (x < 0) and (y >= lines['a'](x)) and (y <= lines['b'](x))

def inPartN(x,y):
  return (y > 0) and (y >= lines['c'](x)) and (y >= lines['d'](x))

def inPartS(x,y):
  return (y < 0) and (y <= lines['c'](x)) and (y <= lines['d'](x))

def inPartNE(x,y):
  return (y > 0) and (x > 0) and (y >= lines['a'](x)) and (y <= lines['d'](x))

def inPartSW(x,y):
  return (y < 0) and (x < 0) and (y <= lines['a'](x)) and (y >= lines['d'](x))

def inPartNW(x,y):
  return (y > 0) and (x < 0) and (y >= lines['b'](x)) and (y <= lines['c'](x))

def inPartSE(x,y):
  return (y < 0) and (x > 0) and (y >= lines['c'](x)) and (y <= lines['b'](x))

def getPartition(startPos):
  x = startPos["x"]
  y = startPos["y"]
  if x == 0 and y == 0:
    return 'C' # stayed in the center, i.e., did nothing 
  for q in boundaries:
    if boundaries[q](x,y):
      return q
  return None

def getNormalizedDragStart(dragStart,dragEnd):
  dx = dragEnd["x"] - dragStart["x"]
  dy = dragEnd["y"] - dragStart["y"]
  mid = {"x":dragStart["x"]+dx/2.0,"y":dragStart["y"]+dy/2.0}
  # translate the midpoint
  return {"x":dragStart["x"] - mid["x"], "y":dragStart["y"] - mid["y"]}

####### End Repurposed ForeCache Analysis Code ########
#######################################################


if __name__ == "__main__":
  #logFileName = sys.argv[1]
  #res = parseLog(logFileName)
  userid = sys.argv[1]
  res = parseLog(userid)
  log = res["log"]
  parsedLog = res["parsedLog"]
  print parsedLog["targetsFoundList"]
  print calculateStudyDuration(log,parsedLog)
  calculateAnswerPositionsFromFoundClicks(log,parsedLog)
  print goodFoundFirst2(log,parsedLog)
  print halfLineStats(log,parsedLog)
  #print matchOctantStrict(log,parsedLog)
  print matchOctantFlexible(log,parsedLog)
