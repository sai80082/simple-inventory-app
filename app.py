from flask import Flask, jsonify, redirect, render_template, request, session
from flask_session import Session
import sqlite3
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
connection = sqlite3.connect("data.db", check_same_thread=False)
connection.row_factory = sqlite3.Row
db = connection.cursor()

app.config['UPLOAD_FOLDER'] = "/trial"


def dbselect(query, data=""):
    db.execute(query, data)
    result = db.fetchall()
    return result


@app.route("/")
def index():
    if session.get("user_id") is None:
        return redirect("/login")
    else:
        return render_template("home.html")


# this function is for logining the registered user into the app
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # storing the input values to variables
        username = request.form.get("username")
        password = request.form.get("password")
        result = dbselect("SELECT * FROM users WHERE username = ?;",  # checking if the data is in the database or not
                          [username])
        try:  # redirecting if the data is not found
            if len(result) == 0 or not (bcrypt.check_password_hash((result[0]["hash"]), password)):
                return render_template(
                    "login.html",
                    message="Incorrect/invalid userid or password.Try again!")
        except:
            return render_template(
                "login.html",
                message="Incorrect/invalid userid or password.Try again!")
        # if the data is valid then user will be redirected to the homepage
        session["user_id"] = result[0]["id"]
        return redirect("/")
    elif session.get("user_id"):
        return redirect("/")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        verifypassword = request.form.get("cpassword")
        result = dbselect("SELECT * FROM users WHERE username = ?;",
                          [username])
        if username == "" or password == "":
            return render_template("register.html",
                                   message="Invalid username or password")
        if len(result) == 1:
            return render_template(
                "register.html", message="Username already exists,Try again!")
        if password != verifypassword:
            return render_template(
                "register.html", message="password doesn't match please try again!")
        hashed = bcrypt.generate_password_hash(password)
        db.execute("INSERT INTO users (username,hash) VALUES(?,?)",
                   [request.form.get("username"), hashed])
        connection.commit()
        result = dbselect("SELECT * FROM users WHERE username = ?;",
                          [request.form.get("username")])
        session["user_id"] = result[0]["id"]
        os.mkdir("userdata/"+str(session["user_id"]) + "/")
        return redirect("/")
    return render_template("register.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/login")


@app.route("/uservalid", methods=["GET", "POST"])
def uservalid():
    result = dbselect("SELECT * FROM users WHERE username = ?;",
                      [request.args.get("q")])
    if len(result) > 0 or len(request.args.get("q")) <= 2:
        return {"value": 1}
    else:
        return {"value": 0}


@app.route("/search", methods=["GET", "POST"])
def search():
    query = request.args.get("q")
    result = dbselect(
        "SELECT itemname,image,units FROM menu WHERE itemname LIKE ? AND userid = ?", ["%"+query+"%", session["user_id"]])

    data = {}
    for i in result:
        temp = list(i)
        data[temp[0]] = {"image": temp[1], "units": temp[2]}
    return jsonify(data)


@app.route("/delete/", methods=["GET", "POST"])
def delete():
    value = request.args.get("delete")
    result = dbselect(
        "SELECT image FROM menu WHERE itemname == ? AND userid = ?", [value, session["user_id"]])
    file = list(result[0])[0]
    os.remove("static/userdata/"+file)
    db.execute("DELETE FROM menu WHERE itemname = ? AND userid = ?",
               [value, session["user_id"]])
    connection.commit()

    return redirect("/")


@app.route('/add', methods=["GET", "POST"])
def upload():
    if request.method == 'POST':
        app.config['UPLOAD_FOLDER'] = "static/userdata/" + \
            str(session["user_id"])+"/"
        name = request.form.get("filename")
        numitems = request.form.get("numitems")
        f = request.files['file']
        extension = os.path.splitext(f.filename)[-1]
        f.save(os.path.join(app.config['UPLOAD_FOLDER'], name+extension))
        db.execute("INSERT INTO menu (itemname,image,units,userid) VALUES (?,?,?,?)", [
                   name, str(session["user_id"])+"/"+name+extension, numitems, session["user_id"]])
        connection.commit()
        return redirect("/")
    else:
        return render_template("add.html")


if __name__ == '__main__':
    app.run('0.0.0.0', 80)
