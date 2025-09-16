from flask import Flask, render_template, request  
from flask_sqlalchemy import SQLAlchemy  
from flask_caching import Cache  
import pandas as pd  
from sklearn.feature_extraction.text import CountVectorizer  
from sklearn.metrics.pairwise import cosine_similarity  

app = Flask(__name__)  

# Configuration  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///your_database.db'  # Change to your actual database URI  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  
app.config['CACHE_TYPE'] = 'SimpleCache'  

db = SQLAlchemy(app)  
cache = Cache(app)  

# Database Models  
class AgroProduct(db.Model):  
    __tablename__ = 'addagroproducts'  
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)  
    description = db.Column(db.String(250), nullable=False)  

class UserProfile(db.Model):  
    id = db.Column(db.Integer, primary_key=True)  
    user_id = db.Column(db.Integer, nullable=False, unique=True)  
    search_history = db.Column(db.String(500))  

# Create the database tables  
with app.app_context():  
    db.create_all()  

# Function to recommend products based on a query  
def recommend_products(query):  
    # Fetch products from the addagroproducts table  
    products_data = pd.DataFrame([(p.id, p.name, p.description) for p in AgroProduct.query.all()], columns=['id', 'name', 'description'])  
    
    count_vectorizer = CountVectorizer().fit_transform(products_data['description'])  
    cosine_sim = cosine_similarity(count_vectorizer, count_vectorizer)  

    idx = products_data[products_data['description'].str.contains(query, case=False, na=False)].index.tolist()  
    if not idx:  
        return []  

    sim_scores = list(enumerate(cosine_sim[idx[0]]))  # Get similarity scores for the first matched product  
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:3]  # Get 2 similar products  
    top_product_indices = [i[0] for i in sim_scores]  

    return products_data.iloc[top_product_indices]  

# Log user searches and update search history  
def log_search(user_id, search_query):  
    user_profile = UserProfile.query.filter_by(user_id=user_id).first()  
    if user_profile:  
        user_profile.search_history += f',{search_query}'  
    else:  
        user_profile = UserProfile(user_id=user_id, search_history=search_query)  
        db.session.add(user_profile)  
    db.session.commit()  

# Search Route with Caching  
@app.route('/search', methods=['GET'])  
@cache.cached(timeout=50, query_string=True)  
def search():  
    query = request.args.get('q')  
    user_id = request.args.get('user_id', 1)  # For demonstration purposes  
    if query:  
        log_search(user_id, query)  
        related_products = recommend_products(query)  
        return render_template('search_results.html', products=related_products, query=query)  
    return render_template('search_results.html', products=[], query=query)  

# Basic Search Results Template  
@app.route('/results')  
def results():  
    return "Results Page (Enter a proper search request to get results!)"  

if __name__ == '__main__':  
    app.run(debug=True)