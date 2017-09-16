

Celery:
cd C:\PROJECTS\flowpipe
celery -A flowpipe.celery.app.app worker -l info


Redis:
"C:\Program Files\Redis\redis-server.exe"


Flower:
cd C:\PROJECTS\flowpipe
flower -A flowpipe.celery.app.app --port=5555

