"""
Azure Machine Learning service performance testing utility.

Usage: AMLPerfClient.py -api [API KEY] sample_file

"""

import sys, json, urllib2, time, threading, argparse, datetime

class AMLRequestGenerator:
    def __init__(self, api_key, requests, sample_file=None, data_file=None, threads=1):
        self.ApiKey = api_key
        self.Data = ""
        self.Url = ""
        self.RequestNumber = requests
        self.Headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ self.ApiKey)}
        self.ResponseTime = []
        self.ProcessingTime = []
        self.AvgResponseTime = 0
        self.AvgProcessingTime = 0
        self.Errors = []
        self.ErrorCount = 0
        self.ThreadCount = threads
        self.Threads = []
        self.TotalTime = 0
        self.Lock = threading.Lock()

        if sample_file:
            self.__parseSampleFile__(sample_file)

    def __parseSampleFile__(self, file_name):
        f = file(file_name)
        sample_code = ""
        for line in f:
            if line.find('try:') > -1: break
            if line.find('import') == -1:
                sample_code += line
        exec sample_code
        self.Data = data
        self.Url = url

    def runTest(self, req_no):
        for req in range(0, req_no):
            resp = self.sendRequest()
               
    def run(self):
        rpt = self.ThreadCount*[self.RequestNumber/self.ThreadCount,]
        start = time.time()       
        if self.RequestNumber % self.ThreadCount:
            rpt[0] += self.RequestNumber % self.ThreadCount
        for th in range(0,self.ThreadCount):
            t = threading.Thread(target=self.runTest, args =(rpt[th],))
            self.Threads.append(t)
            t.start()
        for th in self.Threads:
            th.join()
        self.TotalTime = round(time.time()-start,2)
        self._calculateStatistics()
            
    def _calculateStatistics(self):
        self.ErrorCount = len(self.Errors)
        if len(self.ProcessingTime) > 0:
            self.AvgProcessingTime = int(sum(self.ProcessingTime)/len(self.ProcessingTime))
        if len(self.ResponseTime) > 0:
            self.ResponseTime = [i.split(':') for i in self.ResponseTime] #converting headers into number of seconds
            self.ResponseTime = [datetime.timedelta(hours=int(i[0]), minutes=int(i[1]), seconds=float(i[2])).total_seconds() for i in self.ResponseTime]
            self.AvgResponseTime = round(((sum(self.ResponseTime)/len(self.ResponseTime))*100),2)

    def getStatistics(self):
        print "Total processing time %s s" % self.TotalTime
        print "Mean req processing time: %s ms" % self.AvgProcessingTime
        print "Mean req response time: %s ms" % self.AvgResponseTime
        print "# of succesful requests: %s" % len(self.ProcessingTime)
        print "# of errors: %s" % self.ErrorCount
        print "Error rate: %s%%" % (self.ErrorCount/float(self.RequestNumber) * 100)
        print "# of threads: %s" % self.ThreadCount

    def sendRequest(self):
        body = str.encode(json.dumps(self.Data))
        req = urllib2.Request(self.Url, body, self.Headers)
        try:
            t = time.time()
            response = urllib2.urlopen(req) 
            result = response.read()            
            self.Lock.acquire()
            self.ProcessingTime.append(round(time.time()-t,2)*100)
            self.ResponseTime.append(response.info().getheader('x-ms-request-duration'))
            self.Lock.release()
            return json.loads(result)
        except urllib2.HTTPError, error:
            self.Errors.append(error.code)
        except urllib2.URLError, error:
            #-1 means no response
            self.Errors.append(-1)


#reading environment variables
parser = argparse.ArgumentParser(description="Azure ML performance test tool")
parser.add_argument("sample_file", type=str, help="location of Python sample file generated by AML service")
parser.add_argument("-api", type=str, help="Azure ML API key", required=True)
parser.add_argument("-r", type=int, help="number of requests to be generated", required=True)
parser.add_argument("-t", type=int, help="number of threads (default=1)")
parser.add_argument("-s", action="store_false", help="silent mode (no info)")

args = parser.parse_args()
if  not args.t:
    args.t = 1

aml_gen= AMLRequestGenerator(args.api, args.r, sample_file=args.sample_file, threads = args.t)
aml_gen.run()
if args.s:
    aml_gen.getStatistics()

