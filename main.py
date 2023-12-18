from flask import Flask, render_template, request, flash, redirect, send_from_directory, url_for, abort
from werkzeug.utils import secure_filename

import os
import sqlite3

app = Flask(__name__)


app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

DATABASE = 'tours.db'
app.secret_key = 'your_secret_key'


def create_table():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY,
                photo TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                price TEXT NOT NULL)
             """)

    cursor.execute(
        """CREATE TABLE IF NOT EXISTS saved_tours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tour_id INTEGER,
                name TEXT,
                description TEXT,
                price INTEGER,
                FOREIGN KEY (tour_id) REFERENCES posts (ID))
             """)

    conn.commit()
    conn.close()


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

create_table()




@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']




@app.route("/")
def index():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts")
    data = cursor.fetchall()
    conn.close()
    return render_template("index.html", data=data)



@app.route("/<int:tour_id>")
def tours(tour_id):
    tour = get_post(tour_id)
    return render_template("tours.html", tour=tour)



@app.route("/add_tours/", methods=["GET", "POST"])
def add_tours():
    if request.method == "POST":
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)

        photo = request.files['photo']

        if photo.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            name = request.form['name']
            description = request.form['description']
            price = request.form['price']

            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO posts (photo, name, description, price) VALUES (?, ?, ?, ?)",
                           (filename, name, description, price))
            conn.commit()
            conn.close()

            return render_template("index.html")

    else:
        return render_template("edit.html")


@app.route("/save_tour/<int:tour_id>", methods=["POST"])
def save_tour(tour_id):
    try:
        with app.app_context():
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                tour = cursor.execute("SELECT * FROM posts WHERE ID = ?", (tour_id,)).fetchone()
                if tour is None:
                    abort(404)
                cursor.execute("INSERT INTO saved_tours (tour_id, name, description, price) VALUES (?, ?, ?, ?)",
                               (tour_id, tour[2], tour[3], tour[4]))
                conn.commit()

        flash('Тур збережено!')
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        flash('Помилка при збереженні туру. Спробуйте ще раз або зверніться до адміністратора.', 'error')

    return redirect(url_for('index'))



@app.route("/forbidden_tours/")
def forbidden_tours():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM saved_tours")
    tours_saved = cursor.fetchall()
    conn.close()

    return render_template("base.html", tours_saved=tours_saved)




def get_post(tour_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            tour = conn.execute("SELECT * FROM posts WHERE ID = ?", (tour_id,)).fetchone()

        if tour is None:
            abort(404)
        return tour

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None


app.run(port=55668, debug=True)





