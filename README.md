# MicaDOI
Export mica datasets and generate DOI for them on DataCite.

## Required environment variables
The following code snippets suppose that you have set the following environment variables:

```sh
export MICA_USER=administrator
export MICA_PASSWORD=password
export MICA_HOST="https://mica-demo.obiba.org/"

export DATACITE_CLIENT=<my-datacite-client>
export DATACITE_PASSWORD=<my-datacite-password>
export DATACITE_HOST="https://api.test.datacite.org"
```

In this case, we're using the mica demo server and our DataCite test account. Refer to your department for the datacite credentials.

## Usage
Note: when refering to datasets, it is implied that we're talking about the metadata, not the data itself. This tool does not support the download of data for now.

### Download a dataset's metadata from a mica instance
With the `extract` command, we download the `cag-baseline` dataset and pipe the resulting json into a output/cag-baseline.mica.json file. This file will contain information that will be used to build a DataCite metadata record.

```sh
# extract a specific dataset from mica
poetry run python micadoi/ extract \
  --mica-host $MICA_HOST \
  --mica-user $MICA_USER \
  --mica-password $MICA_PASSWORD \
  cag-baseline > output/cag-baseline.mica.json
```

You can inspect the resulting json. The tool extracts the dataset metadata, its related study and variables.

### Update config.json with the missing information
Some metadata is not present in mica. To fix this, a config.json file contains all the required metadata and must be updated by the user to generate a correct DOI.

See the example config.json file. All fields are required for now. The will become optional if the metadata is somehow added to mica.

# Generate the DOI
It's not time to generate our DOI from our downloaded metadata. We specify the credentials and the path to out *.mica.json file.

```sh
# create a new DOI based on an extracted mica dataset
poetry run python micadoi/ generate-mica-doi \
  --datacite-host $DATACITE_HOST \
  --datacite-user $DATACITE_CLIENT \
  --datacite-password $DATACITE_PASSWORD \
  output/cag-baseline.mica.json > output/cag-baseline.doi.json
```

The result is piped into a file `output/cag-baseline.doi.json`. The id found in this json file is the doi.

The DOI is created in draft mode. This means you can access [DataCite Fabrica]() or [it's test sibling](https://doi.test.datacite.org/repositories/ulaval.pulsar) to inspect, update and publish your DOI.
