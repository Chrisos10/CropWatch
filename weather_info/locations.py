"""
Rwanda Locations Mapping Module
Maps Rwanda's districts and sectors to geographic coordinates
for weather data retrieval
"""

from typing import Dict, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class RwandaLocations:
    """
    Provides geographic coordinates for Rwanda's administrative divisions
    Organized by Province → District → Sectors
    """
    
    # Rwanda's 5 Provinces with their districts and key sectors
    LOCATIONS = {
        'Kigali': {
            'Gasabo': {
                'coordinates': {'lat': -1.9167, 'lon': 30.1333},
                'sectors': {
                    'Bumbogo': {'lat': -1.9167, 'lon': 30.1333},
                    'Gikomero': {'lat': -1.8500, 'lon': 30.1500},
                    'Gisozi': {'lat': -1.9417, 'lon': 30.0917},
                    'Jali': {'lat': -1.8833, 'lon': 30.1167},
                    'Kacyiru': {'lat': -1.9500, 'lon': 30.1000},
                    'Kimihurura': {'lat': -1.9583, 'lon': 30.1000},
                    'Kimironko': {'lat': -1.9500, 'lon': 30.1333},
                    'Kinyinya': {'lat': -1.9333, 'lon': 30.1167},
                    'Ndera': {'lat': -1.9667, 'lon': 30.1500},
                    'Nduba': {'lat': -1.9833, 'lon': 30.1333},
                    'Remera': {'lat': -1.9583, 'lon': 30.1167},
                    'Rusororo': {'lat': -1.9167, 'lon': 30.1667},
                    'Rutunga': {'lat': -1.9000, 'lon': 30.1833},
                }
            },
            'Kicukiro': {
                'coordinates': {'lat': -1.9900, 'lon': 30.1028},
                'sectors': {
                    'Gahanga': {'lat': -2.0167, 'lon': 30.1167},
                    'Gatenga': {'lat': -2.0000, 'lon': 30.0833},
                    'Gikondo': {'lat': -1.9833, 'lon': 30.0667},
                    'Kagarama': {'lat': -1.9833, 'lon': 30.0833},
                    'Kanombe': {'lat': -1.9667, 'lon': 30.1333},
                    'Kicukiro': {'lat': -1.9900, 'lon': 30.1028},
                    'Kigarama': {'lat': -2.0167, 'lon': 30.1333},
                    'Masaka': {'lat': -2.0333, 'lon': 30.1000},
                    'Niboye': {'lat': -2.0000, 'lon': 30.1000},
                    'Nyarugunga': {'lat': -2.0000, 'lon': 30.1167},
                }
            },
            'Nyarugenge': {
                'coordinates': {'lat': -1.9536, 'lon': 30.0606},
                'sectors': {
                    'Gitega': {'lat': -1.9667, 'lon': 30.0500},
                    'Kanyinya': {'lat': -1.9833, 'lon': 30.0167},
                    'Kigali': {'lat': -1.9536, 'lon': 30.0606},
                    'Kimisagara': {'lat': -1.9667, 'lon': 30.0667},
                    'Mageragere': {'lat': -2.0000, 'lon': 30.0833},
                    'Muhima': {'lat': -1.9500, 'lon': 30.0667},
                    'Nyakabanda': {'lat': -1.9667, 'lon': 30.0833},
                    'Nyamirambo': {'lat': -1.9667, 'lon': 30.0500},
                    'Nyarugenge': {'lat': -1.9536, 'lon': 30.0606},
                    'Rwezamenyo': {'lat': -1.9833, 'lon': 30.0333},
                }
            }
        },
        'Eastern': {
            'Bugesera': {
                'coordinates': {'lat': -2.2833, 'lon': 30.1333},
                'sectors': {}
            },
            'Gatsibo': {
                'coordinates': {'lat': -1.6167, 'lon': 30.4167},
                'sectors': {}
            },
            'Kayonza': {
                'coordinates': {'lat': -1.8833, 'lon': 30.5833},
                'sectors': {}
            },
            'Kirehe': {
                'coordinates': {'lat': -2.2167, 'lon': 30.7167},
                'sectors': {}
            },
            'Ngoma': {
                'coordinates': {'lat': -2.1667, 'lon': 30.5167},
                'sectors': {}
            },
            'Nyagatare': {
                'coordinates': {'lat': -1.2833, 'lon': 30.3333},
                'sectors': {}
            },
            'Rwamagana': {
                'coordinates': {'lat': -1.9500, 'lon': 30.4333},
                'sectors': {}
            }
        },
        'Northern': {
            'Burera': {
                'coordinates': {'lat': -1.4833, 'lon': 29.8833},
                'sectors': {}
            },
            'Gakenke': {
                'coordinates': {'lat': -1.6833, 'lon': 29.7833},
                'sectors': {}
            },
            'Gicumbi': {
                'coordinates': {'lat': -1.5833, 'lon': 30.0667},
                'sectors': {}
            },
            'Musanze': {
                'coordinates': {'lat': -1.4983, 'lon': 29.6350},
                'sectors': {}
            },
            'Rulindo': {
                'coordinates': {'lat': -1.7833, 'lon': 30.0500},
                'sectors': {}
            }
        },
        'Southern': {
            'Gisagara': {
                'coordinates': {'lat': -2.5833, 'lon': 29.8333},
                'sectors': {}
            },
            'Huye': {
                'coordinates': {'lat': -2.5967, 'lon': 29.7383},
                'sectors': {}
            },
            'Kamonyi': {
                'coordinates': {'lat': -2.0333, 'lon': 29.9000},
                'sectors': {}
            },
            'Muhanga': {
                'coordinates': {'lat': -2.0833, 'lon': 29.7500},
                'sectors': {}
            },
            'Nyamagabe': {
                'coordinates': {'lat': -2.4833, 'lon': 29.4167},
                'sectors': {}
            },
            'Nyanza': {
                'coordinates': {'lat': -2.3500, 'lon': 29.7500},
                'sectors': {}
            },
            'Nyaruguru': {
                'coordinates': {'lat': -2.6167, 'lon': 29.4500},
                'sectors': {}
            },
            'Ruhango': {
                'coordinates': {'lat': -2.2333, 'lon': 29.7833},
                'sectors': {}
            }
        },
        'Western': {
            'Karongi': {
                'coordinates': {'lat': -2.0000, 'lon': 29.4000},
                'sectors': {}
            },
            'Ngororero': {
                'coordinates': {'lat': -1.7833, 'lon': 29.5833},
                'sectors': {}
            },
            'Nyabihu': {
                'coordinates': {'lat': -1.6500, 'lon': 29.5000},
                'sectors': {}
            },
            'Nyamasheke': {
                'coordinates': {'lat': -2.3333, 'lon': 29.1667},
                'sectors': {}
            },
            'Rubavu': {
                'coordinates': {'lat': -1.6833, 'lon': 29.2667},
                'sectors': {}
            },
            'Rusizi': {
                'coordinates': {'lat': -2.4833, 'lon': 28.9000},
                'sectors': {}
            },
            'Rutsiro': {
                'coordinates': {'lat': -1.9667, 'lon': 29.3333},
                'sectors': {}
            }
        }
    }
    
    @classmethod
    def get_coordinates(cls, district: str, sector: Optional[str] = None) -> Optional[Dict[str, float]]:
        """
        Get coordinates for a district or specific sector
        
        Args:
            district: District name (e.g., 'Gasabo', 'Kicukiro')
            sector: Optional sector name (e.g., 'Bumbogo', 'Remera')
            
        Returns:
            Dictionary with 'lat' and 'lon' keys, or None if not found
        """
        # Search through all provinces
        for province_data in cls.LOCATIONS.values():
            if district in province_data:
                district_data = province_data[district]
                
                # If sector specified, try to get sector coordinates
                if sector and sector in district_data.get('sectors', {}):
                    return district_data['sectors'][sector]
                
                # Otherwise return district coordinates
                return district_data['coordinates']
        
        logger.warning(f"Location not found: {district}" + (f", {sector}" if sector else ""))
        return None
    
    @classmethod
    def get_all_districts(cls) -> List[str]:
        """
        Get list of all districts in Rwanda
        
        Returns:
            List of district names
        """
        districts = []
        for province_data in cls.LOCATIONS.values():
            districts.extend(province_data.keys())
        return sorted(districts)
    
    @classmethod
    def get_districts_by_province(cls, province: str) -> List[str]:
        """
        Get all districts in a specific province
        
        Args:
            province: Province name ('Kigali', 'Eastern', 'Northern', 'Southern', 'Western')
            
        Returns:
            List of district names in that province
        """
        if province in cls.LOCATIONS:
            return sorted(cls.LOCATIONS[province].keys())
        return []
    
    @classmethod
    def get_sectors(cls, district: str) -> List[str]:
        """
        Get all sectors in a specific district
        
        Args:
            district: District name
            
        Returns:
            List of sector names
        """
        for province_data in cls.LOCATIONS.values():
            if district in province_data:
                sectors = province_data[district].get('sectors', {})
                return sorted(sectors.keys())
        return []
    
    @classmethod
    def search_location(cls, query: str) -> List[Dict]:
        """
        Search for locations matching a query string
        
        Args:
            query: Search string (case-insensitive)
            
        Returns:
            List of matching locations with their details
        """
        query = query.lower()
        results = []
        
        for province, province_data in cls.LOCATIONS.items():
            for district, district_data in province_data.items():
                # Check if district matches
                if query in district.lower():
                    results.append({
                        'type': 'district',
                        'province': province,
                        'district': district,
                        'coordinates': district_data['coordinates']
                    })
                
                # Check sectors
                for sector, coords in district_data.get('sectors', {}).items():
                    if query in sector.lower():
                        results.append({
                            'type': 'sector',
                            'province': province,
                            'district': district,
                            'sector': sector,
                            'coordinates': coords
                        })
        
        return results
    
    @classmethod
    def validate_coordinates(cls, lat: float, lon: float) -> bool:
        """
        Validate if coordinates are within Rwanda's boundaries
        
        Rwanda approximate boundaries:
        Latitude: -2.8 to -1.0
        Longitude: 28.8 to 30.9
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if coordinates are within Rwanda
        """
        return (-2.9 <= lat <= -1.0) and (28.7 <= lon <= 31.0)


# Unit tests
if __name__ == "__main__":
    print("=== Rwanda Locations Mapping Module ===\n")
    
    # Test 1: Get coordinates for a district
    print("1. Get coordinates for Gasabo district:")
    coords = RwandaLocations.get_coordinates('Gasabo')
    print(f"   Coordinates: {coords}\n")
    
    # Test 2: Get coordinates for a specific sector
    print("2. Get coordinates for Bumbogo sector:")
    coords = RwandaLocations.get_coordinates('Gasabo', 'Bumbogo')
    print(f"   Coordinates: {coords}\n")
    
    # Test 3: List all districts
    print("3. All districts in Rwanda:")
    districts = RwandaLocations.get_all_districts()
    print(f"   Total: {len(districts)} districts")
    print(f"   {', '.join(districts[:5])}...\n")
    
    # Test 4: Get districts in Kigali province
    print("4. Districts in Kigali Province:")
    kigali_districts = RwandaLocations.get_districts_by_province('Kigali')
    print(f"   {kigali_districts}\n")
    
    # Test 5: Get sectors in Gasabo
    print("5. Sectors in Gasabo district:")
    sectors = RwandaLocations.get_sectors('Gasabo')
    print(f"   Total: {len(sectors)} sectors")
    print(f"   {', '.join(sectors[:5])}...\n")
    
    # Test 6: Search functionality
    print("6. Search for 'Bum':")
    results = RwandaLocations.search_location('Bum')
    for result in results:
        print(f"   {result}\n")
    
    # Test 7: Validate coordinates
    print("7. Validate coordinates:")
    print(f"   Kigali (-1.9441, 30.0619): {RwandaLocations.validate_coordinates(-1.9441, 30.0619)}")
    print(f"   Paris (48.8566, 2.3522): {RwandaLocations.validate_coordinates(48.8566, 2.3522)}")