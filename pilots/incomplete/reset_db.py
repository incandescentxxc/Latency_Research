import sys
import json
sys.path.append("../..")
import db
from incomplete_server import port,dbName,spfn,dfn

start_positions = None
delays = None

with open(spfn,"r") as f:
  start_positions = json.loads(f.read())

with open(dfn,"r") as f:
  delays = json.loads(f.read())

db.updateConnection('localhost:'+str(port),dbName)
db.init(start_positions,delays)
print ("tracker:" + str(db.db.tracker.count()))
