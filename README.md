# cloudapi

## baserestapi

### Example Usage

This example class Droplets is built targeting the DigitalOcean API - other APIs are available.

It is designed to do one thing. Make a GET request to the droplet endpoint and list all available droplets.

Class Droplets inherits from BaseRESTAPI

BaseRESTAPI accepts the following arguments

#### Required 

baseurl: 

Your API base URL

#### Optional

callrateperhour (defaults to 360): 

The rate limit for requests for your API service. The number of requests per hour.
e.g. a rate limit of 360 would mean a request attempted being made every 10 seconds.
                                   
geometric_delay_multiplier (defaults to 2): 

When a request fails BaseRESTAPI backs off geometrically by multiplying the delay between subsequent request attempts by this number.
e.g. first attempt 10s, then wait 20s, then wait 40s ... 
                                            
maximum_geometric_delay_multiplications (defaults to 5): 

The number of geometric backoff attempts of request retries to make.
If no successfull request is made the request is queued for another attempt later.

maximum_failed_attempts (defaults to 1):

A failed attempt is defined as a failed series of geometric back off request attempts.
When a request attempt fails it is placed back on the queue to be attempted later while other requests for your baseurl are given a chance to complete.
maximum_failed_attempts sets how many times your request can be requeued.


You need to export your digital ocean access token to your environment before running this example.

        from cloudapi import BaseRESTAPI
        import os
        import threading
        import datetime

        class Droplets(BaseRESTAPI):
            def __init__(self):
                BaseRESTAPI.__init__(
                    self,
                    baseurl="https://api/digitalocean.com/v2/",
                    callrateperhour=360,
                    geometric_delay_multiplier=2,
                    maximum_geometric_delay_multiplications=5,
                    maximum_failed_attempts=1,
            (
    
                self.token = os.getenv("DIGITALOCEAN_ACCESS_TOKEN","")
                self.baseheaders = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.token} ",
                }
                
            def list_all_droplets(self, **kwargs):
                endpoint = "droplets"
                headers = self.baseheaders
                return self.get_request(endpoint, headers=headers, **kwargs)
     
        if __name__ == "__main__":
            digitalocean_droplets = Droplets()
            
            def make_a_call_to_digitalocea_to_list_all_droplets(x):
                response = digitalocean_droplets.list_all_droplets()
                print(x, datetime.datetime.now())

            for x in range(0, 10):
                threading.Thread(
                    target=make_a_call_to_digitalocea_to_list_all_droplets, args=(x,)
                ).start()
                
                
Running the above code you will see that even if you rapidly make requests using BaseRESTAPI you will get the following output.
No matter how fast you make your requests BaseRESTAPI queues and times your requests to a baseurl for you.

Here you can see a rate limit of 360 does generate a request attempt every 10 seconds or so.


    0 2021-05-26 13:59:50.208497
    1 2021-05-26 14:00:00.219200
    2 2021-05-26 14:00:11.723568
    4 2021-05-26 14:00:21.704766
    5 2021-05-26 14:00:31.753094
    3 2021-05-26 14:00:41.760830
    6 2021-05-26 14:00:51.858056
    7 2021-05-26 14:01:02.185805
    8 2021-05-26 14:01:12.886259
    9 2021-05-26 14:01:22.909099

You can now make GET, POST, PUT, DELETE, HEAD and OPTIONS requests from withing your class without worrying about the timings using...

        self.get_requests(endpoint, **kwargs)
        self.post_requests(endpoint, **kwargs)
        self.put_requests(endpoint, **kwargs)
        self.delete_requests(endpoint, **kwargs)
        self.head_requests(endpoint, **kwargs)
        self.options_requests(endpoint, **kwargs)
        
Making calls to the same baseurl from other classes will still queue the requests to the same baseurl queue.
                
                
                
            
            
                
            
            
