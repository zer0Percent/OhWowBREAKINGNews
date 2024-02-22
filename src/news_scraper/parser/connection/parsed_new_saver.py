import psycopg2
from new_content import NewContent
from connection.config_new_parser import settings
from new_parser_exceptions import DatabaseException, GetRawNewsException
from parser_constants import RAW_NEW_PRELOADED_WORDING

class ParsedNewSaver:

    def __init__(self):
        self.connection_source: psycopg2.connection = psycopg2.connect(
            **settings.database_parameters.connection
        )

        self.cursor_source: psycopg2.cursor = self.connection_source.cursor()

        self.connection_destiny = psycopg2.connection = psycopg2.connect(
            **settings.database_parameters.parsed_new_connection
        )
        self.cursor_destiny: psycopg2.cursor = self.connection_destiny.cursor()


    def get_raw_news(self, dataset_name: str):

        try:

            source_name: str = f'{RAW_NEW_PRELOADED_WORDING}_{dataset_name}'
            raw_news_query = '''
            SELECT new_id, original_url
            FROM dbo.raw_new
            WHERE is_empty=FALSE AND is_retrieved=TRUE AND parsed=FALSE AND should_rescrape=FALSE AND data_source=%s
			ORDER BY new_id DESC
            LIMIT 500
            '''

            self.cursor_source.execute(raw_news_query, (source_name, ))
            self.connection_source.commit()

            result = self.cursor_source.fetchall()
            
            return result
        except Exception as e:
            raise GetRawNewsException(f'Could not get the raw news. Reason {e}.')

    def get_raw_reader_new(self, new_id: int):
    
        try:
            raw_reader_new = '''
            SELECT raw_new, reader_mode_new
            FROM dbo.raw_new
            WHERE new_id = %s
            '''

            self.cursor_source.execute(raw_reader_new, (new_id, ))
            self.connection_source.commit()

            result = self.cursor_source.fetchall()[0]

            raw_new = result[0]
            reader_mode_new = result[1]

            return raw_new, reader_mode_new
        
        except Exception as e:
            raise Exception(f'Could not get the raw and reader mode of the new with identifier {new_id}. Reason {e}')
        

    def update_rescraping_status(self, new_id: int):

        try:
            query_update_rescraping_status = '''
            UPDATE dbo.raw_new
            SET should_rescrape = TRUE
            WHERE new_id = %s
            '''
            self.cursor_source.execute(query_update_rescraping_status, (new_id, ))
            self.connection_source.commit()

        except Exception as e:
            raise DatabaseException(f'Could not update the re-scraping status for the new with identifier: {new_id}. Reason: {e}')

    def persist_new(self, new_content: NewContent, new_id: int, dataset_name: str):
        try:
            query_insert_parsed_new = '''
            INSERT INTO dbo.parsed_new(new_id, title, body, publish_date, authors, language, top_image_url, media_content_urls, is_empty, data_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''

            new = (new_id, new_content.title, new_content.text, new_content.publish_date,
                   new_content.authors, new_content.language, new_content.top_img, new_content.movies, new_content.empty_new, dataset_name)
            self.cursor_destiny.execute(query_insert_parsed_new, new)
            self.connection_destiny.commit()

            update_is_parsed = '''
                UPDATE dbo.raw_new
                SET parsed=TRUE
                WHERE new_id = %s
            '''
            self.cursor_source.execute(update_is_parsed, (new_id, ))
            self.connection_source.commit()


        except Exception as e:
            raise DatabaseException(f'Could not insert the new with identifier {new_id}. Reason {e} ')

    def close_connection_destiny(self):
        self.cursor_destiny.close()
        self.connection_destiny.close()

    def close_connection_source(self):
        self.cursor_source.close()
        self.connection_source.close()