from datetime import datetime
import requests
import click
import json
import models

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
        raise Exception(f"Error in get_dataset: {response.status_code}. {name}")
    return models.MicaDatasetModel.parse_obj(response.json())


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
        raise Exception(f"Error in get_study: {response.status_code}. {name}")
    return models.MicaStudyModel.parse_obj(response.json())


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
    # dataset = MicaDataset(get_dataset(dataset_id, auth))
    dataset = get_dataset(dataset_id, auth)

    # get the study id
    study_id = dataset.obiba_mica_CollectedDatasetDto_type.studyTable.studyId
    # get the study
    # study = MicaStudy(get_study(study_id, auth))
    study = get_study(study_id, auth)

    # convert content json to actual unescaped json
    dataset.content = json.loads(dataset.content)
    study.content = json.loads(study.content)
    for population in study.populations:
        population.content = json.loads(population.content)
        for data_collection_event in population.dataCollectionEvents:
            data_collection_event.content = json.loads(data_collection_event.content)

    output = models.MicaRootDataModel(
        dataset=dataset,
        study=study,
        metadata={"url": f"{auth.url}/dataset/{dataset_id}"},
    )

    click.echo(output.json(by_alias=True))
