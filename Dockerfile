###### grafana images
FROM qnib/terminal

### nginx
RUN dnf install -y nginx
ADD etc/nginx/nginx.conf /etc/nginx/nginx.conf
ADD etc/nginx/conf.d/grafana.conf /etc/nginx/conf.d/
ADD etc/supervisord.d/nginx.ini /etc/supervisord.d/nginx.ini

# Grafana
RUN mkdir -p /var/www/ && \
    curl -fsL http://grafanarel.s3.amazonaws.com/grafana-1.9.1.tar.gz | tar xfz - -C /var/www/ && \
    mv /var/www/grafana-1.9.1 /var/www/grafana
ADD etc/config.1.9.1.js /var/www/grafana/config.js
ADD var/www/grafana/app/dashboards/ /var/www/grafana/app/dashboards/

ADD etc/consul.d/ /etc/consul.d/

ADD etc/supervisord.d/dashboard.ini /etc/supervisord.d/
ADD opt/qnib/grafana/bin/dashboard.py /opt/qnib/grafana/bin/
ADD opt/qnib/grafana/templates/ /opt/qnib/grafana/templates/
