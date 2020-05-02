import sys
import json
import os
sys.path.append("../..")
import db
from incomplete_server import port,localdbName, dbName,spfn,dfn

start_positions = None
delays = None

with open(spfn,"r") as f:
  start_positions = json.loads(f.read())

with open(dfn,"r") as f:
  delays = json.loads(f.read())

uri = os.environ.get('MONGODB_URI')

db.updateConnection('localhost:'+str(port),localdbName)
#db.updateConnection(uri, dbName, retryWrites=False)

db.init(start_positions,delays)
print ("tracker:" + str(db.db.tracker.count()))
