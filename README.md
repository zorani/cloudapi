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

When a request fails BaseRESTAPI backs off geometically by multiplying the delay between subsequent request attempts by this number.
                                            
maximum_geometric_delay_multiplications (defaults to 5): 

The number of geometric attempts of request retries to make.
If no successfull request is made the request is queued for another attempt later.

maximum_failed_attempts (defaults to 1):

A failed attempt is defined as a failed series of geometric back off request attempts.
When a request attempt fails it is placed back on the queue to be attempted later.
maximum_failed_attempts sets how many times your request can be requeued.


        from cloudapi import BaseRESTAPI
        import os
        import threading
        import datetime

        class Droplets(BaseRESTAPI):
            def __init__(self):
                BaseRESTAPI.
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
                
                
                
            
            
                
            
            
