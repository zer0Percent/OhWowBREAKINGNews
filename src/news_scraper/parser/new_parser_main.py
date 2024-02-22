import argparse

from new_parser_runner import NewParserRunner

if __name__ == '__main__':

    
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--data_source", type=str, default=None)

    args = parser.parse_args()
    dataset_name: str = args.data_source
    if dataset_name is None:
        raise Exception(f'No dataset name was provided. Closing tool...')
    
    new_parser_runner = NewParserRunner(dataset_name)
    new_parser_runner.start()