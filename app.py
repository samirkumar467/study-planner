from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DB ----------
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS study (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subject TEXT,
        topic TEXT,
        days INTEGER,
        completed INTEGER DEFAULT 0,
        user TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------- AUTH ----------
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)",(u,p))
        conn.commit()
        conn.close()

        return redirect('/index')
    return render_template("signup.html")

@app.route('/index', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        u = request.form['username']
        p = request.form['password']

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=? AND password=?",(u,p))
        data = cur.fetchone()
        conn.close()

        if data:
            session['user'] = u
            return redirect('/')
        else:
            return "Invalid Login"
    return render_template("index.html")

@app.route('/logout')
def logout():
    session.pop('user',None)
    return redirect('/index')

# ---------- HOME ----------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/index')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM study WHERE user=?",(session['user'],))
    data = cur.fetchall()

    cur.execute("SELECT COUNT(*) FROM study WHERE user=?",(session['user'],))
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM study WHERE user=? AND completed=1",(session['user'],))
    done = cur.fetchone()[0]

    conn.close()

    progress = int((done/total)*100) if total>0 else 0
    remaining = total - done

    return render_template("dashboard.html",
                           data=data,
                           progress=progress,
                           done=done,
                           remaining=remaining,
                           user=session['user'])

# ---------- ADD ----------
@app.route('/add', methods=['POST'])
def add():
    subject = request.form['subject']
    topic = request.form['topic']
    days = request.form['days']

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO study (subject,topic,days,user) VALUES (?,?,?,?)",
                (subject,topic,days,session['user']))
    conn.commit()
    conn.close()

    return redirect('/')

# ---------- COMPLETE ----------
@app.route('/complete/<int:id>')
def complete(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("UPDATE study SET completed=1 WHERE id=?",(id,))
    conn.commit()
    conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)