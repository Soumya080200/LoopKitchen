from flask_marshmallow import Marshmallow

ma = Marshmallow()

class StoreStatusSchema(ma.Schema):
    class Meta:
        fields = ('id', 'storeId', 'status', 'timeStamp')

class MenuHourSchema(ma.Schema):
    class Meta:
        fields = ('id', 'storeId', 'day', 'start_time_local', 'end_time_local')

class StoreSchema(ma.Schema):
    class Meta:
        fields = ('store_id', 'timezone_str')