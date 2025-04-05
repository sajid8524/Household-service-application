
broker_url = "redis://localhost:6379/0"
result_backend = "redis://localhost:6379/1"


timezone = "Asia/Kolkata"
enable_utc = True  


task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']  
task_track_started = True
task_time_limit = 300  


broker_connection_retry_on_startup = True
task_acks_late = True  