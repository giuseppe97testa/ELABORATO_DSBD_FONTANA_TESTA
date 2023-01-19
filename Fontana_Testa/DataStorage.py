from confluent_kafka import Consumer
import json
import mysql.connector
from mysql.connector import errorcode
# Creazione dell'oggetto consumer per interazione con broker Kafka
c = Consumer({
    'bootstrap.servers': 'kafka:9092',
    'group.id': 'mygroup',
    'auto.offset.reset': 'latest'
})
c.subscribe(['promethuesdata']) # Subscription sul topic
try:
    # Connessione ed interazione col database
    mydb = mysql.connector.connect(
        host="mysqldb",
        user="root",
        password="toor",
        database="metrics",
        port=3306
    )
    mycursor = mydb.cursor()

    # Elimina gli elementi delle tabelle se gia presenti.
    # La definizione delle tabelle si trova sulla coda del file.
    mycursor.execute("DELETE FROM metrics")
    mycursor.execute("DELETE FROM autocorrelation")
    mycursor.execute("DELETE FROM seasonability")
    mycursor.execute("DELETE FROM stationarity")
    mycursor.execute("DELETE FROM prediction_max")
    mycursor.execute("DELETE FROM prediction_min")
    mycursor.execute("DELETE FROM prediction_mean")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with your user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)

# MAX, MIN, AVG, DEV_STD
def clientSQL_Metric(metric, max, min, mean, dev_std, duration): # Query di inserimento dati su tabella metrics
        sql = """INSERT INTO metrics (metric, max, min, mean, dev_std, duration) VALUES (%s,%s,%s,%s,%s,%s);"""
        val = (metric, max, min, mean, dev_std, duration)
        mycursor.execute(sql, val)
        mydb.commit()

#AUTOCORRELAZIONE
def clientSQL_Autocorrelation(metric, list_autocorrelation, duration): # Query di inserimento dati su tabella autocorrelation
    for item in list_autocorrelation:
        sql = """INSERT INTO autocorrelation (metric, value, duration) VALUES (%s,%s,%s);"""
        val = (metric, round(item, 4), duration)
        mycursor.execute(sql, val)
        mydb.commit()

#STAGIONALITA
def clientSQL_Seasonability(metric, list_seasonal, duration): # Query di inserimento dati su tabella seasonability
    for item in list_seasonal:
        sql = """INSERT INTO seasonability (metric, value, duration) VALUES (%s,%s,%s);"""
        val = (metric, round(item, 4), duration)
        mycursor.execute(sql, val)
        mydb.commit()

#STAZIONARIETA
def clientSQL_Stationarity(metric, stationarity, duration): # Query di inserimento dati su tabella stationarity
    sql = """INSERT INTO stationarity (metric, p_value,critical_values ,duration) VALUES (%s,%s,%s,%s);"""
    val = (metric, str(stationarity[1]), str(stationarity[4]),duration)
    mycursor.execute(sql, val)
    mydb.commit()

# PREDIZIONE SU MASSIMO
def clientSQL_Prediction_Max(metric, list_max, timing): # Query di inserimento dati su tabella prediction_max
    j = 0
    for i in list_max:
        if j % 2 == 0:
            p = j + 1
            sql = """INSERT INTO prediction_max (metric, timestamp, value, duration) VALUES (%s,%s,%s,%s);"""
            val = (metric, i, list_max[p], timing)
            mycursor.execute(sql, val)
            mydb.commit()
            j += 1
        else:
            j += 1
            continue

# PREDIZIONE SU MEDIA
def clientSQL_Prediction_Mean(metric, list_mean, timing): # Query di inserimento dati su tabella prediction_mean
    j = 0
    for i in list_mean:
        if j % 2 == 0:
            p = j + 1
            sql = """INSERT INTO prediction_mean (metric, timestamp, value, duration) VALUES (%s,%s,%s,%s);"""
            val = (metric, i, list_mean[p], timing)
            mycursor.execute(sql, val)
            mydb.commit()
            j += 1
        else:
            j += 1
            continue

# PREDIZIONE SU MINIMO
def clientSQL_Prediction_Min(metric, list_min, timing): # Query di inserimento dati su tabella prediction_min
    j = 0
    for i in list_min:
        if j % 2 == 0:
            p = j + 1
            sql = """INSERT INTO prediction_min (metric, timestamp, value, duration) VALUES (%s,%s,%s,%s);"""
            val = (metric, i, list_min[p], timing)
            mycursor.execute(sql, val)
            mydb.commit()
            j += 1
        else:
            j += 1
            continue           

# Fase di polling su kafka
while True:
    msg = c.poll(1.0)
    if msg is None:
        continue
    elif msg.error():
        print("Consumer error: {}".format(msg.error()))
        continue
    else:
        record_key = msg.key() # nome metrica
        record_value = msg.value() # valori
        data = json.loads(record_value) # deserializzazione
        #--------------------------
        max = data['Metric']['max']
        min = data['Metric']['min']
        mean = data['Metric']['mean']
        std = data['Metric']['std']

    # Selezione dei dati ed invio al database:

        clientSQL_Metric(record_key, max, min, mean, std, data['Metric']['duration'])
    #---------------------------
        autocorrelation = data['Metadati']['Autocorrelation']
        lista_autocorrelation = json.loads(autocorrelation)
        clientSQL_Autocorrelation(record_key, lista_autocorrelation, data['Metadati']['duration'])
    #-----------------------------
        seasonability = data['Metadati']['Stagionalità']
        list_seasonal = json.loads(seasonability)
        clientSQL_Seasonability(record_key, list_seasonal, data['Metadati']['duration'])
    #-------------------------------
        stationarity = data['Metadati']['Stazionarietà']
        list_stat = json.loads(stationarity)
        clientSQL_Stationarity(record_key, list_stat, data['Metadati']['duration'])
    #-------------------------------
        prediction_max = data['Predizione']['Prediction_Max']
        prediction_min = data['Predizione']['Prediction_Mean']
        prediction_mean = data['Predizione']['Prediction_Min']

    # -------------------------------
        list_max = json.loads(prediction_max) # lista dei valori di massimo predetti
        if (len(list_max) == 0):
            pass
        else:
            clientSQL_Prediction_Max(record_key, list_max, data['Predizione']['duration'])
            pass
    # -------------------------------
        list_min = json.loads(prediction_min)  # lista dei valori di minimo predetti
        if (len(list_min) == 0):
            pass
        else:
            clientSQL_Prediction_Min(record_key, list_min, data['Predizione']['duration'])
            pass
    # -------------------------------
        list_mean = json.loads(prediction_mean)  # lista dei valori di media predetti
        if (len(list_mean) == 0):
            pass
        else:
            clientSQL_Prediction_Mean(record_key, list_mean, data['Predizione']['duration'])
            pass
        print("All Saved in DB")

c.close()
mydb.close()

#Tabelle SQL
"""
CREATE TABLE metrics ( ID INT AUTO_INCREMENT, metric varchar(255),max DOUBLE, min DOUBLE, mean DOUBLE, dev_std DOUBLE, duration varchar(255) ,PRIMARY KEY (ID));
CREATE TABLE autocorrelation (ID INT AUTO_INCREMENT, metric varchar(255),value DOUBLE, duration varchar(255),PRIMARY KEY(ID));
CREATE TABLE seasonability (ID INT AUTO_INCREMENT, metric varchar(255),value DOUBLE,duration varchar(255), PRIMARY KEY(ID));
CREATE TABLE stationarity (ID INT AUTO_INCREMENT, metric varchar(255),p_value DOUBLE,critical_values varchar(255),duration varchar(255), PRIMARY KEY(ID));
CREATE TABLE prediction_mean (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
CREATE TABLE prediction_min (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
CREATE TABLE prediction_max (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
"""