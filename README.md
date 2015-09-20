# Linux-based-Server-Configuration
Udacity nanodegree project 3. Students will be provided a baseline Ubuntu virtual machine and must prepare that virtual machine to host a web application that has been provided. The virtual machine must be configured to protect against a variety of common attacks and host the web application so that it functions appropriately.

IP Address: http://52.88.150.147/
SSH: ssh -i ~/.ssh/udacity_key.rsa grader@52.88.150.147 -p 2200

Hints tips and walkthroughs provided by Udacity.com, askubuntu.com, stackoverflow.com Digitalocean.com and code.google.com.

My Steps

* Create a new user named grader
```
sudo adduser grader
```

* Give the grader the permission to sudo
```
sudo nano /etc/sudoers.d/grader
grader ALL=(ALL) NOPASSWD:ALL
```

* Copy authorized keys to new user and set privileges
```
ls /home/grader
mkdir .ssh
cp /root/.ssh/authorized_keys /home/grader/.ssh/
chmod 700 .ssh
chmod 644 .ssh/authorized_keys
chown -R grader .ssh
chgrp -R grader .ssh
```

* Login with new user
```
ssh -i ~/.ssh/udacity_key.rsa grader@52.88.150.147
```

* Configure SSH (Change the SSH port from 22 to 2200 & restrict root login)
```
nano /etc/ssh/sshd_config
```
Modified lines:
```
Port 2200
PermitRootLogin no
```
Then restart ssh
```
sudo reload ssh
```

* Log back in with new port number
```
ssh -i ~/.ssh/udacity_key.rsa grader@52.88.150.147 -p 2200
```

* Check cannot login as root
```
ssh -i ~/.ssh/udacity_key.rsa grader@52.88.150.147 -p 2200
Permission denied (publickey).
```

* Update all currently installed packages
```
sudo apt-get update
sudo apt-get upgrade
```
If
```
*** System restart required ***
```
Then
```
sudo reboot
```

* Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123)
```
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 2200/tcp
sudo ufw allow 80/tcp
sudo ufw allow 123/tcp
sudo ufw enable
sudo ufw status
```

* Monitor for repeat unsuccessful login attempts and ban attackers.
Documented at Digitalocean.com - "Protect SSH with fail2ban"
```
sudo apt-get install fail2ban
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```
Change the ssh port number line
```
port     = 2200
```
Restart fail2ban
```
sudo service fail2ban restart
```

* Configure the local timezone to UTC. As discussed at askubuntu.com.
```
sudo dpkg-reconfigure tzdata
```
Choose "None of the above" and then "UTC"

* Install and configure Apache to serve a Python mod_wsgi application
```
sudo apt-get install apache2
sudo aptitude install libapache2-mod-wsgi
sudo apt-get install libapache2-mod-wsgi python-dev
```

* Install and configure PostgreSQL (remote connections are disabled by default)
```
sudo apt-get install postgresql
```

* Install Git
```
sudo apt-get install git

```

* Clone project source application from git repository
```
cd /var/www
sudo git clone https://github.com/jsonter/Linux-based-Server-Configuration.git
mv Linux-based-Server-Configuration catalog
```

* Install PIP and required Python packages
```
sudo apt-get install python-pip
sudo pip install flask
sudo pip install httplib2
sudo pip install sqlalchemy
sudo pip install requests
sudo pip install oauth2client
sudo apt-get install python-psycopg2
```

* Create database user
```
sudo su - postgres
psql
CREATE USER catalog WITH PASSWORD 'secure password';
GRANT SELECT, INSERT, DELETE, UPDATE ON ALL TABLES IN SCHEMA public TO catalog;
```

* Configure app
```
sudo cp /var/www/catalog/catalog/catalog.conf /etc/apache2/sites-available
sudo mv /var/www/catalog/catalog/catalog.wsgi /var/www/catalog

```

* Allow users to upload files (pictures) to static.
```
sudo chmod 777 /var/www/catalog/catalog/static
```

* Start serving app.
```
sudo a2ensite catalog
sudo service apache2 restart
```

* Create database and some test data.
```
python /var/www/catalog/catalog/database_setup.py
python /var/www/catalog/catalog/catalogData.py
```

* Get Google and Facebook Logins working on remote host.
Google
```
In Google Developers Console for the project:
Add http://52.88.150.147 to Authorized JavaScript origins.
Re-download client_secrets.json and then up to server.
```
Facebook
```
In Facebook Developers Advanced Setting for project:
Add http://52.88.150.147 to "Valid OAuth redirect URIs"
```

* Restrict access to .git folder
```
cd /var/www/catalog
sudo nano .htaccess
RedirectMatch 404 /\.git
```
This from http://stackoverflow.com/questions/6142437/make-git-directory-web-inaccessible

* Automatic Ubuntu server package updates
```
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
(Answer yes to question)
```
