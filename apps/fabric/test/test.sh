# bash apps/fabric/test/test.sh

rm apps/fabric/log/server/log_0.txt
rm apps/fabric/log/server/log_1.txt
rm apps/fabric/log/server/log_2.txt
rm apps/fabric/log/server/log_3.txt

pkill -f test_server

python3 apps/fabric/test/test_server.py 0 > apps/fabric/log/server/log_0.txt 2>&1 &
python3 apps/fabric/test/test_server.py 1 > apps/fabric/log/server/log_1.txt 2>&1 &
python3 apps/fabric/test/test_server.py 2 > apps/fabric/log/server/log_2.txt 2>&1 &
python3 apps/fabric/test/test_server.py 3 > apps/fabric/log/server/log_3.txt 2>&1 &

#sleep 20
#
#python3 apps/fabric/test/test_cmp.py
#python3 apps/fabric/test/test_mul.py
#python3 apps/fabric/test/test_recon.py