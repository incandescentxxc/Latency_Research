import sys
import random

def makeRandomDelays(minThreshold,maxThreshold,denom):
  latencies = {"fast":0,"quick":0,"med":0,"slow":0}
  latencies["slow"] = random.random() * (maxThreshold-minThreshold)+minThreshold
  if latencies["slow"] > 0:
    latencies["med"] = latencies["slow"] / denom
    latencies["quick"] = latencies["med"] / denom
  return latencies

if __name__ == "__main__":
  if len(sys.argv) > 2:
    minThreshold = float(sys.argv[1])
    maxThreshold = float(sys.argv[2])
    denom = 4.0
    for i in range(0,10):
      print (makeRandomDelays(minThreshold,maxThreshold,denom))
  else:
    print ("usage: python makeDelays.py [minThreshold] [maxThreshold]")
    sys.exit(0)
