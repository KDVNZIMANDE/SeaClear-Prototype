from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secret key

# MongoDB setup
client = MongoClient('mongodb://localhost:27017/')
print(f"Connected to MongoDB: {client.server_info()}")
db = client['seaclear_db']
beaches_collection = db['beaches']
users_collection = db['users']
posts_collection = db['posts']

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.email = user_data['email']
        self.username = user_data['username']
        self.role = user_data['role']

@login_manager.user_loader
def load_user(user_id):
    user_data = users_collection.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return User(user_data)
    return None

# Routes
@app.route('/')
def home():
    beaches = list(beaches_collection.find())
    for beach in beaches:
        if 'Date' in beach and isinstance(beach['Date'], datetime):
            beach['Date'] = beach['Date'].strftime('%Y-%m-%d')
        elif 'Date' not in beach:
            beach['Date'] = 'N/A'
        
        if 'image' not in beach:
            beach['image'] = 'default_beach.jpg'
    
    return render_template('home.html', beaches=beaches)

@app.route('/home1')
def home1():
    beaches = list(beaches_collection.find())
    for beach in beaches:
        if 'Date' in beach and isinstance(beach['Date'], datetime):
            beach['Date'] = beach['Date'].strftime('%Y-%m-%d')
        elif 'Date' not in beach:
            beach['Date'] = 'N/A'
        
        if 'image' not in beach:
            beach['image'] = 'default_beach.jpg'
    
    return render_template('home1.html', beaches=beaches)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/educational')
def educational():
    return render_template('educational.html')

@app.route('/map')
def map():
    return render_template('map.html')

@app.route('/beach/<beach_id>', methods=['GET', 'POST'])
def beach_detail(beach_id):
    # Handle GET request
    # Fetch beach details and comments
    beach = beaches_collection.find_one({'_id': ObjectId(beach_id)})
    if not beach:
        flash('Beach not found.', 'danger')
        return redirect(url_for('home'))
    comments = posts_collection.find({'beach_id': ObjectId(beach_id), 'status': 'approved'})#.sort('timestamp', pymongo.ASCENDING)

    # Determine the map image URL
    map_image = beach.get('map_image', 'default_beach.jpg')

    return render_template('beach_detail.html', beach=beach, comments=comments, map_image=map_image)


@app.route('/post', methods=['POST'])
@login_required
def post():
    content = request.form['content']
    beach_id = request.form['beach_id']
    new_post = {
        'beach_id': ObjectId(beach_id),
        'user_id': current_user.id,
        'username': current_user.username,
        'timestamp': datetime.utcnow(),
        'content': content,
        'status': 'pending',
        'likes': 0
    }
    posts_collection.insert_one(new_post)
    return redirect(url_for('beach_detail', beach_id=beach_id))

@app.route('/like/<post_id>')
@login_required
def like(post_id):
    posts_collection.update_one({'_id': ObjectId(post_id)}, {'$inc': {'likes': 1}})
    post = posts_collection.find_one({'_id': ObjectId(post_id)})
    return redirect(url_for('beach_detail', beach_id=post['beach_id']))

@app.route('/admin')
@login_required
def admin_dashboard():
    admin_user = users_collection.find_one({'role': 'admin'})
    if current_user.role != "admin":
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('home'))
    pending_posts = posts_collection.find({'status': 'pending'})
    beaches = beaches_collection.find()
    posts = posts_collection.find()
    # Define custom sort order using an aggregation pipeline
    pipeline = [
        {
            "$addFields": {
                "sort_order": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$status", "pending"]}, "then": 0},
                            {"case": {"$eq": ["$status", "denied"]}, "then": 1},
                        ],
                        "default": 2  # All other statuses
                    }
                }
            }
        },
        {"$sort": {"sort_order": 1}}
    ]

    # Run the aggregation pipeline to fetch and sort the posts
    posts = list(posts_collection.aggregate(pipeline))
    return render_template('admin.html', posts = posts, beaches=beaches)

@app.route('/admin/approve/<post_id>')
@login_required
def approve_post(post_id):
    if current_user.role != "admin":
        return redirect(url_for('home'))
    posts_collection.update_one({'_id': ObjectId(post_id)}, {'$set': {'status': 'approved'}})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/deny/<post_id>')
@login_required
def deny_post(post_id):
    if current_user.role != "admin":
        return redirect(url_for('home'))
    posts_collection.update_one({'_id': ObjectId(post_id)}, {'$set': {'status': 'denied'}})
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_post/<post_id>')
@login_required
def delete_post(post_id):
    try:
        # Delete the post by its ID
        result = posts_collection.delete_one({'_id': ObjectId(post_id)})
        
        if result.deleted_count > 0:
            flash('Post deleted successfully!', 'success')
        else:
            flash('Post not found!', 'danger')
    except Exception as e:
        flash(f'An error occurred: {str(e)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/edit_beach/<beach_id>', methods=['GET', 'POST'])
@login_required
def edit_beach(beach_id):
    beach = beaches_collection.find_one({"_id": ObjectId(beach_id)})

    if request.method == 'POST':
        updated_data = {
            "name": request.form['name'],
            "location": request.form['location'],
            "date": request.form['date'],
            "entrocciticount": request.form['entrocciticount'],
            "grade": request.form['grade'],
            "temperature": request.form['temperature'],
            "wind_speed": request.form['wind_speed'],
            "wind_direction": request.form['wind_direction'],
            "status": request.form['status'],
        }

        # Handle map_image upload
        if 'map_image' in request.files:
            map_image = request.files['map_image']
            if map_image.filename != '':
                updated_data['map_image'] = map_image.filename
                map_image.save(f"static/uploads/{map_image.filename}")  # Save the file

        # Update the beach document in MongoDB
        beaches_collection.update_one({"_id": ObjectId(beach_id)}, {"$set": updated_data})

        flash('Beach updated successfully!', 'success')
        return redirect(url_for('edit_beach', beach_id=beach_id))

    return render_template('edit_beach.html', beach=beach)

@app.route('/admin/delete_beach/<beach_id>')
@login_required
def delete_beach(beach_id):
    try:
        # Ensure the beach_id is valid
        if not ObjectId.is_valid(beach_id):
            flash('Invalid beach ID.', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Convert beach_id to ObjectId
        beach_id = ObjectId(beach_id)

        # Delete the document from MongoDB
        result = beaches_collection.delete_one({"_id": beach_id})

        if result.deleted_count > 0:
            flash('Beach deleted successfully!', 'success')
        else:
            flash('Beach not found.', 'danger')
    
    except Exception as e:
        # Handle any errors that occur
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_beach', methods=['GET', 'POST'])
@login_required
def add_beach():
    if request.method == 'POST':
        # Collect form data with a default value for each field
        name = request.form.get('name', '')
        location = request.form.get('location', '')
        date = request.form.get('date', '')
        entrocciticount = request.form.get('entrocciticount', '')
        grade = request.form.get('grade', '')
        temperature = request.form.get('temperature', '')
        wind_speed = request.form.get('wind_speed', '')
        wind_direction = request.form.get('wind_direction', '')
        status = request.form.get('status', '')

        # Handle map_image upload
        #map_image = request.files.get('map_image')
        #map_image_filename = None
        #if map_image and map_image.filename:
            #map_image_filename = secure_filename(map_image.filename)
            #map_image.save(os.path.join('static/uploads', map_image_filename)) #TODO

        # Insert the new beach document into MongoDB
        beach_data = {
            "name": name,
            "location": location,
            "date": date,
            "entrocciticount": entrocciticount,
            "grade": grade,
            "temperature": temperature,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "status": status,
            #"map_image": map_image_filename or 'default_beach.jpg'  # Provide a default image if none is uploaded
            "map_image": 'default_beach.jpg'
        }
        beaches_collection.insert_one(beach_data)

        flash('Beach added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))

    # Render the form on GET request
    return render_template('add_beach.html')



@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        username = request.form.get('username')

        # Check if the email already exists in the database
        existing_user = users_collection.find_one({'email': email})
        if existing_user:
            flash('Email address already exists. Please choose another.', 'danger')
            return redirect(url_for('sign_up'))
        
        # Check that both passwords are the same
        if password1 == password2:
            password = password1
        else:
            flash('Please ensure both passwords are the same.', 'danger')
            return redirect(url_for('sign_up'))

        # Hash the password before storing
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Insert new user into the database
        new_user = {
            'email': email,
            'password': hashed_password,
            'username': username,
            'role': 'user'
        }
        users_collection.insert_one(new_user)

        flash('Sign-up successful! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        print(f"Login attempt: email={email}, password={'*' * len(password)}")
        
        user = users_collection.find_one({'email': email})
        print(f"User found in database: {user}")
        
        if user and check_password_hash(user['password'], password):
            user_obj = User(user)
            login_user(user_obj)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/search')
def search():
    query = request.args.get('query', '')
    beaches = list(beaches_collection.find())
    return render_template('search_results.html', query=query, beaches=beaches) 

if __name__ == '__main__':
    app.run(debug=True)