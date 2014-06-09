###### grafana images
FROM qnib/terminal
MAINTAINER "Christian Kniep <christian@qnib.org>"

##### USER
# Set (very simple) password for root
RUN echo "root:root"|chpasswd
ADD root/ssh /root/.ssh
RUN chmod 600 /root/.ssh/authorized_keys
RUN chmod 600 /root/.ssh/id_rsa
RUN chmod 644 /root/.ssh/id_rsa.pub
RUN chown -R root:root /root/*

### SSHD
RUN yum install -y openssh-server
RUN mkdir -p /var/run/sshd
RUN sshd-keygen
RUN sed -i -e 's/#UseDNS yes/UseDNS no/' /etc/ssh/sshd_config
ADD root/ssh /root/.ssh/
ADD etc/supervisord.d/sshd.ini /etc/supervisord.d/sshd.ini

# We do not care about the known_hosts-file and all the security
####### Highly unsecure... !1!! ###########
RUN echo "        StrictHostKeyChecking no" >> /etc/ssh/ssh_config
RUN echo "        UserKnownHostsFile=/dev/null" >> /etc/ssh/ssh_config
RUN echo "        AddressFamily inet" >> /etc/ssh/ssh_config

### nginx
RUN yum install -y nginx
ADD etc/nginx/nginx.conf /etc/nginx/conf.d/nginx.conf
WORKDIR /etc/nginx/
RUN if ! grep "daemon off" nginx.conf ;then sed -i '/worker_processes.*/a daemon off;' nginx.conf;fi
ADD etc/supervisord.d/nginx.ini /etc/supervisord.d/nginx.ini

# Grafana
WORKDIR /opt
RUN wget http://grafanarel.s3.amazonaws.com/grafana-1.5.4.tar.gz
RUN tar xf grafana-1.5.4.tar.gz
ADD etc/config.js /opt/grafana-1.5.4/
RUN mkdir -p /var/www
RUN ln -s /opt/grafana-1.5.4 /var/www/grafana
ADD opt/grafana-1.5.4/app/dashboards/default.json /opt/grafana-1.5.4/app/dashboards/default.json


CMD /bin/supervisord -c /etc/supervisord.conf
