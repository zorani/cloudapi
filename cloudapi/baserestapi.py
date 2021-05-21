import os
import json
import queue
from typing import ClassVar
import requests
from requests import Request, Session
import logging
from queue import Queue
from dataclasses import dataclass
from requests.exceptions import Timeout
import threading

import time


@dataclass
class PreparedRequestBaseURLQueueJob:
    prepared_request: requests.PreparedRequest
    prepared_response: requests.Response = None
    failed_attempts: int = 0


class BaseRESTAPI:
    """ """

    # Dictionary holding queue.Queue() objects indexed by a baseurl string.
    # One queue.Queue() per baseurl string.
    # queue.Queue() contains prepared requests.
    prepared_requests_baseurl_queues = {}
    # Keep track of tickers here, you only need one ticker per baseurl queue.
    # You don't want to keep creating deamon tickers if one already exists.
    prepared_requests_baseurl_tickers = {}

    def __init__(self, baseurl):
        self.baseurl = baseurl
        self.prepared_requests_baseurl_queue = (
            BaseRESTAPI.create_prepared_requests_baseurl_queue(self)
        )
        self.session = Session()
        # self.prepared_requests_baseurl_queue.put(PreparedRequestBaseURLQueueJob())
        self.startapiticker()

    def get_request(self, endpoint, **kwargs):
        url = f"{self.baseurl}{endpoint}"
        myrequest = Request("GET", url, **kwargs)
        prepared_request = self.session.prepare_request(myrequest)
        preparedrequestbaseurlqueuejob = PreparedRequestBaseURLQueueJob(
            prepared_request
        )
        self.prepared_requests_baseurl_queue.put(preparedrequestbaseurlqueuejob)

        while preparedrequestbaseurlqueuejob.prepared_response == None:
            time.sleep(1)
        return preparedrequestbaseurlqueuejob.prepared_response

    @classmethod
    def create_prepared_requests_baseurl_queue(cls, self):
        """
        Creates a queue.Queue() to hold prepared requests while they wait to be processed and sent.
        One queue.Queue() is created per api baseurl.
        A reference for this queue.Queue() is placed in a dictionary class variable indexed by an api baseurl.
        This setup ensures that every intance of the class can access the queue.Queue() for a given baseurl.

        Returns:
            queue.Queue: A queue containing prepared requests waiting to be processed and sent.
        """

        if not self.baseurl in cls.prepared_requests_baseurl_queues:
            cls.prepared_requests_baseurl_queues[self.baseurl] = Queue(maxsize=0)
        return cls.prepared_requests_baseurl_queues[self.baseurl]

    def startapiticker(self):
        """
        We need one ticker per baseurl queue.
        Here we detect to see if an entry has been made in the class variable dictionary
        If so we return, else we start a ticker and note that a ticker has been started for
        the baseurl queue.
        """
        print(BaseRESTAPI.prepared_requests_baseurl_tickers)
        if self.baseurl in BaseRESTAPI.prepared_requests_baseurl_tickers:
            print(f"api ticker already exists for {self.baseurl}")
            return
        print(f"No ticker for {self.baseurl} exists, starting apiticker")
        BaseRESTAPI.prepared_requests_baseurl_tickers[self.baseurl] = True
        self.APITicker(
            self.session,
            self.prepared_requests_baseurl_queue,
            periodsecondsbetweenjobs=5,
            exponentialmaxmultipliercount=5,
        )

    class APITicker:
        """
        The APITicker starts up the job queue and waits for new jobs that need to be processed.
        """

        def __init__(
            self,
            session,
            prepared_requests_baseurl_queue,
            periodsecondsbetweenjobs,
            exponentialmaxmultipliercount,
            apitimeout=5,
            exponentialbackoffmultiplier=2,
        ):
            self.periodsecondsbetweenjobs = periodsecondsbetweenjobs
            self.exponentialmaxmultipliercount = exponentialmaxmultipliercount
            self.apitimeout = apitimeout
            self.exponentialbackoffmultiplier = exponentialbackoffmultiplier
            thread = threading.Thread(
                target=self.run_jobs, args=(session, prepared_requests_baseurl_queue, 5)
            )
            thread.daemon = True
            thread.start()

        def run_jobs(self, session: Session, jobqueue: Queue, maxfailedattempts: int):
            sleepsecondsbetweenjobs = self.periodsecondsbetweenjobs

            sleepsecondsbetweenretries = self.periodsecondsbetweenjobs
            exponentialmultipliercount = 0

            while True:
                # Here we start looping through all the jobs in the queue.
                # If the jobs fail we re-add them to the queue.

                time.sleep(sleepsecondsbetweenjobs)
                while True:
                    print(f"Waiting for job... {jobqueue.qsize()} ")
                    time.sleep(1)
                    try:
                        # preparedrequestjob = PreparedRequestBaseURLQueueJob(
                        #    jobqueue.get(timeout=self.apitimeout)
                        # )
                        preparedrequestjob = jobqueue.get()

                        break
                    except:
                        pass
                # print(preparedrequestjob)
                prepared_request = preparedrequestjob.prepared_request
                # print(prepared_request)

                while True:
                    response = session.send(prepared_request, timeout=self.apitimeout)
                    if response:
                        # If the request returned a successfull response
                        # pass the successfull response to the job object
                        # break and move on to the next job.
                        preparedrequestjob.prepared_response = response
                        sleepsecondsbetweenretries = self.periodsecondsbetweenjobs
                        break
                    else:
                        # So the request failed.
                        # Start exponential backoff retries.
                        # Here we increment the sleep between retries until the retry increment limit is reached.
                        if (
                            exponentialmultipliercount
                            <= self.exponentialmaxmultipliercount
                        ):
                            exponentialmultipliercount = exponentialmultipliercount + 1
                            sleepsecondsbetweenretries = (
                                sleepsecondsbetweenretries
                                * self.exponentialbackoffmultiplier
                            )
                        else:
                            # We have reached our exponential backoff limit.
                            # Check to see if we have reached the job retry limit.
                            if preparedrequestjob.failed_attempts <= maxfailedattempts:
                                preparedrequestjob.failed_attempts = (
                                    preparedrequestjob.failed_attempts + 1
                                )
                                # We place the job back on the queue
                                jobqueue.put(preparedrequestjob)
                            else:
                                # The individual job retry limit has been breached.
                                # Time to accept failure
                                # Add the response to the job, dont add to the queue
                                preparedrequestjob.prepared_response = response
                                sleepsecondsbetweenretries = (
                                    self.periodsecondsbetweenjobs
                                )
                                break
                    time.sleep(sleepsecondsbetweenretries)


if __name__ == "__main__":

    bapi = BaseRESTAPI("https://api.digitalocean.com/v2/")

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer ",
    }

    params = {
        "page": "1",
        "per_page": "1",
    }

    endpoint = "droplets"

    response = bapi.get_request(endpoint, headers=headers, params=params)
    print(response.status_code)
    # print(response.content)

    response = bapi.get_request(endpoint, headers=headers, params=params)
    print(response.status_code)
    # print(response.content)

    response = bapi.get_request(endpoint, headers=headers, params=params)
    print(response.status_code)
    # print(response.content)

    response = bapi.get_request(endpoint, headers=headers, params=params)
    print(response.status_code)
    # print(response.content)

    bapi2 = BaseRESTAPI("https://api.digitalocean.com/v2/")
    response = bapi2.get_request(endpoint, headers=headers, params=params)
    print(response.status_code)

    pass
