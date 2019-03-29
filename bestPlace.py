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

class placesToLive():
    
    def __init__(self,address_list,destination):
        self.cache = klepto.archives.file_archive('places_to_live', serialized=True)
        self.cache_schools = klepto.archives.file_archive('schools', serialized=True)
        self.cache_zillow = klepto.archives.file_archive('zillow', serialized=True)
        self.cache.load()
        self.cache_schools.load()
        self.cache_zillow.load()
        self.destination = destination
        for item in address_list:
            item['zip'] = str(item['zip'])
            
        self.cache['address_list'] = address_list
        
        self.api_key = os.environ.get('GOOGLE_API')
        self.zillow_key = os.environ.get('ZILLOW_API')
        self.school_digger_appID = os.environ.get('SCHOOLDIGGER_APPID')
        self.school_digger_appKey = os.environ.get('SCHOOLDIGGER_APPKEY')
        self.gmaps = googlemaps.Client(key=self.api_key)
        
        list_names = ['train_stations_list','bus_stations_list','travel_time_train_list',
                      'travel_time_bus_list','drive_time_list','walk_time_list','address_details_list',
                     'address_full_list','travel_transit_times','nearby_public_transport',
                      'travel_to_transit_times','schools_data','district_data']
        list_names_schools = ['schools']
        
        list_zillow = ['valuation_list']

        #initiate the dicts in the cache if they don't currently exist
        for key in list_names:
            if key not in self.cache.keys():
                self.cache[key] = []
                
        for key in list_names_schools:
            if key not in self.cache_schools.keys():
                self.cache_schools[key] = []
                
        for key in list_zillow:
            if key not in self.cache_zillow.keys():
                self.cache_zillow[key] = []

    
    def get_time_of_travel(self,time_of_day,
                       datetime_today,
                       day_of_week):
        # datetime_today = datetime.date.today()
        #time of day e.g. 07:00
        #day of week e.g. 1= Monday, 2= Tuesday etc.
        next_day = datetime_today + datetime.timedelta(days=-datetime.datetime.today().weekday()+day_of_week, weeks=1)
        date_string = str(next_day) + '-' + time_of_day
        time_of_travel = datetime.datetime.strptime(date_string, '%Y-%m-%d-%H:%M')
        return(time_of_travel)

    def lookup_nearest_stations(self,address,
                                house_location,
                                nOpts,
                               stationType):
        matches = 0
        for public_transport in self.cache['nearby_public_transport']:
            if((address == public_transport['house_address']) & (stationType==public_transport['stationType'])):
                matches = matches + 1
        if(matches==0):
            public_transport = self.gmaps.places_nearby(house_location,
                                            rank_by="distance",
                                            name=stationType)
            for i in range(0,nOpts):
                value = {
                     'house_address':address,
                     'house_location':house_location,
                     'public_transport_vicinity':public_transport['results'][i]['vicinity'],
                     'types':public_transport['results'][i]['types'],
                     'stationType':stationType,
                     'public_transport_location' : (public_transport['results'][i]['geometry']['location']['lat'],public_transport['results'][i]['geometry']['location']['lng']),
                    }
                self.cache['nearby_public_transport'].append(value)
        return(0)
    
    def lookup_travel_time_to_station(self,
                        time_of_travel,
                        type_of_transport):
               
        for station in self.cache['nearby_public_transport']:
            matches = 0
            for travel_to in self.cache['travel_to_transit_times']:
                if((station['house_address']==travel_to['house_address']) & (station['public_transport_location']==travel_to['public_transport_location']) & (type_of_transport==travel_to['type_of_transport'])):
                    matches = matches + 1
                    
            if(matches==0):
                dd = self.gmaps.directions(station['house_location'],
                                             station['public_transport_location'],
                                             mode=type_of_transport,
                                             departure_time=time_of_travel)
                distance = (dd[0]['legs'][0]['distance']['text'])
                duration = (dd[0]['legs'][0]['duration']['text'])
                value = {'house_address':station['house_address'],
                         'house_location':station['house_location'],
                         'public_transport_location':station['public_transport_location'],
                         'distance':distance,
                         'duration':self.convert_google_duration_to_minutes(duration),
                         'time_of_day' : time_of_travel,
                         'type_of_transport' : type_of_transport,
                         'type_of_station' : station['stationType']
                        }
                self.cache['travel_to_transit_times'].append(value)
        return(0)
    
    def lookup_public_transit_travel_time(self,
                                      final_destination,
                                      time_of_travel):
        for stn in self.cache['nearby_public_transport']:
            start_station = stn['public_transport_vicinity']
            matches = 0
            for trip in self.cache['travel_transit_times']:
                if((start_station == trip['station']) & (final_destination == trip['final_destination']) & (trip['time_of_day'] == time_of_travel)):           
                    matches = matches + 1
            if(matches == 0):
                dd = self.gmaps.directions(stn['public_transport_location'],final_destination,mode='transit',departure_time=time_of_travel)
                distance = (dd[0]['legs'][0]['distance']['text'])
                duration = (dd[0]['legs'][0]['duration']['text'])
                value = {
                    'station_gps':stn['public_transport_location'],
                    'station':stn['public_transport_vicinity'],
                    'final_destination':final_destination,
                    'distance': distance,
                    'duration': self.convert_google_duration_to_minutes(duration),
                    'time_of_day' : time_of_travel,
                    'type_of_transport' : 'transit'
                }
                self.cache['travel_transit_times'].append(value)
        return(0)

    def convert_google_duration_to_minutes(self,string):
        vals = [int(s) for s in string.split() if s.isdigit()]
        if(len(vals)==3): #days+hours+minutes
            train_duration_minutes = vals[0]*24*60+vals[1]*60+vals[2]
        elif(len(vals)==2): #hours+minutes
            train_duration_minutes = vals[0]*60+vals[1]
        else:
            train_duration_minutes = vals[0]
        return(train_duration_minutes)

    def travel_related_values(self):
        for address_dict in self.cache['address_list']:
            address = (address_dict['address'] + ' ' + address_dict['state'] + ' ' +address_dict['zip'])
            if(address not in self.cache['address_full_list']):
                address_gps_dict = self.gmaps.geocode(address)[0]['geometry']['location']
                address_gps = (address_gps_dict['lat'],address_gps_dict['lng'])
                self.lookup_nearest_stations(address,address_gps,5,'Train Station')
                #self.lookup_nearest_stations(address,address_gps,5,'Bus Station')
                self.lookup_public_transit_travel_time(self.destination,datetime.datetime(2019, 3, 28, 7, 0))
                self.lookup_public_transit_travel_time(self.destination,datetime.datetime(2019, 3, 28, 7, 15))
                self.lookup_public_transit_travel_time(self.destination,datetime.datetime(2019, 3, 28, 7, 30))
                self.lookup_public_transit_travel_time(self.destination,datetime.datetime(2019, 3, 28, 7, 45))
                self.lookup_travel_time_to_station(datetime.datetime(2019, 3, 28, 7, 0),'driving')
                self.lookup_travel_time_to_station(datetime.datetime(2019, 3, 28, 7, 0),'walking')
                self.cache['address_details_list'].append({'address':address,'address_gps':address_gps,'full_address':address_dict})
                self.cache['address_full_list'].append(address)
                self.cache.dump()
        return(0)
    
    def school_related_values(self):
        url = "https://api.schooldigger.com/v1.1/districts"
        headers = {"Accept": "application/json"}
        addresses = list(pd.DataFrame(self.cache['schools_data'])['address'])
        for address in self.cache['address_details_list']:
            if(address['address'] not in addresses):
                payload = {'st': address['full_address']['state'], 'nearLatitude': address['address_gps'][0],'nearLongitude': address['address_gps'][1],'isInBoundaryOnly':'true','appID':self.school_digger_appID,'appKey': self.school_digger_appKey}
                r = requests.get(url, headers=headers,params=payload)
                self.cache['schools_data'].append({'address':address['address'],'schools_list':r.json()})
        return(0)


    def get_school_district(self):
        #first we load the current database
        self.cache_schools['address_details_list'] = self.cache['address_details_list']
        print('getting school district')    
        try:
            for address in self.cache['address_details_list']:
                print(address)
                if(len(self.cache_schools['schools'])==0):
                    print('No Schools yet loaded')
                    house_gps_point = Point(address['address_gps'])
                    print(address['address_gps'])
                    for district in self.cache_schools['district_data']:
                        for polyline_line in district['boundary']['polylineCollection']:
                            polygon = polyline.decode(polyline_line['polylineOverlayEncodedPoints'])
                            contains = (Polygon(polygon).contains(house_gps_point))
                            if(contains):
                                print('contains')
                                self.cache_schools['schools'].append({'address':address['address'],'school':district})
                                self.cache_schools.dump()

                    payload = {'st': address['full_address']['state'], 'nearLatitude': address['address_gps'][0],'nearLongitude': address['address_gps'][1],'isInBoundaryOnly':'true','appID':self.school_digger_appID,'appKey': self.school_digger_appKey}
                    r = requests.get(url, headers=headers,params=payload)
                    new_district_id = r.json()['districtList'][0]['districtID']
                    self.update_district_data(new_district_id)     
                elif((address['address'] not in list(pd.DataFrame(self.cache_schools['schools'])['address'])) ):
                    house_gps_point = Point(address['address_gps'])
                    print(address['address_gps'])
                    print('not in list')
                    for district in self.cache_schools['district_data']:
                        for polyline_line in district['boundary']['polylineCollection']:
                            polygon = polyline.decode(polyline_line['polylineOverlayEncodedPoints'])
                            contains = (Polygon(polygon).contains(house_gps_point))
                            if(contains):
                                print('contains')
                                self.cache_schools['schools'].append({'address':address['address'],'school':district})
                                self.cache_schools.dump()
        except:
            print('getting school data failed')
                #print('querying the API',address['address_gps'][0],address['address_gps'][1])
                #payload = {'st': address['full_address']['state'], 'nearLatitude': address['address_gps'][0],'nearLongitude': address['address_gps'][1],'isInBoundaryOnly':'true','appID':self.school_digger_appID,'appKey': self.school_digger_appKey}
                #r = requests.get(url, headers=headers,params=payload)
                #new_district_id = r.json()['districtList'][0]['districtID']
                #self.update_district_data(new_district_id)                     
        return(0)

    def get_district_data_from_name(self,district_name,state):
        print('getting district id for ' + district_name + state)
        url = "https://api.schooldigger.com/v1.1/districts/"
        headers = {"Accept": "application/json"}
        payload = {'st':state,'q':district_name,'appID':self.school_digger_appID,'appKey': self.school_digger_appKey}
        r_district = requests.get(url, headers=headers,params=payload)
        print(r_district.json())
        for district in r_district.json()['districtList']:
            self.update_district_data(district['districtID'])
        return(r_district.json())
    
    def update_district_data(self,district_id):
        districtIDs = []
        for district in self.cache_schools['district_data']:
            districtIDs.append(district['districtID']) 
        if(district_id not in districtIDs):
            print('updating district data ' + str(district_id))
            url = "https://api.schooldigger.com/v1.1/districts/"+district_id
            headers = {"Accept": "application/json"}
            payload = {'appID':self.school_digger_appID,'appKey': self.school_digger_appKey}
            r_district = requests.get(url, headers=headers,params=payload)
            self.cache_schools['district_data'].append(r_district.json())
            self.cache_schools.dump()
        return(0)
    
    def check_cache(self,cache,field,check_val):
        match = 0
        for val in cache:
            if val[field] == check_val:
                match = match + 1
        return(match)
            
            
    def update_zillow_values(self):   
        api = zillow.ValuationApi()
        zillow_data_list = []
        for home in self.cache['address_details_list']:
            if((self.check_cache(self.cache_zillow['valuation_list'],'address',home['address']))==0):
                try:
                    print(home['full_address']['address'],home['full_address']['zip'])
                    zillow_data = api.GetSearchResults(self.zillow_key, home['full_address']['address'],home['full_address']['zip'])
                    z_data = {
                        'address' : home['address'],
                        'valuation_high' : zillow_data.zestimate.valuation_range_high,
                     'zestimate' : zillow_data.zestimate.amount,
                     'valuation_low' : zillow_data.zestimate.valuation_range_low,
                     'zestimate_30_day_change' :zillow_data.zestimate.amount_change_30days,
                     'details' : zillow_data.links.home_details,
                     'overview_link':zillow_data.local_realestate.overview_link}
                    print(z_data)
                    self.cache_zillow['valuation_list'].append(z_data)
                except:
                    print('failed')
        self.cache_zillow.dump()
        