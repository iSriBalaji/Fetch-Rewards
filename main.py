import os
import json
import datetime
import pyaes
import pbkdf2
import binascii
from db_connection import postGres
from json.decoder import JSONDecodeError


# Set the environment variable with the encrytion key and db keys. Just for demonstration it is set here
os.environ["PII_KEY"] = "postgres"
RANDBITS = 99446315885073233365141655680946573896736393686005713140062347178003378443401

# Invalid data from the SQS - Checking Data Integrity
class InvalidData(Exception):
    "The data is incomplete or missing some informations"
    pass

class pipeline:
    
    def __init__(self):
        self.row = None
        self.data = None

    def fetch_data(self):
        """
        It fetches the data from AWS SQS
        """
        
        try:
            resp = os.popen("awslocal sqs receive-message --queue-url http://localhost:4566/000000000000/login-queue").read()
            
            #converting the str type to dict(json)
            response = json.loads(resp)
            self.row = response
            return 1
        except JSONDecodeError as e:
            print("All the data have been fetched from the SQS")
            return None

    def decrypt_data(self, masked_data):
        """
        This recovers the encryted data from
        key stored in the env variable - PII_KEY
        """
        
        PII_KEY = os.environ.get("PII_KEY")

        # generating the same 8 byte random string to generate a key using PBKDF2 derivation algorithm
        random_str = bytes('j\x93\xad?M)\x87\x97', encoding="utf8") #os.urandom(8)
        encrytion_key = pbkdf2.PBKDF2(str(PII_KEY), random_str).read(32)
        
        # Unhexlify the data
        masked_data = binascii.unhexlify(masked_data)
        
        # Retreving the value
        AES_object = pyaes.AESModeOfOperationCTR(encrytion_key, pyaes.Counter(RANDBITS))
        actual_data = AES_object.decrypt(masked_data)
        
        return actual_data.decode("utf-8")
        
        

    def mask_data(self, data):
        """
        It masks the data using AES algorithm
        using the key which is stored as a env
        variable(PII_KEY)
        """
        
        #PII_KEY = os.popen("echo $PII_KEY")
        PII_KEY = os.environ.get("PII_KEY")
        
        # generating a 8 byte random string to generate a key using PBKDF2 derivation algorithm
        random_str = bytes('j\x93\xad?M)\x87\x97', encoding="utf8") #os.urandom(8)
        encrytion_key = pbkdf2.PBKDF2(str(PII_KEY), random_str).read(32)
        
        # Masking the value
        AES_object = pyaes.AESModeOfOperationCTR(encrytion_key, pyaes.Counter(RANDBITS))
        masked_data = AES_object.encrypt(data)
        
        return binascii.hexlify(masked_data).decode("utf-8")

    def flatten(self):
        """
        Extract the data to flatten it to tuple
        along with encryption of device_id and
        ip_address
        """
        body = self.row["Messages"][0]["Body"]
        
        #converting the body of the message to dict(JSON)
        body = json.loads(body)
        
        # getting individual data, it can also be returned directly,
        # but for visibility and to check data integrity saving it separately
        try:
            user_id = body["user_id"]
            app_version = int(body["app_version"].split(".")[0])
            device_type = body["device_type"]
            ip = body["ip"]
            locale = body["locale"]
            if not locale:
                locale = ""
            device_id = body["device_id"]
            create_date = datetime.datetime.now().strftime("%D")
        except:
            print("There is not enough data available in the JSON\nThe data is incomplete or missing some informations")
            return None
        
        # Masking the IP address
        ip_address = self.mask_data(ip)
        device_id = self.mask_data(device_id)
        
        # we are saving the information in a tuple as we can easily pass it in the SQL query to Postgres
        # the schema is (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date)
        data = (user_id, device_type, ip_address, device_id, locale, app_version, create_date)
        self.data = data
        return 1
    
    def check_duplicate(self, data):
        """
        Checking the duplicate records before inserting
        to the table (user_id, device_id, ip_address). Here
        I checked only the user_id
        """
        db = postGres()
        db.connect()
        #records = db.fetchall(f"SELECT * FROM user_logins where user_id = {data[0]} and masked_device_id = {data[3]} and masked_ip = {data[2]}")
        records = db.fetchall(f"SELECT * FROM user_logins where user_id = '{data[0]}'")
        db.close()
        
        if not records: # return true if it is a new user data
            return True
        
        return False
    
    def insert_data(self):
        db = postGres()
        # connecting to the postgres db
        db.connect()
        
        if self.check_duplicate(self.data):
            #Inserting the data into the table
            db.execute(f"INSERT INTO user_logins \
                        (user_id, device_type, masked_ip, masked_device_id, locale, app_version, create_date) \
                        VALUES " + f"{str(self.data)}")
            db.commit()
            # # Closing the connection
            db.close()
            print("The row is successfully inserted into the table")
        
        else:
            print("It is a duplicate record")

# Start of the Automation
def main():
    
    # getting the approximate number of messages in the SQS queue
    messages = os.popen("awslocal sqs get-queue-attributes --queue-url http://localhost:4566/000000000000/login-queue --attribute-names All").read()
    messages = json.loads(messages)
    no_of_messages = int(messages["Attributes"]["ApproximateNumberOfMessages"])
    print(f"There are approximately {str(no_of_messages)} of messages in the queue")
    
    for i in range(no_of_messages+10): # making additional 10 request to check upcoming/extra messages
        print(f"At row {i+1}", end=" ")
        process = pipeline()
        is_data = process.fetch_data()
        
        if is_data:
            is_success = process.flatten()
        else:
            print("Hurray!,Process Completed!")
            break
            
        if is_success:
            process.insert_data()


if __name__ == "__main__":
    main()
