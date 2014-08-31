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
ADD grafana-1.7.0.tar.gz /opt/
ADD etc/config.sample.js /opt/grafana-1.7.0/config.js
RUN mkdir -p /var/www
RUN ln -s /opt/grafana-1.7.0 /var/www/grafana
ADD dashboards.tar /var/www/grafana/app/dashboards/


CMD /bin/supervisord -c /etc/supervisord.conf
