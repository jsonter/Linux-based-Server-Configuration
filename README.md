# Linux-based-Server-Configuration
Udacity nanodegree project 3. Students will be provided a baseline Ubuntu virtual machine and must prepare that virtual machine to host a web application that has been provided. The virtual machine must be configured to protect against a variety of common attacks and host the web application so that it functions appropriately.

Hints tips and walkthroughs provided by Udacity.com, askubuntu.com, stackoverflow.com Digitalocean.com and code.google.com.

My Steps

1. Create a new user named grader
```
sudo adduser grader
```

2. Give the grader the permission to sudo
```
sudo nano /etc/sudoers.d/grader
grader ALL=(ALL) NOPASSWD:ALL
```

3. Copy authorized keys to new user and set privileges
```
ls /home/grader
mkdir .ssh
cp /root/.ssh/authorized_keys /home/grader/.ssh/
chmod 700 .ssh
chmod 644 .ssh/authorized_keys
chown -R grader .ssh
chgrp -R grader .ssh
```

4. Login with new user
```
ssh -i ~/.ssh/udacity_key.rsa grader@52.88.150.147
```

5. Configure SSH (Change the SSH port from 22 to 2200 & restrict root login)
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

5. Log back in with new port number
```
ssh -i ~/.ssh/udacity_key.rsa grader@52.88.150.147 -p 2200
```

6. Check cannot login as root
```
ssh -i ~/.ssh/udacity_key.rsa grader@52.88.150.147 -p 2200
Permission denied (publickey).
```

7. Update all currently installed packages
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

8. Configure the Uncomplicated Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123)
```
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 2200/tcp
sudo ufw allow 80/tcp
sudo ufw allow 123/tcp
sudo ufw enable
sudo ufw status
```

9. Monitor for repeat unsuccessful login attempts and ban attackers.
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

10. Configure the local timezone to UTC. As discussed at askubuntu.com.
```
sudo dpkg-reconfigure tzdata
```
Choose "None of the above" and then "UTC"

11. Install and configure Apache to serve a Python mod_wsgi application
```
sudo apt-get install apache2
sudo aptitude install libapache2-mod-wsgi
sudo apt-get install libapache2-mod-wsgi python-dev
```

12. Install and configure PostgreSQL (remote connections are disabled by default)
```
sudo apt-get install postgresql
```

13. Install Git
```
sudo apt-get install git

```

14. Clone project source application from git repository
```
cd /var/www
sudo git clone https://github.com/jsonter/Linux-based-Server-Configuration.git
mv Linux-based-Server-Configuration catalog
```

15. Install PIP and required Python packages
```
sudo apt-get install python-pip
sudo pip install flask
sudo pip install httplib2
sudo pip install sqlalchemy
sudo pip install requests
sudo pip install oauth2client
sudo apt-get install python-psycopg2

16. Create database user
```
sudo su - postgres
psql
CREATE USER catalog WITH PASSWORD 'secure password';
GRANT SELECT, INSERT, DELETE, UPDATE ON ALL TABLES IN SCHEMA public TO catalog;
```

17. Configure app
```
sudo cp /var/www/catalog/catalog/catalog.conf /etc/apache2/sites-available
sudo mv /var/www/catalog/catalog/catalog.wsgi /var/www/catalog

```

18. Allow users to upload files (pictures) to static.
```
sudo chmod 777 /var/www/catalog/catalog/static
```

19. Start serving app.
```
sudo a2ensite catalog
sudo service apache2 restart
```

20. Create database and some test data.
```
python /var/www/catalog/catalog/database_setup.py
python /var/www/catalog/catalog/catalogData.py
```
