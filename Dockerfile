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
ADD grafana-1.9.1.tar.gz /opt/
ADD etc/config.1.9.1.js /opt/grafana-1.9.1/config.js
RUN mkdir -p /var/www
RUN ln -s /opt/grafana-1.9.1 /var/www/grafana
ADD opt/grafana-1.9.1/app/dashboards/ /opt/grafana-1.9.1/app/dashboards/

ADD etc/consul.d/ /etc/consul.d/
