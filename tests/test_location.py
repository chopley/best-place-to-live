from unittest import TestCase
import datetime
import geopandas as gpd

from bestPlace.bestPlace import location
import bestPlace.helper as helper

 


class LocationTest_Katonah(TestCase):
    def setUp(self):
        location_addresses = helper.read_address_csv('./tests/test_data_houses.csv')
        house_data = {'address':location_addresses['address'][0],
                      'state':location_addresses['state'][0],
                      'locationType':location_addresses['locationType'][0],
                      'zip':location_addresses['zip'][0]}
        self.loc = location(house_data,
                            './tests/test_data_places_of_importance.csv',
                            './tests/test_data_commuting_stations.csv')
 
    def test_get_gps(self):
        a = self.loc.get_gps(self.loc.address)
        self.assertEqual(a, {'lat': 41.250645, 'lng': -73.6845249})
        
    def test_nearest_public_transport_train(self):
        gps_dict = self.loc.get_gps(self.loc.address)
        transport_type = 'Train Station'
        b = self.loc.nearest_public_transport(gps_dict,transport_type)
        self.assertEqual(b['results'][0]['name'], 'Katonah')
        
    def test_nearest_public_transport_bus(self):
        gps_dict = self.loc.get_gps(self.loc.address)
        transport_type = 'Bus Station'
        b = self.loc.nearest_public_transport(gps_dict,transport_type)
        self.assertEqual(b['results'][0]['name'], 'Bedford Rd @ Congdon La')
    
    def test_get_transit_times(self):
        a = self.loc.get_all_transit_times(self.loc.filename_commuting_stations)
        
        
    def test_get_school_district(self):
        a = self.loc.get_gps(self.loc.address)
        a = self.loc.get_school_district()
        self.assertEqual(a['districtList'][0]['districtName'],'Katonah-Lewisboro Union Free School District')
        
    def test_distance_to_public_transport_walking(self):
        transportType = 'Train Station'
        mode = 'walking'
        nOpts = 5
        distance = self.loc.distance_to_public_transport(self.loc.address,transportType,mode,nOpts)
        expected_response = {'house_location': (41.250645, -73.6845249), 
                             'station_location': (41.2595633, -73.6839658), 
                             'distance': '0.7 mi', 
                             'duration': 14,
                             'station_name': 'Katonah',
                             'transportMode': 'walking',
                             'transportType': transportType}
        self.assertEqual(distance[0],expected_response)
        
    def test_distance_to_public_transport_driving(self):
        transportType = 'Train Station'
        mode = 'driving'
        nOpts = 5
        distance = self.loc.distance_to_public_transport(self.loc.address,transportType,mode,nOpts)
        expected_response = {'house_location': (41.250645, -73.6845249), 
                             'station_location': (41.2595633, -73.6839658), 
                             'distance': '0.8 mi', 
                             'duration': 4,
                             'station_name': 'Katonah',
                             'transportMode': 'driving',
                             'transportType': transportType}
        self.assertEqual(distance[0],expected_response)
        
    def test_get_time_of_travel(self):
        self.time_of_travel = self.loc.get_time_of_travel('07:00',datetime.date.today(),1)
        return(self.time_of_travel)
    
    def test_get_school_district_data(self):
        a = self.loc.get_gps(self.loc.address)
        school_district = self.loc.get_school_district()
        school_district_data = self.loc.get_school_district_data(school_district['districtList'][0]['districtID'])
        self.assertEqual(school_district_data['districtName'],'Katonah-Lewisboro Union Free School District')
        
    def test_get_zillow_data(self):
        self.loc.get_zillow_data()


class HelperTest(TestCase):

    def test_switch_lat_long(self):
        a = [(1,2),(3,4)]
        b = [(2,1),(4,3)]
        c = helper.switch_lat_long(a)
        self.assertEqual(c,b)
    
    def test_product_output_df(self):
        house_data = {'address': '7 Orchard Ln, Katonah', 'state': 'NY', 'locationType': 'house', 'zip': 10536}
        places_of_importance = './tests/test_data_places_of_importance.csv'
        commuting_locations = './tests/test_data_commuting_stations.csv'
        house = location(house_data,places_of_importance,commuting_locations)
        df = helper.product_output_df(house)
        test_dict = {'field': {0: 'districtID', 1: 'districtName', 2: 'school_ranking'}, 'values': {0: '3616080', 1: 'Katonah-Lewisboro Union Free School District', 2: 95.0}}
        self.assertEqual(df.to_dict(),test_dict)
        
    def test_append_geo_polygons(self):
        house_data = {'address': '7 Orchard Ln, Katonah', 'state': 'NY', 'locationType': 'house', 'zip': 10536}
        house_data2 = {'address': '6 Applegate Way, Ossining', 'state': 'NY', 'locationType': 'house', 'zip': 10562}
        places_of_importance = './tests/test_data_places_of_importance.csv'
        commuting_locations = './tests/test_data_commuting_stations.csv'
        house = location(house_data,places_of_importance,commuting_locations)
        house_2 = location(house_data2,places_of_importance,commuting_locations)
        agg_df = helper.product_output_df(house)
        agg_df_2 = helper.product_output_df(house_2)
        geo_df = gpd.GeoDataFrame()
        geo_df = helper.append_geo_polygons(house,geo_df,agg_df)
        self.assertEqual(len(geo_df.iloc[0,:]),4)
        self.assertEqual(geo_df['districtID'].values[0],'3616080')
        geo_df = helper.append_geo_polygons(house_2,geo_df,agg_df_2)
        self.assertEqual(len(geo_df.iloc[1,:]),4)
        self.assertEqual(geo_df['districtID'].values[1],'3622020')
            
        
        

        

class LocationTest_Stamford(TestCase):
    def setUp(self):  
        location_addresses = helper.read_address_csv('./tests/test_data_houses.csv')
        
        house_data = {'address':location_addresses['address'][1],
                      'state':location_addresses['state'][1],
                      'locationType':location_addresses['locationType'][1],
                      'zip':location_addresses['zip'][1]}
        self.loc = location(house_data,
                            './tests/test_data_places_of_importance.csv',
                            './tests/test_data_commuting_stations.csv')
               

    def test_update_distances_to_places_of_importance(self):
        distances = self.loc.update_distances_to_places_of_importance('./tests/test_data_places_of_importance.csv','driving')
        self.assertEqual(distances[1]['distance'], '63.9 mi')
 
    def test_get_gps(self):
        a = self.loc.get_gps(self.loc.address)
        self.assertEqual(a, {'lat': 41.1158569, 'lng': -73.5259389})
        
    def test_distance_to_other_places_of_importance(self):
        trip_test = self.loc.distance_to_other_places_of_importance(self.loc.address,'5 Quail Run Road, Woodbury, CT','driving')
        self.assertEqual(trip_test['distance'], '48.7 mi')
        
    def test_nearest_public_transport_train(self):
        gps_dict = self.loc.get_gps(self.loc.address)
        transport_type = 'Train Station'
        b = self.loc.nearest_public_transport(gps_dict,transport_type)
        self.assertEqual(b['results'][0]['name'], 'Talmadge Hill')
        
    def test_nearest_public_transport_bus(self):
        gps_dict = self.loc.get_gps(self.loc.address)
        transport_type = 'Bus Station'
        b = self.loc.nearest_public_transport(gps_dict,transport_type)
        self.assertEqual(b['results'][0]['name'], 'High Ridge Park and High Ridge Park Shelter')
        
    def test_get_school_district(self):
        a = self.loc.get_gps(self.loc.address)
        a = self.loc.get_school_district()
        self.assertEqual(a['districtList'][0]['districtName'],'Stamford School District')
        
    def test_distance_to_public_transport_driving(self):
        transportType = 'Train Station'
        mode = 'driving'
        nOpts = 5
        distance = self.loc.distance_to_public_transport(self.loc.address,transportType,mode,nOpts)
        expected_response = {'house_location': (41.1158569, -73.5259389), 
                             'station_location': (41.116012, -73.498149), 
                             'distance': '2.6 mi', 
                             'duration': 7,
                             'station_name' : 'Talmadge Hill',
                             'transportMode': 'driving',
                             'transportType': transportType
                             }
        self.assertEqual(distance[0],expected_response)
    
    def test_convert_google_duration_to_minutes(self):
        google_time = '1 day 3 hours 27 minutes'
        converted = self.loc.convert_google_duration_to_minutes(google_time)
        self.assertEqual(converted,1647)
        
    def test_get_zillow_data(self):
        self.loc.get_zillow_data()
        
if __name__ == '__main__':
    unittest.main()


        
       

 