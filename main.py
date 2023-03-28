from flask import Flask, json, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from flask_mysqldb import MySQL
from flask_marshmallow import Marshmallow
import pandas as pd
from schemas import *
from datetime import datetime, time, timedelta
import pytz
import numpy as np
from scipy.interpolate import interp1d
from scipy.integrate import quad

app = Flask(__name__)
db = SQLAlchemy()
ma = Marshmallow()
mysql = MySQL()

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql://root:@localhost/loopkitchen"
db.init_app(app)

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(30))

    def __init__(self, status):
        self.status=status

    def save(self):
        db.session.add(self)
        db.session.commit()

class ReportSchema(ma.Schema):
    class Meta:
        fields = ('id', 'status')

report_schema = ReportSchema()

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

class StoreStatusSchema(ma.Schema):
    class Meta:
        fields = ('id', 'storeId', 'status', 'time_stamp')

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

class MenuHourSchema(ma.Schema):
    class Meta:
        fields = ('id', 'store_id', 'day', 'start_time_local', 'end_time_local')

class Store(db.Model):
    store_id = db.Column(db.BigInteger, primary_key=True)
    timezone_str = db.Column(db.String(30))

    def __init__(self, store_id, timezone_str):
        self.store_id=store_id
        self.timezone_str=timezone_str

    def save(self):
        db.session.add(self)
        db.session.commit()

menu_hour_schema = MenuHourSchema()
# menu_hour_schema = MenuHourSchema(many=True)
store_status_schema = StoreStatusSchema()
store_status_schema = StoreStatusSchema(many=True)

def get_utc_time( local_time,local_timezone):
    local = pytz.timezone(local_timezone)
    local_dt = local.localize(local_time, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt

def to_float(d, epoch=datetime(1970,1,1)):
    return (d-epoch).total_seconds()

def find_uptime(store, dt=datetime.now(), time_last_hour=datetime.now() - timedelta(hours=1)):
    
    date = datetime.today()
    date = dt.date()
    day_of_the_week = dt.weekday() 
    print("hello", store)
    business_hour = MenuHour.query.filter(and_(MenuHour.store_id==store.store_id, MenuHour.day==day_of_the_week)).first()
    business_hour = menu_hour_schema.dump(business_hour)
    
    start_time = time(0,0,0)
    end_time = time(23, 59, 59)
    if business_hour is not None and 'start_time_local' in business_hour and 'end_time_local' in business_hour:
        start_time = datetime.strptime(business_hour['start_time_local'], "%H:%M:%S").time() 
        end_time = datetime.strptime(business_hour['end_time_local'], '%H:%M:%S').time()
    
    local_timezone = "America/Chicago"
    if store.timezone_str is not None:
        local_timezone = store.timezone_str
    start_time = datetime.combine(date=date, time=start_time)
    end_time = datetime.combine(date=date, time=end_time)
    start_time = get_utc_time(start_time, local_timezone)
    end_time = get_utc_time(end_time, local_timezone)

    store_status_results = StoreStatus.query.filter(and_(StoreStatus.time_stamp >= start_time, StoreStatus.time_stamp <= end_time)).all()
    store_status_results = store_status_schema.dump(store_status_results)

    x_data = []
    y_data = []
    for store_status in store_status_results:
        x_data.append(to_float(start_time, datetime.strptime(store_status['time_stamp'], '%Y-%m-%d %H:%M:%S.%f').time()))
        if store_status['status'] == 'active':
            y_data.append(1)
        else:
            y_data.append(0)

    x_data = np.array(x_data)
    y_data = np.array(y_data)

    if x_data.size == 0:
        return [0,0]

    f_x = interp1d(x_data, y_data, kind='zero')
    uptime_seconds = quad(f_x, to_float(time_last_hour), to_float(dt))
    downtime_seconds = 3600-uptime_seconds

    return [uptime_seconds, downtime_seconds]

def find_uptime_last_day(store, dt=datetime.now()):

    day_of_the_week = dt.weekday()
    business_hour = MenuHour.query.filter(and_(MenuHour.store_id==store.store_id, MenuHour.day==day_of_the_week)).first()
    business_hour = menu_hour_schema.dump(business_hour)
    start_time = time(0,0,0)
    end_time = time(23, 59, 59)
    if business_hour is not None and 'start_time_local' in business_hour and 'end_time_local' in business_hour:
        start_time = datetime.strptime(business_hour['start_time_local'], "%H:%M:%S").time() 
        end_time = datetime.strptime(business_hour['end_time_local'], '%H:%M:%S').time()
    
    time_array = find_uptime(store=store, dt=start_time, time_last_hour=end_time)
    uptime = timedelta(seconds= time_array[0])
    downtime = timedelta(seconds=time_array[1])

    return [uptime, downtime]

def find_uptime_last_week(store, dt = datetime.now()):
    uptime = timedelta()
    downtime = timedelta()
    for i in range(7):
        day = dt - timedelta(days=i)
        time_array = find_uptime_last_day(store=store, dt=day)
        uptime = uptime+time_array[0]
        downtime=downtime+time_array[1]
    return [uptime, downtime]

def make_new_report(report_id):
    stores = Store.query.all()
    report = []
    store = Store(257406000000000, 'America/Chicago')
    time_array = find_uptime(store=store, dt = datetime.now(), time_last_hour = datetime.now() - timedelta(hours=1))
    for store in stores:
        time_array = find_uptime(store, dt = datetime.now(), time_last_hour = datetime.now() - timedelta(hours=1))
        downtime_last_hour = str(timedelta(seconds=time_array[1]))
        uptime_last_hour = str(timedelta(seconds=time_array[0]))
        time_array = find_uptime_last_day(store)
        uptime_last_day = str(time_array[0])
        downtime_last_day = str(time_array[1])
        time_array = find_uptime_last_week(store=store, dt=datetime.now())
        uptime_last_week = str(time_array[0])
        downtime_last_week = str(time_array[1])
        data = {'Store_Id': store.store_id,
                'uptime_last_hour': uptime_last_hour,
                'uptime_last_day': uptime_last_day,
                'uptime_last_week': uptime_last_week,
                'downtime_last_hour': downtime_last_hour,
                'downtime_last_day': downtime_last_day,
                'downtime_last_week': downtime_last_week
                }
        report.append(data)
    
    df = pd.DataFrame(report)
    df.to_csv(str(report_id)+'.csv')
    
    rp = Report.query.get(report_id)
    if rp is None:
        return
    rp.status = 'Complete'
    db.session.commit()


@app.route('/trigger_report')
def trigger_report(): 
    new_report = Report("Running")
    new_report.save()
    make_new_report(new_report.id)
    return jsonify(new_report.id)

@app.route('/get_report/<report_id>', methods=["GET"])
def get_report(report_id):

    data = Report.query.get(report_id)
    if data is None:
        return "Wrong Report Id"
    
    data = report_schema.dump(data)
    if(data['status']=='Running'):
        return data['status']

    try:
        return {'file': send_file(str(report_id)+'.csv', as_attachment=str(report_id)+'.csv'), 'status': 'Completed'}
    except Exception as e:
        print('Excetion Caused: ', e)
        return 'Error Occured'


if __name__ == '__main__':
    app.run(debug=True)