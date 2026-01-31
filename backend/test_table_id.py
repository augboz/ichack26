import unittest
from table_id import TableStatusTracker


class TestTableStatusTracker(unittest.TestCase):
    
    def test_initialization(self):
        """Test that tracker initializes with correct parameters"""
        tracker = TableStatusTracker(window_size=20, occ_threshold=0.7, update_rate=5)
        self.assertEqual(tracker.window_size, 20)
        self.assertEqual(tracker.occ_threshold, 0.7)
        self.assertEqual(tracker.threshold_value, 14)  # 20 * 0.7
        self.assertEqual(tracker.update_rate, 5)
    
    def test_single_table_update(self):
        """Test updating a single table"""
        tracker = TableStatusTracker(window_size=10, occ_threshold=0.7, update_rate=5)
        sample_map = {1: True}
        
        tracker.update(sample_map)
        
        self.assertIn(1, tracker.samples)
        self.assertEqual(len(tracker.samples[1]), 1)
        self.assertEqual(tracker.samples[1][0], 1)
    
    def test_window_size_limit(self):
        """Test that deque respects max window size"""
        tracker = TableStatusTracker(window_size=5, occ_threshold=0.7, update_rate=5)
        sample_map = {1: True}
        
        for _ in range(10):
            tracker.update(sample_map)
        
        self.assertEqual(len(tracker.samples[1]), 5)
    
    def test_occupied_status_threshold(self):
        """Test that status becomes True when threshold is reached"""
        tracker = TableStatusTracker(window_size=10, occ_threshold=0.7, update_rate=0)
        
        for i in range(7):
            tracker.update({1: True})
        
        updates = tracker.send_updates()
        self.assertIsNotNone(updates)
        self.assertTrue(updates[1])
    
    def test_update_rate_counter(self):
        """Test that send_updates respects update_rate counter"""
        tracker = TableStatusTracker(window_size=10, occ_threshold=0.7, update_rate=5)
        
        # First 5 updates should return None
        for i in range(5):
            tracker.update({1: True})
            updates = tracker.send_updates()
            self.assertIsNone(updates)
        
        # 6th update should return updates
        tracker.update({1: True})
        updates = tracker.send_updates()
        self.assertIsNotNone(updates)
    
    def test_status_changes_from_occupied_to_free(self):
        """Test that status can change from occupied to free"""
        tracker = TableStatusTracker(window_size=5, occ_threshold=0.8, update_rate=0)
        
        # Make it occupied
        for i in range(5):
            tracker.update({1: True})
        updates = tracker.send_updates()
        self.assertTrue(updates[1])
        
        # Make it free
        for i in range(5):
            tracker.update({1: False})
        updates = tracker.send_updates()
        self.assertFalse(updates[1])
    
    def test_multiple_tables_different_states(self):
        """Test multiple tables with different occupancy states"""
        tracker = TableStatusTracker(window_size=10, occ_threshold=0.7, update_rate=0)
        
        for i in range(8):
            tracker.update({1: True, 2: False})
        for i in range(2):
            tracker.update({1: False, 2: False})
        
        updates = tracker.send_updates()
        self.assertTrue(updates[1])
        self.assertFalse(updates[2])


if __name__ == '__main__':
    unittest.main()