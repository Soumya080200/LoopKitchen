from loaddata import *

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

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(30))

    def __init__(self, status):
        self.status=status

    def save(self):
        db.session.add(self)
        db.session.commit()