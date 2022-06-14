# cloudapi

# Install using pip3

    pip3 install cloudapi

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
            
            def make_a_call_to_digitalocean_to_list_all_droplets(x):
                response = digitalocean_droplets.list_all_droplets()
                print(x, datetime.datetime.now())

            for x in range(0, 10):
                threading.Thread(
                    target=make_a_call_to_digitalocean_to_list_all_droplets, args=(x,)
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

## googlebaserestapi

Ha, so google throws a spanner in the works which is why this package has a seperate GoogleBaseRESTAPI.
Google like to authenticate it's api calls using 

    import google.auth
    import google.auth.transport.requests

This walkthrough targets googles DV360 API service. This applies to all google API services using google.auth
to authenticate. 

GoogleBaseRESTAPI takes care of all the authentication and also the call rates as above but you need
to create a couple of json files with your google authentication details.

You then need to export environment variables that point to the location of these json files.

    export GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/.creds/.google/360servicecreds.json
    export GOOGLE_DV360_ACCOUNT_INFO=/home/ubuntu/.creds/.google/360accountinfo.json

### Scope List

You will need a list of scopes for your particular google API service.
For DV360 you need the following,

        scopelist = [
            "https://www.googleapis.com/auth/display-video",
            "https://www.googleapis.com/auth/doubleclickbidmanager"
        ]
        
which we will place these scopes in the 360accountinfo.json file.

### 360servicecreds.json Content

You can generate this service account json file by going to https://console.developers.google.com/iam-admin/iam/ .
It will contain your private key credentials.  Once you have followed the link, select your project, select
"service accounts" and then create a new one.   I would select the role as "viewer".


    {
      "type": "service_account",
      "project_id": <your project id>,
      "private_key_id": <your private key id> ,
      "private_key": <your private key> ,  
      "client_email": <your client email> ,
      "client_id": <your client id> ,
      "auth_uri": "https://accounts.google.com/o/oauth2/auth",
      "token_uri": "https://oauth2.googleapis.com/token",
      "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
      "client_x509_cert_url": <your client_x509_cert_url >
    }

### 360accountinfo.json Content 

You'll need to create this file yourself with your account details for your particular
google api.  For the DV360 API we need the keys advertiser_id, partner_id, and 
service_endpoint.

    {
        "advertiser_id": <your advertisers id>,
        "partner_id": <your partner id>,
        "service_endpoint": "https://displayvideo.googleapis.com/v1/",
        "scopelist" : [ "https://www.googleapis.com/auth/display-video", "https://www.googleapis.com/auth/doubleclickbidmanager"]
    }

Once you have gathered and prepared all of the authentication and account information above and
set the environment variables we can move on to an example using GoogleBaseRESTAPI to access 
the DV360 API and make a basic API call.
    
Here it is... we're creating a new class called DV360 which inherits from GoogleBaseRESTAPI
    
    #!/usr/bin/env python3
    
    from cloudapi import GoogleBaseRESTAPI
    import os
    import threading
    import datetime
    from jettings import Jettings
    
    class DV360(GoogleBaseRESTAPI):
        def __init__(self):
            # You will need to read the account info you have collected in the 360accountinfo.json file.
            self.google_dv360_account_info = os.getenv("GOOGLE_DV360_ACCOUNT_INFO")
            self.jaccountinfo = Jettings(self.google_dv360_account_info)
            # These variables are unique to which ever google service API you are using.
            # They will be different for each google api and you will use them to construct api calls
            # according to the particular api documentation.  
            # Here we will make calls following the DV360 api documentation.
            self.advertiser_id = self.jaccountinfo.gets(["advertiser_id"])
            self.partner_id = self.jaccountinfo.gets(["partner_id"])
            # These variables, "baseurl", and "scopelist" are mandetory for GoogleBaseRESTAPI and need to be passed 
            # to the GoogleBaseRESTAPI init as showen below.
            self.baseurl = self.jaccountinfo.gets(["service_endpoint"])
            self.scopelist = self.jaccountinfo.gets(["scopelist"])
            GoogleBaseRESTAPI.__init__(
                self,
                baseurl=self.baseurl,
                scopelist=self.scopelist,
                callrateperhour=360,
                geometric_delay_multiplier=2,
                maximum_geometric_delay_multiplications=5,
                maximum_failed_attempts=1,
            )
    
        def list_advertisers(self, **kwargs):
            endpoint = "advertisers"
            return self.get_request(
                endpoint, params={"partnerId": self.partner_id}, **kwargs
            )
    
    
    if __name__ == "__main__":
        dv360 = DV360()
    
        def make_a_call_to_dv360_to_list_advertisers(x):
            response = dv360.list_advertisers()
            print(x, datetime.datetime.now())
    
        for x in range(0, 10):
            threading.Thread(
                target=make_a_call_to_dv360_to_list_advertisers, args=(x,)
            ).start()



As in the first example you will see that if you rapid fire requests to a particular google service api 
GoogleBaseRESTAPI will rate limit to the correct rate.

You will see if you run the above code the same output for a rate limit of 360.
A request is queued and sent every 10 seconds or so.

    0 2022-06-13 15:18:01.015369
    2 2022-06-13 15:18:12.530774
    1 2022-06-13 15:18:23.629947
    3 2022-06-13 15:18:35.154949
    4 2022-06-13 15:18:45.118919
    6 2022-06-13 15:18:56.279556
    5 2022-06-13 15:19:07.791847
    7 2022-06-13 15:19:17.902751
    8 2022-06-13 15:19:30.415332
    9 2022-06-13 15:19:40.344704
    
Google will be happy you are not overloading their api servers.