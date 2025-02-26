from app import app, login_manager
from app.db import get_db
from flask import render_template, redirect, request
from flask_login import logout_user, UserMixin, login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from requests import get
from config import username, password
import math


# Defines user
class User(UserMixin):
    def __init__(self, UserID, username):
        self.UserID = UserID
        self.username = username

    def get_id(self):
        return str(self.UserID)


@login_manager.user_loader
def load_user(UserID):
    db = get_db()
    user_search = db.execute("SELECT * FROM User WHERE UserID = ?", (UserID, ))
    user_details = user_search.fetchone()
    if user_details:
        user = User(user_details["UserID"], user_details["username"])
        return user


# Home Page route
@app.route('/')
def index():
    # retrieves data from the BOM API(ln:37)
    # delete "proxies=proxies" if not using a proxy enabled network
    r = get('http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94576.json')
    #opens the JSON file(ln:39) & loads the JSON file(ln:40)
    outsideTempJSON = r.json()
    # retrieves the outside temperature(ln:44),apparent temperature(ln:45), & humidity(ln:46)
    bomData = outsideTempJSON['observations']['data'][0]
    outside_temp = bomData["air_temp"]
    outside_AppTemp = bomData['apparent_t']
    outside_humidity = bomData['rel_hum']
    threshold_get = get_db()
    # executes a sql query that selects the Temperature Threshold from the Database(ln:50 - 51 )
    sql_tg = threshold_get.execute("SELECT Temp_Threshold "
                                   " FROM Temps ")
    temp_get = get_db()
    temp_sql = temp_get.execute("SELECT Inside_Temp "
                                "FROM Temps")
    temp_var = temp_sql.fetchone()['Inside_Temp']
    hum_get = get_db()
    hum_sql = hum_get.execute("SELECT Inside_Humidity "
                              "FROM Temps")
    hum_var = hum_sql.fetchone()
    apparent_temp_get = get_db()
    apparent_temp_sql = apparent_temp_get.execute("SELECT Inside_Apparent_Temp "
                                                  "FROM Temps")
    apparent_temp_var = apparent_temp_sql.fetchone()
    ins_DB = get_db()
    ins_DB.execute("INSERT INTO Temps "
                   "(Outside_Temp, Outside_Humidity, Outside_Apparent_Temp) "
                   "VALUES(?, ?, ?)", (outside_temp, outside_humidity, outside_AppTemp))
    ins_DB.commit()
    safe_temp = 25
    warning_temp = 30
    critical_temp = 35
    temp_status = ""
    if temp_var > critical_temp:
        temp_status = "Critical"
    elif temp_var > warning_temp:
        temp_status = "Warning"
    elif temp_var < safe_temp:
        temp_status = "Safe"
    # passes the variables through the render template to be used with HTML(ln:66 - 70)
    return render_template('index.html', outside_temp=outside_temp,
                           outside_AppTemp=outside_AppTemp,
                           outside_humidity=outside_humidity, apparent_temp_var=apparent_temp_var,
                           temp_var=temp_var, hum_var=hum_var,
                           sql_tg=sql_tg, temp_status=temp_status)


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
        print(Inside_Apparent_Temperature)
        print(Inside_Temp)
        print(Inside_Humidity)
        db_get = get_db()
        db_get.execute("INSERT INTO Temps"
                       "(Inside_Temp, Inside_Humidity, Inside_Apparent_Temp)"
                       "VALUES(?, ?, ?)", (Inside_Temp, Inside_Humidity, Inside_Apparent_Temperature))
        db_get.commit()
        db_get.close()
        return "Uploaded to Database"
    except:
        return "Error Submitting Data"


@app.route('/monitordisplay')
def monitorDisplay():
    # gets all the required data from the Bureau of Meteorology(ln:99)
    # delete "proxies=proxies" if not using a proxy enabled network
    r = get('http://reg.bom.gov.au/fwo/IDQ60901/IDQ60901.94576.json')
    outsideTempJSON = r.json()
    bomData = outsideTempJSON['observations']['data'][0]
    outside_temp = bomData["air_temp"]
    outside_apparent_temp = bomData['apparent_t']
    outside_humidity = bomData['rel_hum']
    threshold_get_monitor = get_db()
    sql_tg_monitor = threshold_get_monitor.execute("SELECT Temp_Threshold "
                                                   " FROM Temps ")
    threshold_get_monitor_var = sql_tg_monitor.fetchone()
    temp_get = get_db()
    temp_sql = temp_get.execute("SELECT Inside_Temp "
                                "FROM Temps")
    current_temp_monitor = temp_sql.fetchone()['Inside_Temp']
    hum_get = get_db()
    hum_sql = hum_get.execute("SELECT Inside_Humidity "
                              "FROM Temps")
    hum_var_monitor = hum_sql.fetchone()
    apparent_temp_get_monitor = get_db()
    apparent_temp_sql_monitor = apparent_temp_get_monitor.execute("SELECT Inside_Apparent_Temp "
                                                                  "FROM Temps")
    apparent_temp_monitor_var = apparent_temp_sql_monitor.fetchone()
    safe_temp_monitor = 25
    warning_temp_monitor = 30
    critical_temp_monitor = 35
    temp_status_monitor = ""
    if current_temp_monitor > critical_temp_monitor:
        temp_status_monitor = "Critical"
    elif current_temp_monitor > warning_temp_monitor:
        temp_status_monitor = "Warning"
    elif current_temp_monitor < safe_temp_monitor:
        temp_status_monitor = "Safe"
    return render_template('index-monitor-screen.html',
                           outside_temp=outside_temp,
                           outside_apparent_temp=outside_apparent_temp,
                           outside_humidity=outside_humidity, temp_status_monitor=temp_status_monitor,
                           apparent_temp_monitor_var=apparent_temp_monitor_var, hum_var_monitor=hum_var_monitor,
                           threshold_get_monitor_var=threshold_get_monitor_var)


@app.route('/manager_threshold')
@login_required
# @login_required
def manager_threshold():
    if request.method == "POST":
        #retrieves the change time field from the HTML form(ln:128)
        #retrieves the change date field from the HTML form(ln:129)
        #retrieves the new temperature threshold field from the HTML form(ln:130)
        #retrives the temperature threshold field from the HTML form(ln:131)
        change_time = request.form.get("change_time")
        change_date = request.form.get("change_date")
        new_tempThreshold = request.form.get("new_tempThreshold")
        temp_Threshold = request.form.get("temp_Threshold")
        db_thresholdLog = get_db()
        #executes an SQL query that inserts the retrieved fields into the database(ln:163 - 168)
        db_thresholdLog.execute("INSERT INTO Threshold_Logs "
                                "(Change_Time, Change_Date, new_tempThreshold) "
                                "VALUES (?, ?, ?); "
                                "INSERT INTO Temps "
                                "(Temp_Threshold) "
                                "VALUES (?)", (change_time, change_date, new_tempThreshold, temp_Threshold))
        db_thresholdLog.commit()
        db_thresholdLog.close()
    return render_template('manager-threshold.html')


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        db_login = get_db()
        username = request.form.get("username")
        password = request.form.get("password")
        check_user = db_login.execute("SELECT * FROM user WHERE username = ?", (username,))
        check_user_results = check_user.fetchall()
        if check_user_results:
            print("User already exists")
        else:
            passwordHash = generate_password_hash(password)
            db_login.execute("INSERT INTO User "
                             "(username, password)"
                             "VALUES(?, ?)", (username, passwordHash))
            db_login.commit()
            db_login.close()
            print("User has signed up")
            return redirect("/login")
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect("/")
    else:
        if request.method == "POST":
            username_login = request.form.get('username')
            password_login = request.form.get('password')
            db_signup = get_db()
            user_search = db_signup.execute("SELECT * FROM User WHERE username = ?", (username_login,))
            user_details = user_search.fetchone()
            db_signup.close()
            if user_details:
                check_password_hash(password_login, "Manager_1")
                user = User(user_details["UserID"], username)
                login_user(user)
                print("Login Successful")
                return redirect("/")
            else:
                    print("Error: incorrect username or password")
        else:
                print("Error - user doesn't exist")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    print("You have logged out")
    return redirect("/")
