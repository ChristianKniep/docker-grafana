###### grafana images
FROM qnib/terminal:light
MAINTAINER "Christian Kniep <christian@qnib.org>"

### nginx
RUN yum install -y nginx
ADD etc/nginx/nginx.conf /etc/nginx/nginx.conf
ADD etc/nginx/conf.d/grafana.conf /etc/nginx/conf.d/
ADD etc/supervisord.d/nginx.ini /etc/supervisord.d/nginx.ini

# Grafana
WORKDIR /opt
RUN wget -q -O /tmp/grafana-1.9.1.tar.gz  http://grafanarel.s3.amazonaws.com/grafana-1.9.1.tar.gz && \
    cd /opt/ && tar xf /tmp/grafana-1.9.1.tar.gz && rm -f /tmp/grafana-1.9.1.tar.gz
ADD etc/config.1.9.1.js /opt/grafana-1.9.1/config.js
RUN mkdir -p /var/www
RUN ln -s /opt/grafana-1.9.1 /var/www/grafana
ADD var/www/grafana/app/dashboards/ /var/www/grafana/app/dashboards/

ADD etc/consul.d/ /etc/consul.d/

ADD etc/supervisord.d/dash.ini /etc/supervisord.d/
ADD opt/qnib/grafana/bin/dashboard.py /opt/qnib/grafana/bin/
ADD opt/qnib/grafana/templates/ /opt/qnib/grafana/templates/
