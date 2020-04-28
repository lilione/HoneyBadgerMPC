kill $(lsof -ti:8080,8081,8082,8083)

python3 apps/fabric/start_server.py 0 &> apps/fabric/test/log/log_0.txt &
python3 apps/fabric/start_server.py 1 &> apps/fabric/test/log/log_1.txt &
python3 apps/fabric/start_server.py 2 &> apps/fabric/test/log/log_2.txt &
python3 apps/fabric/start_server.py 3 &> apps/fabric/test/log/log_3.txt &

sleep 2

python3 apps/fabric/run_client.py