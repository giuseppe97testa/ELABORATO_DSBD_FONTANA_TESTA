Guida allo start-up dell'applicativo:

Indirizzo prometheus: http://15.160.61.227:29090

nota: -per sistemi windows based eliminare sudo dai comandi
	-i comandi devono essere lanciati nella cartella in cui è presente il docker-compose
	- i file sono all’interno della cartella fontana_testa.

1.Avviare Docker o installare Docker
2.Tramite terminale creare una network con il comando:
->sudo docker network create monitoring
Per poter funzionare correttamente bisogna avviare due diversi docker-compose. 
3.Avviare il docker-compose all'interno della cartella KafkaDB tramite comando:
->sudo docker-compose up -d 
All'interno di questo docker-compose sono presenti zookeeper, kafka e mysql.
4.Su un terminale eseguire il comando docker ps. In questo modo verifichiamo che i container sono attivi.
5.Prima di far partire il secondo compose, bisogna creare le tabelle all'interno del DB. Dunque eseguire i seguenti comandi:
->sudo docker exec -it ID_CONTAINER bash (ID_CONTAINER si legge dal docker ps)
->mysql -u root -p metrics (In questo modo entriamo già dentro il DB)
->CREATE TABLE metrics ( ID INT AUTO_INCREMENT, metric varchar(255),max DOUBLE, min DOUBLE, mean DOUBLE, dev_std DOUBLE, duration varchar(255) ,PRIMARY KEY (ID));
CREATE TABLE autocorrelation (ID INT AUTO_INCREMENT, metric varchar(255),value DOUBLE, duration varchar(255),PRIMARY KEY(ID));
CREATE TABLE seasonability (ID INT AUTO_INCREMENT, metric varchar(255),value DOUBLE,duration varchar(255), PRIMARY KEY(ID));
CREATE TABLE stationarity (ID INT AUTO_INCREMENT, metric varchar(255),p_value DOUBLE,critical_values varchar(255),duration varchar(255), PRIMARY KEY(ID));
CREATE TABLE prediction_mean (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
CREATE TABLE prediction_min (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
CREATE TABLE prediction_max (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
In questo modo abbiamo creato le metriche.
6.Eseguire il docker-compose presente nella cartella principale:
->docker-compose up -d
In questo modo avviamo tutti i microservizi.
Per poter vedere i vari risultati, aspettare qualche minuto per permettere il processamento dei dati. 
7.Su postman o su qualsiasi applicazione che permette di fare richieste get e post inserire i vari url per osservare i risultati. 

Elenco_Metriche:
- availableMem
- cpuLoad
- cpuTemp
- diskUsage
- inodeUsage
- networkThroughput
- push_time_seconds
- realUsedMem

Query:
ETL
GET -> http://localhost:5000/metrics/1h
GET -> http://localhost:5000/metrics/3h 
GET -> http://localhost:5000/metrics/12h
GET -> http://localhost:5000/regen_data
POST -> http://localhost:5000/forecasting

DataRetrieval 

GET: http://localhost:5005/metrics/metric/<nome_della_metrica>
GET: http://localhost:5005/metrics/metadati/<nome_della_metrica>
GET: http://localhost:5005/metrics/forecasting/<nome_della_metrica>
GET: http://localhost:5005/metrics

SLA
POST: http://localhost:5002/SLA
GET: http://localhost:5002/assess_Violations
NOTA: Avviare prima le prime due e poi le altre
GET: http://localhost:5002/get_Violations
GET: http://localhost:5002/get_Violations_Num
GET: http://localhost:5002/get_SLA_status
GET: http://localhost:5002/get_SLA_pred
GET: http://localhost:5002/get_SLA_pred_status




