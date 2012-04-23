from flask import Flask, flash, session, escape, make_response, render_template, request, g, redirect, url_for
from functools import wraps
from contextlib import closing
import MySQLdb
import MySQLdb.cursors
app = Flask(__name__)

@app.before_request
def before_request():
    g.db = MySQLdb.connect(host='localhost',
                    port=3306,
                     user='pstoica_4400_2',
                     passwd='lolwut',
                     db='pstoica_4400_2',
                     cursorclass=MySQLdb.cursors.DictCursor)

@app.teardown_request
def teardown_request(exception):
    g.db.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user'):
            cursor = g.db.cursor()
            cursor.execute("SELECT `Name` FROM `User` WHERE Email=%s",
                           session.get('user'))
            g.user = cursor.fetchone()
            return f(*args, **kwargs)
        else:
            flash('Please log in first.', 'error')
            next_url = request.url
            login_url = '%s?next=%s' % (url_for('login'), next_url)
            return redirect(login_url)
    return decorated_function

@app.route('/')
@login_required
def index():
    cursor = g.db.cursor()
    cursor.execute("""SELECT CorkBoard.ID, CorkBoard.Title, User.Name, CorkBoard.Private, MAX(DateAndTime) AS LastUpdate
                FROM `CBWithPrivate` AS CorkBoard
                INNER JOIN `User`
                USING (Email)
                INNER JOIN `PushPin`
                ON CorkBoard.ID = PushPin.CorkBoard
                GROUP BY CorkBoard.Title, CorkBoard.Email
                ORDER BY LastUpdate DESC
                LIMIT 5""")
    recent_updates = cursor.fetchall()
    cursor.execute("""SELECT CorkBoard.Title, COUNT(*) as PushPins, CorkBoard.Private
                FROM `CBWithPrivate` as `CorkBoard`
                INNER JOIN `PushPin`
                ON CorkBoard.ID = PushPin.CorkBoard
                WHERE CorkBoard.Email=%s
                GROUP BY CorkBoard.Title
                ORDER BY CorkBoard.Title ASC""", (session.get('user')))
    my_corkboards = cursor.fetchall()
    return render_template('index.html',
                           recent_updates = recent_updates,
                           my_corkboards = my_corkboards)
    

@app.route('/login', methods=['POST', 'GET'])
def login():
    cursor = g.db.cursor()
    if request.method == 'POST':
        cursor.execute("""SELECT *
                        FROM `User`
                        WHERE Email=%s
                        AND PIN=%s""",
                        (request.form['username'],
                        request.form['password']))
        result = cursor.fetchone()
        if result is None:
            flash("Invalid username or password.", "error")
        else:
            session['user'] = request.form['username']
            flash("You've successfully logged in!", "success")
            return redirect(url_for('index'))
    return render_template('login.html')
    
@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    flash("You've been logged out!", "success")
    return redirect(url_for('login'))

@app.route('/corkboard/add', methods=['POST', 'GET'])
@login_required
def add_corkboard():
    cursor = g.db.cursor()
    cursor.execute("""SELECT *
                    FROM Category""")
    categories = cursor.fetchall()
    if request.method == 'POST':
        match = len([category for category in categories if category['Name'] == request.form['category']])
        if request.form['title'] is not None:
            cursor.execute("""INSERT INTO CorkBoard
                            (`Title`, `Email`, `Category`)
                            VALUES (%s, %s, %s)""",
                            (request.form['title'],
                            session.get('user'),
                            request.form['category']))
            corkboard_id = cursor.lastrowid
            if len(request.form['password']) > 0:
                cursor.execute("""INSERT INTO PrivateCB
                                (`ID`, `Password`)
                                VALUES (%s, %s)""",
                                (corkboard_id,
                                 request.form['password']))
            else:
                cursor.execute("""INSERT INTO PublicCB
                                (`ID`)
                                VALUES (%s)""",
                                (corkboard_id))
            g.db.commit()
            flash("CorkBoard has successfully been added!", "success")
            return redirect(url_for('index'))
    return render_template('add_corkboard.html', categories = categories)
    

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404

app.url_map.strict_slashes = False
app.debug = True
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'


if __name__ == '__main__':
    app.run()