# MicaDOI
Export mica datasets and generate DOI for them on DataCite.

## Required environment variables
The following code snippets will suppose that you have set the following environment variables:

```sh
export MICA_USER=administrator
export MICA_PASSWORD=password
export MICA_HOST="https://mica-demo.obiba.org/"

export DATACITE_CLIENT=ULAVAL.PULSAR
export DATACITE_PASSWORD=#password-goes-here
export DATACITE_HOST="https://api.test.datacite.org"
export DATACITE_DOI_PREFIX="10.82134" # this is specific to the ULAVAL.PULSAR client
```

In this case, we're using the mica demo server and our DataCite test account. Refer to your department for the datacite credentials.

## Usage
Note: when refering to datasets, it is implied that we're talking about the metadata, not the data itself. This tool does not support the download of data for now.

### Download a dataset's metadata from a mica instance
With the `extract` command, we download the `cag-baseline` dataset and pipe the resulting json into a cag-baseline.json file. This file will contain information that will be used to build a DataCite metadata record.

```sh
# extract a specific dataset from mica
poetry run python micadoi/ extract \
  --mica-host $MICA_HOST \
  --mica-user $MICA_USER \
  --mica-password $MICA_PASSWORD \
  cag-baseline > cag-baseline.json
```

You can inspect the resulting json. The tool extracts the dataset metadata, its related study and variables.

### Create a new DOI using a mica metadata json file
With the `generate-mica-doi` command, we generate a new DOI using the mica metadata json file. One special value of a DOI's metadata is the Creators attribute, which is a list of creators with their name, affiliation and identifiers (e.g. ORCID). Create à creators.json file containing the following:
```jsonc
// creators.json
{
    "name": "Me",
    "affiliation": [
        "ulaval"
        // can be an empty list instead
    ],
    "nameIdentifiers": [
        "my-orcid"
        // can be an empty list instead
    ]
}


```

Now execute the following command, specifying our creator.json file with the --creator-path flag.

```sh
# create a new DOI based on an extracted mica dataset
poetry run python micadoi/ generate-mica-doi \
  --datacite-host $DATACITE_HOST \
  --datacite-user $DATACITE_CLIENT \
  --datacite-password $DATACITE_PASSWORD \
  --datacite-prefix $DATACITE_DOI_PREFIX \
  --creator-path creator.json \
  cag-baseline.json > cag-baseline.doi.json
```

The result is piped into a file `cag-baseline.doi.json`. The id found in this json file is the doi. Whether the result is piped to a file or not, the doi is not created in draft mode.

### Get a DOI
With the `get-doi` command, we query the DataCite API for a specific DOI.
If the datacite-user and datacite-password options are not specified, the query will be in publiic mode, which mean it will fail with a 404 Not Found command is a DOI is not published.

```sh
# get a particular doi in json format from dataCite
poetry run python micadoi/ get-doi \
  --datacite-host $DATACITE_HOST \
  --datacite-user $DATACITE_CLIENT \
  --datacite-password $DATACITE_PASSWORD \
  "10.82134/zrry-fb53" > doi.json
```

Here we download the json output of the `10.82134/zrry-fb53` DOI and pipe it into doi.json.

### Update a DOI's attributes
As you might have seen by inspecting the output of the get-doi command, a doi has a specific structure where most of its data is found in an `attributes` object. Updates to a DOI's information is done by modifying this object. The 'update-doi' command will update the doi's attributes with a specified attributes json file.

Start by creating a `attributes.json` file as a single json object (which represents the attributes to update), then add elements to update as necessary. Refer to the DataCite API documentation for the list of attributes. Here is an example where we update the title of the DOI. By default the title of cag-baseline DOI generated through this tool will be `CaG-Baseline`:
```jsonc
// attributes.json
{
    "titles": [
        {
            "title": "CaG-Baseline-v2"
        }
    ]
}
```

```sh
# update a DOI with attributes from a file
poetry run python micadoi/ update-doi \
  --datacite-host $DATACITE_HOST \
  --datacite-user $DATACITE_CLIENT \
  --datacite-password $DATACITE_PASSWORD \
  "10.82134/zrry-fb53" attributes.json
```

### Publish a DOI (make it findable)
With the `publish-doi` command, we make a DOI findable on the DataCite platform. Under the hood, this is the same as executing a update-doi command with `{"event": "publish"}` as the attributes json file.

```sh
# update a DOI with the event:public flag, making it findable
poetry run python micadoi/ publish-doi \
  --datacite-host $DATACITE_HOST \
  --datacite-user $DATACITE_CLIENT \
  --datacite-password $DATACITE_PASSWORD \
  "10.82134/zrry-fb53"
```

There are three states to a DOI:
* draft
* registered
* findable

If you want to unpublish a DOI, you can use the update-doi command with a `{"event": "hide"}` attributes json file.

Alternatively, if you want to register but not publish a draft doi, you can use the update-doi command with a `{"event": "register"}` attributes json file.

The status of a DOI is found in it's `state` attribute.
