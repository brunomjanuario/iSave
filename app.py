from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

def apology(message="ERROR", code=400):
    return render_template("apology.html", top=code, message=message)

@app.route("/", methods=["GET", "POST"])
def index():

    if not session:
        return redirect("/login")

    if session.get("user_id") is None:
        return redirect("/login")

    id = session.get("user_id")

    if request.method == "POST":

        if not request.form.get("target"):
            return apology("Specify a target!",404)

        target = request.form.get("target")

        db.execute("UPDATE users SET target = ? WHERE id=?", target, id)


    target = db.execute("SELECT target FROM users WHERE id=?", id)[0]["target"]

    months1 = []
    months2 = []
    months3 = []

    months1.append(get_month_for_id(id, "01", "January"))
    months2.append(get_month_for_id(id, "02", "February"))
    months3.append(get_month_for_id(id, "03", "March"))
    months1.append(get_month_for_id(id, "04", "April"))
    months2.append(get_month_for_id(id, "05", "May"))
    months3.append(get_month_for_id(id, "06", "June"))
    months1.append(get_month_for_id(id, "07", "July"))
    months2.append(get_month_for_id(id, "08", "August"))
    months3.append(get_month_for_id(id, "09", "September"))
    months1.append(get_month_for_id(id, "10", "October"))
    months2.append(get_month_for_id(id, "11", "November"))
    months3.append(get_month_for_id(id, "12", "December"))

    return render_template("index.html", months1=months1, months2=months2, months3=months3, target=target)


def get_month_for_id(id, month, name):

    month_date = "2022-" + str(month) + "-%"
    amount = db.execute("SELECT IFNULL(SUM(amount), 0) as total FROM history WHERE user_id=? AND date LIKE ?", id, month_date)[0]["total"]
    url = "/month?m=" + str(month)

    return {
        "name": name,
        "url": url,
        "amount": amount
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Submit a username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Submit a password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("That username already exists", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        if not request.form.get("username"):
            return apology("Submit a username", 400)

        if not request.form.get("password"):
            return apology("Submit a passsword", 400)

        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Password and confirmation are different", 400)

        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        if len(rows) == 0:
            username = request.form.get("username")
            password = generate_password_hash(request.form.get("password"))
            db.execute(
                "INSERT INTO users (username, password) VALUES (?,?)", username, password)

            login = db.execute(
                "SELECT * FROM users WHERE username = ?", request.form.get("username"))

            # Remember which user has logged in
            session["user_id"] = login[0]["id"]

            return redirect("/login")

        return apology("Can't register", 400)

    else:
        return render_template("register.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/add", methods=["GET", "POST"])
def add():

    if not session:
        return redirect("/login")

    if session.get("user_id") is None:
        return redirect("/login")

    if request.method == "POST":

        if not request.form.get("amount"):
            return apology("Submit a amount", 400)

        if not request.form.get("date"):
            return apology("Submit a date", 400)

        if not request.form.get("type"):
            return apology("Submit a type", 400)

        amount = float(request.form.get("amount"))

        if amount <= 0:
            return apology("Submit a amount greater than 0", 400)


        date = request.form.get("date")
        type = request.form.get("type")
        id = session.get("user_id")

        if type == 'earnings':
            db.execute("INSERT INTO history (user_id, amount, type, date) VALUES (?,?,?,?)", id, amount, type, date)
        else:
            db.execute("INSERT INTO history (user_id, amount, type, date) VALUES (?,?,?,?)", id, -amount, type, date)

        return redirect("/")

    return render_template("add.html")


@app.route("/history")
def history():

    if not session:
        return redirect("/login")

    if session.get("user_id") is None:
        return redirect("/login")

    id = session.get("user_id")

    history = db.execute("SELECT * FROM history WHERE user_id = ?", id)

    return render_template("history.html", history = history)


@app.route("/month")
def month():

    if not session:
        return redirect("/login")

    if session.get("user_id") is None:
        return redirect("/login")

    id = session.get("user_id")
    month = request.args["m"]

    data = []

    data.append(get_amount_type_for_id_and_month(id, "earnings", month))
    data.append(get_amount_type_for_id_and_month(id, "bills", month))
    data.append(get_amount_type_for_id_and_month(id, "car", month))
    data.append(get_amount_type_for_id_and_month(id, "food", month))
    data.append(get_amount_type_for_id_and_month(id, "others", month))

    return render_template("month.html", month=data)


def get_amount_type_for_id_and_month(id, type, month):

    month_date = "2022-" + month + "-%"
    amount = db.execute("SELECT IFNULL(SUM(amount), 0) as total FROM history WHERE user_id=? AND date LIKE ? AND type LIKE ?", id, month_date, type)[0]["total"]

    return {
        "type": type.upper(),
        "amount": amount
    }
