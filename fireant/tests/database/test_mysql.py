from unittest import TestCase
from unittest.mock import (
    ANY,
    Mock,
    patch,
)

from pypika import (
    Field,
    Column as PypikaColumn,
    MySQLQuery,
)

from fireant.database import MySQLDatabase
from fireant.database.mysql import MySQLTypeEngine
from fireant.database.sql_types import VarChar


class TestMySQLDatabase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mysql = MySQLDatabase(database='testdb')

    def test_defaults(self):
        self.assertEqual('localhost', self.mysql.host)
        self.assertEqual(3306, self.mysql.port)
        self.assertEqual('utf8mb4', self.mysql.charset)
        self.assertIsNone(self.mysql.user)
        self.assertIsNone(self.mysql.password)

    @patch.object(MySQLDatabase, '_get_connection_class')
    def test_connect(self, mock_connection_class):
        mock_pymysql = Mock()
        with patch.dict('sys.modules', pymysql=mock_pymysql):
            mock_pymysql.connect.return_value = 'OK'

            mysql = MySQLDatabase(database='test_database', host='test_host', port=1234,
                                  user='test_user', password='password')
            mysql.connect()

        mock_connection_class.return_value.assert_called_once_with(
              host='test_host', port=1234, db='test_database', charset='utf8mb4',
              user='test_user', password='password', cursorclass=ANY
        )

    def test_trunc_hour(self):
        result = self.mysql.trunc_date(Field('date'), 'hour')

        self.assertEqual('dashmore.TRUNC("date",\'hour\')', str(result))

    def test_trunc_day(self):
        result = self.mysql.trunc_date(Field('date'), 'day')

        self.assertEqual('dashmore.TRUNC("date",\'day\')', str(result))

    def test_trunc_week(self):
        result = self.mysql.trunc_date(Field('date'), 'week')

        self.assertEqual('dashmore.TRUNC("date",\'week\')', str(result))

    def test_trunc_month(self):
        result = self.mysql.trunc_date(Field('date'), 'month')

        self.assertEqual('dashmore.TRUNC("date",\'month\')', str(result))

    def test_trunc_quarter(self):
        result = self.mysql.trunc_date(Field('date'), 'quarter')

        self.assertEqual('dashmore.TRUNC("date",\'quarter\')', str(result))

    def test_trunc_year(self):
        result = self.mysql.trunc_date(Field('date'), 'year')

        self.assertEqual('dashmore.TRUNC("date",\'year\')', str(result))

    def test_date_add_hour(self):
        result = self.mysql.date_add(Field('date'), 'hour', 1)

        self.assertEqual('DATE_ADD("date",INTERVAL 1 HOUR)', str(result))

    def test_date_add_day(self):
        result = self.mysql.date_add(Field('date'), 'day', 1)

        self.assertEqual('DATE_ADD("date",INTERVAL 1 DAY)', str(result))

    def test_date_add_week(self):
        result = self.mysql.date_add(Field('date'), 'week', 1)

        self.assertEqual('DATE_ADD("date",INTERVAL 1 WEEK)', str(result))

    def test_date_add_month(self):
        result = self.mysql.date_add(Field('date'), 'month', 1)

        self.assertEqual('DATE_ADD("date",INTERVAL 1 MONTH)', str(result))

    def test_date_add_quarter(self):
        result = self.mysql.date_add(Field('date'), 'quarter', 1)

        self.assertEqual('DATE_ADD("date",INTERVAL 1 QUARTER)', str(result))

    def test_date_add_year(self):
        result = self.mysql.date_add(Field('date'), 'year', 1)

        self.assertEqual('DATE_ADD("date",INTERVAL 1 YEAR)', str(result))

    def test_to_char(self):
        db = MySQLDatabase()

        to_char = db.to_char(Field('field'))
        self.assertEqual('CAST("field" AS CHAR)', str(to_char))

    # noinspection SqlDialectInspection,SqlNoDataSourceInspection
    @patch.object(MySQLDatabase, 'fetch')
    def test_get_column_definitions(self, mock_fetch):
        MySQLDatabase().get_column_definitions('test_schema', 'test_table')

        mock_fetch.assert_called_once_with(
              'SELECT DISTINCT `column_name`,`column_type` '
              'FROM `INFORMATION_SCHEMA`.`columns` '
              'WHERE `table_schema`=\'test_schema\' AND `table_name`=\'test_table\' '
              'ORDER BY `column_name`',
              connection=None
        )

    @patch.object(MySQLDatabase, 'execute')
    def test_import_csv(self, mock_execute):
        MySQLDatabase().import_csv('abc', '/path/to/file')

        mock_execute.assert_called_once_with(
              'LOAD DATA LOCAL INFILE \'/path/to/file\' INTO TABLE `abc` FIELDS TERMINATED BY \',\'',
              connection=None
        )

    @patch.object(MySQLDatabase, 'execute')
    def test_create_temporary_table_from_columns(self, mock_execute):
        columns = PypikaColumn('a', 'varchar'), PypikaColumn('b', 'varchar(100)')

        MySQLDatabase().create_temporary_table_from_columns('abc', columns)

        mock_execute.assert_called_once_with(
              'CREATE TEMPORARY TABLE "abc" ("a" varchar,"b" varchar(100))',
              connection=None
        )

    @patch.object(MySQLDatabase, 'execute')
    def test_create_temporary_table_from_select(self, mock_execute):
        query = MySQLQuery.from_('abc').select('*')

        MySQLDatabase().create_temporary_table_from_select('def', query)

        mock_execute.assert_called_once_with(
              'CREATE TEMPORARY TABLE "def" AS (SELECT * FROM "abc")',
              connection=None,
        )


class TestMySQLTypeEngine(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mysql_type_engine = MySQLTypeEngine()

    def test_to_ansi(self):
        db_type = 'nvarchar'

        ansi_type = self.mysql_type_engine.to_ansi(db_type)

        self.assertTrue(isinstance(ansi_type, VarChar))

    def test_from_ansi(self):
        ansi_type = VarChar()

        db_type = self.mysql_type_engine.from_ansi(ansi_type)

        self.assertEqual('varchar', db_type)
