WEB_ARCHIVE_NEW_PRELOADED_WORDING = 'web_archive_new'
RAW_NEW_PRELOADED_WORDING = 'raw_new'


WAIT_TIME_REQUEST = 40
WAIT_TIME_READER_MODE_GOT_URL_REDIRECTION_REQUEST = 90
WAIT_TIME_REQUEST_NO_WEBARCHIVE = 4
WAIT_TIME_REDIRECT_SATUS_CODE = 100
WAIT_TIME_REQUEST_PAYWALL = 10

WAIT_TIME_WEBARCHIVE_ERROR = 30

IFRAME_12FTLADDER_XPATH = '/html/body/iframe'

WEB_ARCHIVE_CANDIDATES_TRIALS = 5
WEB_ARCHIVE_RESPONSE_PROPERTIES = ['urlkey', 'timestamp', 'original', 'mimetype', 'statuscode', 'digest', 'length']
WEB_ARCHIVE_BASE_URL = 'https://web.archive.org/web/{timestamp}/{base_url}'
WEBARCHIVE_URL_CANDIDATES_BASE_URL = 'http://web.archive.org/cdx/search/cdx?url={url}'

INVALID_WEB_ARCHIVE_STATUS_CODE = ['401', '508', '403', '502', '402', '405', '429', '520', '500', '409', '404', '-']
REDIRECT_WEB_ARCHIVE_STATUS_CODE = ['308', '301', '307', '302','303']


READER_MODE_BASE_URL = 'about:reader?url='

NOT_POSSIBLE = 'not_possible'
NO_PAYWALL_METHOD = 'no_method'
FT_LADDER = '12ft_ladder'
REMOVE_PAYWALL = 'remove_paywall'
LOGIN_METHOD = 'login' 
PENDING = 'pending'

FT_LADDER_BASE_URL = 'https://12ft.io/{url}'
REMOVE_PAYWALL_BASE_URL = 'https://www.removepaywall.com/{url}'
PAYWALL_METHODS_URLS = {
    FT_LADDER: FT_LADDER_BASE_URL,
    REMOVE_PAYWALL: REMOVE_PAYWALL_BASE_URL
}

PDF_EXTENSION = '.pdf'
HEADER_REQUEST_PDF_FILES = {'User-Agent': 'Mozilla/5.0 (X11; Windows; Windows x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}

NOT_ARCHIVED_URL_IN_WEBARCHIVE_WORDING = 'The Wayback Machine has not archived that URL.'
EXCLUDED_FROM_WEB_ARCHIVE_WORDING = 'This URL has been excluded from the Wayback Machine.'
INVALID_TITLE_READER_MODE = '<title id="reader-title">Internet Archive logo</title>'

DONT_HAVE_PERMISSION_WORDING = "You don''t have permission to access"
ERROR_LOADING_PAGE_WORDING_SPANISH_READER_MODE = 'Fallo al cargar el '
ERROR_LOREM_IPSUM_WORDING = 'Sed ut perspiciatis'
ERROR_REDIRECTING_WEBARCHIVE_WORDING = 'Redirecting to...'

REGEX_INVALID_TITLE = r'(?:^|\s)log in(?:^|\s)|(?:^|\s)wayback machine(?:^|\s)|(?:^|\s)gateway time-out(?:^|\s)|(?:^|\s)attention required!(?:^|\s)|(?:^|\s)access denied(?:^|\s)|(?:^|\s)page does not exist(?:^|\s)|(?:^|\s)error page(?:\s|$)|^error$|(?:^|\s)cannot be found(?:\s|$)|(?:^|\s)page not found(?:\s|$)|(?:^|\s)file not found(?:\s|$)|(?:^|\s)service unavailable(?:\s|$)|(?:^|\s)server error(?:\s|$)|(?:^|\s)content not available(?:\s|$)|(?:^|\s)page is missing(?:\s|$)|(?:^|\s)webpage does not exist(?:\s|$)|(?:^|\s)unable to find the requested page(?:\s|$)|(?:^|\s)the page you\'re looking for is not here(?:\s|$)|(?:^|\s)this URL does not lead to an existing page(?:\s|$)|(?:^|\s)the requested resource is missing(?:\s|$)|(?:^|\s)the page you entered could not be located(?:\s|$)|(?:^|\s)webpage unavailable(?:\s|$)|(?:^|\s)unable to locate page(?:\s|$)|(?:^|\s)page does not exist(?:\s|$)|(?:^|\s)page missing(?:\s|$)|(?:^|\s)resource not found(?:\s|$)|(?:^|\s)the requested page could not be found(?:\s|$)|(?:^|\s)this page isn\'t available(?:\s|$)|(?:^|\s)the URL you entered could not be found on the server(?:\s|$)|(?:^|\s)page is inaccessible(?:\s|$)|(?:^|\s)the requested URL is not found(?:\s|$)|(?:^|\s)this webpage is not available(?:\s|$)|(?:^|\s)the URL you\'re trying to access does not exist(?:\s|$)|(?:^|\s)the resource you\'re trying to access is not available(?:\s|$)|(?:^|\s)apologies the requested page is not available(?:\s|$)|(?:^|\s)regrettably the webpage you\'re trying to access does not exist(?:\s|$)|(?:^|\s)unfortunately the URL you entered could not be located(?:\s|$)|(?:^|\s)sorry the resource you\'re looking for is missing(?:\s|$)|(?:^|\s)regretfully the page you\'re trying to reach is inaccessible(?:\s|$)|(?:^|\s)4[0-9]{2}(?:\s|$)|(?:^|\s)5[0-9]{2}(?:\s|$)|(?:^|\s)4[0-9]{2}.0(?:\s|$)|(?:^|\s)5[0-9]{2}.0(?:\s|$)'
REGEX_INVALID_BODY  = r'Don\'t have an account? Sign up(?:^|\s)|(?:^|\s)too many requests(?:^|\s)|(?:^|\s)is parked free, courtesy of godaddy.com(?:^|\s)|(?:^|\s)cannot be found(?:\s|$)|(?:^|\s)page not found(?:\s|$)|(?:^|\s)can\'t find the page(?:\s|$)|(?:^|\s)cannot find the page(?:\s|$)|(?:^|\s)service unavailable(?:\s|$)|(?:^|\s)server error(?:\s|$)|(?:^|\s)page is missing(?:\s|$)|(?:^|\s)webpage does not exist(?:\s|$)|(?:^|\s)unable to find the requested page(?:\s|$)|(?:^|\s)the page you\'re looking for is not here(?:\s|$)|(?:^|\s)this URL does not lead to an existing page(?:\s|$)|(?:^|\s)the page you entered could not be located(?:\s|$)|(?:^|\s)webpage unavailable(?:\s|$)|(?:^|\s)unable to locate page(?:\s|$)|(?:^|\s)page does not exist(?:\s|$)|(?:^|\s)page missing(?:\s|$)|(?:^|\s)the requested page could not be found(?:\s|$)|(?:^|\s)this page isn\'t available(?:\s|$)|(?:^|\s)the URL you entered could not be found on the server(?:\s|$)|(?:^|\s)page is inaccessible(?:\s|$)|(?:^|\s)the requested URL is not found(?:\s|$)|(?:^|\s)this webpage is not available(?:\s|$)|(?:^|\s)the URL you\'re trying to access does not exist(?:\s|$)|(?:^|\s)apologies the requested page is not available(?:\s|$)|(?:^|\s)regrettably the webpage you\'re trying to access does not exist(?:\s|$)|(?:^|\s)unfortunately the URL you entered could not be located(?:\s|$)|(?:^|\s)regretfully the page you\'re trying to reach is inaccessible(?:\s|$)'