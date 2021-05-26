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
import math

import time
import datetime


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
    baseurl_sessions = {}
    baseurl_period_between_request = {}
    baseurl_geometric_delay_multiplier = {}
    baseurl_maximum_geometric_delay_multiplications = {}

    def __init__(
        self,
        baseurl,
        callrateperhour=360,
        geometric_delay_multiplier=2,
        maximum_geometric_delay_multiplications=5,
    ):
        self.baseurl = baseurl
        self.callrateperhour = callrateperhour
        self.geometric_delay_multiplier = geometric_delay_multiplier
        self.maximum_geometric_delay_multiplications = (
            maximum_geometric_delay_multiplications
        )
        BaseRESTAPI.create_prepared_requests_baseurl_queue(self)
        BaseRESTAPI.create_period_between_requests(self)
        BaseRESTAPI.create_geometric_delay_multiplier(self)
        BaseRESTAPI.create_maximum_geometric_delay_multiplications(self)
        BaseRESTAPI.startapiticker(self)

    def wait_for_response(self, preparedrequestbaseurlqueuejob):
        # If we get the place of the job in the queue, we know that we can wait
        # that times the time period, so we don't need to thrash the cpu with while loops.
        place_in_queue = BaseRESTAPI.prepared_requests_baseurl_queues[
            self.baseurl
        ].qsize()
        # The periods before processing is the place in the queue minus 1,
        # Here we calculate and then wait for that period.
        periods_to_wait = place_in_queue - 1
        time_in_seconds_to_wait = (
            periods_to_wait * BaseRESTAPI.baseurl_period_between_request[self.baseurl]
        )
        # print(f"Sleeping {time_in_seconds_to_wait}")
        time.sleep(time_in_seconds_to_wait)

        # The very last period could have data returned at any point, so we wait with incremental slices
        # of about 1 period.
        delta = 0.01
        delta_value = delta * BaseRESTAPI.baseurl_period_between_request[self.baseurl]
        sleep_time = delta_value
        while preparedrequestbaseurlqueuejob.prepared_response == None:
            sleep_time = sleep_time * 2
            if (
                sleep_time * 5
                < BaseRESTAPI.baseurl_period_between_request[self.baseurl]
            ):
                time.sleep(sleep_time - delta_value)
            else:
                sleep_time = delta_value
        return preparedrequestbaseurlqueuejob.prepared_response

    def get_request(self, endpoint, **kwargs):
        url = f"{self.baseurl}{endpoint}"
        myrequest = Request("GET", url, **kwargs)
        prepared_request = self.get_session().prepare_request(myrequest)
        preparedrequestbaseurlqueuejob = PreparedRequestBaseURLQueueJob(
            prepared_request
        )
        BaseRESTAPI.prepared_requests_baseurl_queues[self.baseurl].put(
            preparedrequestbaseurlqueuejob
        )

        return self.wait_for_response(preparedrequestbaseurlqueuejob)

    def get_session(self):
        if self.baseurl in BaseRESTAPI.baseurl_sessions:
            return BaseRESTAPI.baseurl_sessions[self.baseurl]
        else:
            BaseRESTAPI.baseurl_sessions[self.baseurl] = Session()
            return BaseRESTAPI.baseurl_sessions[self.baseurl]

    @classmethod
    def create_period_between_requests(cls, self):
        if self.baseurl in BaseRESTAPI.baseurl_period_between_request:
            return BaseRESTAPI.baseurl_period_between_request[self.baseurl]
        else:
            BaseRESTAPI.baseurl_period_between_request[self.baseurl] = float(
                3600 / self.callrateperhour
            )
            # return BaseRESTAPI.baseurl_period_between_request[self.baseurl]

    @classmethod
    def create_geometric_delay_multiplier(cls, self):
        if self.baseurl in BaseRESTAPI.baseurl_geometric_delay_multiplier:
            return BaseRESTAPI.baseurl_geometric_delay_multiplier[self.baseurl]
        else:
            BaseRESTAPI.baseurl_geometric_delay_multiplier[
                self.baseurl
            ] = self.geometric_delay_multiplier

    @classmethod
    def create_maximum_geometric_delay_multiplications(cls, self):
        if self.baseurl in BaseRESTAPI.baseurl_maximum_geometric_delay_multiplications:
            return BaseRESTAPI.baseurl_maximum_geometric_delay_multiplications[
                self.baseurl
            ]
        else:
            BaseRESTAPI.baseurl_maximum_geometric_delay_multiplications[
                self.baseurl
            ] = self.maximum_geometric_delay_multiplications

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
        # return cls.prepared_requests_baseurl_queues[self.baseurl]

    @classmethod
    def startapiticker(cls, self):
        """
        We need one ticker per baseurl queue.
        Here we detect to see if an entry has been made in the class variable dictionary
        If so we return, else we start a ticker and note that a ticker has been started for
        the baseurl queue.
        """
        # print(cls.prepared_requests_baseurl_tickers)
        if self.baseurl in cls.prepared_requests_baseurl_tickers:
            #    print(f"api ticker already exists for {self.baseurl}")
            return
        # print(f"No ticker for {self.baseurl} exists, starting apiticker")
        cls.prepared_requests_baseurl_tickers[self.baseurl] = self.APITicker(
            self.get_session(),
            cls.prepared_requests_baseurl_queues[self.baseurl],
            periodsecondsbetweenjobs=BaseRESTAPI.baseurl_period_between_request[
                self.baseurl
            ],
            maximum_geometric_delay_multiplications=5,
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
            maximum_geometric_delay_multiplications,
            apitimeout=5,
            geometric_delay_multiplier=2,
        ):
            self.periodsecondsbetweenjobs = periodsecondsbetweenjobs
            self.maximum_geometric_delay_multiplications = (
                maximum_geometric_delay_multiplications
            )
            self.apitimeout = apitimeout
            self.geometric_delay_multiplier = geometric_delay_multiplier
            thread = threading.Thread(
                target=self.process_jobs,
                args=(session, prepared_requests_baseurl_queue, 5),
            )
            thread.daemon = True
            thread.start()

        def process_jobs(
            self, session: Session, jobqueue: Queue, maxfailedattempts: int
        ):
            sleepsecondsbetweenjobs = self.periodsecondsbetweenjobs

            sleepsecondsbetweenretries = self.periodsecondsbetweenjobs
            geometricmultipliercount = 0

            while True:
                # Here we start looping through all the jobs in the queue.
                # If the jobs fail we re-add them to the queue.
                time.sleep(sleepsecondsbetweenjobs)
                preparedrequestjob = jobqueue.get()
                prepared_request = preparedrequestjob.prepared_request

                # Here we start the cycle of attempting a request and handling failures and delays.
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
                            geometricmultipliercount
                            <= self.maximum_geometric_delay_multiplications
                        ):
                            geometricmultipliercount = geometricmultipliercount + 1

                            sleepsecondsbetweenretries = (
                                sleepsecondsbetweenretries
                                * self.geometric_delay_multiplier
                            )
                        else:
                            # We have reached our exponential backoff limit.
                            # Check to see if we have reached the job retry limit.

                            # We need to reset the multiplier count
                            geometricmultipliercount = 0

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
                                # Reset delay between retries to the basic period between jobs
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
