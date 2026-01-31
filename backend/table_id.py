from collections import deque


class TableStatusTracker:
    def __init__(self, window_size=20, occ_threshold=0.7, update_rate=5):
        self.window_size = window_size
        self.occ_threshold = occ_threshold
        self.threshold_value = int(window_size * occ_threshold)
        self.update_rate = update_rate # How often to send updates
        self.update_counter = 0 # Separate counter for tracking
        self.samples = {}
        self.status = {}

    def update(self, sample_map):
        for table_id, occupied in sample_map.items():
            if table_id not in self.samples: #initalise
                self.samples[table_id] = deque(maxlen=self.window_size) 
                self.status[table_id] = False

            self.samples[table_id].append(1 if occupied else 0)
        
        # Increment counter once per update call, not per table
        self.update_counter += 1
            
    def send_updates(self):
        # Check if it's time to send updates
        if self.update_rate == 0 or self.update_counter >= self.update_rate:
            updates = {} 
            for table_id, sample_deque in self.samples.items():
                occupied_count = sum(sample_deque) 
                self.status[table_id] = occupied_count >= self.threshold_value
                updates[table_id] = self.status[table_id]
            
            self.update_counter = 0  # Reset counter after sending updates
            return updates #send upstream
        
        return None
