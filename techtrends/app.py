import sqlite3
import logging
from datetime import datetime
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort


# Initialize the counter for database connections
db_connection_count = 0

# Initialize the logger with the desired level
logging.basicConfig(level=logging.DEBUG)

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connection_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_connection_count+=1
    return connection

# Function to get the total number of posts in the database
def get_post_count():
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()
    connection.close()
    return post_count[0]

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logging.info('%s, Non-existing article accessed, 404 returned.', datetime.now())
        return render_template('404.html'), 404
    else:
        logging.info('%s, Article "%s" retrieved!', datetime.now(), post['title'])
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logging.info('%s, About Us page retrieved.', datetime.now())
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            logging.info('%s, New article "%s" created!', datetime.now(), title)
            return redirect(url_for('index'))
    return render_template('create.html')

@app.route('/healthz', methods=['GET'])
def healthcheck():
    try:
        conn = get_db_connection()
        conn.execute('SELECT 1 FROM posts LIMIT 1')
        return jsonify(result='OK - healthy'), 200
    except sqlite3.Error as e:
        # If there was an error in the try block above, we can't reach the database
        return jsonify(result='ERROR - unhealthy', error=str(e)), 500


@app.route('/metrics', methods=['GET'])
def metrics():
    return jsonify(db_connection_count=db_connection_count, post_count=get_post_count()), 200


# start the application on port 3111
if __name__ == "__main__":
   app.run(host='0.0.0.0', port='3111')
