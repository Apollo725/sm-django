import os

os.environ['PG_HOST'] = os.environ['POSTGRES_PORT_5432_TCP_ADDR']
os.environ['PG_PORT'] = os.environ['POSTGRES_PORT_5432_TCP_PORT']
os.environ['PG_DB_NAME'] = 'postgres'
os.environ['REDIS_HOST'] = os.environ['REDIS_PORT_6379_TCP_ADDR']
os.environ['REDIS_PORT'] = os.environ['REDIS_PORT_6379_TCP_PORT']

# noinspection PyUnresolvedReferences
from app.sharing_settings import *