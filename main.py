from flask import Flask,render_template,request,session,redirect,url_for,flash,send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session
from flask_caching import Cache  
import pandas as pd  
from sklearn.feature_extraction.text import CountVectorizer  
from sklearn.metrics.pairwise import cosine_similarity
from flask_login import UserMixin
from flask_admin import Admin, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug.utils import secure_filename  
import os
from PIL import Image
from flask_login import login_user,logout_user,login_manager,LoginManager
from flask_login import login_required,current_user
from datetime import datetime


# MY db connection
local_server= True
app = Flask(__name__)
app.secret_key='harshithbhaskar'


# this is for getting unique user access
login_manager=LoginManager(app)
login_manager.login_view='MyAdminIndexView.login_view'  # Correct endpoint for admin login

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['CACHE_TYPE'] = 'SimpleCache' 

db=SQLAlchemy(app)
cache = Cache(app)

class MyAdminIndexView(AdminIndexView):  
    @expose('/')  
    @login_required  
    def index(self):  
        # Check if the current user is an admin  
        if not current_user.is_admin:  
            return "Access denied. You do not have permission to view this page.", 403  
        return super().index()  # Use super() without arguments  

    @expose('/login', methods=['GET', 'POST'])  
    def login_view(self):  
        if request.method == 'POST':  
            username = request.form['username']  
            password = request.form['password']  
            user = User.query.filter_by(username=username).first()  
            if user and check_password_hash(user.password, password):  
                login_user(user)  
                if user.is_admin:  # Redirect to the admin area if the user is an admin  
                    return redirect(url_for('admin.index', _external=True))  
                else:  
                    return "You do not have access to the admin area.", 403  # Alternatively, redirect to a supplier dashboard if you have it.  
            flash('Invalid username or password.')  
        return render_template('login.html')  # Ensure you create this template.  


    @expose('/logout')
    @login_required
    def logout_view(self):
        logout_user()
        return redirect(url_for('login_view'))  # Redirect to the login page

admin = Admin(app, index_view=MyAdminIndexView(), name='MyApp', template_mode='bootstrap3')

# here we will create db models that is tables
class Test(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(100))

class User(UserMixin, db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    username = db.Column(db.String(50), unique=True)  
    email = db.Column(db.String(50), unique=True)  
    phone = db.Column(db.String(20))  
    location = db.Column(db.String(50))  
    password = db.Column(db.String(1000))  
    is_supplier = db.Column(db.Boolean, default=False)  
    is_admin = db.Column(db.Boolean, default=False)  # New field for admin authentication  
    profile_picture = db.Column(db.String(1000), nullable=True)  

class Addagroproducts(db.Model):
    username=db.Column(db.String(50))
    email=db.Column(db.String(50))
    phone=db.Column(db.String(20))
    pid=db.Column(db.Integer,primary_key=True)
    productname=db.Column(db.String(100))
    productdesc=db.Column(db.String(300))
    price=db.Column(db.Integer)
    status=db.Column(db.String(20))
    recommend=db.Column(db.String(20))
    product_picture = db.Column(db.String(1000), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    supplier = db.relationship('User', backref=db.backref('addagroproducts'))

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    housing_per_unit = db.Column(db.Float, nullable=False)
    housing_unit = db.Column(db.String(50), nullable=False)
    feed_requirement = db.Column(db.Float, nullable=False)
    average_weight = db.Column(db.Float, nullable=False)
    recommended_feed = db.Column(db.String(200), nullable=False)
    vaccination_schedule = db.Column(db.String(200), nullable=False)
    cost_per_unit = db.Column(db.Float, nullable=False)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price_per_seedling = db.Column(db.Float, nullable=False)
    seedlings_per_hectare = db.Column(db.Float, nullable=False)
    planting_interval = db.Column(db.String(100))
    weedicides = db.Column(db.String(100))
    weedicides_notes = db.Column(db.String(1000))
    pesticides = db.Column(db.String(100))
    pesticides_notes = db.Column(db.String(1000))
    fertilizers = db.Column(db.String(100))
    fertilizers_notes =db.Column(db.String(1000))


class Complaint(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    user_name = db.Column(db.String(100), nullable=False)  
    supplier_name = db.Column(db.String(100), nullable=False)  
    supplier_phone = db.Column(db.String(15), nullable=False)  
    product_name = db.Column(db.String(100), nullable=False)  
    product_id = db.Column(db.Integer, db.ForeignKey('addagroproducts.pid'), nullable=False)
    supplierRating = db.Column(db.String(5), nullable=False)
    complaint_text = db.Column(db.Text, nullable=False)

class ForumPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) # Foreign key to the User 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User', backref=db.backref('forum_posts', lazy=True)) # Relationship to the User 


class Comment(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    content = db.Column(db.Text, nullable=False)  
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    post_id = db.Column(db.Integer, db.ForeignKey('forum_post.id'), nullable=False)  # Foreign key to the ForumPost  
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  
    author = db.relationship('User', backref=db.backref('comments', lazy=True))  
    post = db.relationship('ForumPost', backref=db.backref('comments', lazy=True)) # Relationship to the ForumPost  

def create_admin_user():
    # Check if admin already exists first
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if not admin_user:
        try:
            admin_user = User(
                username='admin',
                email='admin@example.com',
                phone='1234567890',
                location='Admin Location',
                password=generate_password_hash('adminpassword'),
                is_admin=True,
            )
            db.session.add(admin_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")
class MyAdminIndexView(AdminIndexView):  
    @expose('/')  
    @login_required  
    def index(self, **kwargs):
        # Check if the current user is an admin  
        if not current_user.is_admin:  
            return "Access denied. You do not have permission to view this page.", 403  
        return super(MyAdminIndexView, self).index()
    @expose('/login', methods=['GET', 'POST'])  
    def login_view(self):  
        if request.method == 'POST':  
            username = request.form['username']  
            password = request.form['password']  
            user = User.query.filter_by(username=username).first()  
            if user and check_password_hash(user.password, password):  
                login_user(user)  
                if user.is_admin:  # Redirect to the admin area if the user is an admin  
                    return redirect(url_for('admin.index', _external=True))
                else:  
                    return "You do not have access to the admin area.", 403  # Alternatively, redirect to a supplier dashboard if you have it.  
            flash('Invalid username or password.')  
        return render_template('login.html')  # Ensure you create this template.  

    @expose('/logout')  
    @login_required  
    def logout_view(self):  
        logout_user()  
        return redirect(url_for('login_view'))  # Redirect to the login page    

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Addagroproducts, db.session))
admin.add_view(ModelView(Complaint, db.session))
admin.add_view(ModelView(Product, db.session))
admin.add_view(ModelView(ForumPost, db.session))
admin.add_view(ModelView(Comment, db.session))
admin.add_view(ModelView(Animal, db.session))
with app.app_context():
    db.create_all()
    create_admin_user()
     

@app.route('/')
def index(): 

    return render_template('index.html')
# this display all products added by a suppliers
@app.route('/agroproducts')
def agroproducts():
    query = Addagroproducts.query.join(User, Addagroproducts.supplier_id == User.id)
    
    if current_user.is_authenticated:
        user_location = current_user.location
        # Order by matching location first, then other locations
        from sqlalchemy import case
        query = query.order_by(
            case(
                (User.location == user_location, 0),
                else_=1
            ).asc(),
            Addagroproducts.productname.asc()  # Secondary sort by product name
        )
    else:
        # For non-logged in users, just order by product name
        query = query.order_by(Addagroproducts.productname.asc())
    
    return render_template('agroproducts.html', query=query.all())

# this handle suppliers product uploads
@app.route('/addagroproducts',methods=['POST','GET'])
@login_required
def addagroproduct():
    #if not session.get('is_supplier'):
    if not current_user.is_supplier:
        flash('You are not authorized to add product')
        return redirect(url_for('index'))
    
    if request.method=="POST":
        username=request.form.get('username')
        email=request.form.get('email')
        phone=request.form.get('phone')
        productname=request.form.get('productname')
        productdesc=request.form.get('productdesc')
        price=request.form.get('price')
        

        # Initialize profile_picture_path  
        product_picture_path = None  

        # Handle profile picture upload  
        product_picture = request.files.get('product_picture')  

        if product_picture:  
            # Validate file extension  
            if not (product_picture.filename.lower().endswith(('.png', '.jpg', '.jpeg'))):  
                flash("Only JPG and PNG files are allowed", "warning")  
                return render_template('/signup.html')  

            # Make sure the uploads directory exists  
           
            uploads_dir = os.path.abspath("uploads")  
            print(f"Uploads directory: {uploads_dir}")  # Print directory path  
            os.makedirs(uploads_dir, exist_ok=True)  

            # Generate a secure filename  
            filename = secure_filename(product_picture.filename)  
            product_picture_path = os.path.join(uploads_dir, filename)  

            try:  # Open the uploaded image and resize  
                with Image.open(product_picture) as img:  
                    img.thumbnail((800, 800))  # Resize image to a maximum of 800x800   
                    img.save(product_picture_path)  # Save resized image   
            except Exception as e:  
                print(f"An error occurred while saving the image: {e}")  
                flash("An error occurred while uploading the image.", "danger")  
                return render_template('/addagroproducts.html')

        products=Addagroproducts(username=username,email=email,phone=phone,productname=productname,productdesc=productdesc,price=price,product_picture=filename,supplier_id=current_user.id)
        db.session.add(products)
        db.session.commit()
        flash("Product Added","info")
        return redirect('/agroproducts')
   
    return render_template('addagroproducts.html')

# Route to display and handle the complaint form  
@app.route('/complaint/<string:product_id>', methods=['GET', 'POST'])
@login_required  
def complaint(product_id):  
    product = Addagroproducts.query.get_or_404(product_id)
    if request.method == 'POST':  
        user_name = request.form.get('username')  
        supplier_name = request.form.get('supplier_name')    
        supplier_phone = request.form.get('supplier_phone')
        product_name =   request.form.get('product_name')
        supplierRating = request.form.get('supplierRating')
        complaint_text = request.form.get('complaint_text')  

        new_complaint = Complaint(  
            user_name=user_name,  
            supplier_name=supplier_name,  
            supplier_phone=supplier_phone,  
            product_name=product_name,
            product_id=product.pid, 
            supplierRating=supplierRating,   
            complaint_text=complaint_text  
        )  

        db.session.add(new_complaint)  
        db.session.commit()  
        return redirect('/agroproducts') 

    return render_template('complaint.html', product=product)


# Function to recommend products based on a query  
def recommend_products(query):  
    # Fetch products from the addagroproducts table  
    products_data = pd.DataFrame([(p.pid, p.productname, p.description) for p in Addagroproducts.query.all()], columns=['pid', 'productname', 'productdesc'])  
    
    count_vectorizer = CountVectorizer().fit_transform(products_data['productdesc'])  
    cosine_sim = cosine_similarity(count_vectorizer, count_vectorizer)  

    idx = products_data[products_data['productdesc'].str.contains(query, case=False, na=False)].index.tolist()  
    if not idx:  
        return []  

    sim_scores = list(enumerate(cosine_sim[idx[0]]))  # Get similarity scores for the first matched product  
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:3]  # Get 2 similar products  
    top_product_indices = [i[0] for i in sim_scores]  

    return products_data.iloc[top_product_indices]  

# Log user searches and update search history  
def log_search(id, search_query):  
    user_profile = User.query.filter_by(id=id).first()  
    if user_profile:  
        user_profile.search_history += f',{search_query}'  
    else:  
        user_profile = User(id=id, search_history=search_query)  
        db.session.add(user_profile)  
    db.session.commit() 

# Allow a user to search a particular product
@app.route('/search', methods=['GET'])  
def search():  
    query = request.args.get('query')  # Get the search query  
    products = Addagroproducts.query.filter(Addagroproducts.productname.ilike(f'%{query}%')).all()  # Perform a case-insensitive search  
    return render_template('search.html', products=products) 

@app.route("/bom", methods=["GET", "POST"])
def bom():
    # Fetch all products and animals from the database
    products = Product.query.all()
    animals = Animal.query.all()

    # Initialize variables for template rendering
    selected_product = None
    total_price = None
    total_seedlings = None
    hectares = None
    housing_requirement = None
    feed_requirement = None
    vaccination_schedule = None
    total_cost = None

    if request.method == "POST":
        farming_type = request.form.get("farming_type", "crops")

        if farming_type == "livestock":
            # Handle livestock calculation
            animal_type = request.form.get("animal_type")
            try:
                quantity = int(request.form.get("quantity", 0))
                if quantity <= 0:
                    raise ValueError
            except ValueError:
                flash("Quantity must be a positive integer", "danger")
                return redirect(url_for('bom'))

            animal = Animal.query.filter_by(id=animal_type).first()
            if not animal:
                flash("Animal type not found", "danger")
                return redirect(url_for('bom'))

            housing_requirement = f"{quantity} animals need {quantity * animal.housing_per_unit} {animal.housing_unit}"
            feed_requirement = quantity * animal.feed_requirement
            vaccination_schedule = animal.vaccination_schedule
            total_cost = quantity * animal.cost_per_unit

            animal_data = {
                "average_weight": animal.average_weight,
                "recommended_feed": animal.recommended_feed,
                "housing_requirement": housing_requirement,
                "feed_requirement": feed_requirement,
                "vaccination_schedule": vaccination_schedule
            }

            return render_template("bom.html",
                products=products,
                animals=animals,
                farming_type=farming_type,
                animal_type=animal_type,
                quantity=quantity,
                animal_data=animal_data,
                total_cost=total_cost,
                total_price=None,
                total_seedlings=None,
                hectares=None,
                selected_product=None)
        else:
            # Handle crop calculation
            try:
                hectares = float(request.form["hectares"])
                product_id = request.form["product"]
                selected_product = Product.query.get(product_id)

                if selected_product:
                    total_seedlings = hectares * selected_product.seedlings_per_hectare
                    total_price = total_seedlings * selected_product.price_per_seedling
            except (ValueError, TypeError):
                flash("Invalid input for hectares or product selection", "danger")
                return redirect(url_for('bom'))

            return render_template("bom.html",
                products=products,
                animals=animals,
                total_price=total_price,
                total_seedlings=total_seedlings,
                hectares=hectares,
                selected_product=selected_product,
                farming_type=farming_type)

    # Render page for GET requests with the list of products and animals
    return render_template("bom.html",
        products=products,
        animals=animals,
        selected_product=None,
        farming_type='crops')


# this handle all the file upload to a folder called uploads
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

# Handle current user profile in a view mode
@app.route('/profile')  
@login_required  
def profile():  
    user = User.query.get(current_user.id)  # Assuming you have a logged-in user
    print(f"User profile picture path: {user.profile_picture}")  
    return render_template('profile.html', user=user)

# Profile update route handles how a user can update their profile
@app.route('/update_profile_picture', methods=['POST'])  
@login_required  
def update_profile_picture():  
    profile_picture = request.files.get('profile_picture') 
    username = request.form.get('username')
    email = request.form.get('email') 
    phone = request.form.get('phone')
    location = request.form.get('location')

    if profile_picture:  
        uploads_dir = os.path.abspath("uploads")  
        os.makedirs(uploads_dir, exist_ok=True)  
        filename = secure_filename(profile_picture.filename)  
        profile_picture_path = os.path.join('uploads', filename)  # Save relative path  

        try:  
            # Open and save the image with a thumbnail  
            with Image.open(profile_picture) as img:  
                img.thumbnail((800, 800))  
                img.save(os.path.join(uploads_dir, filename))  # Save image to disk  

            # Update the user record in the database  
            current_user.profile_picture = filename  # Save just the filename to the database
            current_user.username = username
            current_user.email = email
            current_user.phone = phone
            current_user.location = location  
            db.session.commit()  # Commit the changes to the database  
            flash("Profile picture updated successfully!", "success")  
        except Exception as e:  
            flash("An error occurred while uploading the image.", "danger")  
            print(e)  

    return redirect(url_for('profile'))  # Redirect back to the profile page

# Signup page route
@app.route('/signup', methods=['POST', 'GET'])  
def signup():  
    if request.method == "POST":  
        username = request.form.get('username')  
        email = request.form.get('email')  
        phone = request.form.get('phone')  
        location = request.form.get('location')  
        password = request.form.get('password')  
        is_supplier = request.form.get('is_supplier') == 'on'  

        # Initialize profile_picture_path  
        profile_picture_path = None  

        # Handle profile picture upload  
        profile_picture = request.files.get('profile_picture')  

        if profile_picture:  
            # Validate file extension  
            if not (profile_picture.filename.lower().endswith(('.png', '.jpg', '.jpeg'))):  
                flash("Only JPG and PNG files are allowed", "warning")  
                return render_template('/signup.html')  

            # Make sure the uploads directory exists  
           
            uploads_dir = os.path.abspath("uploads")  
            print(f"Uploads directory: {uploads_dir}")  # Print directory path  
            os.makedirs(uploads_dir, exist_ok=True)  

            # Generate a secure filename  
            filename = secure_filename(profile_picture.filename)  
            profile_picture_path = os.path.join(uploads_dir, filename)  

            try:  # Open the uploaded image and resize  
                with Image.open(profile_picture) as img:  
                    img.thumbnail((800, 800))  # Resize image to a maximum of 800x800   
                    img.save(profile_picture_path)  # Save resized image   
            except Exception as e:  
                print(f"An error occurred while saving the image: {e}")  
                flash("An error occurred while uploading the image.", "danger")  
                return render_template('/signup.html')  

        # Check if the email already exists  
        user = User.query.filter_by(email=email).first()  
        if user:  
            flash("Email Already Exist", "warning")  
            return render_template('/signup.html')  

        hashed_password = generate_password_hash(password)  
        newuser = User(  
            username=username,  
            email=email,  
            password=hashed_password,  
            phone=phone,  
            location=location,  
            is_supplier=is_supplier,  
            profile_picture=filename  # Store the picture path in the User model  
        )  
        db.session.add(newuser)  
        db.session.commit()  
        flash("Signup Successful! Please Login", "success")  
        return render_template('login.html')  

    return render_template('signup.html')

# Login Page Route
@app.route('/login',methods=['POST','GET'])
def login():
    if request.method == "POST":
        email=request.form.get('email')
        password=request.form.get('password')
        user=User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_supplier'] = user.is_supplier
            flash("Login Success","primary")
            return redirect(url_for('index'))
        else:
            flash("invalid credentials","warning")
            return render_template('login.html')    

    return render_template('login.html')

# Logout page Route
@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        new_post = ForumPost(title=title, content=content, author_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash('Your post has been added!', 'success')
        return redirect(url_for('forum'))
    
    posts = ForumPost.query.order_by(ForumPost.timestamp.desc()).all()
    return render_template('forum.html', posts=posts)


@app.route('/add_comment/<int:post_id>', methods=['POST'])  
@login_required  
def add_comment(post_id):  
    post = ForumPost.query.get_or_404(post_id) # Get the post, or return a 404 error if not found  
    content = request.form.get('comment_content') # Get comment content from the form  
    if content:  
        new_comment = Comment(content=content, author_id=current_user.id, post_id=post.id)  
        db.session.add(new_comment)  
        db.session.commit()  
        flash('Your comment has been added!', 'success')  
    return redirect(url_for('forum'))  # Redirect back to the forum  

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Logout SuccessFul","warning")
    return redirect(url_for('login'))



app.run(debug=True)    
