import os
import pandas as pd
import sqlite3

# ---------------------- PATH SETUP ----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# ---------------------- LOAD DATA ----------------------
print("Loading datasets...")

books = pd.read_csv(os.path.join(DATA_DIR, 'Books.csv'), encoding='latin-1')
users_df = pd.read_csv(os.path.join(DATA_DIR, 'Users.csv'), encoding='latin-1')
ratings = pd.read_csv(os.path.join(DATA_DIR, 'Ratings.csv'), encoding='latin-1')

# ---------------------- CONNECT DB ----------------------
db_path = os.path.join(BASE_DIR, 'books.db')
conn = sqlite3.connect(db_path)

conn.execute("PRAGMA foreign_keys = 1")
cursor = conn.cursor()

# ---------------------- USERS TABLE ----------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# ---------------------- USER BOOKS TABLE ----------------------
cursor.execute('''
CREATE TABLE IF NOT EXISTS user_books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    isbn TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# =========================================================
# 📊 BOOK DATA PROCESSING
# =========================================================

print("Processing dataset...")

# Merge datasets
df = pd.merge(ratings, books, on='ISBN')
df = pd.merge(df, users_df, on='User-ID')

# Drop unnecessary column
df = df.drop('Age', axis=1)

# ---------------------- CLEAN DATA ----------------------

# Fix Year column
df['Year-Of-Publication'] = pd.to_numeric(df['Year-Of-Publication'], errors='coerce')
df = df.dropna(subset=['Year-Of-Publication'])
df['Year-Of-Publication'] = df['Year-Of-Publication'].astype(int)

# Remove invalid ratings (0 means no rating)
df = df[df['Book-Rating'] > 0]
df['ISBN'] = df['ISBN'].astype(str).str.strip()
# Extract country
df['Country'] = df['Location'].apply(lambda x: x.split(',')[-1].strip())

# ---------------------- FEATURE ENGINEERING ----------------------

# Average rating
avg_rating = df.groupby('Book-Title')['Book-Rating'].mean().reset_index()
avg_rating.rename(columns={'Book-Rating': 'avg_rating'}, inplace=True)

# Number of reads
num_reads = df.groupby('Book-Title')['Book-Rating'].count().reset_index()
num_reads.rename(columns={'Book-Rating': 'num_reads'}, inplace=True)

# Merge features
book_data = df.merge(avg_rating, on='Book-Title')
book_data = book_data.merge(num_reads, on='Book-Title')

# Keep only popular books (performance optimization)
popular_books = num_reads[num_reads['num_reads'] >= 50]
book_data = book_data[book_data['Book-Title'].isin(popular_books['Book-Title'])]

# Remove duplicates
book_data.drop_duplicates('Book-Title', inplace=True)

# Select required columns only
book_data = book_data[
    ['ISBN', 'Book-Title', 'Book-Author', 'Year-Of-Publication',
     'Publisher', 'Country', 'avg_rating', 'num_reads']
]
# ---------------------- SAVE TO DATABASE ----------------------

book_data.to_sql('book_data', conn, if_exists='replace', index=False)

print("book_data table created ✅")

# ---------------------- FINALIZE ----------------------

conn.commit()
conn.close()

print("Database ready ✅")