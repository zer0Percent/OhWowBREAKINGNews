I would really **appreciate** it if you find this tool interesting — please mention it in your work and let me know! <br>
✨Happy scraping!✨

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/xctkst44k5o)

# OhWowBREAKINGNews (✨Thread's Version✨)
**OhWowBREAKINGNews (✨Thread's Version✨)** is a multithreaded scraper, based on Selenium, that helps you retrieve the content of news articles by specifying their URLs. This tool consists of two parts that are executed separately:

1. A scraper that retrieves two formats of the article's HTML: what we call the `raw` format (the entire HTML article), and the `reader mode` format (the article content opened with Firefox Reader Mode).
2. A parser that, given the `raw` and/or `reader` format, extracts all relevant information and stores it in a PostgreSQL table.

# How It Works

The tool launches several headless Firefox browsers depending on the number of threads you specify. Each thread performs a GET request using the provided news URL. To use this tool, you will need to download the Geckodriver for Selenium automation.

The scraping process is summarized in the following diagram:

![Alt text here](new_scraper_schema.png)

Given a news URL, the tool checks whether the domain uses a paywall. If not, it retrieves all available timestamps from the Web Archive. If timestamps exist, the tool filters for those that return HTTP status codes in the [200–300] range. For each URL, all timestamps are stored locally to avoid repeated API calls.

If a paywall is detected, the scraper applies the relevant paywall bypass method from the local `newmodeling` database and formats the URL accordingly.

If no timestamps are found, the tool attempts to access and scrape the original input URL.

# Database Tables

Two PostgreSQL databases are required: one for the raw/reader HTML articles and another for the parsed content. The required table definitions are split into two files: `new_data.sql` and `new_modeling.sql`.

We recommend backing up your databases and storing them in a secure location in case something goes wrong (you don’t want to lose your data!).

## Scraper

To run the scraper, create two databases: one to store scraped HTML and one for parsed content.

### News Scraper

#### `new_data.sql` file

This file defines three tables used during scraping:

`dbo.url_domain`: Stores paywall method information for each domain. If the domain of a candidate URL isn’t listed, the scraper will default to using the Web Archive. Fields:

- `id`: Identifier for the domain and subdomains <br>
- `subdomain_name`: Subdomain <br>
- `domain_name`: Domain name <br>
- `suffix`: Domain suffix <br>
- `paywall_method`: Applied paywall method. Options:
  - `no_method` <br>
  - `remove_paywall` <br>
  - `12ft_ladder` <br>
- `checked`: Flag indicating the domain was manually reviewed for paywalls <br>

After creating the table, populate it with `url_domain.sql`.

`dbo.web_archive_new`: Stores timestamps retrieved from the Web Archive to avoid redundant API calls. Fields:

- `id`: Unique identifier for the record <br>
- `new_id`: ID of the news item from the input CSV <br>
- `potential_urls`: List of timestamp URLs and their HTTP status codes <br>
- `is_empty`: Flag indicating whether any timestamps exist <br>
- `is_retrieved`: Flag indicating whether timestamps were retrieved <br>

`dbo.preloaded_content`: Prevents reloading large CSVs already imported. Fields:

- `id`: Unique identifier <br>
- `data_source`: Dataset name <br>

`dbo.raw_new`: Stores both `raw` and `reader` mode HTML. Fields:

- `id`: Unique identifier for the record <br>
- `new_id`: News ID from the input CSV <br>
- `original_url`: URL to be scraped <br>
- `raw_new`: Raw HTML content <br>
- `reader_mode_new`: Reader mode HTML content <br>
- `is_empty`: Flag for empty content <br>
- `is_retrieved`: Flag for successful retrieval <br>
- `parsed`: Flag indicating whether it was parsed <br>
- `should_rescrape`: Flag indicating if both HTMLs are empty and re-scraping might be needed <br>
- `data_source`: Dataset name <br>

### State Definitions (`dbo.raw_new` and `dbo.web_archive_new`)

- **State 1**: `is_empty = false AND is_retrieved = false` → Not yet scraped  
- **State 2**: `is_empty = false AND is_retrieved = true` → Successfully retrieved  
- **State 3**: `is_empty = true AND is_retrieved = true` → Retrieval failed  

#### `new_modeling.sql` file

This file defines one table for parsed content:

`dbo.parsed_new`: Fields:

- `id`: Unique identifier <br>
- `new_id`: News ID from input <br>
- `title`: News title <br>
- `body`: News body <br>
- `publish_date`: Publication date <br>
- `authors`: List of authors <br>
- `language`: Language of the article <br>
- `top_image_url`: Top image URL <br>
- `media_content_urls`: Linked media URLs <br>
- `is_empty`: Flag for empty parsed content  
  A news article is considered empty if all of: `title`, `body`, `publish_date`, `authors`, `top_image_url`, and `media_content_urls` are `null`. <br>
- `data_source`: Dataset name <br>

### News Parser

The parser extracts data from `raw_new` and `reader_mode_new` in `dbo.raw_new`, storing it in `dbo.parsed_new`.

Parsing logic depends on which formats are present:

- If both `raw_new` and `reader_mode_new` have content:  
  - Extract `title`, `body`, `language`, `authors` from `reader_mode_new`  
  - Extract `publish_date`, `top_image_url`, `media_content_urls` from `raw_new`

- If only `reader_mode_new` is present: parse only that

- If only `raw_new` is present: parse only that

# Requirements

Just clone the repository and:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Install the SpaCy model for author NER:
   ```bash
   python -m spacy download en_core_web_trf
   ```

3. Install the latest version of Mozilla Firefox

4. Download the latest [Geckodriver](https://github.com/mozilla/geckodriver/releases) and place it in the `ohwowbreakingnews` folder

5. Install PostgreSQL (we recommend [pgAdmin](https://www.pgadmin.org/download/) for ease of use)

   5.1. Create the databases `newdata` and `newmodeling` <br>
   5.2. Create the `dbo` schema in both <br>
   5.3. Run `new_data.sql` on `newdata`, and `new_modeling.sql` on `newmodeling` <br>
   5.4. Run `url_domain.sql` on the `dbo.url_domain` table in `newdata` <br>

# CSV Format for URLs

The input CSV must have two columns: `id` and `url`. Example:

```csv
id,url
38,"www.abcd.com"
606,"www.hahahaha.com"
947,"www.idontknow.com"
```

# Running the Tool

Before running, configure your `database.toml` file by setting the `user` and `password` fields.

We use two database connections:

- `connection`: Connects to `newdata` (raw HTML)
- `parsed_new_connection`: Connects to `newmodeling` (parsed data)

## News Scraper

Run from the `./OhWowBREAKINGNews/` folder:

```bash
python new_scraper_main.py [-c CHUNK_SIZE] [-t THREADS] [-f CSV_FILE] [-s DATASET_NAME]
```

- `-c`: Number of news articles per chunk  
- `-t`: Number of threads (browsers to open in parallel)  
- `-f`: Path to the input CSV  
- `-s`: Dataset name (must be unique)

## News Parser

Run from `src/news_scraper/parser/`:

```bash
python new_parser_main.py [-s DATASET_NAME]
```

- `-s`: Name of the dataset you want to parse