import sys
import logging
import psycopg2
from config import settings
from src.connection.database_exceptions import DatabaseException, ExtractPaywallMethodException
from src.news_scraper.constants import WEB_ARCHIVE_NEW_PRELOADED_WORDING, RAW_NEW_PRELOADED_WORDING

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

class NewSaver:
    
    def __init__(self, connection, cursor) -> None:

        self.connection: psycopg2.connection = connection
        self.cursor: psycopg2.cursor = cursor

    @staticmethod
    def compute_acquirable_news(dataset_name: str) -> list:
        connection: psycopg2.connection = psycopg2.connect(
            **settings.database_parameters.connection
        )

        cursor: psycopg2.cursor = connection.cursor()

        adquirable_query = ''' 
        SELECT new_id, original_url from dbo.raw_new
        WHERE is_empty=FALSE AND is_retrieved=FALSE AND should_rescrape=FALSE and data_source = %s;
        '''

        data_source: str = f'{RAW_NEW_PRELOADED_WORDING}_{dataset_name}'
        cursor.execute(adquirable_query, (data_source, ))
        connection.commit()

        result: list = cursor.fetchall()

        cursor.close()
        connection.close()

        return result
    
    def save_news(self, new_id: int, raw_new, reader_mode_new):
        try:

            update_url_query = '''
            UPDATE dbo.raw_new
            SET is_empty = FALSE,
                is_retrieved = TRUE,
                raw_new = %s,
                reader_mode_new = %s
            WHERE
                new_id=%s;
            '''

            self.cursor.execute(update_url_query, (raw_new, reader_mode_new, new_id))
            self.connection.commit()

            return True
        except Exception as e:
            raise DatabaseException(f'Could not save the new with identifier {new_id}. Reason {e}')

    def update_scraping_status(self, new_id: int):

        try:
            update_scraping_status_query = '''
            UPDATE dbo.raw_new
            SET is_empty = TRUE,
                is_retrieved = TRUE
            WHERE
                new_id=%s;
            '''

            self.cursor.execute(update_scraping_status_query, (new_id, ))
            self.connection.commit()

            return True
        except Exception as e:
            raise DatabaseException(f'Could not update the scraping status of the new with identifier {new_id}. Reason {e}')

    def empty_new(self, new_id: int):

        try:
            empty_new_query = '''
            UPDATE dbo.raw_new
            SET raw_new = %s,
                reader_mode_new = %s
            WHERE
                new_id=%s;
            '''

            empty_content: str = ''
            self.cursor.execute(empty_new_query, (empty_content.encode('utf-8'), empty_content.encode('utf-8'), new_id))
            self.connection.commit()

            return True
        except Exception as e:
            raise DatabaseException(f'Could not empty the new with identifier {new_id}. Reason {e}')

    def save_pdf(self, new_id: int, pdf_file):

        try:
            update_pdf_file = '''
            UPDATE dbo.raw_new
            SET is_empty = FALSE,
                is_retrieved = TRUE,
                raw_new = %s
            WHERE
                new_id=%s
            '''

            self.cursor.execute(update_pdf_file, (pdf_file, new_id))
            self.connection.commit()
            
            return True
        except Exception as e:
            raise DatabaseException(f'Could not save the PDF file with identifier {new_id}. Reason {e}')

    def save_webarchive_urls(self, new_id: int, potential_urls: list):
        try:
            update_potential_url_query = '''
            UPDATE dbo.web_archive_new
            SET is_empty = FALSE,
                is_retrieved = TRUE,
                potential_urls = %s
            WHERE
                new_id=%s
            '''
            self.cursor.execute(update_potential_url_query, (potential_urls, new_id))
            self.connection.commit()

            return True

        except Exception as e:
            raise DatabaseException(f'Could not save the potentials Web Archive URLs for the new with identifier {new_id}. Reason {e}')


    @staticmethod
    def new_identifiers_already_preloaded(dataset_name: str):

        try:
            connection: psycopg2.connection = psycopg2.connect(
                **settings.database_parameters.connection
            )
            cursor: psycopg2.cursor = connection.cursor()

            WEB_ARCHIVE_NEW_PRELOADED_WORDING
            web_archive_preload_name: str = f'{WEB_ARCHIVE_NEW_PRELOADED_WORDING}_{dataset_name}'
            cursor.execute("SELECT EXISTS ( SELECT 1 FROM dbo.preloaded_content WHERE data_source = %s )", (web_archive_preload_name, ))
            connection.commit()
            web_archive_is_already_preloaded: bool = bool(cursor.fetchone()[0])

            raw_new_preload_name: str = f'{RAW_NEW_PRELOADED_WORDING}_{dataset_name}'
            cursor.execute("SELECT EXISTS ( SELECT 1 FROM dbo.preloaded_content WHERE data_source = %s )", (raw_new_preload_name, ))
            connection.commit()
            raw_new_is_already_preloaded: bool = bool(cursor.fetchone()[0])

            cursor.close()
            connection.close()
            return web_archive_is_already_preloaded and raw_new_is_already_preloaded

        except Exception as e:
            cursor.close()
            connection.close()
            raise DatabaseException(f'Could not determine if the new identifiers were preloaded before. Reason {e}')
    @staticmethod
    def preload_new_ids_webarchive(new_ids: list, dataset_name: str):
        try:
            data_source: str = f'{WEB_ARCHIVE_NEW_PRELOADED_WORDING}_{dataset_name}'
            connection: psycopg2.connection = psycopg2.connect(
                **settings.database_parameters.connection
            )

            cursor: psycopg2.cursor = connection.cursor()

            cursor.execute("SELECT EXISTS ( SELECT 1 FROM dbo.preloaded_content WHERE data_source = %s )", (data_source,))
            connection.commit()
            is_already_preloaded: bool = bool(cursor.fetchone()[0])

            if is_already_preloaded:
                logging.info(f'The identifiers for the table {data_source} are already preloaded.')
                return False
            
            for new_id in new_ids:
                values = (new_id, data_source)
                cursor.execute("INSERT INTO dbo.web_archive_new (new_id, data_source) VALUES (%s, %s)", values)
                connection.commit()
            connection.commit()

            cursor.execute("INSERT INTO dbo.preloaded_content(data_source) VALUES (%s)", (data_source,))
            connection.commit()

            cursor.close()
            connection.close()
            logging.info(f'Preloaded {len(new_ids)} new identifiers in the dbo.web_archive_new table.')

            return True
        
        except Exception as e:
            cursor.close()
            connection.close()
            raise DatabaseException(f'Could not save the web archive identifiers into dbo.web_archive_new table. Reason: {e}')
    
    @staticmethod
    def preload_news_rawnew(news: list, dataset_name: str):
        try:
            data_source: str = f'{RAW_NEW_PRELOADED_WORDING}_{dataset_name}'
            connection: psycopg2.connection = psycopg2.connect(
                **settings.database_parameters.connection
            )

            cursor: psycopg2.cursor = connection.cursor()

            cursor.execute("SELECT EXISTS ( SELECT 1 FROM dbo.preloaded_content WHERE data_source = %s )", (data_source,))
            is_already_preloaded: bool = bool(cursor.fetchone()[0])
            connection.commit()

            if is_already_preloaded:
                logging.info(f'The identifiers and urls of news for the table dbo.raw_new are already preloaded.')
                return False
            
            for new_id, new_url in news:
                values = (new_id, new_url, data_source)
                cursor.execute('''INSERT INTO dbo.raw_new (new_id, original_url, data_source)
                                  VALUES (%s, %s, %s)
                               ''', values)
                connection.commit()
            connection.commit()

            cursor.execute('''INSERT INTO dbo.preloaded_content(data_source) 
                              VALUES (%s)
                           ''', (data_source,))
            connection.commit()

            cursor.close()
            connection.close()
            logging.info(f'Preloaded {len(news)} news in the dbo.raw_new table.')

            return True
        except Exception as e:
            cursor.close()
            connection.close()
            raise DatabaseException(f'Could not save the new identifiers into dbo.raw_new table. Reason: {e}')

    def get_saved_web_archive_results(self, new_id: int):

        try:
            query_loaded_web_archive_results = '''
            SELECT potential_urls
            FROM dbo.web_archive_new
            WHERE new_id = %s
            '''
            self.cursor.execute(query_loaded_web_archive_results, (new_id, ))
            self.connection.commit()

            query_result: list = self.cursor.fetchall()

            if len(query_result) == 0:
                return list()

            result: list | None = query_result[0][0]
            if result == None:
                return list()

            return result

        except Exception as e:
            raise DatabaseException(f'Could not get if the new has already potential URLs retrieved from WebArchive. Reason: {e}')

    def get_paywall_method(self, domain: str):

        try:
            query_paywall_method = '''
            SELECT paywall_method
            FROM dbo.url_domain
            WHERE domain_name = %s
            '''
            self.cursor.execute(query_paywall_method, (domain, ))
            self.connection.commit()

            result: list = self.cursor.fetchall()

            if len(result) == 0:
                return None
            
            return result[0][0]
            
        except Exception as e:
            raise ExtractPaywallMethodException(f'Could not retrieve the paywall method for the domain {domain}. Reason {e}')
        
    def close(self):
        self.cursor.close()
        self.connection.close()

    def commit_changes(self):
        self.connection.commit()