from flask import Flask,jsonify, request, json
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from flask_marshmallow import Marshmallow
import pandas as pd
from datetime import datetime, timezone

app = Flask(__name__)

db = SQLAlchemy()
ma = Marshmallow()
mysql = MySQL()

class StoreStatus(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    store_id = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(15), nullable=False)
    time_stamp = db.Column(db.DateTime(timezone=True), nullable=False)

    def __init__(self, store_id, status, time_stamp):
        self.store_id=store_id
        self.status=status
        self.time_stamp=time_stamp
    
    def save(self):
        db.session.add(self)
        db.session.commit()

class MenuHour(db.Model):
    id = db.Column(db.BigInteger, primary_key=True)
    store_id = db.Column(db.BigInteger, nullable=False)
    day = db.Column(db.Integer)
    start_time_local = db.Column(db.Time(timezone=False))
    end_time_local = db.Column(db.Time(timezone=False))

    def __init__(self, store_id, day, start_time_local, end_time_local):
        self.store_id=store_id
        self.day=day
        self.start_time_local=start_time_local
        self.end_time_local=end_time_local

    def save(self):
        db.session.add(self)
        db.session.commit()

class Store(db.Model):
    store_id = db.Column(db.BigInteger, primary_key=True)
    timezone_str = db.Column(db.String(30))

    def __init__(self, store_id, timezone_str):
        self.store_id=store_id
        self.timezone_str=timezone_str

    def save(self):
        db.session.add(self)
        db.session.commit()


app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/loopkitchen"
db.init_app(app)

with app.app_context():
    db.create_all()

def add_store_status(store_id, status, time_stamp):
    try:
        new_status = StoreStatus(store_id=store_id, status=status, time_stamp=time_stamp)
        db.session.add(new_status)
        db.session.commit()
    except Exception:
        print("could not save status to db", Exception)

def add_menu_hour(store_id, day, start_time_local, end_time_local):
    try:
        new_menu_hour = MenuHour(store_id=store_id, day=day, start_time_local=start_time_local, end_time_local=end_time_local)
        db.session.add(new_menu_hour)
        db.session.commit()
    except Exception as exp:
        print("could not save menu hour to db", exp)

def add_store(store_id, timezone):
    new_store = Store(store_id=store_id, timezone_str=timezone)
    try:
        db.session.add(new_store)
        db.session.commit()
    except Exception as exception:
        print("could not save store to db", exception)

def convert_csv_to_data_frame(filename):
    df = pd.read_csv(filename)
    return df

@app.route('/loadstatus', methods=["GET"])
def load_status_data():
    df = convert_csv_to_data_frame("store_status.csv")
    for ind, row in df.iterrows():
        time_stamp = row['timestamp_utc']
        time_stamp = time_stamp.replace(" UTC", "")
        time_stamp_obj = datetime.strptime(time_stamp, '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=timezone.utc)
        add_store_status(row['store_id'], row['status'], time_stamp_obj)
    return "success"

@app.route('/loadmenuhours', methods=["GET"])     
def load_menu_hours():
    df = convert_csv_to_data_frame("menu_hours.csv")
    for ind, row in df.iterrows():
        start_time = datetime.strptime(row['start_time_local'], '%H:%M:%S').time()
        end_time = datetime.strptime(row['end_time_local'], '%H:%M:%S').time()
        add_menu_hour(row['store_id'], row['day'], start_time, end_time)
    return "success" 

@app.route('/loadstores', methods=["GET"]) 
def load_stores():
    df = convert_csv_to_data_frame("stores.csv")
    for ind, row in df.iterrows():
        add_store(row['store_id'], row['timezone_str'])
    return "success" 

if __name__ == '__main__':
    app.run(debug=True)
