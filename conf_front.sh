#!/bin/bash
sudo apt install apache2
sudo chmod -R 777 /var/www
sudo chown -R ubuntu /var/www/html
cd /home/ubuntu/Cloud-projects/
cp -R frontend/* /var/www/html/frontend
