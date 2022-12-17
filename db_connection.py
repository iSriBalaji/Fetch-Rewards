## Importing the necessary packages
import psycopg2
from configparser import ConfigParser

# Configuration Path
#db_path = "/Users/priyavarman/Documents/SriBalaji-Assessment/data-engineering-take-home/database.ini"
db_path = "database.ini"   #please set the database.ini path here!

class postGres:

    def __init__(self, filename=db_path, section='postgresql'):
        self.parser = ConfigParser() 
        self.parser.read(filename)
        self.db = {} 

        if self.parser.has_section(section):
            self.params = self.parser.items(section)
            for param in self.params:
                self.db[param[0]] = param[1]
        else:
            raise Exception("There is no configuration file in the respective location")
        
    def connect(self):
        """
        This function connects to the postgres DB
        running in the container
        """
        self.conn = None
        try:
            self.conn = psycopg2.connect(host = self.db['host'], 
                                        database = self.db['database'], 
                                        user = self.db['user'], 
                                        password = self.db['password'],
                                        port = self.db['port']
                                        )
        except (Exception, psycopg2.DatabaseError) as err: 
            print(f"Database connection error:  {err}")
    
    def close(self):
        """
        It closes the connection that is
        already established by the connect
        function
        """
        if self.conn and not self.conn.closed:
            self.conn.close()
        self.conn = None

    def commit(self):
        """
        To save all the changes in
        the table we commit
        """
        self.conn.commit()
    
    def execute(self, query, args=None):
        """
        It execute queries to perform 
        any process to the table
        """
        
        # if not already connected connect to the database
        if self.conn is None or self.conn.closed:
            self.connect()
        curs = self.conn.cursor()
        try:
            curs.execute(query, args)
        except Exception as ex:
            self.conn.rollback()
            curs.close()
            raise ex
        return curs
    
    def fetchall(self, query, args=None):
        """
        To get the results from the query
        executed
        """
        curs = self.execute(query, args)
        rows = curs.fetchall()
        curs.close()
        return rows  

# CREATE TABLE IF NOT EXISTS user_logins(
#     user_id             varchar(128),
#     device_type         varchar(32),
#     masked_ip           varchar(256),
#     masked_device_id    varchar(256),
#     locale              varchar(32),
#     app_version         integer,
#     create_date         date
# );
