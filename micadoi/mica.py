from datetime import datetime
import requests
import click
import json

DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DATASET_ENDPOINT = "/ws/draft/collected-dataset/{}/"
STUDY_ENDPOINT = "/ws/draft/individual-study/{}/"


class MicaDataset:
    def __init__(self, raw_data):
        self.data = raw_data
        self.lang = "en"

    @property
    def id(self):
        return self.data["id"]

    @property
    def name(self):
        for lang_obj in self.data["name"]:
            if lang_obj["lang"] == self.lang:
                return lang_obj["value"]

    @property
    def acronym(self):
        for lang_obj in self.data["acronym"]:
            if lang_obj["lang"] == self.lang:
                return lang_obj["value"]

    @property
    def custom_content(self):
        return self.data["content"]

    @property
    def raw_content(self):
        return self.data

    @property
    def studyId(self):
        return self.data["obiba.mica.CollectedDatasetDto.type"]["studyTable"]["studyId"]

    @property
    def populationId(self):
        return self.data["obiba.mica.CollectedDatasetDto.type"]["studyTable"][
            "populationId"
        ]

    @property
    def dataCollectionEventId(self):
        return self.data["obiba.mica.CollectedDatasetDto.type"]["studyTable"][
            "dataCollectionEventId"
        ]

    @property
    def table(self):
        return self.data["obiba.mica.CollectedDatasetDto.type"]["studyTable"]["table"]

    @property
    def entityType(self):
        return self.data["entityType"]

    @property
    def published(self):
        return self.data["published"]

    @property
    def timestamps(self):
        converted_timestamps = {}
        for key, value in self.data["timestamps"].items():
            converted_timestamps[key] = datetime.strptime(value, DATETIME_FORMAT)
        return converted_timestamps

    @property
    def variableTypes(self):
        return self.data["variableType"]


class MicaStudy:
    def __init__(self, raw_data):
        self.data = raw_data
        self.lang = "en"

    @property
    def id(self):
        return self.data["id"]

    @property
    def name(self):
        for lang_obj in self.data["name"]:
            if lang_obj["lang"] == self.lang:
                return lang_obj["value"]

    @property
    def acronym(self):
        for lang_obj in self.data["acronym"]:
            if lang_obj["lang"] == self.lang:
                return lang_obj["value"]

    @property
    def custom_content(self):
        return self.data["content"]

    @property
    def raw_content(self):
        return self.data

    @property
    def timestamps(self):
        converted_timestamps = {}
        for key, value in self.data["timestamps"].items():
            converted_timestamps[key] = datetime.strptime(value, DATETIME_FORMAT)
        return converted_timestamps

    @property
    def objectives(self):
        for lang_obj in self.data["objectives"]:
            if lang_obj["lang"] == self.lang:
                return lang_obj["value"]


class MicaAuth:
    """
    Authentication Object
    """

    url = None
    username = None
    password = None

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password


def get_dataset(name: str, auth: MicaAuth):
    """
    Takes a dataset name (e.g. "cag-baseline") and an auth DTO
    returns a requests.Response object on 200, raise an exception otherwise
    """
    path = f"{auth.url}/ws/draft/collected-dataset/{name}"

    headers = {"Accept": "application/json, */*"}
    response = requests.get(
        path,
        auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
        headers=headers,
    )
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")
    return response.json()


def get_study(name: str, auth: MicaAuth):
    """
    Takes a study name (e.g. "cag") and an auth DTO
    returns a requests.Response object on 200, raise an exception otherwise
    """

    path = f"{auth.url}/ws/draft/individual-study/{name}"

    headers = {"Accept": "application/json, */*"}
    response = requests.get(
        path,
        auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
        headers=headers,
    )
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")
    return response.json()


def get_variables(dataset_id: str, limit: int, locale: str, auth: MicaAuth):
    """
    Uses the mica rest API's rql system to select all variables related to a specific dataset
    returns a requests.Response object on 200, raise an exception otherwise
    """

    path = f"{auth.url}/ws/variables/_rql?query=dataset(in(Mica_dataset.id,{dataset_id})),variable(limit(0,{limit}),fields(attributes.label.*,attributes.description.*,variableType,valueType,categories.*,unit,attributes.Mlstr_area*),sort(index,name)),locale({locale})"  # noaq: E501

    headers = {"Accept": "application/json, */*"}
    response = requests.get(
        path,
        auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
        headers=headers,
    )
    if response.status_code != 200:
        raise Exception(f"Error: {response.status_code}")
    return response.json()


@click.command()
@click.option("--mica-host", help="Mica host")
@click.option("--mica-user", help="Mica user")
@click.option("--mica-password", help="Mica password")
@click.argument("dataset_id")
def extract(mica_host, mica_user, mica_password, dataset_id):
    if not mica_host:
        raise Exception("Mica host is required")
    if not mica_user:
        raise Exception("Mica user is required")
    if not mica_password:
        raise Exception("Mica password is required")

    # create auth object
    auth = MicaAuth(mica_host, mica_user, mica_password)

    # download dataset metadata
    dataset = MicaDataset(get_dataset(dataset_id, auth))

    # determine number of variables
    variable_count = get_variables(dataset_id, 1, "en", auth)["variableResultDto"][
        "totalHits"
    ]

    # download all variables related to dataset
    variables = get_variables(dataset_id, variable_count, "en", auth)[
        "variableResultDto"
    ]["obiba.mica.DatasetVariableResultDto.result"]["summaries"]

    # remove repetitive data from variables
    # (they each have the study and dataset name, among other things)
    cleaned_variables = []
    for variable in variables:
        cleaned_variables.append(
            {
                "id": variable["id"],
                "name": variable["name"],
                "variableType": variable["variableType"],
                "variableLabel": variable["variableLabel"],
                "annotations": variable["annotations"],
                "valueType": variable["valueType"],
                "categories": variable.get("categories", []),
            }
        )

    # get the study id
    study_id = dataset.studyId

    # get the study
    study = MicaStudy(get_study(study_id, auth))

    click.echo(
        json.dumps(
            {
                "metadata": {
                    "url": f"{auth.url}/dataset/{dataset_id}",
                },
                "dataset": dataset.data,
                "study": study.data,
                "variables": cleaned_variables,
            },
            indent=2,
        )
    )


def load(json_data):
    """
    Loads a JSON object into a MicaDataset object (and related objects)
    """
    return {
        "metadata": json_data["metadata"],
        "dataset": MicaDataset(json_data["dataset"]),
        "study": MicaStudy(json_data["study"]),
        "variables": json_data["variables"],
    }
