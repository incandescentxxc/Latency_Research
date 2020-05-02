from pymongo import MongoClient
import json

MONGODB_URI = None  # 'localhost'
client = MongoClient(MONGODB_URI)
db = None  # client['forecache_userstudy_database']


# used for deployment
def updateConnection(uri, dbname, retryWrites=False):
    global MONGODB_URI, db
    MONGODB_URI = uri
    client = MongoClient(MONGODB_URI, retryWrites=retryWrites)
    db = client[dbname]


def init(start_positions, delays):
    initializeTracking(start_positions, delays)
    try:
        db.confirmed.remove()
    except:
        pass
    try:
        db.claims.remove()
    except:
        pass
    try:
        db.completed.remove()
    except:
        pass
    try:
        db.puzzle.remove()
    except:
        pass
    try:
        db.training.remove()
    except:
        pass


def initializeTracking(start_positions, delays):
    try:
        db.tracker.remove()
    except:
        pass

    for i in range(len(start_positions)):
        for j in range(len(delays)):
            print (i, j)
            db.tracker.insert_one({"pos": {"sp": i, "d": j}, "count": 0})


def initializeSptracker(start_positions):
    try:
        db.sptracker.remove()
    except:
        pass
    for i in range(len(start_positions)):
        db.sptracker.insert({"pos": i, "count": 0})


def initializeDtracker(delays):
    try:
        db.dtracker.remove()
    except:
        pass

    for i in range(len(delays)):
        db.dtracker.insert({"pos": i, "count": 0})


def updateTracker():
    val = db.tracker.find_and_modify(query={}, sort={"count": 1}, update={"$inc": {"count": 1}}, upsert=True)
    return val["pos"]


# gets the position with the lowest count
def updateSptracker():
    val = db.sptracker.find_and_modify(query={}, sort={"count": 1}, update={"$inc": {"count": 1}})
    return val["pos"]


def updateDtracker():
    val = db.dtracker.find_and_modify(query={}, sort={"count": 1}, update={"$inc": {"count": 1}})
    return val["pos"]


def saveConfirmed(userid, timestampMillis):
    db.confirmed.update({"userid": userid}, {"userid": userid, "timestampMillis": timestampMillis}, upsert=True)


def saveClaimed(userid, timestampMillis):
    db.claims.update({"userid": userid}, {"userid": userid, "timestampMillis": timestampMillis}, upsert=True)


def saveCompleted(userid, timestampMillis):
    db.completed.update({"userid": userid}, {"userid": userid, "timestampMillis": timestampMillis}, upsert=True)


def saveForm(userid, formName, formDict, timestampMillis):
    db.forms.insert({"userid": userid, "formName": formName, "formData": formDict, "timestampMillis": timestampMillis})


def saveLogBatch(userid, batchId, batchData):
    db.puzzle.insert({"userid": userid, "batchId": batchId, "batchData": batchData})


def saveTrainingLogBatch(userid, batchId, batchData):
    db.training.insert({"userid": userid, "batchId": batchId, "batchData": batchData})


def checkIfValid(userid):
    return db.confirmed.find_one({"userid": userid}) is not None


def checkIfFinished(userid):
    return db.completed.find_one({"userid": userid}) is not None


def checkIfClaimed(userid):
    return db.claimed.find_one({"userid": userid}) is not None


# WARNING: not atomic!
def claimConfirmationCode(confcode):
    doClaim = False
    confcode = str(request.args.get('confcode'))
    doClaim = db.checkIfValid(confcode) and db.checkIfFinished(confcode) and (not db.checkIfClaimed(confcode))
    if doClaim:
        db.saveClaimed(confcode)
    return doClaim


def getOrderedLog(userid):
    answers = db.puzzle.find({"userid": userid})
    puzzleDict = {}
    for a in answers:
        puzzleDict[int(a["batchId"])] = a["batchData"]
    results = []
    for batchId in sorted(puzzleDict.keys()):
        results.extend(puzzleDict[batchId])
    return results


def getOrderedTrainingLog(userid):
    answers = db.training.find({"userid": userid})
    trainingDict = {}
    for a in answers:
        trainingDict[int(a["batchId"])] = a["batchData"]
    results = []
    for batchId in sorted(trainingDict.keys()):
        results.extend(trainingDict[batchId])
    return results


def getCompleted():
    completed = db.completed.find()
    result = []
    for c in completed:
        result.append(c["userid"])
    return result


def getConfirmed():
    confirmed = db.completed.find()
    result = []
    for c in confirmed:
        result.append(c["userid"])
    return result


'''
def savePerfLogs(userid,taskname,logs):
  #userid = content['userid']
  #taskname = content['taskname']
  #logs = content['logs']

  currentLogs = db.current_logs
  logEntry = currentLogs.find_one({"userid":userid,"taskname":taskname})
  if logEntry is None:
    currentLogs.insert({"userid":userid,"taskname":taskname,"logs":logs})
  else:
    for logName in logs:
      if logName in logEntry['logs']:
        logEntry['logs'][logName].extend(logs[logName])
      else:
        logEntry['logs'][logName] = logs[logName]
    currentLogs.update({'userid':userid,"taskname":taskname}, {"$set": logEntry}, upsert=False)

def recordTaskTimestamp(userid,taskname,timestampMillis,state):
  db.task_timings.insert({"timestampMilis":timestampMillis,"state":state,"userid":userid,"taskname":taskname})

def saveSnapshots(snapshots):
  if len(snapshots) > 0:
    db.snapshots.insert_many(snapshots)

###### For Analysis #######
def getUserids():
  userids = db.userids.find()
  results = []
  for record in userids:
    results.append(record['userid'])
  return results

def getAnswers():
  answers = db.task_answers.find()
  results = []
  for record in answers:
    results.append(record)
  return results

def getAnswersForUserAndTask(userid,taskname):
  answers = db.task_answers.find({"userid":userid,"taskname":taskname})
  results = []
  for record in answers:
    results.append(record)
  return results

def getPerfLogsCursor():
  return db.current_logs.find()

def getPerfLogs():
  currentLogs = db.current_logs.find()
  results = []
  for record in currentLogs:
    results.append(record)
  return results

def getPerfLogsForUserAndTask(userid,taskname):
  currentLogs = db.current_logs
  logEntry = currentLogs.find_one({"userid":userid,"taskname":taskname})
  return logEntry

def getTaskTimings(userid,taskname):
  timings = db.task_timings.find({"userid":userid,"taskname":taskname})
  results = []
  for record in timings:
    results.append(record)
  return results

def getSnapshotsForUserAndTask(userid,taskname):
  snapshots = db.snapshots.find({"userid":userid,"taskname":taskname})
  results = []
  for record in snapshots:
    results.append(record)
  return results

def getSnapshots():
  snapshots = db.snapshots.find()
  results = []
  for record in snapshots:
    results.append(record)
  return results
'''
