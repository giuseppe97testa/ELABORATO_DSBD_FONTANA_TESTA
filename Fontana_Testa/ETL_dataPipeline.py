from prometheus_api_client import PrometheusConnect, MetricsList, MetricSnapshotDataFrame, MetricRangeDataFrame
from prometheus_api_client.utils import parse_datetime
from confluent_kafka import Producer
from flask import Flask, jsonify, request
from datetime import timedelta
from statsmodels.tsa.stattools import acf, adfuller, kpss
from statsmodels.graphics.tsaplots import plot_acf
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import json
import time

broker = "kafka:9092"
topic = "promethuesdata"
conf = {'bootstrap.servers': broker}

all_metric = [] # viene riempito con le metriche scelte
monitoring1 = []
monitoring3 = [] # necessarie per i valori temporali
monitoring12 = []
val = [] # riempita con i valori calcolati
metric_forecast = ['availableMem', 'cpuLoad', 'cpuTemp', 'diskUsage', 'networkThroughput']

def metrics_scraping(broker, topic):
    all_metric.clear()
    p = Producer(**conf)
    c = 0
    prom = PrometheusConnect(url="http://15.160.61.227:29090", disable_ssl=True)
    query_metric = prom.custom_query(query='{job="summary", instance="106"}')
    for i in query_metric:
        if i['value'][1] != '0':
            all_metric.append(i['metric']['__name__'])

    try: 
        all_metric.remove('connectionStatus') # metrica rimosse per inutilità dei dati forniti
        all_metric.remove('timestamp') # metrica rimosse per inutilità dei dati forniti
    except: 
        pass
    
    all_data_time = ['1h', '3h', '12h']
    end_time = parse_datetime("now")
    chunk_size = timedelta(minutes=20)
    for timing in all_data_time:       
        start_time = parse_datetime(timing)
        for item in all_metric:
            c += 1
            mean = [] # lista dei medi
            maxx = [] # lista dei massimi
            minn = [] # lista dei minimi
            print(c)
            label_config = {'job': 'summary', 'instance': '106'}
            try:
                sT_1 = time.time() # Ritorna il tempo corrente
                metric_data = prom.get_metric_range_data(
                        metric_name=item,
                        label_config=label_config,
                        start_time=start_time,
                        end_time=end_time,
                        chunk_size=chunk_size,
                    )
                metric_df = MetricRangeDataFrame(metric_data) # Creazione del data frame
                # Calcolo dei valori previsti
                max_value = round(metric_df['value'].max(), 2)
                min_value = round(metric_df['value'].min(), 2)
                mean_value = round(metric_df['value'].mean(), 2)
                std_value = round(metric_df['value'].std(), 2)
                eT_1 = time.time() # Ritorna il tempo corrente
                print("prodotto monitoring")

                #Metadati
                sT_2 = time.time() # Ritorna il tempo corrente
                autocorrelation = acf(metric_df['value']) # Autocorrelazione
                aut = autocorrelation.tolist() # Trasformo i valori in una lista
                del aut[0] #Cancelliamo il primo elemento della lista poichè è un numero che non ci serve

                stationarity = adfuller(metric_df['value'],autolag='AIC') #Stazionarietà

                seasonability = seasonal_decompose(metric_df['value'], model='additive', period=10)
                sea = seasonability.seasonal.tolist() # Trasformo i valori in una lista
                eT_2 = time.time() # Ritorna il tempo corrente

                #Predizione
                if item in metric_forecast: # Selezioniamo le metriche di cui fare la predizione
                    sT_3 = time.time() # Ritorna il tempo corrente
                    # Ricampionamento
                    mean_prediction = metric_df['value'].resample(rule='2T').mean()
                    max_prediction = metric_df['value'].resample(rule='2T').max()
                    min_prediction = metric_df['value'].resample(rule='2T').min()
                    # Funzione di predizione
                    tsmodel_mean = ExponentialSmoothing(mean_prediction, trend='add', seasonal='add',seasonal_periods=5).fit() 
                    tsmodel_max = ExponentialSmoothing(max_prediction, trend='add', seasonal='add',seasonal_periods=5).fit()
                    tsmodel_min = ExponentialSmoothing(min_prediction, trend='add', seasonal='add',seasonal_periods=5).fit()

                    # Predizione dei valori
                    pmean = tsmodel_mean.forecast(5)
                    prediction_mean = pmean.to_dict() # trasformo in dizionario
                    for key, value in prediction_mean.items(): # append su lista per problemi al JSON
                        mean.append(str(key))
                        mean.append(str(value))

                    pmax = tsmodel_max.forecast(5)
                    prediction_max = pmax.to_dict() # trasformo in dizionario
                    for key, value in prediction_max.items(): # append su lista per problemi al JSON
                        maxx.append(str(key))
                        maxx.append(str(value))

                    pmin = tsmodel_min.forecast(5)
                    prediction_min = pmin.to_dict() # trasformo in dizionario
                    for key, value in prediction_min.items(): # append su lista per problemi al JSON
                        minn.append(str(key))
                        minn.append(str(value))
                    eT_3 = time.time() # Ritorna il tempo corrente

                else: # setta il valore 0 per metriche di cui non si vuole una predizione
                    sT_3 = 0
                    eT_3 = 0
                    prediction_mean = 0
                    prediction_max = 0
                    prediction_min = 0

                #JSON dei valori di monitoraggio interno
                monitoring_values = {
                    "Generate Metadati":{
                        "Computation Time (s)": round(eT_2-sT_2,4),
                    } ,
                    "Generate Prediction":{
                        "Computation Time (s)": round(eT_3-sT_3,4),
                    }  ,
                    "Generating Metrics":{
                        "Metric Name": item,
                        "Computation Time (s)": round(eT_1-sT_1,4),
                        "Timing": timing
                    } 
                }
                # divisione del monitoraggio per durata temporale
                if (timing == '1h'):
                    monitoring1.append(monitoring_values)
                if (timing == '3h'):
                    monitoring3.append(monitoring_values)
                if (timing == '12h'):
                    monitoring12.append(monitoring_values)

                # JSON dei valori calcolati
                value = {
                    "Metric": {
                        "duration":timing,
                        "max":max_value,
                        "min": min_value,
                        "mean": mean_value,
                        "std": std_value
                    } ,
                    "Metadati":{
                        "duration":timing,
                        "Autocorrelation": json.dumps(aut),
                        "Stazionarietà": json.dumps(stationarity),
                        "Stagionalità": json.dumps(sea)
                    } ,
                    "Predizione" : {
                        "duration":timing,
                        "Prediction_Max": json.dumps(maxx),
                        "Prediction_Min":json.dumps(minn),
                        "Prediction_Mean": json.dumps(mean)
                    }
                }
                val.append(value)
            except:
                continue
            # Producer Kafka
            try:
                record_key = item # nome metrica
                record_value = json.dumps(value) # valori
                p.produce(topic, key=record_key, value=record_value, callback=delivery_callback)
                print("prodotto kafka")
            except BufferError:
                print('%% Local producer queue is full (%d messages awaiting delivery): try again\n' % len(p))
                p.poll(0)
            
            print('%% Waiting for %d deliveries\n' % len(p))
            p.flush()

# Funzione richiamata dal producer
def delivery_callback(err, msg):
    if err:
        print('%% Message failed delivery: %s\n' % err)
    else:
        print('%% Message delivered to %s [%d] @ %d\n' % (msg.topic(), msg.partition(), msg.offset()))

#Funzione per aggiornare la lista delle metriche da predire.
def list_forecastin(list_forecast):
    j = 0
    for i in list_forecast:
        metric_forecast[j] = i
        j += 1

metrics_scraping(broker,topic) # scraping iniziale

# REST API per sistema di monitoraggio interno ed altre funzionalità
app = Flask(__name__)
@app.route('/metrics/1h')
def get_incomes_1():
    return jsonify(monitoring1)

@app.route('/metrics/3h')
def get_incomes_3():
    return jsonify(monitoring3)

@app.route('/metrics/12h')
def get_incomes_12():
    return jsonify(monitoring12)

@app.route('/all_data') # ritorna la lista dei valori calcolati
def get_all_data():
    return val

@app.route('/regen_data') # riproduce la data pipeline
def regen_data():
    metrics_scraping(broker, topic)
    return jsonify("Dati rigenerati")

@app.route('/forecasting', methods = ['POST']) # Permette di modificare le metriche su cui fare la predizione
def forecastin_metric():
    req = request.json # il modello del JSON si trova sotto
    data = json.loads(request.data)
    metric_forecast = data.values()
    list_forecastin(metric_forecast)
    return req

@app.route('/test_forecast') # test di verifica sulle metriche da predire
def forecast_test():
    return jsonify(metric_forecast)

""" 
Esempio di Json per la post su /forecast
{

  "Metrica1":"diskUsage", 
  "Metrica2" : "cpuUsage",
  "Metrica3" : "cpuTemp"
}
"""

    
if __name__ == '__main__':
    app.run(debug = False, host='0.0.0.0', port=5000)




