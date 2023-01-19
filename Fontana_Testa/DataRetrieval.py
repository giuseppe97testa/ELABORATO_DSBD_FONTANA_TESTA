from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import errorcode

def clientSQL():
    try:
        mydb = mysql.connector.connect(
            host="mysqldb",
            user="root",
            password="toor",
            database="metrics",
            port=3306
        )
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your user name or password")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print("Database does not exist")
        else:
            print(err)
    else: # se la connessione va a buon fine
        mycursor = mydb.cursor() # crea il cursore per interagire con il BD
        app = Flask(__name__)

        @app.route('/metrics') # risorsa per QUERY su tutti i dati disponibili nel DB
        def get_metrics():
            metrics = []

            mycursor.execute("SELECT * FROM metrics;")
            metrics.append("MAX, MIN, MEAN, DEV_STD of all metrics")
            for item in mycursor:
                metrics.append(item)

            mycursor.execute("SELECT * FROM autocorrelation;")
            metrics.append("AUTOCORRELATION of all metrics")
            for item in mycursor:
                metrics.append(item)

            mycursor.execute("SELECT * FROM seasonability;")
            metrics.append("SEASONABILITY of all metrics")
            for item in mycursor:
                metrics.append(item)

            mycursor.execute("SELECT * FROM stationarity;")
            metrics.append("STATIONARITY of all metrics")
            for item in mycursor:
                metrics.append(item)
            
            mycursor.execute("SELECT * FROM prediction_max;")
            metrics.append("PREDICTION MAX OF 10 MINUTES of all metrics")
            for item in mycursor:
                metrics.append(item)

            mycursor.execute("SELECT * FROM prediction_min;")
            metrics.append("PREDICTION MIN OF 10 MINUTES of all metrics")
            for item in mycursor:
                metrics.append(item)

            mycursor.execute("SELECT * FROM prediction_mean;")
            metrics.append("PREDICTION MEAN OF 10 MINUTES of all metrics")
            for item in mycursor:
                metrics.append(item)

            return jsonify(metrics)

        @app.route('/metrics/metric/<metric_name>') # risorsa per QUERY sulle metriche per nome metrica
        def show_metric_by_name(metric_name):
            metrics = []
            sql = "SELECT * FROM metrics WHERE metric = '{0}';".format(metric_name)
            mycursor.execute(sql)
            metrics.append("MAX, MIN, MEAN, DEV_STD")
            for item in mycursor:
                metrics.append(item)
            return jsonify(metrics)

        @app.route('/metrics/metadati/<metric_name>') # risorsa per QUERY sui metadati per nome metrica
        def show_metadata_by_name(metric_name):
            pippo = [] # easter egg, se lo avete trovato 5 punti in più all'esame :)
            sql1 = "SELECT * FROM autocorrelation WHERE metric = '{0}';".format(metric_name)
            mycursor.execute(sql1)
            pippo.append("Autocorrelazione")
            for item in mycursor:
                pippo.append(item)

            sql2 = "SELECT * FROM stationarity WHERE metric = '{0}';".format(metric_name)
            mycursor.execute(sql2)
            pippo.append("Stazionarietà")
            for item in mycursor:
                pippo.append(item)

            sql3 = "SELECT * FROM seasonability WHERE metric = '{0}';".format(metric_name)
            mycursor.execute(sql3)
            pippo.append("Stagionalità")
            for item in mycursor:
                pippo.append(item)
            
            return jsonify(pippo)
        
        @app.route('/metrics/forecasting/<metric_name>') # risorsa per QUERY su predizioni per nome metrica
        def show_forecast_by_name(metric_name):
            metrics = []
            sql = "SELECT * FROM prediction_max WHERE metric = '{0}';".format(metric_name)
            mycursor.execute(sql)
            metrics.append("PREDICTION_MAX")
            for item in mycursor:
                metrics.append(item)

            sql = "SELECT * FROM prediction_min WHERE metric = '{0}';".format(metric_name)
            mycursor.execute(sql)
            metrics.append("PREDICTION_MIN")
            for item in mycursor:
                metrics.append(item)
            
            sql = "SELECT * FROM prediction_mean WHERE metric = '{0}';".format(metric_name)
            mycursor.execute(sql)
            metrics.append("PREDICTION_MEAN")
            for item in mycursor:
                metrics.append(item)
            return jsonify(metrics)

        if __name__ == '__main__':
            app.run(debug = False, host='0.0.0.0', port=5005)
            
        mydb.close()

clientSQL()