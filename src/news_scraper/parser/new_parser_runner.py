import re
import sys
import logging
import parser_constants
from new_parser import NewParser
from new_content import NewContent
from connection.parsed_new_saver import ParsedNewSaver
from new_parser_exceptions import DatabaseException, GetRawNewsException

file_handler = logging.FileHandler(filename='news_parser.log')
stdout_handler = logging.StreamHandler(stream=sys.stdout)

handlers = [file_handler, stdout_handler]
logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers,
    force=True
)
logger=logging.getLogger('NewParserRunner')

class NewParserRunner:

    def __init__(self, dataset_name: str) -> None:
        self.new_saver: ParsedNewSaver = ParsedNewSaver()
        self.new_parser: NewParser = NewParser(logger)

        self.dataset_name = dataset_name

    def start(self):

        try:
            parsed_news_count: int = 0
            logging.info(f'Parsing and inserting news...')
            while True:
                raw_news: list = self.new_saver.get_raw_news(self.dataset_name)

                if len(raw_news) == 0:
                    logging.info(f'Parsed and inserted {parsed_news_count} news. Closing parser.')
                    self.new_saver.close_connection_destiny()
                    self.new_saver.close_connection_source()
                    break
                parsed_news: int = self.parse_news(raw_news, self.dataset_name)
                parsed_news_count += parsed_news
                logging.info(f'Parsed {parsed_news_count}.')
                del raw_news

        except GetRawNewsException as e:
            logging.error(f'{e.message}')
            logging.info('Closing tool.')
            self.new_saver.close_connection_source()
            self.new_saver.close_connection_destiny()
            
        except Exception as e:
            logging.error(f'Could not insert the users. Reason: {e}')
            logging.info('Closing tool.')
            self.new_saver.close_connection_source()
            self.new_saver.close_connection_destiny()

    def parse_news(self, raw_news: list, dataset_name: str):

            parsed_news: int = 0
            for new_id, original_url in raw_news:
                try:
                    raw_new, reader_mode_new = self.new_saver.get_raw_reader_new(new_id)                    
                    new_content: NewContent = NewContent(
                        title = None,
                        text = None,
                        publish_date = None,
                        authors = None,
                        language = None,
                        top_img = None,
                        movies = None,
                        empty_new = True
                    )
                    
                    raw_new, reader_mode_new = self.read_new_content(raw_new, reader_mode_new, original_url)

                    no_content_in_new: bool = raw_new == '' and reader_mode_new == ''
                    if no_content_in_new:
                        self.new_saver.update_rescraping_status(new_id)
                    
                    new_with_only_raw_content: bool = raw_new != '' and reader_mode_new == ''
                    if new_with_only_raw_content:
                        
                        type_content: str = parser_constants.RAW_CONTENT
                        if self._is_pdf(original_url):
                            type_content = parser_constants.PDF_CONTENT

                        logger.info(f'[{type_content}] Parsing with {type_content} mode content. New with identifier {new_id}')
                        new_content = self.new_parser.parse_single_content(content=raw_new, new_id=new_id, type=type_content)

                        parsed_news += 1
                        logger.info(f'[{parser_constants.RAW_CONTENT}] New parsed with identifier {new_id}')
                    
                    new_with_only_reader_mode_content: bool = raw_new == '' and reader_mode_new != ''
                    if new_with_only_reader_mode_content:

                        logger.info(f'[{parser_constants.READER_CONTENT}] Parsing with {parser_constants.READER_CONTENT} mode content. New with identifier {new_id}')
                        new_content =self.new_parser.parse_single_content(content=reader_mode_new, new_id=new_id, type=parser_constants.READER_CONTENT)

                        parsed_news += 1
                        logger.info(f'[{parser_constants.READER_CONTENT}] New parsed with identifier {new_id}')

                    
                    new_with_raw_and_reader_content: bool = raw_new != '' and reader_mode_new != ''
                    if new_with_raw_and_reader_content:

                        logger.info(f'[{parser_constants.RAW_READER_CONTENT}] Parsing with {parser_constants.RAW_READER_CONTENT} mode content. New with identifier {new_id}')
                        new_content = self.new_parser.parse(raw_new, reader_mode_new, new_id)
                        
                        parsed_news += 1
                        logger.info(f'[{parser_constants.RAW_READER_CONTENT}] New parsed with identifier {new_id}')

                    self.new_saver.persist_new(new_content, new_id, dataset_name)

                except DatabaseException as e:
                    logger.error(f'Could not save the new. {e}')
                except Exception as e:
                    logger.error(f'Could not parse the new. {e}')
                finally:
                    del raw_new
                    del reader_mode_new

            return parsed_news

    def read_new_content(self, raw_new, reader_mode_new, original_url: str):

        try:
            is_pdf: bool = self._is_pdf(original_url)

            if is_pdf:
                return raw_new, ''
            
            raw_new_html: str = bytearray(raw_new).decode()
            reader_mode_new_html: str = bytearray(reader_mode_new).decode()

            raw_new_html = self.preprocess_html(raw_new_html)
            reader_mode_new_html = self.preprocess_html(reader_mode_new_html)

            return raw_new_html, reader_mode_new_html
            
        except Exception as e:
            raise Exception(f'Could not read the content of the new. Reason {e}')

    def preprocess_html(self, html):

        try:
            result: str = ''
            removed_html_entities: str = self.remove_html_entities(html)
            removed_p_tag_webarchive: str = self.remove_p_tag_webarchive(removed_html_entities)

            result = removed_p_tag_webarchive

            return result
        except Exception as e:
            raise Exception(f'Could not preprocess the HTML content. Reason {e}')

    def remove_html_entities(self, html: str):

        try:
            removed_entities: str = html.replace('&amp;', 'and')
            removed_entities = re.sub(parser_constants.REMOVE_HTML_ENTITIES_REGEX, ' ', removed_entities)
            return removed_entities
        except Exception as e:
            raise Exception(f'Could not remove the HTML entities. Reason {e}')
        
    def remove_p_tag_webarchive(self, html: str):

        try:
            removed_p_tag = re.sub(parser_constants.REMOVE_P_TAG_WEBARCHIVE_REGEX, '', html)
            return removed_p_tag
        except Exception as e:
            raise Exception(f'Could not remove the p HTML tag. Reason {e}')
        
    def _is_pdf(self, url: str):
        return parser_constants.PDF_WORDING in url

