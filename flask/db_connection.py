import mysql.connector
from ldarunner import LDARunner
from textprocessor import TextProcessor


class DBConnection(object):
    def __init__(self, db_host='localhost', db_user='root', db_password='root', db_database='news_db2'):
        self.host = db_host
        self.user = db_user
        self.password = db_password
        self.database = db_database
        self.connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password,
                                                  database=self.database)
        self.cursor = self.connection.cursor(buffered=True)
        self.ldarun = LDARunner()
        self.tp = TextProcessor()
