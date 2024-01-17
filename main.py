import pandas as pd
import json
from google.cloud import bigquery
from google.cloud.exceptions import GoogleCloudError, NotFound


def create_dataset_if_not_exists(client, project_id, dataset_id):
    """Creates a BigQuery dataset if it does not exist."""
    dataset_ref = client.dataset(dataset_id, project=project_id)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {dataset_id} already exists.")
    except NotFound:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"  # Specify the location
        client.create_dataset(dataset)
        print(f"Dataset {dataset_id} created.")


def load_csv_to_bigquery(csv_path, table_id, client):
    """Load CSV data into a BigQuery table."""
    dataframe = pd.read_csv(csv_path)
    job_config = bigquery.LoadJobConfig()
    job_config.autodetect = True
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE

    try:
        load_job = client.load_table_from_dataframe(dataframe, table_id, job_config=job_config)
        load_job.result()  # Wait for the job to finish
        print(f"The data from {csv_path} has been successfully loaded into {table_id}")
    except GoogleCloudError as e:
        raise RuntimeError(f"Error loading data from {csv_path} into BigQuery: {e}")


def load_config(config_path):
    """Load configuration from a JSON file."""
    with open(config_path, 'r') as file:
        return json.load(file)


if __name__ == "__main__":
    try:
        config = load_config('config.json')
        bigquery_client = bigquery.Client.from_service_account_json(config['json_path'])

        # Create dataset if it does not exist
        create_dataset_if_not_exists(bigquery_client, config['project_id'], config['dataset_id'])

        # Loading each CSV into its corresponding BigQuery table
        for csv_key, csv_path in config['csv_paths'].items():
            table_id = f"{config['project_id']}.{config['dataset_id']}.{csv_key}"
            load_csv_to_bigquery(csv_path, table_id, bigquery_client)

    except RuntimeError as e:
        print(e)