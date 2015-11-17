# -*- coding: utf-8 -*-

import logging
import logging.config


def getLogger(config, name, suffix=''):
    logFile = config.get('Logging', 'logfile')
    logging.config.fileConfig('logging.cfg', defaults=dict(
        logfile=logFile % dict(timestamp=suffix)
    ))
    return logging.getLogger(name)
