[loggers]
keys=root,forge

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=DEBUG
handlers=consoleHandler,fileHandler

[logger_forge]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=forge
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=simpleFormatter
args=('%(logfile)s',)

[formatter_simpleFormatter]
format=%(asctime)s | %(name)-32s | %(levelname)-8s | %(message)s
datefmt=

[Logging]
logfile: ${logfilefolder}forge_%(timestamp)s.log
