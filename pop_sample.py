from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from bson.objectid import ObjectId
import random

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['seaclear_db']  # Replace with your actual database name

# Sample data
beaches = [
    {
        "name": "Clifton 4th Beach",
        "location": "Cape Town",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "entrocciticount": "0",
        "grade": "A",
        "temperature": "22°C",
        "wind_speed": "15 km/h",
        "wind_direction": "SE",
        "status": "Open",
        "map_image": "clifton_4th.jpg"
    },
    {
        "name": "Muizenberg Beach",
        "location": "Cape Town",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "entrocciticount": "5",
        "grade": "B",
        "temperature": "20°C",
        "wind_speed": "20 km/h",
        "wind_direction": "SW",
        "status": "Open",
        "map_image": "muizenberg.jpg"
    },
    {
        "name": "Bloubergstrand",
        "location": "Cape Town",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "entrocciticount": "1",
        "grade": "A",
        "temperature": "23°C",
        "wind_speed": "25 km/h",
        "wind_direction": "NW",
        "status": "Open",
        "map_image": "bloubergstrand.jpg"
    }
]

users = [
    {
        "email": "user1@example.com",
        "password": generate_password_hash("password123", method="pbkdf2:sha256", salt_length=8),
        "user_name": "User One",
        "role": "user"
    },
    {
        "email": "admin@example.com",
        "password": generate_password_hash("adminpass", method="pbkdf2:sha256", salt_length=8),
        "user_name": "Admin User",
        "role": "admin"
    }
]

# Function to generate random posts
def generate_posts(beach_ids, user_ids):
    posts = []
    for _ in range(10):  # Generate 10 sample posts
        posts.append({
            "content": f"Sample post content {random.randint(1, 100)}",
            "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d %H:%M:%S"),
            "status": random.choice(["active", "archived"]),
            "likes": random.randint(0, 100),
            "beach_id": ObjectId(random.choice(beach_ids)),
            "user_id": random.choice(user_ids)
        })
    return posts

# Insert data into collections
beach_collection = db.beaches
user_collection = db.users
post_collection = db.posts

# Insert beaches
beach_result = beach_collection.insert_many(beaches)
print(f"Inserted {len(beach_result.inserted_ids)} beaches")

# Insert users
user_result = user_collection.insert_many(users)
print(f"Inserted {len(user_result.inserted_ids)} users")

# Generate and insert posts
posts = generate_posts(beach_result.inserted_ids, user_result.inserted_ids)
post_result = post_collection.insert_many(posts)
print(f"Inserted {len(post_result.inserted_ids)} posts")

print("Sample data insertion complete!")