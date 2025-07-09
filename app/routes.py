from app import app, login_manager
from app.db import get_db
from flask import render_template, redirect, request, flash, abort
from flask_login import logout_user, UserMixin, login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from requests import get
import math


# Defines user
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

    def get_id(self):
        return str(self.id)


@login_manager.user_loader
def load_user(user_id):
    db = get_db()
    user_details = db.execute("SELECT * FROM User WHERE UserID = ?", (user_id,)).fetchone()
    if user_details:
        return User(user_details["UserID"], user_details["username"])
    return None


@app.route('/')
def index():
    try:
        # Get BOM data
        r = get('http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94576.json')
        bom_data = r.json()['observations']['data'][0]
        outside_temp = bom_data["air_temp"]
        outside_AppTemp = bom_data['apparent_t']
        outside_humidity = bom_data['rel_hum']

        db = get_db()
        sql_tg = db.execute("SELECT Temp_Threshold FROM Temps").fetchone()
        temp_var = db.execute("SELECT Inside_Temp FROM Temps").fetchone()['Inside_Temp']
        hum_var = db.execute("SELECT Inside_Humidity FROM Temps").fetchone()
        apparent_temp_var = db.execute("SELECT Inside_Apparent_Temp FROM Temps").fetchone()

        db.execute(
            "INSERT INTO Temps (Outside_Temp, Outside_Humidity, Outside_Apparent_Temp) VALUES (?, ?, ?)",
            (outside_temp, outside_humidity, outside_AppTemp)
        )
        db.commit()

        # Temperature thresholds
        safe_temp, warning_temp, critical_temp = 25, 30, 35
        temp_status = ""
        if temp_var > critical_temp:
            temp_status = "Critical"
        elif temp_var > warning_temp:
            temp_status = "Warning"
        elif temp_var < safe_temp:
            temp_status = "Safe"

        return render_template('index.html',
                               outside_temp=outside_temp,
                               outside_AppTemp=outside_AppTemp,
                               outside_humidity=outside_humidity,
                               apparent_temp_var=apparent_temp_var,
                               temp_var=temp_var,
                               hum_var=hum_var,
                               sql_tg=sql_tg,
                               temp_status=temp_status)
    except Exception as e:
        print(f"Error loading home page: {e}")
        abort(500)


@app.route('/inside_temps', methods=['POST'])
def get_data():
    try:
        Inside_Temp = request.json['Temp']
        Inside_Humidity = request.json['Humidity']
        p = ((int(Inside_Humidity) / 100) * 6.105 *
             math.exp((17.27 * int(Inside_Temp)) /
                      (237.7 + int(Inside_Temp))))
        inside_AppTemp = int(Inside_Temp) + 0.33 * p - 4
        Inside_Apparent_Temperature = round(inside_AppTemp, 1)

        db = get_db()
        db.execute("INSERT INTO Temps (Inside_Temp, Inside_Humidity, Inside_Apparent_Temp) VALUES (?, ?, ?)",
                   (Inside_Temp, Inside_Humidity, Inside_Apparent_Temperature))
        db.commit()
        db.close()
        return "LOG: Uploaded to Database"
    except Exception as e:
        print(f"Error in inside_temps: {e}")
        return "LOG: Error submitting data"


@app.route('/monitordisplay')
def monitorDisplay():
    try:
        r = get('http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94576.json')
        bom_data = r.json()['observations']['data'][0]
        outside_temp = bom_data["air_temp"]
        outside_apparent_temp = bom_data['apparent_t']
        outside_humidity = bom_data['rel_hum']

        db = get_db()
        threshold = db.execute("SELECT Temp_Threshold FROM Temps").fetchone()
        current_temp_monitor = db.execute("SELECT Inside_Temp FROM Temps").fetchone()['Inside_Temp']
        hum_var_monitor = db.execute("SELECT Inside_Humidity FROM Temps").fetchone()
        apparent_temp_monitor_var = db.execute("SELECT Inside_Apparent_Temp FROM Temps").fetchone()

        # Threshold logic
        safe_temp, warning_temp, critical_temp = 25, 30, 35
        temp_status_monitor = ""
        if current_temp_monitor > critical_temp:
            temp_status_monitor = "Critical"
        elif current_temp_monitor > warning_temp:
            temp_status_monitor = "Warning"
        elif current_temp_monitor < safe_temp:
            temp_status_monitor = "Safe"

        return render_template('index-monitor-screen.html',
                               outside_temp=outside_temp,
                               outside_apparent_temp=outside_apparent_temp,
                               outside_humidity=outside_humidity,
                               temp_status_monitor=temp_status_monitor,
                               apparent_temp_monitor_var=apparent_temp_monitor_var,
                               hum_var_monitor=hum_var_monitor,
                               threshold_get_monitor_var=threshold)
    except Exception as e:
        print(f"Error loading monitor display: {e}")
        abort(500)


@app.route('/manager_threshold', methods=["GET", "POST"])
@login_required
def manager_threshold():
    if request.method == "POST":
        try:
            change_time = request.form.get("change_time")
            change_date = request.form.get("change_date")
            new_tempThreshold = request.form.get("new_tempThreshold")
            temp_Threshold = request.form.get("temp_Threshold")

            db = get_db()
            db.execute("INSERT INTO Threshold_Logs (Change_Time, Change_Date, new_tempThreshold) VALUES (?, ?, ?)",
                       (change_time, change_date, new_tempThreshold))
            db.execute("INSERT INTO Temps (Temp_Threshold) VALUES (?)", (temp_Threshold,))
            db.commit()
            db.close()
            flash("Threshold updated successfully.", "success")
        except Exception as e:
            print(f"Error updating threshold: {e}")
            flash("Error updating threshold.", "danger")
    return render_template('manager-threshold.html')


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        db = get_db()
        username = request.form.get("username")
        password = request.form.get("password")

        check_user = db.execute("SELECT * FROM User WHERE username = ?", (username,)).fetchone()
        if check_user:
            flash("Error: User already exists!", "danger")
        else:
            password_hash = generate_password_hash(password)
            db.execute("INSERT INTO User (username, password) VALUES (?, ?)", (username, password_hash))
            db.commit()
            db.close()
            flash("Registration successful! Please log in.", "success")
            return redirect("/login")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    if request.method == "POST":
        username_login = request.form.get("username")
        password_login = request.form.get("password")

        db = get_db()
        user_details = db.execute("SELECT * FROM User WHERE username = ?", (username_login,)).fetchone()
        db.close()

        if user_details and check_password_hash(user_details["password"], password_login):
            user = User(user_details["UserID"], user_details["username"])
            login_user(user)
            print("LOG: User Login Successful!")
            return redirect("/")
        else:
            flash("Invalid username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect("/")
