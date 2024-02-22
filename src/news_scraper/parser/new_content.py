class NewContent:

    def __init__(self, title: str, text: str,
                 publish_date: str, authors: list, language: str,
                 top_img: str, movies: list, empty_new: bool) -> None:
        
        self.title: str = title
        self.text: str = text
        self.publish_date: str = publish_date
        self.authors: list = authors
        self.language: str = language
        self.top_img: str = top_img
        self.movies: list = movies
        self.empty_new: bool = empty_new

    def set_title(self, new_title: str):
        self.title = new_title

    def set_text(self, new_text: str):
        self.text = new_text
    
    def set_publish_date(self, date: str):
        self.publish_date = date

    def set_authors(self, authors: list):
        self.authors = authors

    def set_language(self, new_language: str):
        self.language = new_language

    def set_top_image(self, top_img: str):
        self.top_img = top_img

    def set_media(self, media: list):
        self.movies = media

    def determine_if_is_empty(self):
       self.empty_new =  self.title is None and \
               self.text is None and \
               self.publish_date is None and \
               self.authors is None and \
               self.top_img is None and \
               self.movies  is None



    