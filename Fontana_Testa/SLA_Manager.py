from prometheus_api_client import PrometheusConnect, MetricsList, MetricSnapshotDataFrame, MetricRangeDataFrame
from prometheus_api_client.utils import parse_datetime
from flask import Flask, jsonify, request
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from datetime import timedelta
import json
import requests

metric_names = [] # Lista contenente le metriche definite per la predizione
metric_ranges = [] # Lista contenente i range di valori ammissibili per le metriche da predire
violations = [] # Lista contenente le violazioni dell'SLA status
sla_prediction = [] # Lista contenete possibili violazioni future

def metric_scraping():
    violations.clear() # pulitura della lista
    sla_prediction.clear() # pulitura della lista
    prom = PrometheusConnect(url="http://15.160.61.227:29090", disable_ssl=True)
    end_time = parse_datetime("now")
    chunk_size = timedelta(minutes=20)
    label_config = {'job': 'summary', 'instance': '106'}
    all_data_time = ['1h','3h','12h']
    
    for timing in all_data_time:
        count = 0
        start_time = parse_datetime(timing)
        for item in metric_names:
                try:
                    metric_data = prom.get_metric_range_data(
                        metric_name=item,
                        label_config=label_config,
                        start_time=start_time,
                        end_time=end_time,
                        chunk_size=chunk_size,
                    )
                    metric_df = MetricRangeDataFrame(metric_data) # Creazione della data frame
                    range_violation(metric_df,timing, count)
                    future_violations(metric_df,count)
                    count +=1
                except:
                    continue

def future_violations(metrics,count): # Funzione che controlla possibili violazioni future di 10 minuti
    resample = metrics['value'].resample(rule='1T').mean()
    prediction = ExponentialSmoothing(resample, trend='add', seasonal='add', seasonal_periods=10).fit()
    pred = prediction.forecast(steps=10)
    prediction_list = list(pred)
    for i in range(len(prediction_list)):
        if prediction_list[i] < metric_ranges[count][0] or prediction_list[i] > metric_ranges[count][1]:
            #print("VIOLAZIONE NEI 10 minuti: ", pred.keys()[i], "VALORE: ", prediction_list[i])
            violation = {
                "Metrica": metrics['__name__'][i],
                "Timestamp": pred.keys()[i],
                "Valore": prediction_list[i],
            }
            sla_prediction.append(violation)

def range_violation(metrics, duration,count): # Funzione che controlla se avvengono delle violazioni
    for i in range(len(metrics)):
        if metrics['value'][i] < metric_ranges[count][0] or metrics['value'][i] > metric_ranges[count][1]:
            #print("VIOLAZIONE A:", metrics['value'].keys()[i], "VALORE: ", metrics['value'][i],
                  #"METRICA: ", metrics['__name__'][i], "Duration:",duration)
            violation = {
                "Metrica": metrics['__name__'][i],
                "Timestamp": metrics['value'].keys()[i],
                "Valore": metrics['value'][i],
                "Duration": duration
            }
            violations.append(violation)

def post_to_ETL(metric_name): # funzione che effettua post su ETL_DataPipeline.py per modificare il set di metrica da predire
    url = 'http://etl_data_pipeline:5000/forecasting'
    if len(metric_names) > 0:
        metric_names.clear() # pulisce la lista
    for i in metric_name:
        metric_names.append(i)
    metric = { # JSON per post
              "Metrica1" : metric_names[0], 
              "Metrica2" : metric_names[1],
              "Metrica3" : metric_names[2],
              "Metrica4": metric_names[3],
              "Metrica5": metric_names[4],
              }
    x = requests.post(url, json = metric)
    print(x.text)

def list_range_metric(metric_range): # Funzione che riempie la lista dei range
    for i in metric_range:
        metric_ranges.append(i)
        #print(i)
    return

app = Flask(__name__)
@app.route('/SLA', methods = ['POST'])
def forecastin_metric(): # Post per modificare l'SLA set ed i rispettivi range ammessi
    req = request.json
    data = json.loads(request.data)
    metric = list(data.keys())
    metric_range = list(data.values())
    post_to_ETL(metric)
    list_range_metric(metric_range)
    return req

@app.route('/assess_Violations')
def assess_Violations(): # Get per verificare se ci siano violazioni nei dati generati
    metric_scraping()
    return jsonify(violations)

@app.route('/get_Violations') # Get che ritorna le violazioni
def get_Violations():
    return jsonify(violations)

@app.route('/get_Violations_Num') # Get che ritorna il numero di violazioni suddivise per tempistiche
def violation_Num():
    tre = 0
    una = 0
    dodici = 0
    for item in violations:
        if item['Duration'] == '1h':
            una += 1
        if item['Duration'] == '3h':
            tre += 1
        if item['Duration'] == '12h':
            una += 1
    vlt = {
        "Violazioni in un'ora":una,
        "Violazioni in tre ore:":tre,
        "Violazioni in dodici ore:": dodici
    }
    return jsonify(vlt)

@app.route('/get_SLA_status') # Get che ritorna il numero di violazioni suddivise per tempistiche e nome metrica
def sla_Status():
    sla_status = []
    for nome in metric_names:
        tre = 0
        una = 0
        dodici = 0
        for item in violations:
            if item['Duration'] == '1h' and item['Metrica'] == nome:
                una += 1
            if item['Duration'] == '3h'and item['Metrica'] == nome:
                tre += 1
            if item['Duration'] == '12h'and item['Metrica'] == nome:
                dodici += 1
        vlt = {
            "Metric": nome,
            "Violazioni in un'ora": una,
            "Violazioni in tre ore:": tre,
            "Violazioni in dodici ore:": dodici
        }
        sla_status.append(vlt)
    return jsonify(sla_status)

@app.route('/get_SLA_pred') # Get che mostra le violazioni previste
def get_Predictions():
    return jsonify(sla_prediction)

@app.route('/get_SLA_pred_status') # Get che mostra le violazioni previste suddivise per nome metrica
def sla_Prediction_Status():
    sla_status = []
    for nome in metric_names:
        num = 0
        for item in sla_prediction:
            if item['Metrica'] == nome:
                num += 1
        vlt = {
            "Metric": nome,
            "Violazioni possibili in 10 minuti": num,
        }
        sla_status.append(vlt)
    return jsonify(sla_status)

"""
Formattazione del messaggio json per la richiesta post
{
  "availableMem": [0, 90.44], 
  "cpuLoad"     : [0, 10.00],
  "cpuTemp"     : [0, 44.00], 
  "diskUsage"   : [0, 2.9487],
  "realUsedMem" : [0, 9.62]
"""
if __name__ == '__main__':
    app.run(debug = False, host='0.0.0.0', port=5002)
