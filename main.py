# aircraft_info_search/main.py
import sqlite3
from typing import List, Optional

class AircraftSearcher:
    def __init__(self, db_path: str = "data/icao_aircraft.db"):
        """Initialize the aircraft searcher with database path."""
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
    
    def search_aircraft(self, search_term: str) -> List[sqlite3.Row]:
        """
        Search for aircraft by model name, manufacturer, or description.
        Returns list of matching aircraft records.
        """
        if not self.connection:
            if not self.connect():
                return []
        
        # Search in model, manufacturer, and description fields (case-insensitive)
        query = """
        SELECT manufacturer, model, type_designator, description, engine_type, engine_count, wtc
        FROM aircraft 
        WHERE LOWER(model) LIKE LOWER(?) 
           OR LOWER(manufacturer) LIKE LOWER(?)
           OR LOWER(description) LIKE LOWER(?)
           OR LOWER(type_designator) LIKE LOWER(?)
        ORDER BY model
        """
        
        search_pattern = f"%{search_term}%"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern))
            results = cursor.fetchall()
            return results
        except sqlite3.Error as e:
            print(f"Error searching database: {e}")
            return []
    
    def get_type_designator(self, search_term: str) -> Optional[str]:
        """
        Get the type designator for a specific aircraft model.
        Returns the first match found.
        """
        results = self.search_aircraft(search_term)
        if results:
            return results[0]['type_designator']
        return None
    
    def display_results(self, results: List[sqlite3.Row]):
        """Display search results in a formatted way."""
        if not results:
            print("No aircraft found matching your search.")
            return
        
        print(f"\nFound {len(results)} aircraft:")
        print("-" * 120)
        print(f"{'Manufacturer':<25} {'Model':<40} {'Type':<8} {'Description':<15} {'Engine':<10} {'Count':<5} {'WTC':<3}")
        print("-" * 120)
        
        for row in results:
            print(f"{row['manufacturer']:<25} {row['model']:<40
                                               } {row['type_designator']:<8} {row['description']:<15} {row['engine_type']:<10} {row['engine_count']:<5} {row['wtc']:<3}")

def main():
    """Main function to run the aircraft search program."""
    print("ICAO Aircraft Database Search")
    print("=" * 40)
    
    # Initialize searcher
    searcher = AircraftSearcher()
    
    if not searcher.connect():
        print("Failed to connect to database. Make sure icao_aircraft.db exists in the current directory.")
        return
    
    try:
        while True:
            print("\nOptions:")
            print("1. Search for aircraft")
            print("2. Get type designator only")
            print("3. Quit")
            
            choice = input("\nEnter your choice (1-3): ").strip()
            
            if choice == '1':
                search_term = input("Enter aircraft model/manufacturer to search: ").strip()
                if search_term:
                    results = searcher.search_aircraft(search_term)
                    searcher.display_results(results)
                
            elif choice == '2':
                search_term = input("Enter aircraft model to get type designator: ").strip()
                if search_term:
                    type_designator = searcher.get_type_designator(search_term)
                    if type_designator:
                        print(f"Type designator for '{search_term}': {type_designator}")
                    else:
                        print(f"No aircraft found matching '{search_term}'")
                        
            elif choice == '3':
                print("Goodbye!")
                break
                
            else:
                print("Invalid choice. Please enter 1, 2, or 3.")
                
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        searcher.close()

if __name__ == "__main__":
    main()