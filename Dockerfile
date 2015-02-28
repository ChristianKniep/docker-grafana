###### grafana images
FROM qnib/terminal
MAINTAINER "Christian Kniep <christian@qnib.org>"

### nginx
RUN yum install -y nginx
ADD etc/nginx/nginx.conf /etc/nginx/nginx.conf
ADD etc/nginx/conf.d/grafana.conf /etc/nginx/conf.d/
ADD etc/supervisord.d/nginx.ini /etc/supervisord.d/nginx.ini

# Grafana
WORKDIR /opt
#ADD grafana-1.9.1.tar.gz /opt/
ADD https://github.com/influxdb/grafana/archive/influx-0.9rc4.zip /opt/
RUN unzip influx-0.9rc4.zip && ln -s /opt/grafana-influx-0.9rc4 /var/www/grafana/
ADD etc/config.1.9.1.js /var/www/grafana/config.js
RUN mkdir -p /var/www
ADD opt/grafana-1.9.1/app/dashboards/ /var/www/grafana/app/dashboards/

ADD etc/consul.d/ /etc/consul.d/
