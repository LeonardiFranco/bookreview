import os
import csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Check for environment variable
if not os.getenv("DATABASE_URL"):
	DB_URL = "postgresql://postgres:c90d@localhost:5432/project1"
	#raise RuntimeError("DATABASE_URL is not set")
else:
	DB_URL = os.getenv("DATABASE_URL")

# Set up database
engine = create_engine(DB_URL)
db = scoped_session(sessionmaker(bind=engine))

with open('books.csv') as csvfile:
	reader = csv.DictReader(csvfile)
	for row in reader:
		db.execute('INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)',
		 {'isbn':row['isbn'], 'title':row['title'], 'author':row['author'], 'year':row['year']})
	db.commit()