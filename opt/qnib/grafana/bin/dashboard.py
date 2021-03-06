#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""

Usage:
    dashboard.py [options]
    dashboard.py (-h | --help)
    dashboard.py --version

Options:
    --slurmjob-template <path>  Slurm job dashboard template.
                                [default: /opt/qnib/grafana/templates/slurm_job.j2]
    --slurm-template <path>     Slurm Dashbard.
                                [default: /opt/qnib/grafana/templates/slurm.j2]
    --delay <int>           Seconds delay inbetween loop runs [default: 10]
    --server                    If set loops over fetching information.
    -h --help                   Show this screen.
    --version                   Show version.
    --loglevel, -L=<str>        Loglevel [default: INFO]
                                (ERROR, CRITICAL, WARN, INFO, DEBUG)
    --log2stdout, -l            Log to stdout, otherwise to logfile. [default: False]
    --logfile, -f=<path>        Logfile to log to (default: <scriptname>.log)
    --cfg, -c=<path>            Configuration file.

"""

# load librarys
import logging
import os
import re
import codecs
import math
import ast
import sys
from datetime import datetime
from ConfigParser import RawConfigParser, NoOptionError
import time
import consul
from jinja2 import Template

try:
    from docopt import docopt
except ImportError:
    HAVE_DOCOPT = False
else:
    HAVE_DOCOPT = True

__author__ = 'Christian Kniep <christian()qnib.org>'
__copyright__ = 'Copyright 2015 QNIB Solutions'
__license__ = """GPL v2 License (http://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)"""


class QnibConfig(RawConfigParser):
    """ Class to abstract config and options
    """
    specials = {
        'TRUE': True,
        'FALSE': False,
        'NONE': None,
    }

    def __init__(self, opt):
        """ init """
        RawConfigParser.__init__(self)
        if opt is None:
            self._opt = {
                "--log2stdout": False,
                "--logfile": None,
                "--loglevel": "ERROR",
            }
        else:
            self._opt = opt
            self.logformat = '%(asctime)-15s %(levelname)-5s [%(module)s] %(message)s'
            self.loglevel = opt.get('--loglevel')
            self.log2stdout = opt['--log2stdout']
            if self.loglevel is None and opt.get('--cfg') is None:
                print "please specify loglevel (-L)"
                sys.exit(0)
            self.eval_cfg()

        self.eval_opt()
        self.set_logging()
        logging.info("SetUp of QnibConfig is done...")


    def do_get(self, section, key, default=None):
        """ Also lent from: https://github.com/jpmens/mqttwarn
            """
        try:
            val = self.get(section, key)
            if val.upper() in self.specials:
                return self.specials[val.upper()]
            return ast.literal_eval(val)
        except NoOptionError:
            return default
        except ValueError:  # e.g. %(xxx)s in string
            return val
        except:
            raise
            return val


    def config(self, section):
        ''' Convert a whole section's options (except the options specified
                explicitly below) into a dict, turning

                    [config:mqtt]
                    host = 'localhost'
                    username = None
                    list = [1, 'aaa', 'bbb', 4]

                into

                    {u'username': None, u'host': 'localhost', u'list': [1, 'aaa', 'bbb', 4]}

                Cannot use config.items() because I want each value to be
                retrieved with g() as above
            SOURCE: https://github.com/jpmens/mqttwarn
            '''

        d = None
        if self.has_section(section):
            d = dict((key, self.do_get(section, key))
                     for (key) in self.options(section) if key not in ['targets'])
        return d


    def eval_cfg(self):
        """ eval configuration which overrules the defaults
            """
        cfg_file = self._opt.get('--cfg')
        if cfg_file is not None:
            fd = codecs.open(cfg_file, 'r', encoding='utf-8')
            self.readfp(fd)
            fd.close()
            self.__dict__.update(self.config('defaults'))


    def eval_opt(self):
        """ Updates cfg according to options """

        def handle_logfile(val):
            """ transforms logfile argument
                """
            if val is None:
                logf = os.path.splitext(os.path.basename(__file__))[0]
                self.logfile = "%s.log" % logf.lower()
            else:
                self.logfile = val

        self._mapping = {
            '--logfile': lambda val: handle_logfile(val),
        }
        for key, val in self._opt.items():
            if key in self._mapping:
                if isinstance(self._mapping[key], str):
                    self.__dict__[self._mapping[key]] = val
                else:
                    self._mapping[key](val)
                break
            else:
                if val is None:
                    continue
                mat = re.match("\-\-(.*)", key)
                if mat:
                    self.__dict__[mat.group(1)] = val
                else:
                    logging.info("Could not find opt<>cfg mapping for '%s'" % key)


    def set_logging(self):
        """ sets the logging """
        self._logger = logging.getLogger()
        self._logger.setLevel(logging.DEBUG)
        if self.log2stdout:
            hdl = logging.StreamHandler()
            hdl.setLevel(self.loglevel)
            formatter = logging.Formatter(self.logformat)
            hdl.setFormatter(formatter)
            self._logger.addHandler(hdl)
        else:
            hdl = logging.FileHandler(self.logfile)
            hdl.setLevel(self.loglevel)
            formatter = logging.Formatter(self.logformat)
            hdl.setFormatter(formatter)
            self._logger.addHandler(hdl)


    def __str__(self):
        """ print human readble """
        ret = []
        for key, val in self.__dict__.items():
            if not re.match("_.*", key):
                ret.append("%-15s: %s" % (key, val))
        return "\n".join(ret)

    def __getitem__(self, item):
        """ return item from opt or __dict__
        :param item: key to lookup
        :return: value of key
        """
        if item in self.__dict__.keys():
            return self.__dict__[item]
        else:
            return self._opt[item]


class SlurmDash(object):
    """ Class to hold the functioanlity of the script
    """

    def __init__(self, cfg):
        """ Init of instance
        """
        self._cfg = cfg
        self._consul = consul.Consul(host='consul.service.consul')
        self._template = {}
        self._last_idx = None
        self._last_run = time.time()
        self._target = {
            'slurmjob': '/var/www/grafana/app/dashboards/slurm_%(jobid)s.json',
            'slurm': '/var/www/grafana/app/dashboards/slurm.json',
        }
        with open(cfg['--slurmjob-template'], "r") as fd:
            self._template['slurmjob'] = Template(fd.read())
        with open(cfg['--slurm-template'], "r") as fd:
            self._template['slurm'] = Template(fd.read())

    def run(self):
        """ do the hard work
        """
        if self._cfg['--server']:
            self.loop()
        else:
            self.fetch_info()

    def loop(self):
        """ loops over changes in kv key
        """
        while True:
            logging.debug("wait for index '%s'" % self._last_idx)
            try:
                self._last_idx, val = self._consul.kv.get('slurm/job/', wait='30s', index=self._last_idx)
            except KeyboardInterrupt:
                logging.info("Gracefully exit after CTRL-C")
                self.close()
                break
            self.fetch_info()
            now = time.time()
            since = now - self._last_run
            delay = max(0, int(self._cfg['--delay']) - since)
            self._cfg._logger.info("Took: %ssec, sleep for %ssec" % (since, delay))
            self._last_run = now
            time.sleep(delay)
            logging.debug("Got index '%s'" % self._last_idx)

    def close(self):
        """  exists
        """
        pass

    def fetch_info(self):
        """ fetches info from K/V store
        """
        idx, values = self._consul.kv.get('slurm/job/', recurse=True)
        jobs = {}
        if values is None:
            return
        dt_end = None
        dt_start = None
        dt_diff = {}
        def diff_time(start, end):
            dt_diff = {}
            return math.floor(((end-start).seconds) / 60)
            #dt_diff['day'] = divmod(dt_end-dt_start,86400)  # days
            #dt_diff['hour'] = divmod(dt_diff['day'][1],3600)  # hours
            #dt_diff['min'] = divmod(dt_diff['hour'][1],60)  # minutes
            #dt_diff['sec'] = divmod(dt_diff['min'][1],60)  # minutes
            #return dt_diff

        for value in values:
            jobid, key = value['Key'].split("/")[2:]
            jobid = int(jobid)
            val = value['Value']
            key = key.lower()
            if jobid not in jobs.keys():
                jobs[jobid] = {}
            if key == 'nodelist':
                jobs[jobid][key] = val.split(",")
            elif key == "start":
                dt_start = datetime.fromtimestamp(int(val))
                jobs[jobid]['start_grafana'] = dt_start.strftime("%FT%H:%M:%S.%fZ")
                jobs[jobid]['start_human'] = dt_start.strftime("%F %H:%M:%S")
                if dt_end:
                    jobs[jobid]['duration'] = diff_time(dt_start, dt_end)
            elif key == 'end':
                dt_end = datetime.fromtimestamp(int(val))
                if dt_start:
                    jobs[jobid]['duration'] = diff_time(dt_start, dt_end)
                jobs[jobid]['end_human'] = dt_end.strftime("%H:%M:%S")
            else:
                jobs[jobid][key] = val

        # Overview board

        running_jobs = []
        finished_jobs = []
        for jobid, job in jobs.items():
            job['jobid'] = jobid
            if 'end_human' in job.keys():
                try:
                    payload = (jobid, job['jobname'], job['user'], job['start_human'], job['duration'], job['derived_ec'])
                except KeyError:
                    if 'derived_ec' not in job.keys():
                        self._cfg._logger.warn("Jobid '%(jobid)s' has no 'derived_ec'!?" % job)
                        payload = (jobid, job['jobname'], job['user'], job['start_human'], job['duration'], "?")
                    else:
                        self._cfg._logger.error("Jobid '%s' has something missing... %s!?" % (job['jobid'], ",".join(job.keys())))
                        payload = (jobid, "?", "?", "?", "?", "?")
                finished_jobs.append(payload)
            else:
                try:
                    payload = (jobid, job['jobname'], job['user'], job['start_human'])
                except KeyError:
                    if 'jobname' not in job.keys():
                        self._cfg._logger.warn("Jobid '%(jobid)s' has no 'jobname" % job)
                        payload = (jobid, "?", job['user'], job['start_human'])
                    else:
                        self._cfg._logger.error("Jobid '%s' has something missing... %s!?" % (job['jobid'], ",".join(job.keys())))
                        payload = (jobid, "?", "?", "?")
                running_jobs.append(payload)
            if os.path.exists('/var/www/grafana/app/dashboards/slurm_%s.json' % jobid):
                logging.debug("Dashboard for jobid '%(jobid)s' / '%(jobname)s' already existing" % job)
                continue
            logging.info("Create Dashboard for job %(jobid)s '%(jobname)s'" % job)
            out = self._template['slurmjob'].render(**job)
            with open(self._target['slurmjob'] % job, "w") as fd:
                fd.write(out)

        out = self._template['slurm'].render({'running': sorted(running_jobs),
                                              'finished': reversed(sorted(finished_jobs)[-5:])})
        with open(self._target['slurm'], "w") as fd:
            fd.write(out)


def main():
    """ main function """
    options = None
    if HAVE_DOCOPT:
        options = docopt(__doc__, version='Test Script 0.1')
    qcfg = QnibConfig(options)
    slurmd = SlurmDash(qcfg)
    slurmd.run()


if __name__ == "__main__":
    main()
