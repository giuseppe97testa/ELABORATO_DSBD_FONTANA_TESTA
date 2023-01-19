Guida allo start-up dell'applicativo:

Indirizzo prometheus: http://15.160.61.227:29090

nota:
- per sistemi windows based eliminare sudo dai comandi;
- i comandi devono essere lanciati nella cartella in cui sono presenti i vari docker compose;
- i file sono all’interno della cartella fontana_testa.

Passi:
- Avviare Docker o installare Docker
- Tramite terminale creare una network con il comando:-> sudo docker network create monitoring
Per verificare la presenza della network:
-> sudo docker network ls
Per poter funzionare correttamente bisogna avviare due diversi dockercompose.
Andare nella cartella in cui sono presenti i file. E poi:
- Avviare il docker-compose all'interno della cartella KafkaDB tramite comando:
->sudo docker-compose up -d
All'interno di questo docker-compose sono presenti zookeeper, kafka e mysql.
Su un terminale eseguire il comando sudo docker ps. In questo modo
verifichiamo che i container sono attivi.
- Prima di far partire il secondo compose, bisogna creare le tabelle all'interno del
DB. Dunque, eseguire i seguenti comandi:
->sudo docker exec -it ID_CONTAINER_SQL bash (ID_CONTAINER si legge
dal docker ps)
->mysql -u root -p metrics (La password è toor. In questo modo entriamo
già dentro il DB)
Dunque dentro il DB creiamo le varie tabelle con i comandi:
◼ CREATE TABLE metrics ( ID INT AUTO_INCREMENT, metric varchar(255),max DOUBLE, min DOUBLE, mean DOUBLE, dev_std DOUBLE, duration varchar(255) ,PRIMARY KEY (ID));
◼ CREATE TABLE autocorrelation (ID INT AUTO_INCREMENT, metric varchar(255),value DOUBLE, duration varchar(255),PRIMARY KEY(ID));
◼ CREATE TABLE seasonability (ID INT AUTO_INCREMENT, metric varchar(255),value DOUBLE,duration varchar(255), PRIMARY KEY(ID));
◼ CREATE TABLE stationarity (ID INT AUTO_INCREMENT, metric varchar(255),p_value DOUBLE,critical_values varchar(255),duration varchar(255), PRIMARY KEY(ID));
◼ CREATE TABLE prediction_mean (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
◼ CREATE TABLE prediction_min (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
◼ CREATE TABLE prediction_max (ID INT AUTO_INCREMENT, metric varchar(255), timestamp varchar(255), value varchar(255), duration varchar(255),PRIMARY KEY(ID) );
Nel caso qui presente, il topic è già creato nel compose. 
In alternativa si può creare il topic tramite comando sul terminale:
-> sudo docker exec -it kafkdb_kafka_1 kafka-topics --create --replicationfactor 1 --partitions 1 --topic prometheusdata --bootstrap-server localhost:9092.
- Eseguire il docker-compose presente nella cartella principale:
	->docker-compose up -d
In questo modo avviamo tutti i microservizi. È necessario aspettare qualche minuto poiché devono essere scaricati ed installati.
Per poter vedere i vari risultati, aspettare qualche minuto per permettere il processamento dei dati.
-Tramite estensione di google chrome talend api tester, postaman o su qualsiasi applicazione che permette di fare richieste get e post inserire i vari url per
osservare i risultati

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

DATARETRIEVAL 
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



