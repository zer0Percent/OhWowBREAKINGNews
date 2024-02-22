import re
import time
import random
import requests
from bs4 import BeautifulSoup
from src.news_scraper import constants
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from src.news_scraper.exceptions.new_retriever_thread_exception import CandidateWebArchiveUrlException, GetRequestWebArchiveException, NewRawModeException, NewReaderModeException, NewWithPaywallMethod

class NewRetrieverThread:
    def __init__(self, browser) -> None:
        self.browser = browser

    def scrape_new(self, new_id: int, new_url: str, wait_time: float):

        url_with_protocol: list = self._add_http_protocol(new_url)

        raw_new: str = ''
        reader_mode_new: str = ''

        for url in url_with_protocol:
            try:
                raw_new = self.get_raw_new(new_id=new_id, new_url=url, status_code='', wait_time=wait_time)
                reader_mode_new = self.get_reader_mode_new(new_id=new_id, new_url=url, status_code='', wait_time=wait_time)    
                break
            except Exception as e:
                raw_new = ''
                reader_mode_new = ''
                continue

        result_sanitization: tuple = self._sanity_check_news(raw_new=raw_new, reader_mode_new=reader_mode_new)

        raw_new = result_sanitization[0]
        reader_mode_new = result_sanitization[1]

        return raw_new, reader_mode_new
    
    def scrape_web_archive_url(self, new_id: int, new_url: str, status_code: str):
        try:
            
            raw_new: str = ''
            reader_mode_new: str = ''

            if status_code not in constants.INVALID_WEB_ARCHIVE_STATUS_CODE:
                raw_new: str = self.get_raw_new(new_id=new_id, new_url=new_url, status_code=status_code)
                reader_mode_new: str = self.get_reader_mode_new(new_id=new_id, new_url=new_url, status_code=status_code)

            result_sanitization: tuple = self._sanity_check_news(raw_new=raw_new, reader_mode_new=reader_mode_new)

            raw_new = result_sanitization[0]
            reader_mode_new = result_sanitization[1]

            return raw_new, reader_mode_new
        except Exception as e:
            return '', ''

    def get_raw_new(self, new_id: int, new_url: str, status_code: str, wait_time: float = constants.WAIT_TIME_REQUEST):
        try:
            page_source: str = self._run_get_in_browser(new_url, status_code, wait_time)
            return page_source
            
        except Exception as e:
            raise NewRawModeException(f'Could not get the raw new of the new with identifier {new_id}. Reason {e}')
    
    def get_new_paywall(self, new_id: int, new_url: str, paywall_method: str):
        try:
            self.browser.get(new_url)
            time.sleep(constants.WAIT_TIME_REQUEST_PAYWALL + round(random.uniform(1, 1.9), 2))

            # press enter if we get a dialog
            if paywall_method == constants.FT_LADDER:
                self.browser.switch_to.frame(self.browser.find_element(By.XPATH, constants.IFRAME_12FTLADDER_XPATH))

            return self.browser.page_source

        except Exception as e:
            raise NewRawModeException(f'Could not get the raw new of the new with identifier {new_id}. Using paywall method: {paywall_method}. Reason {e}')

    def get_reader_mode_new(self, new_id: int, new_url: str, status_code: str, wait_time: float = constants.WAIT_TIME_REQUEST):

        try:
            page_source: str = self._run_get_in_browser(f'{constants.READER_MODE_BASE_URL}{new_url}', status_code, wait_time)

            # Handle redirections here!
            while constants.ERROR_REDIRECTING_WEBARCHIVE_WORDING in page_source:
                
                url_redirected: str = NewRetrieverThread._get_redirected_url(page_source)

                if url_redirected == '':
                    return ''

                page_source = self._run_get_in_browser(url=f'{constants.READER_MODE_BASE_URL}{url_redirected}', status_code='0', base_wait_time=constants.WAIT_TIME_READER_MODE_GOT_URL_REDIRECTION_REQUEST)

            return page_source
        except Exception as e:
            raise NewReaderModeException(f'Could not get the reader mode version of the new with identifier {new_id}. Reason {e}')
    

    def scrape_pdf_file(self, new_id: int, new_url: str):

        try:

            result = ''
            url_with_protocol: str = self._add_http_protocol(new_url)[0]
            response_pdf: requests.Response = requests.get(url=url_with_protocol, headers=constants.HEADER_REQUEST_PDF_FILES, timeout=120)

            if response_pdf.status_code == 200:
                result = response_pdf.content

            result = NewRetrieverThread._sanitize_pdf(result)

            return result
        
        except Exception as e:
            raise NewRawModeException(f'Could not get the PDF file for the new with identifier {new_id}. Reason {e}')

    def _run_get_in_browser(self, url: str, status_code: str, base_wait_time: float):

        try:
            self.browser.get(url)

            time_sleep_raw: float = base_wait_time
            if status_code in constants.REDIRECT_WEB_ARCHIVE_STATUS_CODE:
                # We wait more time when a redirection is done
                time_sleep_raw = constants.WAIT_TIME_REDIRECT_SATUS_CODE
            time.sleep(time_sleep_raw + round(random.uniform(1, 1.9), 2))
            self._press_return()
            page_source = self.browser.page_source
            return page_source
        
        except Exception as e:
            raise e
        
    def _run_get_in_browser_raw_new(self, url: str, status_code: str, base_wait_time):
        try:
            self.browser.get(url)
            time_sleep_raw: float = base_wait_time
            if status_code in constants.REDIRECT_WEB_ARCHIVE_STATUS_CODE:
                # We wait more time when a redirection is done
                time_sleep_raw = constants.WAIT_TIME_REDIRECT_SATUS_CODE
            time.sleep(time_sleep_raw + round(random.uniform(1, 1.9), 2))
            self._press_return()

            return self.browser.page_source
        
        except Exception as e:
            raise e

    def _press_return(self):
        try:    
            actions = ActionChains(self.browser)
            alert = self.browser.switch_to.alert
            alert.accept()
            del actions
        except Exception as e:
            del actions
            ...

    def get_new_with_paywall_method(self, new_id: int, new_url: str, paywall_method: str):

        raw_new: str = ''
        reader_mode_new: str = ''

        url_with_http_protocol: list = self._add_http_protocol(new_url)
        for url in url_with_http_protocol:
            try:
                paywall_method_url: str = NewRetrieverThread.get_paywall_url(url, paywall_method)
                raw_new = self.get_new_paywall(new_id, paywall_method_url, paywall_method)

                break
            
            except NewWithPaywallMethod as e:
                raise e
            except Exception as e:
                raw_new = ''
                reader_mode_new = ''
                continue
        
        result_sanitization: tuple = self._sanity_check_news(raw_new=raw_new, reader_mode_new='')

        raw_new = result_sanitization[0]
        reader_mode_new = result_sanitization[1]

        return raw_new, reader_mode_new
    
    def get_candidate_webarchive_urls(self, new_id: int, new_url: str):
        try:
            
            urls: list = list()
            url_with_http_protocol: list = self._add_http_protocol(new_url)
            
            for url in url_with_http_protocol:

                web_archive_url = constants.WEBARCHIVE_URL_CANDIDATES_BASE_URL.format(url=url)

                response: requests.Response = NewRetrieverThread.get_candidate_urls_in_webarchive(web_archive_url)

                if response.status_code != 200:
                    return list()

                urls_candidates: list = NewRetrieverThread._build_web_archive_response(response.content.decode())

                if len(urls_candidates) > 0:
                    urls = urls_candidates
                    break
            
            return urls
        
        except GetRequestWebArchiveException as e:
            e.message = f'{e} Identifier: {new_id}. URL: {new_url}'
            raise e
        
        except Exception as e:
            raise CandidateWebArchiveUrlException(f'Could not retrieve the candidate URLs in Web Archive of the URL with identifier {new_id}. Reason {e}')

    def _sanity_check_news(self, raw_new: str, reader_mode_new: str):

        try:
            # Check the content for each new
            raw_new_result: str = raw_new
            reader_mode_new_result: str = reader_mode_new

            if NewRetrieverThread._is_empty(raw_new) or NewRetrieverThread._is_invalid_raw_new(raw_new):
                raw_new_result = ''

            if NewRetrieverThread._is_empty(reader_mode_new) or NewRetrieverThread._is_invalid_reader_mode_new(reader_mode_new):
                reader_mode_new_result = ''

            return raw_new_result, reader_mode_new_result

        except Exception as e:
            raise Exception(f'Could not sanitize the new when scraping it. {e}')
        
    def _is_invalid_raw_new(raw_new: str):

        # If contains in the title 404 (similar status codes) or page not found
        try:
            is_valid_raw_new: bool =  NewRetrieverThread._is_error_page_raw_new(raw_new) or \
                                      constants.NOT_ARCHIVED_URL_IN_WEBARCHIVE_WORDING in raw_new or \
                                      constants.EXCLUDED_FROM_WEB_ARCHIVE_WORDING in raw_new or \
                                      constants.DONT_HAVE_PERMISSION_WORDING in raw_new

            return is_valid_raw_new
        except Exception as e:
            raise Exception(f'Could not validate the raw new. Reason {e}')
        
    def _is_invalid_reader_mode_new(reader_mode_new: str):

        try:
            return NewRetrieverThread._is_error_page_reader_mode_new(reader_mode_new) or \
                   constants.ERROR_LOADING_PAGE_WORDING_SPANISH_READER_MODE in reader_mode_new or \
                   constants.DONT_HAVE_PERMISSION_WORDING in reader_mode_new or \
                   constants.INVALID_TITLE_READER_MODE in reader_mode_new

        except Exception as e:
            raise Exception(f'Could not validate the reader mode new. Reason {e}')

    @staticmethod
    def _sanitize_pdf(pdf_object):
        try:
            sanitized_pdf = pdf_object

            decoded_pdf = pdf_object.decode()

            if NewRetrieverThread._is_error_page_raw_new(decoded_pdf): #TODO. Test this
                sanitized_pdf = ''

            return sanitized_pdf
        except UnicodeDecodeError as e:
            return pdf_object
        except AttributeError as e:
            return ''
        except Exception as e:
            return ''
    @staticmethod
    def _get_redirected_url(redirecting_webarchive_html: str):

        try:
            # Look for the HTML element that contains the redirected URL.
            reader_soup: BeautifulSoup = BeautifulSoup(redirecting_webarchive_html, 'html.parser')
            content_element = reader_soup.find(class_="content")
            
            tags: list = content_element.find_all('a')

            if len(tags) == 0:
                return ''

            return tags[0]['href']
        except Exception as e:
            raise Exception(f'Could not get the redirection URL. Reason {e}')

    @staticmethod
    #Looks for any <title> and <body> that contains 404 (or any error status code) or page not found no sensitive case.
    def _is_error_page_raw_new(html: str):

        is_invalid_title: bool = NewRetrieverThread._is_invalid_title(html)
        is_invalid_body: bool = NewRetrieverThread._is_invalid_body_raw_new(html)

        return is_invalid_title or is_invalid_body

    @staticmethod
    def _is_error_page_reader_mode_new(html: str):

        is_invalid_title: bool = NewRetrieverThread._is_invalid_title(html)
        is_invalid_body: bool = NewRetrieverThread._is_invalid_body_reader_mode(html)

        return is_invalid_title or is_invalid_body
    
    @staticmethod
    def _is_invalid_title(html: str):
        matches = re.findall(r'<title[^>]*>(.*?)<\/title>', html, re.IGNORECASE | re.DOTALL)

        if len(matches) == 0:# If there are not titles, then is invalid title
            return True
        
        for title in matches:

            if title == '':
                return True
            
            tidy_title: str = title.replace(',', ' ').replace(':', ' ').replace('|', ' ').replace('\n', ' ').replace('’', '\'').replace('.0', ' ').replace('.', ' ')
            tidy_title: str = re.sub(' +', ' ', tidy_title)
            if re.search(constants.REGEX_INVALID_TITLE, tidy_title, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _is_invalid_body_raw_new(html: str):
        matches = re.findall(r'<body[^>]*>(.*?)<\/body>', html, re.IGNORECASE | re.DOTALL)
        if len(matches) == 0: # If there are not bodies, then is invalid body
            return True
        
        is_webarchive_wording_in_html: bool = 'web.archive' in html
        for body in matches:
            
            if not is_webarchive_wording_in_html: # Then we need to check that the regex to look for not found
                body_soup: BeautifulSoup = BeautifulSoup(body, 'html.parser')
                text: str = body_soup.get_text()

                if text == '':
                    del body_soup
                    return True

                tidy_text: str = text.replace('.', ' ').replace(',', ' ').replace(':', ' ')\
                                     .replace('|', ' ').replace('\n', ' ').replace('’', '\'').replace('.0', ' ').replace('.', ' ')
                tidy_text: str = re.sub(' +', ' ', tidy_text)
                
                if re.search(constants.REGEX_INVALID_BODY, tidy_text, re.IGNORECASE):
                    return True
                
            else:
                # We assume that, if it comes from web.archive, then it has valuable body content and hence is a valid body. THIS HEURISTIC IS NOT PERFECT!
                return False
        return False

    @staticmethod
    def _is_invalid_body_reader_mode(html: str):

        soup_reader_mode = BeautifulSoup(html, 'html.parser')

        content_div = soup_reader_mode.find('div', {'class': 'content'})
        if content_div is None:
            return True

        text_reader_mode: str = content_div.get_text()
        tidy_text: str = text_reader_mode.replace('.', ' ').replace(',', ' ').replace(':', ' ')\
                                         .replace('|', ' ').replace('\n', ' ').replace('’', '\'').replace('.', ' ')
        tidy_text: str = re.sub(' +', ' ', tidy_text)
                
        if re.search(constants.REGEX_INVALID_BODY, tidy_text, re.IGNORECASE) or constants.ERROR_LOREM_IPSUM_WORDING in tidy_text:
            return True

        return False

    @staticmethod
    def get_candidate_urls_in_webarchive(web_archive_url: str):

        response: requests.Response = None
        for _ in range(0, constants.WEB_ARCHIVE_CANDIDATES_TRIALS):

            try:
                response = requests.get(web_archive_url)
                if response.status_code == 200:
                    break
            except Exception as e:
                time.sleep(constants.WAIT_TIME_WEBARCHIVE_ERROR)
                continue

        if response is not None:
            return response
        raise GetRequestWebArchiveException('Could not get the candidate URLs in Web Archive. Timed out.')

    @staticmethod
    def _build_web_archive_response(response: str):

        try:
            urls: list = NewRetrieverThread.format_response(response)
            urls = urls[1:]
            return urls
        except Exception as e:
            raise GetRequestWebArchiveException(f'Could not build the response for the WebArchive request. Reason {e}')


    def _add_http_protocol(self, url: str) -> list:
        
        has_http_protocol = 'http' in url
        if has_http_protocol:
            return [url]
        if url[0] == '/':
            url = url[1:]
        return [f'http://{url}', f'https://{url}']
    
    @staticmethod
    def format_response(response: str):
        try:
            if response == '':
                return list()
            
            response_items: list = list()
            response_items.append(constants.WEB_ARCHIVE_RESPONSE_PROPERTIES)

            response_lines: list = response.split('\n')

            for line in response_lines:
                response_line = line.split(' ')

                if len(response_line) == len(constants.WEB_ARCHIVE_RESPONSE_PROPERTIES):
                    response_items.append(response_line)

            return response_items
        except Exception as e:
            raise e

    def build_webarchive_urls(self, web_archive_result: list):
        try:
            # sort by url[4] (status code) and timestamp[1] URL
            sorted_web_archive_result: list = sorted(web_archive_result, key=lambda url: (url[4], url[1]))
            web_archive_urls: list = [(constants.WEB_ARCHIVE_BASE_URL.format(timestamp=url[1], base_url= url[2]), url[4]) for url in sorted_web_archive_result] #4th element is the status code
            return web_archive_urls
        except Exception as e:
            raise e
        
    @staticmethod
    def get_paywall_url(new_url, paywall_method):

        try:
            base_url: str = constants.PAYWALL_METHODS_URLS.get(paywall_method)
            return base_url.format(url=new_url)
        except Exception as e:
            raise Exception(f'Could not get the URL with paywall method. Reason {e}')
        
    @staticmethod
    def _is_empty(new: str):
        return new is None or new == ''