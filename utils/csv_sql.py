# aircraft_info_search/utils/csv_sql.py


"""
Simple CSV to SQLite Converter for ICAO Aircraft Database
Creates optimized database for fast model → type designator lookups
"""

import sqlite3
import csv
from pathlib import Path

def create_aircraft_database(csv_file="../docs/csv_files/icao_aircraft_data.csv", db_file="../data/icao_aircraft.db"):
    """Convert CSV to SQLite database with indexes"""
    
    if not Path(csv_file).exists():
        print(f"Error: CSV file '{csv_file}' not found")
        return False
    
    print(f"Creating database from {csv_file}...")
    
    # Connect to database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Drop existing table if it exists
        cursor.execute("DROP TABLE IF EXISTS aircraft")
        
        # Create aircraft table
        cursor.execute("""
            CREATE TABLE aircraft (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacturer TEXT NOT NULL,
                model TEXT,
                type_designator TEXT NOT NULL,
                description TEXT,
                engine_type TEXT,
                engine_count INTEGER,
                wtc TEXT
            )
        """)
        
        # Import CSV data
        imported_count = 0
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            
            for row in csv_reader:
                try:
                    cursor.execute("""
                        INSERT INTO aircraft 
                        (manufacturer, model, type_designator, description, 
                         engine_type, engine_count, wtc)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['manufacturer'].strip(),
                        row['model'].strip(),
                        row['type_designator'].strip(),
                        row['description'].strip(),
                        row['engine_type'].strip(),
                        int(row['engine_count']) if row['engine_count'].isdigit() else None,
                        row['wtc'].strip()
                    ))
                    imported_count += 1
                    
                    if imported_count % 1000 == 0:
                        print(f"Imported {imported_count} records...")
                        
                except Exception as e:
                    print(f"Error importing row: {e}")
                    continue
        
        # Create indexes for fast lookups
        print("Creating indexes...")
        indexes = [
            "CREATE INDEX idx_model ON aircraft(model)",
            "CREATE INDEX idx_type_designator ON aircraft(type_designator)",
            "CREATE INDEX idx_manufacturer ON aircraft(manufacturer)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Commit changes
        conn.commit()
        
        # Show results
        cursor.execute("SELECT COUNT(*) FROM aircraft")
        total_records = cursor.fetchone()[0]
        
        print(f"\n✅ Database created successfully!")
        print(f"📁 File: {db_file}")
        print(f"📊 Records: {total_records:,}")
        print(f"🚀 Ready for fast lookups!")
        
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    create_aircraft_database()