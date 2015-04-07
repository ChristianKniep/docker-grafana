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
ADD var/www/grafana/app/dashboards/ /var/www/grafana/app/dashboards/

ADD etc/consul.d/ /etc/consul.d/

# docopt
RUN yum install -y python-pip libyaml-devel python-devel
RUN pip install neo4jrestclient pyyaml docopt python-consul jinja2

ADD etc/supervisord.d/slurmdash.ini /etc/supervisord.d/slurmdash.ini
ADD opt/qnib/grafana/bin/slurm_dashboard.py /opt/qnib/grafana/bin/
ADD opt/qnib/grafana/templates/ /opt/qnib/grafana/templates/
