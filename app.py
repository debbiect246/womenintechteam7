import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
if os.path.exists("env.py"):
    import env


app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

mongo = PyMongo(app)


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # check if username already exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        if (request.form.get("password") != request.form.get("password1")):
            flash("Passwords don't match")
            return redirect(url_for("register"))
        else:
            register = {
                "username": request.form.get("username").lower(),
                "password": generate_password_hash(
                    request.form.get("password"))
            }
            mongo.db.users.insert_one(register)

        # put the new user into 'session' cookie
        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("home"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # check if username exists in db
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            # ensure hashed password matches user input
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}!".format(
                    request.form.get("username")))
                return redirect(url_for("home"))
            else:
                # invalid password match
                flash("Incorrect Username and/or Password")
                return redirect(url_for("login"))

        else:
            # username doesn't exist
            flash("Incorrect Username and/or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    # remove user from session cookie
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/meetups")
def meetups():
    meetups = list(mongo.db.meetups.find())
    return render_template(
        "meetups.html", meetups=meetups)


@app.route("/add_event/", methods=["GET", "POST"])
def add_event():
    if "user" in session:
        if request.method == "POST":
            event = {
                "name": request.form.get("name").lower(),
                "description": request.form.get("description"),
                "meetup_type": request.form.get("type"),
                "city": request.form.getlist("city"),
                "address": request.form.getlist("address"),
                "date": request.form.getlist("date"),
                "time": request.form.getlist("time"),
                "topic": request.form.getlist("topic"),
                "added_by": session["user"]
                }
            mongo.db.meetuos.insert_one(event)

            flash("Your Event Was Successfully Created and Added to the Calendar!")
            return render_template("home.html")

        types = list(mongo.db.meetup_types.find().sort("meetup_type", 1))
        topics = list(mongo.db.topics.find().sort("topic", 1))
        return render_template(
            "add_event.html", types=types, topics=topics)
    return render_template("unauthorised_error.html")



@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        flash("Thanks {}, we have received your message!".format(
            request.form.get("name")))
    return render_template("contact.html", page_title="Contact")


if __name__ == "__main__":
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=True)
