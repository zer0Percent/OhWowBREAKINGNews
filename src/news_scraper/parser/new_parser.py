import io
import re
import time
import spacy
import logging
import parser_constants
from pypdf import PdfReader
from dateutil import parser
from datetime import datetime
from newspaper import Article
from bs4 import BeautifulSoup
from langdetect import detect
from new_content import NewContent

class NewParser:

    spacy_nlp: spacy.Language = spacy.load("en_core_web_trf") # TODO: Write in the documentation: You must install this!

    def __init__(self, logger: logging.Logger) -> None:
        self.logger: logging.Logger = logger

    def parse_single_content(self, content, new_id: int, type: str):

        try:

            parsed_content: NewContent = None

            if type == parser_constants.PDF_CONTENT:
                
                # Transform the content to readable PDF.
                pdf_article: PdfReader = PdfReader(io.BytesIO(content))

                pdf_content: NewContent = NewParser._parse_pdf(pdf_article)
                parsed_content: NewContent = pdf_content

                del pdf_article

            if type == parser_constants.READER_CONTENT: # Use beautiful soup

                soup_article: BeautifulSoup = BeautifulSoup(content, 'html.parser')

                new_content: NewContent = NewParser._parse_soup_article(soup_article, new_id)
                parsed_content: NewContent = new_content

                del soup_article

            if type == parser_constants.RAW_CONTENT: # Use NewsPaper3K
                
                article: Article = NewParser._get_article(content)

                new_content: NewContent = NewParser._parse_newspaper3k_article(article, new_id)
                parsed_content: NewContent = new_content

                del article

            return parsed_content

        except Exception as e:
            raise Exception(f'[{type}] - New identifier {new_id} {e}')

    def parse(self, raw_new: str, reader_mode_new: str, new_id: int):

        try:
            raw_content: NewContent = self.parse_single_content(content=raw_new, new_id=new_id, type=parser_constants.RAW_CONTENT)
            reader_content: NewContent = self.parse_single_content(content=reader_mode_new, new_id=new_id, type=parser_constants.READER_CONTENT)

            new_content: NewContent = NewParser.build_new_content(raw_content, reader_content, new_id)

            return new_content

        except Exception as e:
            raise Exception(f'[{parser_constants.RAW_READER_CONTENT}] - {e}')

    @staticmethod
    def build_new_content(raw_content: NewContent, reader_content: NewContent, new_id: int):

        try:
            final_content: NewContent = NewContent(
                title = None,
                text = None,
                publish_date = None,
                authors = None,
                language = None,
                top_img = None,
                movies = None,
                empty_new = True
            )

            NewParser.set_properties_from_reader(raw_content, reader_content, final_content)
            NewParser.set_properties_from_raw(raw_content, reader_content, final_content)
            
            final_content.determine_if_is_empty()

            return final_content
        except Exception as e:
            raise Exception(f'Could not build the final object of the new with identifier {new_id}. {e}')

    @staticmethod
    def set_properties_from_reader(raw_content: NewContent, reader_content: NewContent, final_content: NewContent):
        try:
            # Authors, title, body, language. 
            final_title: str = reader_content.title
            final_body: str = reader_content.text
            final_language: str = reader_content.language
            final_authors: list = reader_content.authors

            #If missing, then from raw content
            if final_title is None:
                final_title = raw_content.title

            if final_body is None:
                # If the reader's body is None, then we set the title, body and language from the raw_content
                final_body = raw_content.text
                final_language = raw_content.language
                final_title = raw_content.title

            if final_language is None:
                final_language = raw_content.language

            if final_authors is None:
                final_authors = raw_content.authors

            final_content.set_title(final_title)
            final_content.set_text(final_body)
            final_content.set_language(final_language)
            final_content.set_authors(final_authors)

        except Exception as e:
            raise Exception(f'Could not set the reader properties to the final new object. Reason {e}')
        
    @staticmethod
    def set_properties_from_raw(raw_content: NewContent, reader_content: NewContent, final_content: NewContent):
        try:
            final_publish_date: str = raw_content.publish_date
            final_top_image: str = raw_content.top_img
            final_media: list = raw_content.movies

            if final_publish_date is None:
                final_publish_date = reader_content.publish_date
            
            if final_top_image is None:
                final_top_image = reader_content.top_img

            if final_media is None:
                final_media = reader_content.movies

            final_content.set_publish_date(final_publish_date)
            final_content.set_top_image(final_top_image)
            final_content.set_media(final_media)

        except Exception as e:
            raise Exception(f'Could not set the raw properties to the final new object. Reason {e}')
        
    @staticmethod
    def _parse_pdf(pdf: PdfReader):

        try:
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

            title: str = NewParser._get_title_pdf(pdf)
            text: str = NewParser._get_body_pdf(pdf)
            publish_date: str = NewParser._get_publish_date_pdf(pdf)

            language: str = NewParser._guess_language(text)

            new_content.set_title(title)
            new_content.set_text(text)
            new_content.set_publish_date(publish_date)
            new_content.set_language(language)

            new_content.determine_if_is_empty()

            return new_content
        except Exception as e:
            raise Exception(f'Could not parse the PDF. Reason {e}')

    @staticmethod
    def _get_title_pdf(pdf: PdfReader):

        try:
            title_text: str = pdf.metadata.get('/Title', '')
            title: str = NewParser._tidy_title(title_text)
            title = title.replace('\x00', '')

            title_new: str = None
            if NewParser._is_valid(title):
                title_new = title

            return title_new
        except Exception as e:
            raise Exception(f'Could not get the title of the PDF. Reason {e}')
    @staticmethod
    def _get_body_pdf(pdf: PdfReader):

        try:
            body: str = ''
            for page_num in range(pdf._get_num_pages()):
                page_obj = pdf._get_page(page_num)
                body += page_obj.extract_text()
            
            body = NewParser._tidy_body(body)
            body = body.replace('\x00', '')

            body_new: str = None
            if NewParser._is_valid(body):
                body_new = body
            
            return body_new
        except Exception as e:
            raise Exception(f'Could not get the body of the PDF. Reason {e}')
        
    @staticmethod
    def _get_publish_date_pdf(pdf: PdfReader):

        try:
            date_not_parsed: str = pdf.metadata.get('/CreationDate', None)

            date_new: str = None
            if date_not_parsed is None or date_not_parsed == '':
                return date_new
            
            date_sliced: str = date_not_parsed[2:14]
            date: datetime = datetime.strptime(date_sliced, '%Y%m%d%H%M%S')
            formatted_date: str = date.strftime('%Y-%m-%d %H:%M')

            return formatted_date
        except Exception as e:
            raise Exception(f'Could not get the publish date of the PDF. Reason {e}')

    @staticmethod
    def _parse_soup_article(soup_article: BeautifulSoup, new_id: int):

        try:
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

            title: str = NewParser._get_title_soup(soup_article)
            text: str = NewParser._get_body_soup(soup_article)
            publish_date: str = NewParser._get_publish_date_soup(soup_article)
            authors: list = NewParser._get_authors_soup(soup_article)
            top_img: str = NewParser._get_top_image_soup(soup_article)

            language: str = NewParser._guess_language(text)


            new_content.set_title(title)
            new_content.set_text(text)
            new_content.set_publish_date(publish_date)
            new_content.set_authors(authors)
            new_content.set_top_image(top_img)
            new_content.set_language(language)

            new_content.determine_if_is_empty()
            return new_content

        except Exception as e:
            raise Exception(f'Could not parse the new. {e}')

    @staticmethod
    def _get_title_soup(soup_article: BeautifulSoup):
        try:
            title_element = soup_article.find(class_=parser_constants.CLASS_TITLE_READER)

            title_text: str = title_element.get_text()

            title: str = NewParser._tidy_title(title_text)

            title_new: str = None
            if NewParser._is_valid(title):
                title_new = title

            return title_new
        except Exception as e:
            raise Exception(f'Could not parse the title. Reason {e}')
        
    @staticmethod
    def _get_body_soup(soup_article: BeautifulSoup):
        try:
            body_element = soup_article.find(class_=parser_constants.CLASS_TEXT_READER)
            body_text: str = body_element.get_text() if body_element is not None else ''
            body: str = NewParser._tidy_body(body_text)

            body_new: str = None
            if NewParser._is_valid(body):
                body_new = body
            
            return body_new
        except Exception as e:
            raise Exception(f'Could not parse the body. Reason {e}')
        
    @staticmethod
    def _get_publish_date_soup(soup_article: BeautifulSoup):
        try:
            content_element = soup_article.find(class_=parser_constants.CLASS_TEXT_READER)
            date_candidates: list = content_element.find_all('time') if content_element is not None else list()

            date_new: str = None
            if len(date_candidates) != 0:
                date_new = date_candidates[0].get('datetime')

            if date_new == '':
                date_new = None

            if date_new is not None:
                date_new = NewParser._parse_date(date_new)
            

            return date_new
        except Exception as e:
            raise Exception(f'Could not parse the publish date. Reason {e}')

    @staticmethod
    def _get_authors_soup(soup_article: BeautifulSoup):
        try:
            authors_element = soup_article.find(class_=parser_constants.CLASS_AUTHORS_READER)

            authors: list = list()
            if authors is not None:
                authors: list = NewParser._get_authors_nlp(authors_element.get_text())

            new_authors: list = None
            if len(authors) != 0:
                new_authors = authors

            return new_authors

        except Exception as e:
            raise Exception(f'Could not parse the authors. Reason {e}')
        
    @staticmethod
    def _get_authors_nlp(authors: str):
        try:
            authors_nlp = NewParser.spacy_nlp(authors)

            authors: list = list()
            for word in authors_nlp.ents:
                
                if word.label_ == 'PERSON':
                    authors.append(word.text)

            return authors
        except Exception as e:
            raise Exception(f'Could not apply NLP with Spacy to get the named entities. Reason {e}')
    
    @staticmethod
    def _get_top_image_soup(soup_article: BeautifulSoup):
        try:
            content_element = soup_article.find(class_=parser_constants.CLASS_TEXT_READER)
            images: list = content_element.findAll('img') if content_element is not None else list()

            image_new: str = None
            if len(images) != 0:
                image_new = images[0].get('src') # TODO: Write DOC. We assume the top image is the first we find with the img HTML tag

            return image_new
        except Exception as e:
            raise Exception(f'Could not get the top image. Reason {e}')

    @staticmethod
    def _parse_newspaper3k_article(article: Article, new_id: int):
        try:
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
            article.parse()

            title: str = NewParser._get_title_newspaper3k(article)
            text: str  = NewParser._get_text_newspaper3k(article)
            publish_date: str = NewParser._parse_date(str(article.publish_date)) if article.publish_date is not None else None #TODO: Parse the date properly!
            authors: list = NewParser._get_authors_newspaper3k(article)
            language: str = NewParser._guess_language(text)
            top_image: str = NewParser._get_top_image(article)
            media: list = NewParser._get_media(article)

            new_content.set_title(title)
            new_content.set_text(text)
            new_content.set_publish_date(publish_date)
            new_content.set_authors(authors)
            new_content.set_language(language)
            new_content.set_top_image(top_image)
            new_content.set_media(media)
            
            new_content.determine_if_is_empty()
            
            return new_content

        except Exception as e:
            raise Exception(f'Could not parse the new. Reason {e}')

    @staticmethod
    def _get_text_newspaper3k(article: Article):

        try:
            body: str = article.text if article.text is not None else ''
            body = NewParser._tidy_body(body)

            new_body: str = None
            if NewParser._is_valid(body):
                new_body = body
            
            return new_body
        except Exception as e:
            raise Exception(f'Could not get the body with NewsPaper3k. Reason {e}')

    @staticmethod
    def _get_authors_newspaper3k(article: Article):
        try:
            authors: list = article.authors

            joined_authors: str = " ".join(authors)
            authors: list = NewParser._get_authors_nlp(joined_authors)

            new_authors: list = None
            if len(authors) != 0:
                new_authors = authors

            return new_authors
        except Exception as e:
            raise Exception(f'Could not get the authors. Reason {e}')

    @staticmethod
    def _get_title_newspaper3k(article: Article):

        try:
            title: str = article.title
            title = NewParser._tidy_title(title)

            new_title: str = None
            if NewParser._is_valid(title):
                new_title = title
            
            return new_title
        except Exception as e:
            raise Exception(f'Could not get the title with NewsPaper3k. Reason {e}')

    @staticmethod
    def _is_valid(text: str):
        
        is_valid: bool = text is not None and \
                         text != '' and \
                         parser_constants.LOREM_IPSUM_INVALID_WORDING not in text

        return is_valid

    @staticmethod
    def _tidy_text(text: str):
        try:
            split_return: str = " ".join(text.split('\n'))

            split_return = split_return.replace('\t', ' ')
            remove_repeated_whitespace: str = re.sub(' +', ' ', split_return)
            remove_repeated_whitespace = remove_repeated_whitespace.strip()
            
            replaced_apostrophe_possessive: str = NewParser._replace_apostrophe(remove_repeated_whitespace)

            result: str = replaced_apostrophe_possessive
            return result
        except Exception as e:
            raise Exception(f'Could not tidy the text. Reason: {e}')
    @staticmethod
    def _replace_apostrophe(text: str):

        try:
            replaced: str = re.sub(parser_constants.NORMALIZE_APOSTROPHES, '\'', text)
            result: str = replaced
            return result
        except Exception as e:
            raise Exception(f'Could not replace the apostrophe possessive. Reason {e}')
    @staticmethod
    def _tidy_title(title: str):
        
        try:
            tidy_title: str = NewParser._tidy_text(title)
            tidy_title = tidy_title.replace('_', ' ')
            tidy_title = re.sub(' +', ' ', tidy_title)
            tidy_title = tidy_title.strip()
            
            return tidy_title
        except Exception as e:
            raise Exception(f'Could not tidy the title. {e}')

    @staticmethod
    def _tidy_body(body: str):

        try:
            tidy_body = NewParser._tidy_text(body)
            return tidy_body
        except Exception as e:
            raise Exception(f'Could not tidy the body. {e}')

    @staticmethod
    def _format_date(date: str | datetime, new_id: int):

        try:
            date_format: str = parser_constants.DATE_FORMAT
            if type(date) == datetime:
                date_formated: str = date.strftime(date_format)
                date_object_formated: datetime = datetime.strptime(date_formated, date_format)

                return date_object_formated
            
            if type(date) == str:
                date_object: datetime = parser.parse(date)
                date_str: str = str(date_object).split('+')[0]
                date_object_formated: datetime = datetime.strptime(date_str, date_format)
                return date_object_formated
            
            return None

        except Exception as e:
            raise Exception(f'Could not parse the publish date of the new with identifier {new_id}. Date: {date}. Reason {e}')

    @staticmethod
    def _guess_language(text: str):
        # ISO 639-1 codes
        try:
            if text is None or text == '':
                return parser_constants.UNKNOWN_LANG
            
            return detect(text)
        except Exception as e:
            raise Exception(f'Could not determine the language of the new. Reason {e}')
    @staticmethod
    def _get_top_image(article: Article):
        try:
            top_img: str = article.top_img

            new_top_img: str = None
            if top_img is not None and top_img != '':
                new_top_img = top_img

            return new_top_img
        except Exception as e:
            raise Exception(f'Could not get the top image. Reason {e}')
        
    @staticmethod
    def _get_media(article: Article):
        try:
            media: list = article.movies

            new_media: list = None
            if media is not None and len(media) != 0:
                new_media = media

            return new_media
        except Exception as e:
            raise Exception(f'Could not get the media. Reason {e}')
        
    @staticmethod
    def _get_article(content: str):

        try:
            article: Article = Article('')
            article.html = content
            article.download_state = 2

            return article

        except Exception as e:
            raise Exception(f'Could not get the Article with NewsPaper3k. Reason {e}')
        
    @staticmethod
    def _parse_date(date):
        try: 
            if NewParser._is_timestamp(date):
                timestamp_date: int = int(date)
                if NewParser._is_in_miliseconds(timestamp_date):
                    timestamp_date /=  1000.0
                date_object = datetime.fromtimestamp(timestamp_date)
            else:
                date_object = parser.parse(date)

            formatted_date = date_object.strftime(parser_constants.DATE_FORMAT)
            return formatted_date
        except Exception as e:
            raise Exception(f'Could not parse de date {date}. Reason {e}')
        
    @staticmethod
    def _is_timestamp(date):
        try:
            int(date)
            return True
        except Exception as e:
            return False

    @staticmethod
    def _is_in_miliseconds(timestamp: int):
        return timestamp > time.mktime(time.gmtime())
