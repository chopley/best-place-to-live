from unittest import TestCase
from bestPlace.bestPlace import location
import datetime
import csv
 


class LocationTest_Katonah(TestCase):
    def setUp(self):
        address = []
        state = []
        type = []
        with open('./tests/test_data.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            for row in readCSV:
                address.append(row[0])
                state.append(row[1])
                type.append(row[2])
        self.loc = location(address[0],state[0],type[0])
 
    def test_get_gps(self):
        a = self.loc.get_gps()
        self.assertEqual(a, {'lat': 41.250645, 'lng': -73.6845249})
        
    def test_nearest_public_transport_train(self):
        a = self.loc.get_gps()
        transport_type = 'Train Station'
        b = self.loc.nearest_public_transport(transport_type)
        self.assertEqual(b['results'][0]['name'], 'Katonah')
        
    def test_nearest_public_transport_bus(self):
        a = self.loc.get_gps()
        transport_type = 'Bus Station'
        b = self.loc.nearest_public_transport(transport_type)
        self.assertEqual(b['results'][0]['name'], 'Bedford Rd @ Congdon La')
        
    def test_get_school_district(self):
        a = self.loc.get_gps()
        a = self.loc.get_school_district()
        self.assertEqual(a['districtList'][0]['districtName'],'Katonah-Lewisboro Union Free School District')
        
    def test_distance_to_public_transport_walking(self):
        transportType = 'Train Station'
        mode = 'walking'
        nOpts = 5
        distance = self.loc.distance_to_public_transport(transportType,mode,nOpts)
        expected_response = {'house_location': (41.250645, -73.6845249), 'station_location': (41.2595633, -73.6839658), 'distance': '0.7 mi', 'duration': 14}
        self.assertEqual(distance[0],expected_response)
        
    def test_distance_to_public_transport_driving(self):
        transportType = 'Train Station'
        mode = 'driving'
        nOpts = 5
        distance = self.loc.distance_to_public_transport(transportType,mode,nOpts)
        expected_response = {'house_location': (41.250645, -73.6845249), 'station_location': (41.2595633, -73.6839658), 'distance': '0.8 mi', 'duration': 4}
        self.assertEqual(distance[0],expected_response)
        
    def test_get_time_of_travel(self):
        self.time_of_travel = self.loc.get_time_of_travel('07:00',datetime.date.today(),1)
        return(self.time_of_travel)

class LocationTest_Stamford(TestCase):
    def setUp(self):  
        address = []
        state = []
        type = []    
        with open('./tests/test_data.csv') as csvfile:
            readCSV = csv.reader(csvfile, delimiter=';')
            for row in readCSV:
                address.append(row[0])
                state.append(row[1])
                type.append(row[2])
        self.loc = location(address[1],state[1],type[1])

 
    def test_get_gps(self):
        a = self.loc.get_gps()
        self.assertEqual(a, {'lat': 41.1158569, 'lng': -73.5259389})
        
    def test_nearest_public_transport_train(self):
        a = self.loc.get_gps()
        transport_type = 'Train Station'
        b = self.loc.nearest_public_transport(transport_type)
        self.assertEqual(b['results'][0]['name'], 'Talmadge Hill')
        
    def test_nearest_public_transport_bus(self):
        a = self.loc.get_gps()
        transport_type = 'Bus Station'
        b = self.loc.nearest_public_transport(transport_type)
        self.assertEqual(b['results'][0]['name'], 'High Ridge Park and High Ridge Park Shelter')
        
    def test_get_school_district(self):
        a = self.loc.get_gps()
        a = self.loc.get_school_district()
        self.assertEqual(a['districtList'][0]['districtName'],'Stamford School District')
        
    def test_distance_to_public_transport_driving(self):
        transportType = 'Train Station'
        mode = 'driving'
        nOpts = 5
        distance = self.loc.distance_to_public_transport(transportType,mode,nOpts)
        expected_response = {'house_location': (41.1158569, -73.5259389), 
                             'station_location': (41.116012, -73.498149), 
                             'distance': '3.0 mi', 
                             'duration': 7}
        self.assertEqual(distance[0],expected_response)
    
    def test_convert_google_duration_to_minutes(self):
        google_time = '1 day 3 hours 27 minutes'
        converted = self.loc.convert_google_duration_to_minutes(google_time)
        self.assertEqual(converted,1647)
        
if __name__ == '__main__':
    unittest.main()


        
       

 