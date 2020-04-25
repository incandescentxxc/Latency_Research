function isNumber(n) {
  return !isNaN(parseFloat(n)) && isFinite(n);
};

// function written to replace the $.param function from jQuery.
// I don't need a fancy params building function, so I chose to eliminate
// the jQuery dependency.
// shallow parsing of parameters in the dictionary passed as input (i.e., dat)
// shallow = absolutely no nested parsing, so don't pass anything crazy!
function buildParams(dat) {
  var parsedParams = [];
  for(var key in dat) {
    var val = dat[key];
    if((val == null) || (typeof(val) === 'undefined')) {
      val = "";
    }
    var p = encodeURIComponent(key) + "=";
    if((typeof val === 'string') || isNumber(val) || (typeof val === 'boolean')) {
      p += encodeURIComponent(val);
    } else { // is some object
      //console.log("is object");
      p += encodeURIComponent(JSON.stringify(val));
    }
    //parsedParams.push(encodeURIComponent(key) + "=" + encodeURIComponent(val));
    //console.log(["param",key,JSON.stringify(val),encodeURIComponent(JSON.stringify(val))]);
    parsedParams.push(p);
  }
  return parsedParams.join("&");
};

function sendRequestHelper(dat,requestType,responseType,url,callback,errorCallback) {
  var paramsString = buildParams(dat);
  var newUrl = (requestType==="GET") ? url + "?" + paramsString : url;
  //console.log(newUrl);
  var oReq = new XMLHttpRequest();
  oReq.open(requestType,newUrl, true); // async = true
  oReq.responseType = responseType;
  oReq.onload = function (oEvent) {
    if(oReq.readyState == 4) { // state = DONE
      var reqStatus = oReq.status;
      if(reqStatus == 200) { // status = OK
        var data = oReq.response;
        if(responseType === "") { // assume we want the DOM string instead
          data = oReq.responseText;
        }
        callback && callback(data);
      } else {
        if(errorCallback) { // if error handling is provided
          errorCallback(reqStatus);
        } else { // just call the callback anyway
          callback && callback(null);
        }
      }
    }
  };

  if(requestType==="GET") {
    oReq.send();
  } else { // post method
    oReq.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    oReq.send(paramsString);
  }
};

function sendGetRequestHelper(dat,responseType,url,callback,errorCallback) {
  sendRequestHelper(dat,"GET",responseType,url,callback,errorCallback);
};
function sendPostRequestHelper(dat,responseType,url,callback,errorCallback) {
  sendRequestHelper(dat,"POST",responseType,url,callback,errorCallback);
};
function sendGetRequest(dat,url,callback) {
  sendGetRequestHelper(dat,"",url,callback);
};
function sendPostRequest(dat,url,callback) {
  sendPostRequestHelper(dat,"",url,callback);
};

// take a huge log and send it in pieces, one at a time
function sendInBatches(userid,log,batchNumberObj,url,callback) {
  var batchSize = 1000;
  var i = 0;
  var batchId = 0;
  var totalBatches = Math.ceil(1.0 * log.length / batchSize);
  console.log("totalBatches",totalBatches);
  function sendBatch() {
    batchNumberObj.innerText = Math.floor((batchId+1)*100/totalBatches)+"%";
    i+=batchSize;
    batchId++;
    if(i >= log.length) {
      callback();
      return;
    }
    console.log("sending batch","i",i,"batchId",batchId);
    var beg = i;
    var end = i+batchSize;
    if(end > log.length) {
      end = log.length;
    }
    var rawstuff = {"batchId":batchId,"batchData":log.slice(beg,end)};
    var dat = {"userid":userid,"logBatch":JSON.stringify(rawstuff)};
    sendPostRequest(dat,url,sendBatch);
  };
  var beg = 0;
  var end = batchSize;
  if(end > log.length) end = log.length;
  var rawstuff = {"batchId":batchId,"batchData":log.slice(beg,end)};
  var dat = {"userid":userid,"logBatch":JSON.stringify(rawstuff)};
  console.log("sending batch","i",i,"batchId",batchId);
  sendPostRequest(dat,url,sendBatch);
};
