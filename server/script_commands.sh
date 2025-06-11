sudo apt update && sudo apt upgrade -y

sudo apt install mysql-server -y

sudo mysql_secure_installation

sudo mysql -u root -p

CREATE DATABASE time_capsule;

##grant access and create a user for the project
CREATE USER 'TC_proj'@'localhost' IDENTIFIED BY '2201';
GRANT ALL PRIVILEGES ON time_capsule.* TO 'TC_proj'@'localhost';
FLUSH PRIVILEGES;

##exit sql
EXIT;

