# -*- coding: utf-8 -*-

import logging
import logging.config


def getLogger(config, name, suffix=''):
    configFile = config.get('Logging', 'config')
    logFile = config.get('Logging', 'logfile')
    sqlLogFile = config.get('Logging', 'sqlLogfile')
    logging.config.fileConfig(configFile, defaults=dict(
        logfile=logFile % dict(timestamp=suffix),
        sqlLogFile=sqlLogFile % dict(timestamp=suffix)
    ))
    return logging.getLogger(name)
