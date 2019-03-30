from unittest import TestCase
from bestPlace.bestPlace import location
 


class LocationTest(TestCase):
    def setUp(self):
        self.loc = location('7 Orchard Ln, Katonah','house')
 
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

        
       

 