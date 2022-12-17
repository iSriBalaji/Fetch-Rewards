## Files and their usage
1. main.py - is the primary file which 
            - fetches the data from the SQS
            - flatten it
            - mask the PII data
            - insert the data into the Postgres            
            - also find the number of messages in the SQS queue automatically            - check for duplicate records
            - check for data integrity and eliminates the value
2. db_connection.py - connects to the Postgres DB running in the container
            - connect to the DB
            - execute queries
            - fetch data if the query returns any value(to check duplicate records)
            - to commit the changes to the table
            - to close the connection
3. database.ini - contains the passwords and user_id to the database
            - learned from a youtube video
4. sample.json - consists of sample data
            - to understand the structure of the data
            - helps in writing transformation scripts

## Steps to run the code
Just use the ./run.sh script to start the process. It will automatically call the main.py and detect how many messages are in the queue and complete the operation from start to end

## Please make sure the following before running the program
- Run the python code with version 3(python3) in the script or in the terminal
- We can set the keys and passwords in the environment variables. but for demonstration, It is used directly
- change or make sure the db_path is right in the db_connection.py(it is the path of database.ini)

## Questions & Answers
1. <strong>How will you read messages from the queue?</strong>
- I have used the python package os to run a terminal command and get the output - <strong>os.popen()</strong>
- Converted the string response to python dictionary using JSON package
other ways - we can also save the responses in the file, read it and make the corresponding transformation. but it will consume a lot of space. <aws sqs command> > data.json. We can also use the python package boto3 package if we have direct access to the AWS SQS

2. What type of data structures should be used?
- I have processed all the data in dictionary(JSON) format from the beginning
- After masking the data, I returned the data as <strong>tuple</strong> as we can easily pass it in the SQL query

3. How will you mask the PII data so that duplicate values can be identified?
- I initially had this approach: we can swift each of the characters two or three steps. Say, we have the order [0,1,2,3,4,5,6,7,8,9] and our IP address is 192.168. 1.1 we can shift any steps to change the values 2-->5(3-step move) and 6-->9(3-step move). so the IP will be 425.401.4.4 at the end. We can also perform the same with the alphabet in device_id. In this way, we can also identify the duplicate values even when we mask it
<strong>My approach </strong> I have encrypted the data before inserting it into the database by using AES two-way encryption algorithm. In my previous job, we used a hp enterprise plugin to encrypt data using a key specific to each column. So, I thought this approach is more effective than the previous method. Also, it follows most of the data privacy laws such as GDPR.
If we need to find the duplicates we can check the similarity of user_id, device_id, and ip_address to identify the specific user

4. What will be your strategy for connecting and writing to Postgres?
I have used Psycopg, a PostgreSQL database adapter that can be used along with python to make connections with the database using cursors similar to MySQL connector. I watched a youtube video on it and utilized the functions specifically useful to solve our problem. I tested each of the functions and modules separately; performed unit testing and moved to the main.py file.
Initially, I started writing shell scripts for it but after finding psycopg package I switched to it as it is easy to use

5. Where and how will your application run?
<strong> ./run.sh </strong> to run the main python script; which runs the entire process within the docker itself
It can be automated to run easily by performing the following operations
- run the main.py file within the 01_call_python_scripts.sh script which starts the process when we run the make start command in the terminal
- In order to fetch the upcoming messages from the  SQS we can run a CRON job which can run every 60 or 30 mins to transform and insert them into the database

## Other Questions
1. How would you deploy this application in production?
During my AWS CCP preparation, I learned about ECS where we can deploy our docker containers, or in Google Cloud, we have Cloud Run and similar services. Also, in the tutorial I watched, they uploaded their docker image to the hub from which we can use the same image anywhere we need.

2. What other components would you want to add to make this production ready?
To deploy it to AWS ECS, we can use aws-cli and we also need ECR(registry where we can store our docker image) and ECS. We need to add a Dockerfile that tells the docker how to create the docker image(such as port number, python version, alpine or ubuntu dist, working directory, etc...) from it. Then we can move the image to the ECR. After that, we can run the container in ECS where we should decide how much memory and computations are required to run it. Then we can build and run the application which I learned from a blog.

3. How can this application scale with a growing data set? 
In my previous job, we usually try increasing the cluster size of the service if we deploy it in the cloud. Also, now we are getting the messages one by one and making the transformations. We can get a set of 50 or 100 rows of data together and perform the transformation in one stretch to save time. Pandas in python easily handle data frames and transform the data. Also, we can insert a set of 50 data into the database simultaneously.
We can experiment with other approaches and measure the performance of the container to handle a massive dataset. I always ask my mentors and talk with other teammates on different approaches to make a process efficient.

4. How can PII be recovered later on?
I have written a decrypt function in the main.py which can be used to recover the PII data again. We just have to pass the encrypted data to the function to recover the actual data. Please try to too!

## Here is the Video recording if the code did not run unfortunate situations
[FetchRewards_SriBalaji_Muruganandam.mov]()

Note: During installation of docker, I encountered a problem with my os(ubuntu) and after some time I borrowed my friend's PC to complete the assessment. the path and username priya you see in the code and the video is because of this :)

## References
https://www.geeksforgeeks.org/python-os-urandom-method/
https://www.youtube.com/watch?v=ZjebvGhxONA
https://cryptobook.nakov.com/symmetric-key-ciphers/aes-encrypt-decrypt-examples
https://stackoverflow.com/questions/8381193/handle-json-decode-error-when-nothing-returned