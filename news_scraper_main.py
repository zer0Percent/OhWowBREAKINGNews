import argparse
from src.news_scraper.news_scraper_runner import NewsScraperRunner

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--chunk_size", type=int, default=15)
    parser.add_argument("-t", "--threads", type=int, default=4)
    parser.add_argument("-f", "--csv_file", type=str, default=None)
    parser.add_argument("-s", "--data_source", type=str, default=None)

    args = parser.parse_args()

    urls_path: str = args.csv_file
    if urls_path is None:
        raise Exception(f'No URLs were provided. Closing tool...')
    
    dataset_name: str = args.data_source
    if dataset_name is None:
        raise Exception(f'No dataset name was provided. Closing tool...') 
    
    chunk_size = args.chunk_size
    threads = args.threads

    new_scraper_runner: NewsScraperRunner = NewsScraperRunner(
        urls_path=urls_path,
        threads=threads,
        chunk_size=chunk_size,
        dataset_name=dataset_name
    )

    new_scraper_runner.start()