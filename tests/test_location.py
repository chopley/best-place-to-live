from unittest import TestCase
from bestPlace.bestPlace import location
 


class LocationTest(TestCase):
    def setUp(self):
        self.loc = location('7 Orchard Ln, Katonah','house')
 
    def test_get_gps(self):
        a = self.loc.get_gps()
        self.assertEqual(a, {'lat': 41.250645, 'lng': -73.6845249})
        
       

 