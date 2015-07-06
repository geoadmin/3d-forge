# -*- coding: utf-8 -*-

import logging
import logging.config


def getLogger(config, name, suffix=''):
    configFile = config.get('Logging', 'config')
    logFile = config.get('Logging', 'logfile')
    sqlLogFile = config.get('Logging', 'sqlLogfile')
    logging.config.fileConfig(configFile, defaults=dict(
        logfile='%s_%s' % (logFile, suffix),
        sqlLogFile='%s_%s' % (sqlLogFile, suffix)
    ))
    return logging.getLogger(name)
