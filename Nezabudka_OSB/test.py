from datetime import datetime, timedelta
from app.templates.result_by_id_day.html import name_user

current_date = datetime.today()
my_day = 2
result = current_date + timedelta(days=my_day)
result = str(result)
data_now = result[8:10] + "." + result[5:7] + "." + result[:4]
print(data_now)