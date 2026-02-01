#!/usr/bin/env python3
"""
Generate synthetic occupancy data for Imperial Chemistry study spaces.

This script generates one week of occupancy logs following typical study patterns:
- ~0% occupancy between 12 AM - 6 AM (closed/empty)
- Gradual increase from 6 AM to peak around 2-4 PM (90%+)
- Gradual decrease towards midnight

Usage:
    python generate_occupancy_data.py
"""

import mysql.connector
from datetime import datetime, timedelta
import random
import math


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'yazool921',  # UPDATE THIS
    'database': 'occupancy_db'
}

# Simulation parameters
START_DATE = datetime(2025, 1, 20, 0, 0, 0)  # Monday, Jan 20, 2025
DAYS = 7
SAMPLE_INTERVAL_MINUTES = 5  # Log every 5 minutes


def get_base_occupancy_probability(hour, minute):
    """
    Calculate base occupancy probability based on time of day.
    
    Returns a probability between 0 and 1 representing the likelihood
    a desk is occupied at the given time.
    
    Pattern:
    - 12 AM - 6 AM: ~0-5% (library closed/nearly empty)
    - 6 AM - 8 AM: 5-20% (early arrivals)
    - 8 AM - 12 PM: 20-70% (morning ramp-up)
    - 12 PM - 3 PM: 70-95% (peak hours)
    - 3 PM - 6 PM: 80-90% (afternoon sustained)
    - 6 PM - 9 PM: 60-75% (evening study)
    - 9 PM - 12 AM: 30-10% (winding down)
    """
    time_decimal = hour + minute / 60.0
    
    # Midnight to 6 AM - closed/empty
    if 0 <= time_decimal < 6:
        return 0.02 + 0.03 * (time_decimal / 6.0)
    
    # 6 AM to 8 AM - early arrivals
    elif 6 <= time_decimal < 8:
        progress = (time_decimal - 6) / 2.0
        return 0.05 + 0.15 * progress
    
    # 8 AM to 12 PM - morning ramp-up
    elif 8 <= time_decimal < 12:
        progress = (time_decimal - 8) / 4.0
        # Smooth S-curve
        return 0.20 + 0.50 * (1 - math.cos(progress * math.pi)) / 2
    
    # 12 PM to 3 PM - peak hours
    elif 12 <= time_decimal < 15:
        progress = (time_decimal - 12) / 3.0
        return 0.70 + 0.25 * (1 - math.cos(progress * math.pi)) / 2
    
    # 3 PM to 6 PM - sustained afternoon
    elif 15 <= time_decimal < 18:
        progress = (time_decimal - 15) / 3.0
        return 0.95 - 0.05 * progress  # Slight drop from peak
    
    # 6 PM to 9 PM - evening study
    elif 18 <= time_decimal < 21:
        progress = (time_decimal - 18) / 3.0
        return 0.75 - 0.15 * (1 - math.cos(progress * math.pi)) / 2
    
    # 9 PM to midnight - winding down
    else:
        progress = (time_decimal - 21) / 3.0
        return 0.30 * (1 - progress)


def get_day_modifier(weekday):
    """
    Adjust occupancy based on day of week.
    
    Args:
        weekday: 0=Monday, 6=Sunday
    
    Returns:
        Multiplier for base occupancy (0.0 to 1.2)
    """
    # Monday-Thursday: normal to high
    if weekday in [0, 1, 2, 3]:
        return 1.0
    # Friday: slightly lower
    elif weekday == 4:
        return 0.85
    # Saturday: much lower
    elif weekday == 5:
        return 0.5
    # Sunday: moderate (exam prep)
    else:
        return 0.7


def should_desk_be_occupied(current_time, desk_state, base_probability):
    """
    Determine if a desk should be occupied based on probability and state persistence.
    
    Args:
        current_time: datetime object
        desk_state: dict with 'is_occupied' and 'last_change_time'
        base_probability: base occupancy probability (0-1)
    
    Returns:
        Boolean indicating if desk should be occupied
    """
    # Add some stickiness - people don't change seats every 5 minutes
    time_since_change = (current_time - desk_state['last_change_time']).total_seconds() / 60.0
    
    # If recently changed state, less likely to change again
    if time_since_change < 15:  # Less than 15 minutes
        change_probability = 0.05
    elif time_since_change < 30:  # 15-30 minutes
        change_probability = 0.15
    elif time_since_change < 60:  # 30-60 minutes
        change_probability = 0.25
    else:  # Over an hour
        change_probability = 0.40
    
    # Decide if state should change
    if random.random() < change_probability:
        # State change - use base probability to determine new state
        return random.random() < base_probability
    else:
        # Keep current state
        return desk_state['is_occupied']


def generate_occupancy_logs():
    """Generate and insert occupancy logs for all desks over the specified period."""
    
    # Connect to database
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get all desks
        cursor.execute("""
            SELECT d.desk_id, d.name, s.name as space_name
            FROM Desks d
            JOIN Space s ON d.space_id = s.space_id
            JOIN Building b ON s.building_id = b.building_id
            WHERE b.name = 'Imperial Chemistry'
            ORDER BY d.desk_id
        """)
        desks = cursor.fetchall()
        
        print(f"Found {len(desks)} desks in Imperial Chemistry")
        print(f"Generating occupancy logs from {START_DATE} for {DAYS} days")
        print(f"Sample interval: {SAMPLE_INTERVAL_MINUTES} minutes")
        print(f"Total samples per desk: {(DAYS * 24 * 60) // SAMPLE_INTERVAL_MINUTES}")
        print()
        
        # Initialize desk states
        desk_states = {}
        for desk in desks:
            desk_states[desk['desk_id']] = {
                'is_occupied': False,
                'last_change_time': START_DATE
            }
        
        # Generate logs
        current_time = START_DATE
        end_time = START_DATE + timedelta(days=DAYS)
        
        batch_size = 1000
        batch = []
        total_logs = 0
        
        while current_time < end_time:
            # Get time-based factors
            hour = current_time.hour
            minute = current_time.minute
            weekday = current_time.weekday()
            
            base_prob = get_base_occupancy_probability(hour, minute)
            day_modifier = get_day_modifier(weekday)
            adjusted_prob = min(0.98, base_prob * day_modifier)  # Cap at 98%
            
            # Process each desk
            for desk in desks:
                desk_id = desk['desk_id']
                desk_state = desk_states[desk_id]
                
                # Determine occupancy
                is_occupied = should_desk_be_occupied(current_time, desk_state, adjusted_prob)
                
                # Update state if changed
                if is_occupied != desk_state['is_occupied']:
                    desk_state['is_occupied'] = is_occupied
                    desk_state['last_change_time'] = current_time
                
                # Add to batch
                batch.append((desk_id, is_occupied, current_time))
                
                # Insert batch if full
                if len(batch) >= batch_size:
                    cursor.executemany(
                        "INSERT INTO Desk_Occupancy_Logs (desk_id, is_occupied, timestamp) VALUES (%s, %s, %s)",
                        batch
                    )
                    conn.commit()
                    total_logs += len(batch)
                    print(f"Inserted {total_logs:,} logs... (current time: {current_time})", end='\r')
                    batch = []
            
            # Move to next time interval
            current_time += timedelta(minutes=SAMPLE_INTERVAL_MINUTES)
        
        # Insert remaining logs
        if batch:
            cursor.executemany(
                "INSERT INTO Desk_Occupancy_Logs (desk_id, is_occupied, timestamp) VALUES (%s, %s, %s)",
                batch
            )
            conn.commit()
            total_logs += len(batch)
        
        print(f"\n✓ Successfully inserted {total_logs:,} occupancy logs")
        
        # Show summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)
        
        cursor.execute("""
            SELECT 
                s.name as space_name,
                COUNT(DISTINCT d.desk_id) as desk_count,
                COUNT(l.log_id) as log_count,
                ROUND(AVG(CASE WHEN l.is_occupied THEN 1 ELSE 0 END) * 100, 2) as avg_occupancy_pct
            FROM Space s
            JOIN Desks d ON s.space_id = d.space_id
            JOIN Desk_Occupancy_Logs l ON d.desk_id = l.desk_id
            WHERE s.building_id = (SELECT building_id FROM Building WHERE name = 'Imperial Chemistry')
            GROUP BY s.space_id, s.name
            ORDER BY s.name
        """)
        
        for row in cursor.fetchall():
            print(f"\n{row['space_name']}:")
            print(f"  Desks: {row['desk_count']}")
            print(f"  Logs: {row['log_count']:,}")
            print(f"  Average Occupancy: {row['avg_occupancy_pct']}%")
        
        # Show hourly patterns
        print("\n" + "="*60)
        print("AVERAGE HOURLY OCCUPANCY PATTERN (All Floors)")
        print("="*60)
        
        cursor.execute("""
            SELECT 
                HOUR(l.timestamp) as hour,
                ROUND(AVG(CASE WHEN l.is_occupied THEN 1 ELSE 0 END) * 100, 1) as avg_occupancy_pct,
                COUNT(*) as samples
            FROM Desk_Occupancy_Logs l
            JOIN Desks d ON l.desk_id = d.desk_id
            JOIN Space s ON d.space_id = s.space_id
            WHERE s.building_id = (SELECT building_id FROM Building WHERE name = 'Imperial Chemistry')
            GROUP BY HOUR(l.timestamp)
            ORDER BY hour
        """)
        
        print("\nHour | Occupancy | Samples")
        print("-" * 35)
        for row in cursor.fetchall():
            bar = '█' * int(row['avg_occupancy_pct'] / 5)
            print(f"{row['hour']:2d}:00 | {row['avg_occupancy_pct']:5.1f}%   | {bar}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    print("Imperial Chemistry Occupancy Data Generator")
    print("=" * 60)
    
    try:
        generate_occupancy_logs()
        print("\n✓ Data generation complete!")
        
    except mysql.connector.Error as err:
        print(f"\n✗ Database error: {err}")
        print("\nPlease ensure:")
        print("  1. MySQL is running")
        print("  2. Database credentials in DB_CONFIG are correct")
        print("  3. The setup SQL script has been executed")
        
    except KeyboardInterrupt:
        print("\n\n✗ Operation cancelled by user")