import googlemaps,os,json
import datetime
import zillow
import requests
import pandas as pd
import pickle,polyline
import klepto
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import xmltodict
import pprint
import requests_cache

class location():
    requests_cache.install_cache('api_cache', backend='sqlite', expire_after=3600)
    def __init__(self,address,state,type,zip):
        """
        """
        self.address = address
        self.state = state
        self.type = type
        self.zip= zip
        self.api_key = os.environ.get('GOOGLE_API')
        self.school_digger_appID = os.environ.get('SCHOOLDIGGER_APPID')
        self.school_digger_appKey = os.environ.get('SCHOOLDIGGER_APPKEY')
        self.zillow_key = os.environ.get('ZILLOW_API')
        self.gmaps = googlemaps.Client(key=self.api_key)
    
    def get_gps(self,address):
        """
        """
        self.address_gps_dict = self.gmaps.geocode(address)[0]['geometry']['location']
        return(self.address_gps_dict)
    
    def nearest_public_transport(self,gps_dict,transportType):
        """
        """
        self.public_transport = self.gmaps.places_nearby(location = (gps_dict['lat'],gps_dict['lng']),
                                rank_by="distance",
                                name=transportType)
        return(self.public_transport)
    
    def distance_to_public_transport(self,address,transportType,mode,nOpts):
        """
        """
        gps_dict = self.get_gps(address)
        public_transport = self.nearest_public_transport(gps_dict,transportType)
        station_distance = []
        for station in public_transport['results'][0:nOpts]:
            directions = self.gmaps.directions((gps_dict['lat'],gps_dict['lng']),
                             (station['geometry']['location']['lat'],station['geometry']['location']['lng']),
                             mode=mode,
                             departure_time=datetime.datetime(2019, 4, 28, 7, 0))
            distance = (directions[0]['legs'][0]['distance']['text'])
            duration = (directions[0]['legs'][0]['duration']['text'])
            distance = {"house_location" : (gps_dict['lat'],gps_dict['lng']),
                        "station_location" : (station['geometry']['location']['lat'],station['geometry']['location']['lng']),
                        "distance" : distance,
                        "duration" : self.convert_google_duration_to_minutes(duration)
                        }
            station_distance.append(distance)
        return(station_distance)
                
    
    def get_school_district(self):
        """
        """
        gps_dict = self.get_gps(self.address)
        url = "https://api.schooldigger.com/v1.1/districts"
        headers = {"Accept": "application/json"}
        payload = {'st': self.state, 'nearLatitude': gps_dict['lat'],'nearLongitude': gps_dict['lng'],'isInBoundaryOnly':'true','appID':self.school_digger_appID,'appKey': self.school_digger_appKey}
        r = requests.get(url, headers=headers,params=payload)
        return(r.json())
    
    def get_school_district_data(self,district_id):
        url = "https://api.schooldigger.com/v1.1/districts/"+district_id
        headers = {"Accept": "application/json"}
        payload = {'appID':self.school_digger_appID,'appKey': self.school_digger_appKey}
        self.r_district_data = requests.get(url, headers=headers,params=payload)
        return(self.r_district_data.json())
    
    def get_time_of_travel(self,time_of_day,
                   datetime_today,
                   day_of_week):
        """
        get a datetime of travel based on today's date and choosing the date for the following day of week
        time of day e.g. 07:00
        datetime_today = datetime.date.today()
        day of week e.g. 1= Monday, 2= Tuesday etc.
        """
    
        next_day = datetime_today + datetime.timedelta(days=-datetime.datetime.today().weekday()+day_of_week, weeks=1)
        date_string = str(next_day) + '-' + time_of_day
        time_of_travel = datetime.datetime.strptime(date_string, '%Y-%m-%d-%H:%M')
        return(time_of_travel)
    
    def convert_google_duration_to_minutes(self,string):
        """
        """
        vals = [int(s) for s in string.split() if s.isdigit()]
        if(len(vals)==3): #days+hours+minutes
            train_duration_minutes = vals[0]*24*60+vals[1]*60+vals[2]
        elif(len(vals)==2): #hours+minutes
            train_duration_minutes = vals[0]*60+vals[1]
        else:
            train_duration_minutes = vals[0]
        return(train_duration_minutes)
    
    def get_zillow_data(self):
        api = zillow.ValuationApi()
        zillow_data = api.GetSearchResults(self.zillow_key, self.address,self.zip)
        z_data = {
            'valuation_high' : zillow_data.zestimate.valuation_range_high,
         'zestimate' : zillow_data.zestimate.amount,
         'valuation_low' : zillow_data.zestimate.valuation_range_low,
         'zestimate_30_day_change' :zillow_data.zestimate.amount_change_30days,
         'details' : zillow_data.links.home_details,
         'overview_link':zillow_data.local_realestate.overview_link}
        print(z_data)




    

        