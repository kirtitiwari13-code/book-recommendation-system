import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def get_recommendations(book_title):
    try:
        books = pd.read_csv('data/Books.csv').head(10000)
        books['features'] = books['Book-Author'].fillna('') + " " + books['Publisher'].fillna('')
        
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(books['features'])
        
        if book_title not in books['Book-Title'].values:
            return []
            
        idx = books[books['Book-Title'] == book_title].index[0]
        cosine_sim = cosine_similarity(tfidf_matrix[idx], tfidf_matrix).flatten()
        
        # Get top 10 indices
        similar_indices = cosine_sim.argsort()[-11:-1][::-1]
        
        # Select the columns we need
        recommended_books = books.iloc[similar_indices][['Book-Title', 'Image-URL-M', 'ISBN']]
        
        # Convert to a list of dictionaries
        return recommended_books.to_dict('records')
        
    except Exception as e:
        print(f"Error: {e}")
        return []