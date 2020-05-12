To start service run in tmux this commands. one per window.

gunicorn app.wsgi -b 0.0.0.0:8320 --pid=/var/run/sm/8320.pid --access-logformat='%(t)s %({X-Real-IP}i)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' --access-logfile - 2>&1 |tee -a /var/log/sm/sm-frontend.log
gunicorn app.wsgi -b 0.0.0.0:8321 --pid=/var/run/sm/8321.pid --access-logformat='%(t)s %({X-Real-IP}i)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' --access-logfile - 2>&1 |tee -a /var/log/sm/sm-frontend.log


For the list of new API's made in SM try to maintain this sheet:
https://docs.google.com/spreadsheets/d/1TzzxDIhZXWkppRMhNOJpKvAvm3YLzn0n1RLlxshGMhY/edit#gid=513336152

(since June 2018)
