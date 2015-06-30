# -*- coding: utf-8 -*-

import logging
import logging.config
import ConfigParser
import sqlalchemy
from sqlalchemy.exc import ProgrammingError
from contextlib import contextmanager


class DB:

    class Server:

        def __init__(self, config):
            self.logger = logging.getLogger('forge.DB.Server')
            self.host = config.get('Server', 'host')
            self.port = config.getint('Server', 'port')

    class Admin:

        def __init__(self, config):
            self.logger = logging.getLogger('forge.DB.Admin')
            self.user = config.get('Admin', 'user')
            self.password = config.get('Admin', 'password')

    class Database:

        def __init__(self, config):
            self.logger = logging.getLogger('forge.DB.Database')
            self.name = config.get('Database', 'name')
            self.user = config.get('Database', 'user')
            self.password = config.get('Database', 'password')

    class Logging:

        def __init__(self, config):
            self.configFile = config.get('Logging', 'config')
            self.logFile = config.get('Logging', 'logfile')
            self.sqlLogFile = config.get('Logging', 'sqlLogfile')
            logging.config.fileConfig(self.configFile, defaults=dict(
                logfile=self.logFile,
                sqlLogFile=self.sqlLogFile
            ))
            self.logger = logging.getLogger('forge.DB.Logging')

    def __init__(self, configFile):
        config = ConfigParser.RawConfigParser()
        config.read(configFile)

        self.loggingConf = DB.Logging(config)
        self.serverConf = DB.Server(config)
        self.adminConf = DB.Admin(config)
        self.databaseConf = DB.Database(config)

        self.logger = logging.getLogger('forge.DB')

        self.superEngine = sqlalchemy.create_engine(
            'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % dict(
                user=self.adminConf.user,
                password=self.adminConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database='postgres'
            )
        )

        self.adminEngine = sqlalchemy.create_engine(
            'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % dict(
                user=self.adminConf.user,
                password=self.adminConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database=self.databaseConf.name
            )
        )
        self.userEngine = sqlalchemy.create_engine(
            'postgresql+psycopg2://%(user)s:%(password)s@%(host)s:%(port)d/%(database)s' % dict(
                user=self.databaseConf.user,
                password=self.databaseConf.password,
                host=self.serverConf.host,
                port=self.serverConf.port,
                database=self.databaseConf.name
            )
        )
        self.logger.info('Database engines ready (server: %(host)s:%(port)d)' % dict(
            host=self.serverConf.host,
            port=self.serverConf.port
        ))

    @contextmanager
    def superConnection(self):
        conn = self.superEngine.connect()
        isolation = conn.connection.connection.isolation_level
        conn.connection.connection.set_isolation_level(0)
        yield conn
        conn.connection.connection.set_isolation_level(isolation)
        conn.close()

    @contextmanager
    def adminConnection(self):
        conn = self.adminEngine.connect()
        isolation = conn.connection.connection.isolation_level
        conn.connection.connection.set_isolation_level(0)
        yield conn
        conn.connection.connection.set_isolation_level(isolation)
        conn.close()

    def createUser(self):
        self.logger.info('Action: createUser()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "CREATE ROLE %(role)s WITH NOSUPERUSER INHERIT LOGIN ENCRYPTED PASSWORD '%(password)s'" % dict(
                        role=self.databaseConf.user,
                        password=self.databaseConf.password
                    )
                )
            except ProgrammingError as e:
                self.logger.warning('Could not create user %(role)s: %(err)s' % dict(
                    role=self.databaseConf.user,
                    err=str(e)
                ))

    def dropUser(self):
        self.logger.info('Action: dropUser()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "DROP ROLE %(role)s" % dict(
                        role=self.databaseConf.user
                    )
                )
            except ProgrammingError as e:
                self.logger.warning('Could not drop user %(role)s: %(err)s' % dict(
                    role=self.databaseConf.user,
                    err=str(e)
                ))

    def createDatabase(self):
        self.logger.info('Action: createDatabase()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "CREATE DATABASE %(name)s WITH OWNER %(role)s ENCODING 'SQL_ASCII'" % dict(
                        name=self.databaseConf.name,
                        role=self.databaseConf.user
                    )
                )
            except ProgrammingError as e:
                self.logger.warning('Could not create database %(name)s with owner %(role)s: %(err)s' % dict(
                    name=self.databaseConf.name,
                    role=self.databaseConf.user,
                    err=str(e)
                ))

    def dropDatabase(self):
        self.logger.info('Action: dropDatabase()')
        with self.superConnection() as conn:
            try:
                conn.execute(
                    "DROP DATABASE %(name)s" % dict(
                        name=self.databaseConf.name
                    )
                )
            except ProgrammingError as e:
                self.logger.warning('Could not drop database %(name)s: %(err)s' % dict(
                    name=self.databaseConf.name,
                    err=str(e)
                ))

    def setupPostgis(self):
        self.logger.info('Action: setupPostgis()')
        with self.adminConnection() as conn:
            try:
                conn.execute("""
                    CREATE EXTENSION postgis;
                    ALTER SCHEMA public OWNER TO %(role)s;
                    ALTER TABLE public.spatial_ref_sys OWNER TO %(role)s;
                """ % dict(role=self.databaseConf.user))
            except ProgrammingError as e:
                self.logger.warning('Could not setup postgis on %(name)s: %(err)' % dict(
                    name=self.databaseConf.name,
                    err=str(e)
                ))

    def create(self):
        self.logger.info('Action: create()')
        self.createUser()
        self.createDatabase()
        self.setupPostgis()

    def destroy(self):
        self.logger.info('Action: destroy()')
        self.dropDatabase()
        self.dropUser()
