from flask import Flask, render_template, request, jsonify, session, redirect
import pandas as pd
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from recommend import get_recommendations

app = Flask(__name__)
app.secret_key = 'super_secret_key'   # 🔐 REQUIRED

 
# Load data
books_df = pd.read_csv('data/Books.csv', encoding='latin-1')

# Clean ISBN
books_df['ISBN'] = books_df['ISBN'].astype(str).str.strip()

# ---------------------- HOME ----------------------
@app.route('/')
def home():
    return render_template('home.html') 
# ---------------------- INDEX ----------------------

@app.route('/index')
def index():
    books = books_df.to_dict('records')
    return render_template('index.html', books=books)


# ---------------------- SEARCH ----------------------
@app.route('/search')
def search():
    query = request.args.get('query', '').lower()
    results = books_df[
        books_df['Book-Title'].str.lower().str.contains(query, na=False) |
        books_df['Book-Author'].str.lower().str.contains(query, na=False)
    ].to_dict('records')
    return render_template('index.html', books=results, query=query)


# ---------------------- BOOK DETAILS ----------------------
@app.route('/book/<isbn>')
def book_details(isbn):
    # ✅ Clean incoming ISBN
    isbn = str(isbn).strip()

    # ✅ Ensure dataset ISBNs are also clean
    books_df['ISBN'] = books_df['ISBN'].astype(str).str.strip()

    # 🔍 Try exact match
    book_row = books_df[books_df['ISBN'] == isbn]

    # 🔁 Fallback: try partial match (handles weird formatting issues)
    if book_row.empty:
        book_row = books_df[books_df['ISBN'].str.contains(isbn, na=False)]

    if not book_row.empty:
        book = book_row.iloc[0].to_dict()
        return render_template('details.html', book=book)

    return "Book not found", 404

# ---------------------- RECOMMEND ----------------------
@app.route('/recommend')
def recommend_api():
    title = request.args.get('title')
    try:
        return jsonify(get_recommendations(title))
    except:
        return jsonify([])


# ---------------------- LOGIN ----------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect('/')
        else:
            return "Invalid credentials"
    return render_template('login.html')


# ---------------------- SIGNUP ----------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        conn = sqlite3.connect('books.db')
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            return "User already exists"

        conn.close()
        return redirect('/')

    return render_template('signup.html')


# ---------------------- LOGOUT ----------------------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/')


# ---------------------- UPDATE STATUS ----------------------
@app.route('/update_status', methods=['POST'])
def update_status():
    if 'user_id' not in session:
        return "Login required", 401

    user_id = session['user_id']
    isbn = request.form['isbn']
    status = request.form['status']

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    # Delete old entry (simpler than conflict handling)
    cursor.execute("DELETE FROM user_books WHERE user_id=? AND isbn=?", (user_id, isbn))

    cursor.execute(
        "INSERT INTO user_books (user_id, isbn, status) VALUES (?, ?, ?)",
        (user_id, isbn, status)
    )

    conn.commit()
    conn.close()

    return "Saved"

# ----------------------  FILTER ----------------------
@app.route('/filter', methods=['GET', 'POST'])
def filter_books():
    import sqlite3
    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'books.db')

    conn = sqlite3.connect(db_path)

    # ✅ THIS LINE FIXES EVERYTHING
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    query = "SELECT * FROM book_data WHERE 1=1"
    params = []

    if request.method == 'POST':
        min_rating = request.form.get('min_rating')
        year = request.form.get('year')
        author = request.form.get('author')
        publisher = request.form.get('publisher')
        country = request.form.get('country')
        sort_by = request.form.get('sort_by')

        if min_rating:
            query += " AND avg_rating >= ?"
            params.append(float(min_rating))

        if year:
            query += " AND `Year-Of-Publication` = ?"
            params.append(year)

        if author:
            query += " AND `Book-Author` LIKE ?"
            params.append(f"%{author}%")

        if publisher:
            query += " AND Publisher LIKE ?"
            params.append(f"%{publisher}%")

        if country:
            query += " AND Country LIKE ?"
            params.append(f"%{country}%")

        # Sorting
        if sort_by == 'rating':
            query += " ORDER BY avg_rating DESC"
        elif sort_by == 'reads':
            query += " ORDER BY num_reads DESC"

    cursor.execute(query, params)
    books = cursor.fetchall()

    conn.close()

    return render_template('filter.html', books=books)

# ---------------------- READ BOOKS ----------------------
@app.route('/read')
def reads():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    cursor.execute("SELECT isbn FROM user_books WHERE user_id=? AND status='read'", (session['user_id'],))
    isbns = [row[0] for row in cursor.fetchall()]
    conn.close()

    books = books_df[books_df['ISBN'].isin(isbns)].to_dict('records')
    return render_template('read.html', books=books)


# ---------------------- READING BOOKS ----------------------
@app.route('/reading')
def reading():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('books.db')
    cursor = conn.cursor()

    cursor.execute("SELECT isbn FROM user_books WHERE user_id=? AND status='reading'", (session['user_id'],))
    isbns = [row[0] for row in cursor.fetchall()]
    conn.close()

    books = books_df[books_df['ISBN'].isin(isbns)].to_dict('records')
    return render_template('reading.html', books=books)


# ---------------------- ABOUT ----------------------
@app.route('/about')
def about():
    return render_template('about.html')


# ---------------------- RUN ----------------------
if __name__ == '__main__':
    app.run(debug=True)