import sys
import time
import random
import logging
import tldextract
import pandas as pd
from config import settings
from multiprocessing.pool import ThreadPool
from src.news_scraper import constants
from src.connection.new_saver import NewSaver
from src.threading.threadmanager import ThreadManager
from src.connection.thread_database import ThreadDatabase
from src.connection.database_exceptions import DatabaseException
from src.news_scraper.new_retriever_thread import NewRetrieverThread
from src.news_scraper.exceptions.new_retriever_thread_exception import NewRetrieverThreadException, NewWithPaywallMethod, WebArchiveException

file_handler = logging.FileHandler(filename='news_scraper.log')
stdout_handler = logging.StreamHandler(stream=sys.stdout)

handlers = [file_handler, stdout_handler]
logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
    handlers=handlers,
    force=True
)
logger=logging.getLogger('NewScraperRunner')

class NewsScraperRunner:
    
    def __init__(self, urls_path: str, threads: int, chunk_size: int, dataset_name: str) -> None:
        self.urls_path: str = urls_path
        self.threads: int = threads
        self.chunk_size: int = chunk_size

        self.urls_path: str = urls_path
        self.dataset_name = dataset_name
    
    def start(self):
        thread_db: ThreadDatabase = None
        try:
            self._populate_news()
            
            dataset: list = NewSaver.compute_acquirable_news(self.dataset_name)
            if len(dataset) == 0:
                logger.info(f'No URLs to scrape. Closing tool...')
                return
            
            logger.info(f'Number of URLs to scrape: {len(dataset)}')
            random.shuffle(dataset)
            
            thread_db: ThreadDatabase = ThreadDatabase(self.threads)
            chunks = NewsScraperRunner._chunk_dataset(dataset, self.chunk_size)
            args = NewsScraperRunner._build_arguments(
                    chunks=chunks,
                    thread_database=thread_db
            )
            ThreadPool(self.threads).starmap(NewsScraperRunner.scrape, args)

        except Exception as e:
            logger.error(e)
            if thread_db:
                thread_db.close_pool_connections()
    
    def _populate_news(self):
        try:
            new_identifiers_already_preloaded: bool = NewSaver.new_identifiers_already_preloaded(self.dataset_name)
            if new_identifiers_already_preloaded:
                logger.info(f'New identifiers are already preloaded.')
                return 
            
            logger.info(f'Populating new identifiers...')
            news = list(pd.read_csv(self.urls_path).itertuples(index=False, name=None))
            new_ids: list = [new[0] for new in news]
            NewSaver.preload_new_ids_webarchive(new_ids, self.dataset_name)

            NewSaver.preload_news_rawnew(news, self.dataset_name)

            del news
            del new_ids
        except DatabaseException as e:
            raise e

    @staticmethod
    def scrape(
            news: list,
            thread_database: ThreadDatabase):
        
        try:
            thread_manager: ThreadManager = ThreadManager(thread_pool_connection=thread_database)
            browser = NewsScraperRunner._get_browser(thread_manager=thread_manager)

            connection, cursor = thread_manager.get_database_connection()
            new_saver: NewSaver = NewSaver(connection=connection, cursor=cursor)

            new_retriever_thread: NewRetrieverThread = NewRetrieverThread(
                browser=browser
            )

            NewsScraperRunner.trial_retrieval(
                data=news,
                new_retriever_thread=new_retriever_thread,
                new_saver = new_saver
            )

            thread_manager.dispose_from_pool()
            thread_manager.close_browser()
        except Exception as e:
            logging.error(f'Fatal error when scraping on the thread: {thread_manager.thread_id}. Reason: {e}')
            thread_manager.dispose_from_pool()
            thread_manager.close_browser()

    @staticmethod
    def trial_retrieval(data: list, new_retriever_thread: NewRetrieverThread, new_saver: NewSaver):

        for new_id, new_url in data:

            try:
                logger.info(f'Scraping {new_url}. Identifier: {new_id}')
                url_chunks = tldextract.extract(new_url)
                paywall_method: str = new_saver.get_paywall_method(url_chunks.domain)

                raw_new: str = ''
                reader_mode_new: str = ''
                is_free_of_paywall: bool = False

                if paywall_method is not None:
                    is_free_of_paywall: bool = NewsScraperRunner.free_of_paywall(paywall_method)
                    if is_free_of_paywall:
                        raw_new, reader_mode_new = NewsScraperRunner.retrieve_new(new_retriever_thread, new_saver, new_id, new_url)
                    else:
                        raw_new, reader_mode_new = new_retriever_thread.get_new_with_paywall_method(new_id, new_url, paywall_method)
                    
                else:
                    logger.warning(f'No domain found ({url_chunks.domain}) in url_domain table for the new with identifier {new_id}.')
                
                # We retry those URLs that have Paywall Method and were not retrieved
                are_empty: bool = raw_new == '' and \
                                  reader_mode_new == ''
                should_retry_with_webarchive: bool = are_empty and not is_free_of_paywall
                if should_retry_with_webarchive:
                    raw_new, reader_mode_new = NewsScraperRunner.retrieve_new(new_retriever_thread, new_saver, new_id, new_url)

                # Finally, we check again. If empty, then we do not store anything
                are_empty: bool = raw_new == '' and \
                                 reader_mode_new == ''
                if are_empty:
                    logger.warning(f'The new with identifier {new_id} could not be scraped. URL: {new_url}')
                    new_saver.update_scraping_status(new_id=new_id)
                    new_saver.empty_new(new_id=new_id)
                else:
                    
                    if NewsScraperRunner.is_pdf_file(new_url):
                        new_saver.save_pdf(
                            new_id=new_id,
                            pdf_file=raw_new
                        )
                        
                        logger.info(f'PDF file with identifier {new_id} saved.')
                    else:

                        new_saver.save_news(
                            new_id=new_id,
                            raw_new=raw_new.encode('utf-8'),
                            reader_mode_new=reader_mode_new.encode('utf-8')
                        )

                        logger.info(f'Raw new with identifier {new_id} saved.')
                    
                    new_saver.commit_changes()


                del raw_new
                del reader_mode_new

            except NewWithPaywallMethod as e:
                logger.error(e)

            except NewRetrieverThreadException as e:
                logger.error(e)

            except Exception as e:
                logger.error(e)

    @staticmethod
    def retrieve_new(new_retriever_thread: NewRetrieverThread, new_saver: NewSaver, new_id: int, new_url: str):

        raw_new: str = ''
        reader_mode_new: str = ''
        try:            
            if NewsScraperRunner.is_pdf_file(new_url):

                logger.info(f'Scraping PDF file for the URL {new_url} with identifier {new_id}')
                raw_new = new_retriever_thread.scrape_pdf_file(new_id, new_url)

                return raw_new, reader_mode_new

            web_archive_result, web_archive_already_loaded = NewsScraperRunner.get_web_archive_urls(new_retriever_thread, new_saver, new_id, new_url)

            if not web_archive_already_loaded:
                time.sleep(constants.WAIT_TIME_REQUEST + round(random.uniform(1, 1.9), 2))

            if len(web_archive_result) == 0:
                logger.warning(f'No Web Archive candidates found for the URL with identifier {new_id}. URL: {new_url}')
                
                result_scrape = new_retriever_thread.scrape_new(new_id=new_id,
                                                                new_url=new_url,
                                                                wait_time=constants.WAIT_TIME_REQUEST_NO_WEBARCHIVE)
                raw_new = result_scrape[0]
                reader_mode_new = result_scrape[1]

            else:

                log_info_web_archive_loaded: str = f'Web Archive URLs already loaded for the new with identifier {new_id}. URL {new_url}'
                if not web_archive_already_loaded:
                    new_saver.save_webarchive_urls(new_id, web_archive_result)
                    log_info_web_archive_loaded = f'Saved {len(web_archive_result)} Web Archive URLs for the new with identifier {new_id}. URL: {new_url}'
                logger.info(log_info_web_archive_loaded)
                
                web_archive_urls: list = new_retriever_thread.build_webarchive_urls(web_archive_result)

                for webarchive_url, status_code in web_archive_urls:
                    raw_new, reader_mode_new = new_retriever_thread.scrape_web_archive_url(new_id, webarchive_url, status_code)
                    if raw_new != '' or reader_mode_new != '':
                        break
            
            are_empty: bool = raw_new == '' and reader_mode_new == ''
            has_web_archive_urls_but_none_of_them_works: bool = are_empty and len(web_archive_result) != 0
            if has_web_archive_urls_but_none_of_them_works: # Then try to scrape it without Web Archive
                
                logger.info(f'Found {len(web_archive_result)} URLs in Web Archive for the new with identifier {new_id} but none of them worked. Trying to scrape it without Web Archive')
                result_scrape = new_retriever_thread.scrape_new(new_id=new_id,
                                                                new_url=new_url,
                                                                wait_time=constants.WAIT_TIME_REQUEST_NO_WEBARCHIVE)
                raw_new = result_scrape[0]
                reader_mode_new = result_scrape[1]

            return raw_new, reader_mode_new

        except WebArchiveException as e:
            logger.error(f'{e}. Waiting {constants.WAIT_TIME_WEBARCHIVE_ERROR}')
            time.sleep(constants.WAIT_TIME_WEBARCHIVE_ERROR)
            return '', ''

        except DatabaseException as e:
            logger.error(e)
            return '', ''

        except NewRetrieverThreadException as e:
            logger.error(e)
            return '', ''

        except Exception as e:
            logger.error(e)
            return '', ''

    @staticmethod
    def is_pdf_file(url: str):

        try:
            return constants.PDF_EXTENSION in url
        except Exception as e:
            raise Exception(f'Could not evaluate whether the new {url} is a PDF file. Reason {e}')

    @staticmethod
    def get_web_archive_urls(new_retriever_thread: NewRetrieverThread, new_saver: NewSaver, new_id: int, new_url: str):

        try:
            
            web_archive_results_loaded: list = new_saver.get_saved_web_archive_results(new_id)
            already_loaded: bool = False
            if len(web_archive_results_loaded) != 0:
                already_loaded = True
                return web_archive_results_loaded, already_loaded

            return new_retriever_thread.get_candidate_webarchive_urls(new_id, new_url), already_loaded
        except Exception as e:
            raise e

    @staticmethod
    def free_of_paywall(paywall_method: str):    
        return (paywall_method != constants.REMOVE_PAYWALL and paywall_method != constants.FT_LADDER)
     
    @staticmethod
    def _chunk_dataset(news: list, chunk_size: int):
        chunks: list = list()

        for i in range(0, len(news), chunk_size):
            chunk_data: list = news[i : i + chunk_size]
            chunks.append(chunk_data)

        return chunks
    
    @staticmethod
    def _build_arguments(chunks: list,
                         thread_database: ThreadDatabase):

        result = list()
        for chunk in chunks:
            result.append(tuple([chunk]) + (thread_database,))

        return result
    
    @staticmethod
    def _get_browser(thread_manager: ThreadManager):
        return thread_manager.get_browser('firefox')