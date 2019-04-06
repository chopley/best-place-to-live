import googlemaps,os,json
import datetime
import zillow
import requests
import pandas as pd
import pickle,polyline
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
import xmltodict
import pprint
import requests_cache
import csv
import polyline

class helperFunctions():
        
    def read_address_csv(self,fileName):
        houses = pd.read_csv(fileName,delimiter=';')
        return(houses)
    
    def switch_lat_long(self,list_of_coords):
        return_list_of_coords = []
        for coord in list_of_coords:
           return_list_of_coords.append((coord[1],coord[0]))
        return(return_list_of_coords)

class location():
    requests_cache.install_cache('api_cache', backend='sqlite', expire_after=72000)
    def __init__(self,location_dict,filename_other_places_of_importance,filename_commuting_stations):
        """
        """
        self.address = location_dict['address']
        self.state = location_dict['state']
        self.type = location_dict['locationType']
        self.zip= location_dict['zip']
        self.station_distance = []
        self.distances = []
        self.transit_distance = []
        self.filename_commuting_stations = filename_commuting_stations
        self.api_key = os.environ.get('GOOGLE_API')
        self.school_digger_appID = os.environ.get('SCHOOLDIGGER_APPID')
        self.school_digger_appKey = os.environ.get('SCHOOLDIGGER_APPKEY')
        self.zillow_key = os.environ.get('ZILLOW_API')
        self.gmaps = googlemaps.Client(key=self.api_key)
        
        #populate various other useful attributes
        self.address_gps = self.get_gps(self.address)
        
        #populate object attributes
        self.distances.append(self.update_distances_to_places_of_importance(filename_other_places_of_importance,'driving'))
        self.station_distance.append(self.distance_to_public_transport(self.address,'Train Station','driving',5))
        self.station_distance.append(self.distance_to_public_transport(self.address,'Train Station','walking',5))
        self.station_distance.append(self.distance_to_public_transport(self.address,'Subway Station','driving',5))
        self.transit_distance.append(self.get_all_transit_times(self.filename_commuting_stations))
        self.school_district_data = self.get_school_district_data(self.get_school_district()['districtList'][0]['districtID'])
        self.decode_polylines()
        self.update_dataframes()
        

    def update_dataframes(self):
        to_station = []
        for station_distance in self.station_distance:
            to_station = to_station + station_distance
        self.df_station_distance = pd.DataFrame(to_station)  
        self.df_travel_distances = self.df_station_distance.merge(pd.DataFrame(self.transit_distance[0]),left_on = 'station_location',right_on = 'station_location')
        self.df_travel_distances['total_duration'] = self.df_travel_distances['duration_x'] + self.df_travel_distances['duration_y']
        self.df_travel_distances = self.df_travel_distances[['distance_x','duration_x','station_name_x','transportMode_x','transportType_x','destination','total_duration']].sort_values('total_duration')
        self.df_travel_aggregate = self.df_travel_distances.groupby(['destination','duration_x','transportMode_x']).agg({'total_duration':['min','max'],
                                                                                                         'duration_x':['min','max']
                                                                                                        })
        self.decode_polylines()
        self.df_places_of_importance = pd.DataFrame(self.distances[0])
        
        self.df_places_of_importance['HouseAddress'] = self.address
        self.df_travel_distances['HouseAddress'] = self.address
        self.df_station_distance['HouseAddress'] = self.address
        
        maximum_distance_to_station = 50
        self.df_travel_minimums = self.df_travel_distances[self.df_travel_distances['duration_x']<maximum_distance_to_station].groupby(['HouseAddress','destination']).min().reset_index()[['HouseAddress','station_name_x','duration_x','destination','total_duration']]
    
    def decode_polylines(self):
        plines = []
        for pline in self.school_district_data['boundary']['polylineCollection']:  
            plines.append(polyline.decode(pline['polylineOverlayEncodedPoints']))
        self.school_district_polylines = plines
        return(plines)
        
        
    def update_distances_to_places_of_importance(self,filename,transportMode):
        distances = []
        destinations = pd.read_csv(filename,delimiter=';')
        for index, row in destinations.iterrows():
            dict_address = {'address' : row['address']}
            dict_destination = self.distance_to_other_places_of_importance(self.address,row['address'],transportMode)
            distances.append(dict_destination)
        return(distances)
             
    def get_gps(self,address):
        """
        """
        self.address_gps_dict = self.gmaps.geocode(address)[0]['geometry']['location']
        return(self.address_gps_dict)
    
    def convert_directions_to_distance_duration(self,directions):
        distance = (directions[0]['legs'][0]['distance']['text'])
        duration = (directions[0]['legs'][0]['duration']['text'])
        return({'distance' : distance, 'duration' : self.convert_google_duration_to_minutes(duration)})
    
    def distance_to_other_places_of_importance(self,start_location_address,destination_address,transportMode):
        gps_dict_start = self.get_gps(start_location_address)
        gps_dict_destination = self.get_gps(destination_address)
        directions = self.gmaps.directions((gps_dict_start['lat'],gps_dict_start['lng']),
                 (gps_dict_destination['lat'],gps_dict_destination['lng']),
                 mode=transportMode,
                 departure_time=datetime.datetime(2019, 4, 28, 7, 0))
        directions = self.convert_directions_to_distance_duration(directions)
        mode = {'transportMode' : transportMode, 'destination' : destination_address ,'destination_location' : (gps_dict_destination['lat'],gps_dict_destination['lng']) }
        directions.update(mode)
        return(directions)
    
    def get_all_transit_times(self,commuting_destinations_station_filename):
        transit_destination_stations = pd.read_csv(commuting_destinations_station_filename,delimiter=';')
        distances = []
        for stations in self.station_distance:
            for station in stations:
                for index, row in transit_destination_stations.iterrows():
                    dict_start_station = {'station_name' : station['station_name'],'station_location' : station['station_location'], 'transportType' : station['transportType']}
                    distance = self.distance_on_public_transport(station['station_location'],row['address'])
                    dict_start_station.update(distance)
                    distances.append(dict_start_station)            
        return(distances)
        #transit_originating_stations = self.station_distance
        #transit_distances = []
        #for index, row in transit_stations.iterrows():
        #    distance = distance_on_public_transport()
            
    
    def distance_on_public_transport(self,start_station_location,destination_station_address):
        transportMode = 'transit'
        gps_dict_destination = self.get_gps(destination_station_address)
        directions = self.gmaps.directions(start_station_location,
                 (gps_dict_destination['lat'],gps_dict_destination['lng']),
                 mode=transportMode,
                 departure_time=datetime.datetime(2019, 4, 28, 7, 0))
        directions = self.convert_directions_to_distance_duration(directions)
        mode = {'transportMode' : transportMode, 'destination' : destination_station_address ,'destination_location' : (gps_dict_destination['lat'],gps_dict_destination['lng']) }
        directions.update(mode)
        return(directions)

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
                        "duration" : self.convert_google_duration_to_minutes(duration),
                        "station_name" : (station['name']),
                        "transportMode" : mode,
                        "transportType" : transportType
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




    

        