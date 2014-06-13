###### grafana images
FROM qnib/terminal
MAINTAINER "Christian Kniep <christian@qnib.org>"

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
ADD grafana-1.5.4.tar.gz /opt/
ADD etc/config.sample.js /opt/grafana-1.5.4/
RUN mkdir -p /var/www
RUN ln -s /opt/grafana-1.5.4 /var/www/grafana
ADD opt/grafana-1.5.4/app/dashboards/default.json /opt/grafana-1.5.4/app/dashboards/default.json


CMD /bin/supervisord -c /etc/supervisord.conf
