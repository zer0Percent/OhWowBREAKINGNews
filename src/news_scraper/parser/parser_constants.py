RAW_NEW_PRELOADED_WORDING = 'raw_new'

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

#CONTENT TYPES
RAW_CONTENT = 'RAW CONTENT'
READER_CONTENT = 'READER CONTENT'
RAW_READER_CONTENT = 'RAW & READER'
PDF_CONTENT = 'PDF'


#READER MODE CONSTANTS
CLASS_TITLE_READER = 'reader-title'
CLASS_TEXT_READER = 'moz-reader-content reader-show-element'
CLASS_AUTHORS_READER = 'credits reader-credits'

#CLEANING REGEX
REMOVE_P_TAG_WEBARCHIVE_REGEX = r"<p>The Wayback Machine - https:\/\/web\.archive\.org\/web\/.*?<\/p>"
REMOVE_HTML_ENTITIES_REGEX = r'&[^;]{0,5};'
NORMALIZE_APOSTROPHES = r'#39;|&#39;|"|ʺ|“|”|ˊ|˴|‘|´|`|ˈ|ʿ|ˋ|ʼ|ʻ|ˮ|’|ʽ|ʹ|ʾ|\''

#WORDINGS
UNKNOWN_LANG = 'unknown'
PDF_WORDING = '.pdf'
LOREM_IPSUM_INVALID_WORDING = 'Sed ut perspiciatis'
