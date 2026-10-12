"""Top 100 US metropolitan areas (by population, Census estimates), as (metro label, principal city, state).

The principal city is used for NPI Registry lookups and Places text queries.
"""

METROS = [
    ("New York", "New York", "NY"), ("Los Angeles", "Los Angeles", "CA"), ("Chicago", "Chicago", "IL"),
    ("Dallas-Fort Worth", "Dallas", "TX"), ("Houston", "Houston", "TX"), ("Atlanta", "Atlanta", "GA"),
    ("Washington DC", "Washington", "DC"), ("Philadelphia", "Philadelphia", "PA"), ("Miami", "Miami", "FL"),
    ("Phoenix", "Phoenix", "AZ"), ("Boston", "Boston", "MA"), ("Riverside-San Bernardino", "Riverside", "CA"),
    ("San Francisco-Oakland", "San Francisco", "CA"), ("Detroit", "Detroit", "MI"), ("Seattle", "Seattle", "WA"),
    ("Minneapolis-St. Paul", "Minneapolis", "MN"), ("Tampa", "Tampa", "FL"), ("San Diego", "San Diego", "CA"),
    ("Denver", "Denver", "CO"), ("Orlando", "Orlando", "FL"), ("Charlotte", "Charlotte", "NC"),
    ("Baltimore", "Baltimore", "MD"), ("St. Louis", "St. Louis", "MO"), ("San Antonio", "San Antonio", "TX"),
    ("Austin", "Austin", "TX"), ("Portland", "Portland", "OR"), ("Sacramento", "Sacramento", "CA"),
    ("Pittsburgh", "Pittsburgh", "PA"), ("Las Vegas", "Las Vegas", "NV"), ("Cincinnati", "Cincinnati", "OH"),
    ("Kansas City", "Kansas City", "MO"), ("Columbus", "Columbus", "OH"), ("Indianapolis", "Indianapolis", "IN"),
    ("Cleveland", "Cleveland", "OH"), ("Nashville", "Nashville", "TN"), ("San Jose", "San Jose", "CA"),
    ("Virginia Beach-Norfolk", "Virginia Beach", "VA"), ("Jacksonville", "Jacksonville", "FL"),
    ("Providence", "Providence", "RI"), ("Raleigh", "Raleigh", "NC"), ("Milwaukee", "Milwaukee", "WI"),
    ("Oklahoma City", "Oklahoma City", "OK"), ("Louisville", "Louisville", "KY"), ("Memphis", "Memphis", "TN"),
    ("Richmond", "Richmond", "VA"), ("Salt Lake City", "Salt Lake City", "UT"), ("Birmingham", "Birmingham", "AL"),
    ("Fresno", "Fresno", "CA"), ("Grand Rapids", "Grand Rapids", "MI"), ("Buffalo", "Buffalo", "NY"),
    ("Hartford", "Hartford", "CT"), ("Tucson", "Tucson", "AZ"), ("Tulsa", "Tulsa", "OK"), ("Worcester", "Worcester", "MA"),
    ("Rochester", "Rochester", "NY"), ("Omaha", "Omaha", "NE"), ("Greenville", "Greenville", "SC"),
    ("New Orleans", "New Orleans", "LA"), ("Knoxville", "Knoxville", "TN"), ("Bridgeport-Stamford", "Bridgeport", "CT"),
    ("Albuquerque", "Albuquerque", "NM"), ("Bakersfield", "Bakersfield", "CA"), ("McAllen", "McAllen", "TX"),
    ("Albany", "Albany", "NY"), ("Baton Rouge", "Baton Rouge", "LA"), ("Allentown", "Allentown", "PA"),
    ("New Haven", "New Haven", "CT"), ("El Paso", "El Paso", "TX"), ("Sarasota-North Port", "Sarasota", "FL"),
    ("Columbia", "Columbia", "SC"), ("Oxnard-Thousand Oaks", "Oxnard", "CA"), ("Dayton", "Dayton", "OH"),
    ("Charleston", "Charleston", "SC"), ("Cape Coral-Fort Myers", "Cape Coral", "FL"), ("Boise", "Boise", "ID"),
    ("Lakeland", "Lakeland", "FL"), ("Stockton", "Stockton", "CA"), ("Colorado Springs", "Colorado Springs", "CO"),
    ("Greensboro", "Greensboro", "NC"), ("Little Rock", "Little Rock", "AR"), ("Des Moines", "Des Moines", "IA"),
    ("Deltona-Daytona Beach", "Daytona Beach", "FL"), ("Akron", "Akron", "OH"), ("Ogden", "Ogden", "UT"),
    ("Poughkeepsie", "Poughkeepsie", "NY"), ("Winston-Salem", "Winston-Salem", "NC"), ("Madison", "Madison", "WI"),
    ("Provo-Orem", "Provo", "UT"), ("Syracuse", "Syracuse", "NY"), ("Wichita", "Wichita", "KS"),
    ("Durham-Chapel Hill", "Durham", "NC"), ("Palm Bay-Melbourne", "Melbourne", "FL"), ("Toledo", "Toledo", "OH"),
    ("Augusta", "Augusta", "GA"), ("Harrisburg", "Harrisburg", "PA"), ("Spokane", "Spokane", "WA"),
    ("Jackson", "Jackson", "MS"), ("Chattanooga", "Chattanooga", "TN"), ("Scranton", "Scranton", "PA"),
    ("Lancaster", "Lancaster", "PA"),
]

assert len(METROS) == 100, len(METROS)
