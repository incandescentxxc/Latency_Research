import uuid
import os, sys
from flask import Flask, Response, request, session, send_file, make_response, render_template, url_for, redirect
from math import sqrt
import random
import numpy as np
from scipy.interpolate import griddata
import json
import time

sys.path.append("../..")
import makeDelays
import db

# collage_root="/data/scidb/000/2/user_study_images/"
# collage_root="/Users/leibatt/vis/code/search-study-data"
# collage_root="/Users/leibatt/code/search-study-data/"
collage_root = "../../"

spfn = "../../start_positions_pilot.json"
dfn = "../../delays_pilot.json"

# for making random delays
useRandom = True
# random.seed(103)
random.seed(109)
minThreshold = 7000
maxThreshold = 14000
denom = 4.0

start_positions = None
delays = None

with open(spfn, "r") as f:
    start_positions = json.loads(f.read())

with open(dfn, "r") as f:
    delays = json.loads(f.read())

app = Flask(__name__, template_folder="../../templates", static_folder="../../static")
app.secret_key = '_\x13\xb0\x8ev\xfbn\xb8\xc7A\xd0\x01\x14G,s\xe2\xda\xa0\x10\xa1>x.'
port = 5002
dbName = 'ss_pilot_incomplete_database'
db.updateConnection('localhost:' + str(port), dbName)

current_milli_time = lambda: int(round(time.time() * 1000))


# --------------Web Page Handlers--------------#
@app.route('/preview/search-study/')
def renderLandingPreview():
    return redirect(url_for('renderConsentFormPreview'))


@app.route('/search-study/')
def renderLanding():
    return redirect(url_for('renderConsentForm'))


@app.route('/preview/search-study/finish/')
def renderFinishPreview():
    response = make_response(render_template(os.path.join('pilots', 'cclusters', 'preview', 'finish_preview.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/finish/')
def renderFinish():
    # msg="user: "+session["guid"]+" | page: finish | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    # db.saveCompleted(session["guid"],current_milli_time())
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'finish.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/preview/search-study/puzzle-instr/')
def renderPuzzleInstrPreview():
    response = make_response(
        render_template(os.path.join('pilots', 'cclusters', 'preview', 'puzzle-instr_preview.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/puzzle-instr/')
def renderPuzzleInstr():
    # guid = getUserIDHelper() # generate id
    # session["guid"] = guid # store for later
    ##msg="user: "+session["guid"]+" | page: puzzle-instr | timestamp: "+str(current_milli_time())
    ##print msg
    ##app.logger.info(msg)
    # db.saveConfirmed(guid,current_milli_time())
    # app.logger.info(guid+" | start")
    # response = make_response(render_template(os.path.join('pilots','incomplete','puzzle-instr.html'),guid=guid))
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'puzzle-instr.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/preview/search-study/puzzle/', methods=["GET", "POST"])
def renderPuzzlePreview():
    posVals = start_positions[0]
    delayVals = delays[0]
    collection = "balanced-500-375"
    xgrid = 20
    ygrid = 20
    solution_dist = 8
    x_start = posVals["start"]["x"]
    y_start = posVals["start"]["y"]
    x_init = posVals["goodp"]["x"]
    y_init = posVals["goodp"]["y"]
    x1_init = posVals["badp"]["x"]
    y1_init = posVals["badp"]["y"]
    imagesDict = generateImagesDictHelper(collection, xgrid, ygrid, solution_dist, x_start, y_start, \
                                          x_init, y_init, x1_init, y1_init)
    params = {"delayVals": delayVals, "posVals": posVals, "imagesDict": imagesDict}

    response = make_response(render_template(os.path.join('pilots', 'cclusters', 'preview', 'test_preview.html'),
                                             delayVals_fast=params["delayVals"]["fast"],
                                             delayVals_quick=params["delayVals"]["quick"],
                                             delayVals_med=params["delayVals"]["med"],
                                             delayVals_slow=params["delayVals"]["slow"],
                                             good_pos_x=params["posVals"]["goodp"]["x"],
                                             good_pos_y=params["posVals"]["goodp"]["y"],
                                             bad_pos_x=params["posVals"]["badp"]["x"],
                                             bad_pos_y=params["posVals"]["badp"]["y"],
                                             starting_pos_x=params["posVals"]["start"]["x"],
                                             starting_pos_y=params["posVals"]["start"]["y"],
                                             imagesDict=json.dumps(params["imagesDict"])))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/puzzle/', methods=["GET", "POST"])
def renderPuzzle():
    # msg="user: "+session["guid"]+" | page: puzzle | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    params = chooseExperimentalParameters(zoom=True)
    # return {"delayVals":delayVals,"posVals":posVals,"imagesDict":imagesDict}
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'test_zoom.html'),
                                             delayVals_fast=params["delayVals"]["fast"],
                                             delayVals_quick=params["delayVals"]["quick"],
                                             delayVals_med=params["delayVals"]["med"],
                                             delayVals_slow=params["delayVals"]["slow"],
                                             good_pos=json.dumps(params["posVals"]["goodps"]),
                                             bad_pos=json.dumps(params["posVals"]["badps"]),
                                             starting_pos_x=params["posVals"]["start"]["x"],
                                             starting_pos_y=params["posVals"]["start"]["y"],
                                             imagesDict=json.dumps(params["imagesDict"]
                                             )))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/preview/search-study/pre-test/')
def renderPreTestPreview():
    guid = getUserIDHelper()  # generate id
    session["guid"] = guid  # store for later
    db.saveConfirmed(guid, current_milli_time())
    app.logger.info(guid + " | preview-start")
    response = make_response(
        render_template(os.path.join('pilots', 'cclusters', 'preview', 'pre_test_preview.html'), guid=guid))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/pre-test/')
def renderPreTest():
    guid = getUserIDHelper()  # generate id
    session["guid"] = guid  # store for later
    # msg="user: "+session["guid"]+" | page: pre-test | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    db.saveConfirmed(guid, current_milli_time())
    app.logger.info(guid + " | start")
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'pre_test.html'), guid=guid))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/preview/search-study/post-test/')
def renderPostTestPreview():
    response = make_response(render_template(os.path.join('pilots', 'cclusters', 'preview', 'post_test_preview.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/post-test/')
def renderPostTest():
    # msg= "user: "+session["guid"]+" | page: post-test | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'post_test.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/loc-instr/')
def renderLocInstr():
    # msg="user: "+session["guid"]+" | page: loc-instr | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'post_test.html')))
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'loc-instr.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/loc-questionnaire/', methods=["GET", "POST"])
def renderLocQuestionnaire():
    # msg="user: "+session["guid"]+" | page: loc-questionnaire | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'loc_questionnaire.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/preview/search-study/consent-form/')
def renderConsentFormPreview():
    response = make_response(
        render_template(os.path.join('pilots', 'cclusters', 'preview', 'consent_form_preview.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/consent-form/')
def renderConsentForm():
    # msg="user: null | page: consent-form | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'consent_form.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/spatial-first/', methods=["GET", "POST"])
def renderSpatialFirst():
    # msg="user: "+session["guid"]+" | page: spatial-first | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'spatial-first.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/spatial-instr/')
def renderSpatialInstr():
    # msg="user: "+session["guid"]+" | page: spatial-instr | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'spatial-instr.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/spatial-rest/')
def renderSpatialRest():
    # msg="user: "+session["guid"]+" | page: spatial-rest | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'spatial-rest.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/spatial-second/')
def renderSpatialSecond():
    # msg="user: "+session["guid"]+" | page: spatial-second | timestamp: "+str(current_milli_time())
    # print msg
    # app.logger.info(msg)
    response = make_response(render_template(os.path.join('pilots', 'incomplete', 'spatial-second.html')))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# --------------End Web Page Handlers--------------#

# --------------Form Handlers--------------#

# write form data to file
def handleForm(formName, form):
    userid = form['id']
    # print formName,dict(form)
    # do something with the log
    logpath = os.path.join("logs", userid)
    # print logpath
    try:
        os.makedirs(logpath)
    except:
        pass
    try:
        # print "got here"
        with open(os.path.join(logpath, formName + "_" + str(userid) + ".txt"), "w") as myfile:
            myfile.write(json.dumps(dict(form)))
    except:
        with open(formName + "_" + userid + ".txt", "w") as myfile:
            myfile.write(json.dumps(dict(form)))


@app.route('/search-study/save-responses/locus/', methods=['POST'])
def handleLocForm():
    handleForm("locus", request.form)
    response = Response("done")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/save-responses/pre-test/', methods=['POST'])
def handlePreTestForm():
    handleForm("pre-test", request.form)
    response = Response("done")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/save-responses/post-test/', methods=['POST'])
def handlePostTestForm():
    # print request.form
    handleForm("post-test", request.form)
    response = Response("done")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/save-responses/spatial-first/', methods=['POST'])
def handleSpatialFirstForm():
    handleForm("spatial-first", request.form)
    response = Response("done")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/save-responses/spatial-second/', methods=['POST'])
def handleSpatialSecondForm():
    handleForm("spatial-second", request.form)
    response = Response("done")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# --------------End Form Handlers--------------#

# -------------- Condition Handlers --------------#

# try to claim the confirmation code
@app.route('/search-study/claim-code/')
def claimConfirmationCode():
    confcode = str(request.args.get('confcode'))
    doClaim = db.claimConfirmationCode(confcode)
    response = Response(json.dumps(doClaim))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# get the answers from the spatial-answers.json file
@app.route('/search-study/get-spatial-answers/')
def getSpatialAnswers():
    text = ""
    with open("spatial-answers.json", "r") as f:
        text = f.read()
    response = Response(text)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


# what delay parameters should we use?
def chooseDelays():
    pos = db.updateDtracker()
    return delays[pos]


def choosePositions():
    pos = db.updateSptracker()
    return start_positions[pos]


def generate16Regions(posVals):
    good_init = posVals["goodps"] # [{"x": 1, "y": 14}, {"x":18, "y":37}, {"x":29, "y":21},{"x":32, "y":7}]
    bad_init = posVals["badps"]
    res = {
        "fast_pos": [],
        "slow_pos": [],
        "quick_pos": [],
        "med_pos": [],
    }
    for good_pos in good_init:
        position = {
            "x":good_pos["x"] // 10,
            "y":good_pos["y"] // 10,
        }
        res["fast_pos"].append(position)
    for bad_pos in bad_init:
        position = {
            "x":bad_pos["x"] // 10,
            "y":bad_pos["y"] // 10,
        }
        res["slow_pos"].append(position)
    for i in range(3):
        for j in range(3):
            position = {"x":i,"y":j}
            if(position not in res["fast_pos"] and position not in res["slow_pos"]):
                res["med_pos"].append(position)
    # grid_x, grid_y = np.mgrid[1:5:1, 1:5:1]
    # points = np.random.randint(4, size=(8, 2))
    # grid_z0 = griddata(points, np.array([4, 4, 3, 3, 2, 2, 1, 1]), (grid_x, grid_y), method='nearest')
    # while not ((np.count_nonzero(grid_z0 == 4) == 4) and (np.count_nonzero(grid_z0 == 1) == 4)):
    #     points = np.random.randint(4, size=(8, 2))
    #     grid_z0 = griddata(points, np.array([4, 4, 3, 3, 2, 2, 1, 1]), (grid_x, grid_y), method='nearest')
    # res = {
    #     "fast_pos": [{"x": tup[0], "y": tup[1]} for tup in zip(np.where(grid_z0 == 1)[0], np.where(grid_z0 == 1)[1])],
    #     "slow_pos": [{"x": tup[0], "y": tup[1]} for tup in zip(np.where(grid_z0 == 4)[0], np.where(grid_z0 == 4)[1])],
    #     "quick_pos": [{"x": tup[0], "y": tup[1]} for tup in zip(np.where(grid_z0 == 2)[0], np.where(grid_z0 == 2)[1])],
    #     "med_pos": [{"x": tup[0], "y": tup[1]} for tup in zip(np.where(grid_z0 == 3)[0], np.where(grid_z0 == 3)[1])],
    # }
    return res


def chooseCondition():
    pos = db.updateTracker()
    # choose one location object out of current 4
    if useRandom:
        return start_positions[pos["sp"]], makeDelays.makeRandomDelays(minThreshold, maxThreshold, denom)
    else:
        return start_positions[pos["sp"]], delays[pos["d"]]


def chooseExperimentalParameters(zoom=False):
    posVals, delayVals = chooseCondition()
    # delayVals = chooseDelays()
    # posVals = choosePositions()
    # collection = "500-375"
    collection = "balanced-500-375"
    # xgrid = 20
    # ygrid = 20
    xgrid = 40
    ygrid = 40
    solution_dist = 8
    x_start = posVals["start"]["x"]
    y_start = posVals["start"]["y"]
    good_init = posVals["goodps"] # [{"x": 1, "y": 14}, {"x":18, "y":37}, {"x":29, "y":21},{"x":32, "y":7}]
    bad_init = posVals["badps"]

    imagesDict = {}
    if zoom:
        imagesDict = generateImagesDictHelper(collection, xgrid, ygrid, solution_dist, x_start, y_start, \
                                              good_init, bad_init, generate16Regions(posVals),
                                              delayVals)
    else:
        imagesDict = generateImagesDictHelper(collection, xgrid, ygrid, solution_dist, x_start, y_start, \
                                              good_init, bad_init)

    return {"delayVals": delayVals, "posVals": posVals, "imagesDict": imagesDict}


# --------------End Condition Handlers--------------#

@app.route('/search-study/')
def hello_world():
    response = Response('Hello, World!')
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/get-user-id/')
def getUserID():
    response = Response(getUserIDHelper())
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


def getUserIDHelper():
    return str(uuid.uuid1())


@app.route('/search-study/store-log-data-in-batches/', methods=['POST'])
def storeLogDataInBatches():
    rawstuff = request.form['logBatch']
    userid = request.form['userid']
    currBatch = json.loads(rawstuff)
    batchId = currBatch["batchId"]
    batchData = currBatch["batchData"]
    db.saveLogBatch(userid, batchId, batchData)
    response = Response("done")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/image_positions.json/')
def generateImagesDict():
    '''
    The request expects three queryies:
    x and y which are integers between 0 and 19 included
    collection = the folder to look into. For now, we have 500-375
    '''
    collection = str(request.args.get('collection'))
    xgrid = int(request.args.get('xgrid'))  # width of collage, in images
    ygrid = int(request.args.get('ygrid'))  # height of collage, in images
    # distance each target should be from solution location
    solution_dist = int(request.args.get('solution_dist'))
    x_start = int(request.args.get('x'))  # starting position x
    y_start = int(request.args.get('y'))  # starting position y

    x_init = int(request.args.get('sol1_x'))  # solution 1 position x
    y_init = int(request.args.get('sol1_y'))  # solution 1 position y

    x1_init = int(request.args.get('sol2_x'))  # solution 2 position x
    y1_init = int(request.args.get('sol2_y'))  # solution 2 position y
    myDict = generateImagesDictHelper(collection, xgrid, ygrid, solution_dist, x_start, y_start, x_init, y_init,
                                      x1_init, y1_init)
    # Return json object
    response = Response(json.dumps(myDict, sort_keys=True))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


def checkLocationinPositions(comp_list, x, y):

    for i in range(len(comp_list)):
        if(comp_list[i]["x"] == x and comp_list[i]["y"] == y):
            return True
    return False


def checkLocationinRegion(regions, x_in, y_in, delays):
    scaled = (x_in // 10, y_in // 10)
    delay = 0
    for key in regions.keys():
        pos = regions[key]
        for val in pos:
            if val["x"] == scaled[0] and val["y"] == scaled[1]:
                if key == "fast_pos":
                    delay = delays["fast"]
                if key == "slow_pos":
                    delay = delays["slow"]
                if key == "med_pos":
                    delay = delays["med"]
                if key == "quick_pos":
                    delay = delays["quick"]

    return delay


def generateImagesDictHelper(collection, xgrid, ygrid, solution_dist, x_start, y_start, \
                             good,bad, regions={}, delays={}):
    files = os.listdir(collage_root + collection)
    files.pop(files.index('solution2.jpg'))
    random.shuffle(files)
    offset = 0  # random.randint(0, len(files)-1)
    # if offset + 450 >= len(files):
    #  offset -= 450

    '''
    #Control the shortest distance between solution images
    def shortestDistance(x1, y1, x2, y2):
      return sqrt((x1 - x2)*(x1-x2) + (y1 - y2)*(y1-y2))
  
    if x_start < 10:
      x_init = x_start + random.randint(solution_dist, 10)
    else:
      x_init = x_start - random.randint(solution_dist, 10)
    if y_start < 10:
      y_init = y_start + random.randint(solution_dist, 10)
    else:
      y_init = y_start - random.randint(solution_dist, 10)
  
    if x_start < 10:
      x1_init = x_start + random.randint(solution_dist, 10)
    else:
      x1_init = x_start - random.randint(solution_dist, 10)
    
    y1_init = random.randint(0, ygrid-1)
    '''
	#"goodps":[{"x": 14, "y": 1}, {"x":37, "y":18}, {"x":21, "y":29},{"x":7, "y":32}],
	#"badps":[{"x":16,"y":12},{"x":4, "y":23},{"x":25, "y":37},{"x":31, "y":5}],


    # Generate output Dictionary
    myDict = {"x": {}}
    for x in range(xgrid):
        myDict["x"][str(x)] = {"y": {}}  # {'x': {'0': {'y': {}}}}
        for y in range(ygrid):
            myDict["x"][str(x)]["y"][str(y)] = {"sample": {}}  # {'x': {'0': {'y': {'0': {'sample': {}}}}}}

    for x in range(xgrid):
        for y in range(ygrid):
            if (checkLocationinPositions(good,x, y) or checkLocationinPositions(bad, x, y)):
                # myDict["x"][str(x)]["y"][str(y)]["sample"]["100"] = "solution.jpg"
                myDict["x"][str(x)]["y"][str(y)]["sample"]["100"] = "solution2.jpg"
                offset += 1  # it's confusing here but we poped more files than the increment in here
            else:
                myDict["x"][str(x)]["y"][str(y)]["sample"]["100"] = str(files[offset])
                offset += 1
            myDict["x"][str(x)]["y"][str(y)]["delay"] = checkLocationinRegion(regions, x, y, delays)
    return myDict  # {'x': {'0': {'y': {'0': {'sample': {'100': {'file_name'}}}}}}}


@app.route('/search-study/images/<collection>/')
def serveImage(collection):
    image_name = request.args.get('image_name')
    response = make_response(send_file(collage_root + collection + "/" + image_name))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/log-accss/', methods=["GET"])
def logAccess():
    userid = str(request.args.get('userid'))
    page = str(request.args.get('page'))
    app.logger.info(userid + " | access | " + page)
    response = make_response("true")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/search-study/log-completed/', methods=["GET"])
def logCompleted():
    userid = request.args.get('userid')
    db.saveCompleted(userid, current_milli_time())
    app.logger.info(userid + " | completed study")
    response = make_response("true")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


def setupTrackers():
    db.initializeSptracker(start_positions)
    db.initializeDtracker(delays)


if __name__ == "__main__":
    setupTrackers()
    app.run(host="0.0.0.0", port=5000)

    # app.run(host='0.0.0.0', port=5064, debug=True)
