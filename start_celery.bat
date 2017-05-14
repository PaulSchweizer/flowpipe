

Celery:
cd C:\PROJECTS\flowpipe
celery -A flowpipe.celery.app.app worker -l info


Redis:
C:\Program Files\Redis\redis-server.exe


Flower:
C:\PROJECTS\flowpipe>flower -A flowpipe.mycelery.mycelery.app --port=5555

