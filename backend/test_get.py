import unittest
import json
from get import app, tracker


class TestFlaskAPI(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and reset tracker before each test"""
        self.app = app
        self.client = self.app.test_client()
        # Reset tracker
        tracker.samples = {}
        tracker.status = {}
        tracker.update_counter = 0
    
    def test_get_empty_tables(self):
        """Test getting statuses when no tables exist"""
        response = self.client.get('/api/tables')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data, {})
    
    def test_get_all_tables(self):
        """Test getting all table statuses"""
        # Add some sample data
        tracker.update({1: True, 2: False, 3: True})
        tracker.send_updates()
        
        response = self.client.get('/api/tables')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(len(data), 3)
        # Flask converts dict keys to strings in JSON
        self.assertIn('1', data)
        self.assertIn('2', data)
        self.assertIn('3', data)
    
    def test_get_single_table_exists(self):
        """Test getting status of a specific table that exists"""
        # Add enough samples to exceed threshold (14 out of 20)
        for _ in range(15):
            tracker.update({1: True})
        tracker.send_updates()
        
        response = self.client.get('/api/tables/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        self.assertEqual(data['table_id'], 1)
        self.assertTrue(data['occupied'])
    
    def test_get_single_table_not_exists(self):
        """Test getting status of a table that doesn't exist"""
        response = self.client.get('/api/tables/999')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        
        self.assertIn('error', data)
    
    def test_table_occupied_status(self):
        """Test that table shows as occupied when threshold is reached"""
        # Add mostly occupied samples (threshold 0.7 * 20 = 14)
        for _ in range(15):
            tracker.update({1: True})
        tracker.send_updates()
        
        response = self.client.get('/api/tables/1')
        data = json.loads(response.data)
        self.assertTrue(data['occupied'])
    
    def test_table_free_status(self):
        """Test that table shows as free when mostly empty"""
        for _ in range(5):
            tracker.update({1: False})
        tracker.send_updates()
        
        response = self.client.get('/api/tables/1')
        data = json.loads(response.data)
        self.assertFalse(data['occupied'])
    
    def test_multiple_tables_mixed_status(self):
        """Test multiple tables with different statuses"""
        # Table 1: occupied
        for _ in range(15):
            tracker.update({1: True, 2: False})
        tracker.send_updates()
        
        response = self.client.get('/api/tables')
        data = json.loads(response.data)
        
        self.assertTrue(json.loads(response.data)['1'])
        self.assertFalse(json.loads(response.data)['2'])


if __name__ == '__main__':
    unittest.main()