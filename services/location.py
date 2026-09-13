"""Phone number prefix → Indian city/state/location mapping"""

import re
from typing import Optional

# Indian telecom circle mapping by phone prefix (first 4 digits after +91)
# Each entry: (city, state, latitude, longitude)
PHONE_LOCATION_MAP = {
    # Maharashtra / Mumbai
    "980": ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    "981": ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    "982": ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    "983": ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    "986": ("Pune", "Maharashtra", 18.5204, 73.8567),
    "987": ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    "989": ("Nagpur", "Maharashtra", 21.1458, 79.0882),
    "770": ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    "771": ("Mumbai", "Maharashtra", 19.0760, 72.8777),
    "772": ("Pune", "Maharashtra", 18.5204, 73.8567),

    # Delhi / NCR
    "720": ("Delhi", "Delhi", 28.7041, 77.1025),
    "721": ("Delhi", "Delhi", 28.7041, 77.1025),
    "725": ("Delhi", "Delhi", 28.7041, 77.1025),
    "726": ("Delhi", "Delhi", 28.7041, 77.1025),
    "727": ("Noida", "Uttar Pradesh", 28.5355, 77.3910),
    "728": ("Gurgaon", "Haryana", 28.4595, 77.0266),
    "729": ("Faridabad", "Haryana", 28.4089, 77.3178),
    "981": ("Delhi", "Delhi", 28.7041, 77.1025),
    "987": ("Delhi", "Delhi", 28.7041, 77.1025),

    # Karnataka / Bangalore
    "810": ("Bangalore", "Karnataka", 12.9716, 77.5946),
    "811": ("Bangalore", "Karnataka", 12.9716, 77.5946),
    "812": ("Bangalore", "Karnataka", 12.9716, 77.5946),
    "813": ("Bangalore", "Karnataka", 12.9716, 77.5946),
    "814": ("Mysore", "Karnataka", 12.2958, 76.6394),
    "815": ("Mangalore", "Karnataka", 12.9141, 74.8560),
    "819": ("Hubli", "Karnataka", 15.3647, 75.1240),
    "820": ("Bangalore", "Karnataka", 12.9716, 77.5946),
    "821": ("Bangalore", "Karnataka", 12.9716, 77.5946),
    "822": ("Mysore", "Karnataka", 12.2958, 76.6394),

    # Gujarat / Ahmedabad
    "900": ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    "901": ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    "902": ("Surat", "Gujarat", 21.1702, 72.8311),
    "903": ("Vadodara", "Gujarat", 22.3072, 73.1812),
    "904": ("Rajkot", "Gujarat", 22.3039, 70.8022),
    "905": ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    "906": ("Surat", "Gujarat", 21.1702, 72.8311),
    "909": ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    "910": ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    "911": ("Surat", "Gujarat", 21.1702, 72.8311),
    "912": ("Vadodara", "Gujarat", 22.3072, 73.1812),
    "913": ("Rajkot", "Gujarat", 22.3039, 70.8022),
    "917": ("Ahmedabad", "Gujarat", 23.0225, 72.5714),
    "918": ("Surat", "Gujarat", 21.1702, 72.8311),
    "919": ("Ahmedabad", "Gujarat", 23.0225, 72.5714),

    # Tamil Nadu / Chennai
    "770": ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    "773": ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    "774": ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    "775": ("Coimbatore", "Tamil Nadu", 11.0168, 76.9558),
    "776": ("Madurai", "Tamil Nadu", 9.9252, 78.1198),
    "777": ("Chennai", "Tamil Nadu", 13.0827, 80.2707),
    "778": ("Salem", "Tamil Nadu", 11.6643, 78.1460),
    "779": ("Chennai", "Tamil Nadu", 13.0827, 80.2707),

    # UP / Lucknow
    "850": ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    "851": ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    "852": ("Kanpur", "Uttar Pradesh", 26.4499, 80.3319),
    "853": ("Agra", "Uttar Pradesh", 27.1767, 78.0081),
    "854": ("Varanasi", "Uttar Pradesh", 25.3176, 82.9739),
    "855": ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),
    "856": ("Noida", "Uttar Pradesh", 28.5355, 77.3910),
    "857": ("Ghaziabad", "Uttar Pradesh", 28.6692, 77.4538),
    "858": ("Meerut", "Uttar Pradesh", 28.9845, 77.7064),
    "859": ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462),

    # Rajasthan / Jaipur
    "740": ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    "741": ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    "742": ("Jodhpur", "Rajasthan", 26.2389, 73.0243),
    "743": ("Udaipur", "Rajasthan", 24.5854, 73.7125),
    "744": ("Kota", "Rajasthan", 25.2138, 75.8648),
    "745": ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    "746": ("Ajmer", "Rajasthan", 26.4499, 74.6399),
    "747": ("Bikaner", "Rajasthan", 28.0229, 73.3194),
    "748": ("Jaipur", "Rajasthan", 26.9124, 75.7873),
    "749": ("Jodhpur", "Rajasthan", 26.2389, 73.0243),

    # West Bengal / Kolkata
    "880": ("Kolkata", "West Bengal", 22.5726, 88.3639),
    "881": ("Kolkata", "West Bengal", 22.5726, 88.3639),
    "882": ("Kolkata", "West Bengal", 22.5726, 88.3639),
    "883": ("Howrah", "West Bengal", 22.5958, 88.2636),
    "884": ("Durgapur", "West Bengal", 23.5204, 87.3119),
    "885": ("Kolkata", "West Bengal", 22.5726, 88.3639),
    "886": ("Siliguri", "West Bengal", 26.7271, 88.3953),
    "887": ("Kolkata", "West Bengal", 22.5726, 88.3639),
    "888": ("Kolkata", "West Bengal", 22.5726, 88.3639),
    "889": ("Kolkata", "West Bengal", 22.5726, 88.3639),

    # Andhra Pradesh / Hyderabad
    "700": ("Hyderabad", "Telangana", 17.3850, 78.4867),
    "701": ("Hyderabad", "Telangana", 17.3850, 78.4867),
    "702": ("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185),
    "703": ("Hyderabad", "Telangana", 17.3850, 78.4867),
    "704": ("Vijayawada", "Andhra Pradesh", 16.5062, 80.6480),
    "705": ("Hyderabad", "Telangana", 17.3850, 78.4867),
    "706": ("Tirupati", "Andhra Pradesh", 13.6288, 79.4192),
    "707": ("Hyderabad", "Telangana", 17.3850, 78.4867),
    "708": ("Warangal", "Telangana", 17.9784, 79.5941),
    "709": ("Hyderabad", "Telangana", 17.3850, 78.4867),

    # Punjab / Chandigarh
    "920": ("Chandigarh", "Punjab", 30.7333, 76.7794),
    "921": ("Ludhiana", "Punjab", 30.9010, 75.8573),
    "922": ("Amritsar", "Punjab", 31.6340, 74.8723),
    "923": ("Jalandhar", "Punjab", 31.3260, 75.5762),
    "924": ("Chandigarh", "Punjab", 30.7333, 76.7794),
    "925": ("Ludhiana", "Punjab", 30.9010, 75.8573),
    "926": ("Patiala", "Punjab", 30.3398, 76.3869),
    "927": ("Chandigarh", "Punjab", 30.7333, 76.7794),
    "928": ("Amritsar", "Punjab", 31.6340, 74.8723),
    "929": ("Chandigarh", "Punjab", 30.7333, 76.7794),

    # Madhya Pradesh / Bhopal
    "830": ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    "831": ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    "832": ("Indore", "Madhya Pradesh", 22.7196, 75.8577),
    "833": ("Jabalpur", "Madhya Pradesh", 23.1815, 79.9864),
    "834": ("Gwalior", "Madhya Pradesh", 26.2183, 78.1828),
    "835": ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    "836": ("Ujjain", "Madhya Pradesh", 23.1765, 75.7885),
    "837": ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),
    "838": ("Indore", "Madhya Pradesh", 22.7196, 75.8577),
    "839": ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126),

    # Kerala / Trivandrum
    "950": ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),
    "951": ("Kochi", "Kerala", 9.9312, 76.2673),
    "952": ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),
    "953": ("Kozhikode", "Kerala", 11.2588, 75.7804),
    "954": ("Thrissur", "Kerala", 10.5276, 76.2144),
    "955": ("Kochi", "Kerala", 9.9312, 76.2673),
    "956": ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),
    "957": ("Kollam", "Kerala", 8.8932, 76.6141),
    "958": ("Kochi", "Kerala", 9.9312, 76.2673),
    "959": ("Thiruvananthapuram", "Kerala", 8.5241, 76.9366),

    # Bihar / Patna
    "760": ("Patna", "Bihar", 25.6093, 85.1376),
    "761": ("Patna", "Bihar", 25.6093, 85.1376),
    "762": ("Gaya", "Bihar", 24.7963, 84.9947),
    "763": ("Muzaffarpur", "Bihar", 26.1209, 85.3647),
    "764": ("Bhagalpur", "Bihar", 25.2425, 86.9842),
    "765": ("Patna", "Bihar", 25.6093, 85.1376),
    "766": ("Patna", "Bihar", 25.6093, 85.1376),
    "767": ("Patna", "Bihar", 25.6093, 85.1376),
    "768": ("Gaya", "Bihar", 24.7963, 84.9947),
    "769": ("Patna", "Bihar", 25.6093, 85.1376),

    # Odisha / Bhubaneswar
    "870": ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    "871": ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    "872": ("Cuttack", "Odisha", 20.4625, 85.8830),
    "873": ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    "874": ("Sambalpur", "Odisha", 21.4704, 83.9700),
    "875": ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    "876": ("Berhampur", "Odisha", 19.3149, 84.7942),
    "877": ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    "878": ("Bhubaneswar", "Odisha", 20.2961, 85.8245),
    "879": ("Cuttack", "Odisha", 20.4625, 85.8830),

    # Assam / Guwahati
    "940": ("Guwahati", "Assam", 26.1445, 91.7362),
    "941": ("Guwahati", "Assam", 26.1445, 91.7362),
    "942": ("Silchar", "Assam", 24.8333, 92.7789),
    "943": ("Guwahati", "Assam", 26.1445, 91.7362),
    "945": ("Dibrugarh", "Assam", 27.4728, 94.9120),
    "946": ("Guwahati", "Assam", 26.1445, 91.7362),
    "947": ("Guwahati", "Assam", 26.1445, 91.7362),

    # Jharkhand / Ranchi
    "947": ("Ranchi", "Jharkhand", 23.3441, 85.3096),
    "948": ("Jamshedpur", "Jharkhand", 22.8046, 86.2029),
    "949": ("Dhanbad", "Jharkhand", 23.7957, 86.4304),
    "950": ("Ranchi", "Jharkhand", 23.3441, 85.3096),

    # Chhattisgarh / Raipur
    "960": ("Raipur", "Chhattisgarh", 21.2514, 81.6296),
    "961": ("Raipur", "Chhattisgarh", 21.2514, 81.6296),
    "962": ("Bhilai", "Chhattisgarh", 21.2091, 81.4314),
    "963": ("Raipur", "Chhattisgarh", 21.2514, 81.6296),

    # Goa
    "970": ("Panaji", "Goa", 15.4909, 73.8278),
    "971": ("Panaji", "Goa", 15.4909, 73.8278),
    "972": ("Margao", "Goa", 15.2993, 73.9573),
    "973": ("Panaji", "Goa", 15.4909, 73.8278),

    # Uttarakhand / Dehradun
    "975": ("Dehradun", "Uttarakhand", 30.3165, 78.0322),
    "976": ("Dehradun", "Uttarakhand", 30.3165, 78.0322),
    "977": ("Haridwar", "Uttarakhand", 29.9457, 78.1642),
    "978": ("Dehradun", "Uttarakhand", 30.3165, 78.0322),

    # Himachal Pradesh / Shimla
    "980": ("Shimla", "Himachal Pradesh", 31.1048, 77.1734),
    "981": ("Shimla", "Himachal Pradesh", 31.1048, 77.1734),

    # Haryana / Gurgaon
    "981": ("Gurgaon", "Haryana", 28.4595, 77.0266),
    "982": ("Faridabad", "Haryana", 28.4089, 77.3178),

    # Jammu & Kashmir
    "941": ("Srinagar", "Jammu & Kashmir", 34.0837, 74.7973),
    "942": ("Jammu", "Jammu & Kashmir", 32.7266, 74.8570),
    "943": ("Srinagar", "Jammu & Kashmir", 34.0837, 74.7973),

    # Chhattisgarh
    "975": ("Raipur", "Chhattisgarh", 21.2514, 81.6296),
    "976": ("Bilaspur", "Chhattisgarh", 22.0822, 82.1518),
}

# Default location if prefix not found
DEFAULT_LOCATION = ("Unknown", "India", 20.5937, 78.9629)


def get_location_from_phone(phone_number: str) -> dict:
    """
    Extract city/state/lat/lng from Indian phone number prefix.
    
    Args:
        phone_number: Phone number in any format (+91-XXXXXXXXXX, 91XXXXXXXXXX, etc.)
    
    Returns:
        dict with city, state, latitude, longitude
    """
    # Remove all non-digits
    digits = re.sub(r'[^\d]', '', phone_number)
    
    # Handle +91 prefix
    if digits.startswith('91') and len(digits) > 10:
        digits = digits[2:]
    
    # Take first 4 digits for lookup (Indian mobile numbers have 10 digits, first 4 identify the telecom circle)
    if len(digits) >= 4:
        prefix = digits[:4]
    elif len(digits) >= 3:
        prefix = digits[:3]
    else:
        city, state, lat, lng = DEFAULT_LOCATION
        return {"city": city, "state": state, "latitude": lat, "longitude": lng}
    
    # Try 4-digit match first, then 3-digit
    result = PHONE_LOCATION_MAP.get(prefix)
    if result is None:
        result = PHONE_LOCATION_MAP.get(prefix[:3])
    
    if result:
        city, state, lat, lng = result
    else:
        city, state, lat, lng = DEFAULT_LOCATION
    
    return {"city": city, "state": state, "latitude": lat, "longitude": lng}


def get_all_india_threats(analyses: list) -> list:
    """
    Group analyses by city and return map points with threat counts.
    
    Args:
        analyses: List of analysis dicts with city, state, latitude, longitude, risk_level
    
    Returns:
        List of ThreatMapPoint dicts
    """
    city_data = {}
    
    for a in analyses:
        city = a.get("city") or "Unknown"
        state = a.get("state") or "Unknown"
        lat = a.get("latitude") or 20.5937
        lng = a.get("longitude") or 78.9629
        risk_level = a.get("risk_level", "LOW")
        
        key = f"{city}_{state}"
        
        if key not in city_data:
            city_data[key] = {
                "city": city,
                "state": state,
                "latitude": lat,
                "longitude": lng,
                "totalThreats": 0,
                "highRiskCount": 0,
                "mediumRiskCount": 0,
                "lowRiskCount": 0,
            }
        
        city_data[key]["totalThreats"] += 1
        
        if risk_level == "HIGH":
            city_data[key]["highRiskCount"] += 1
        elif risk_level == "MEDIUM":
            city_data[key]["mediumRiskCount"] += 1
        else:
            city_data[key]["lowRiskCount"] += 1
    
    return list(city_data.values())
