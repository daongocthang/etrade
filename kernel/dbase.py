import os
from configparser import ConfigParser
from contextlib import contextmanager
from enum import Enum

from mysql.connector import Error, MySQLConnection


def read_db_config(filename='config.ini', section='mysql'):
    """ Read database configuration file and return a dictionary object
    :param filename: name of the configuration file
    :param section: section of database configuration
    :return: a dictionary of database parameters
    """
    # create parser and read ini configuration file
    parser = ConfigParser()
    parser.read(filename)

    # get section, default to mysql
    db = {}
    if parser.has_section(section):
        items = parser.items(section)
        for item in items:
            db[item[0]] = item[1]
    else:
        raise Exception('{0} not found in the {1} file'.format(section, filename))

    return db


def quote(param):
    return "'{}'".format(param) if isinstance(param, str) else str(param)


def sqlparse(params, is_value=True, sep=','):
    if is_value:
        return sep.join([quote(p) for p in params])
    else:
        return sep.join([str(p) for p in params])


class SqlClause(Enum):
    """SQL Clauses in MySQL Server"""

    SELECT = """SELECT {} FROM {} {};"""
    INSERT = """INSERT INTO {} ({}) VALUES ({});"""
    UPDATE = """UPDATE {} SET {} {};"""
    DELETE = """DELETE FROM {} {};"""
    CREATE_TABLE = """CREATE TABLE IF NOT EXISTS {} ({});"""

    def value_with(self, *args):
        return self.value.format(*args)


class Table:
    def __init__(self, name):
        self.name = name
        self._where_clauses = []
        self._join_clause = ''
        self._sort_clause = ''
        self._limit_clause = ''

        # Create `config.ini` file if not exists
        if not os.path.exists('config.ini'):
            conf = [
                "[mysql]",
                "host = localhost",
                "database = test",
                "user = root",
                "password ="
            ]
            with open('config.ini', 'w') as f:
                f.write('\n'.join(conf))

        self._conf = read_db_config()

    @contextmanager
    def database(self, commit=False):
        conn = MySQLConnection(**self._conf)
        assert conn is not None and conn.is_connected(), "Connection is not available"
        curs = conn.cursor(buffered=True, dictionary=True)
        try:
            yield curs
            if commit: conn.commit()
        except Error as er:
            print(er)
            if commit: conn.rollback()
        finally:
            if curs is not None: curs.close()
            if conn is not None and conn.is_connected(): conn.close()

    def join(self, other, match, style='INNER'):
        self._join_clause = f"{style} JOIN `{other}` ON {self.name}.{match} = {other}.{match}"
        return self

    def where(self, field, comparison, pattern):
        self._where_clauses.append('{} {} {}'.format(field, comparison, pattern))
        return self

    def order_by(self, cols, desc=False):
        self._sort_clause = f"ORDER BY {', '.join(cols)} {'DESC' if desc else 'ASC'}"
        return self

    def limit(self, clause):
        self._sort_clause = f"LIMIT {clause}"
        return self

    def conditions(self):
        suffix_clauses = [self._join_clause,
                          'WHERE {}'.format(' AND '.join(self._where_clauses)) if len(self._where_clauses) > 0 else '',
                          self._sort_clause,
                          self._limit_clause]
        self._sort_clause = ''
        self._join_clause = ''
        self._limit_clause = ''
        self._where_clauses.clear()
        return ' '.join(suffix_clauses)

    """
    Database CRUD Operations
    """

    def create_if_not_exists(self, definition: list):
        qry = SqlClause.CREATE_TABLE.value_with(self.name, ','.join(definition))
        with self.database() as db:
            db.execute(qry)

    def select(self, clause):
        qry = SqlClause.SELECT.value_with(clause, self.name, self.conditions())
        with self.database() as db:
            db.execute(qry)
            return list(db.fetchall())

    def update(self, params):
        p = ','.join([k + ' = ' + quote(v) for k, v in params.items()])
        qry = SqlClause.UPDATE.value_with(self.name, p, self.conditions())
        with self.database(True) as db:
            db.execute(qry)

    def insert(self, params: dict):
        qry = SqlClause.INSERT.value_with(self.name, sqlparse(params.keys(), is_value=False), sqlparse(params.values()))
        with self.database(True) as db:
            db.execute(qry)

    def delete(self):
        qry = SqlClause.DELETE.value_with(self.name)
        with self.database(True) as db:
            db.execute(qry)
