# bash apps/fabric/test/test.sh

rm -rf sharedata

rm -rf apps/fabric/log/server/
mkdir apps/fabric/log/server/

pkill -f test_server

ps -ax

python3 apps/fabric/test/test_server.py 0 &> apps/fabric/log/server/log_0.txt &
python3 apps/fabric/test/test_server.py 1 &> apps/fabric/log/server/log_1.txt &
python3 apps/fabric/test/test_server.py 2 &> apps/fabric/log/server/log_2.txt &
python3 apps/fabric/test/test_server.py 3 &> apps/fabric/log/server/log_3.txt &