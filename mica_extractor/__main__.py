import requests
import argparse
import json


parser = argparse.ArgumentParser(description="Mica data extractor")

parser.add_argument("--username", help="username")
parser.add_argument("--password", help="password")
parser.add_argument("--url", help="url")
parser.add_argument("--dataset", help="dataset")


class Auth:
    """
    Authentication DTO
    """

    url = None
    username = None
    password = None

    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password


class Dataset:
    """
    Simple container to facilitate extraction of specific information (like name and id)
    """

    def __init__(self, json_data: dict):
        self.data = json_data

    def get_id(self):
        return self.data["id"]

    def get_name(self, lang):
        for lang_obj in self.data["name"]:
            if lang_obj["lang"] == lang:
                return lang_obj["value"]

    def get_custom_content(self):
        return self.data["content"]

    def get_study_id(self):
        return self.data["obiba.mica.CollectedDatasetDto.type"]["studyTable"][
            "studyId"
        ]  # noaq: E501

    def __str__(self):
        return f"<Dataset {self.get_id()} (Study: {self.get_study_id()})>"


class Study:
    """
    Simple container to facilitate extraction of specific information (like name and id)
    """

    def __init__(self, json_data: dict):
        self.data = json_data

    def get_id(self):
        return self.data["id"]

    def get_name(self, lang):
        for lang_obj in self.data["name"]:
            if lang_obj["lang"] == lang:
                return lang_obj["value"]

    def __str__(self):
        return f"<Study {self.get_id()}>"


def get_dataset(name: str, auth: Auth):
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
    return response


def get_study(name: str, auth: Auth):
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
    return response


def get_variables(dataset_id: str, limit: int, locale: str, auth: Auth):
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
    return response


def main():
    # parse input, or request manual input on missing data
    args = parser.parse_args()
    username = args.username or input("Username: ")
    password = args.password or input("Password: ")
    url = args.url or input("Url: ")
    dataset_id = args.dataset or input("Dataset id: ")
    auth = Auth(url, username, password)

    # get the dataset
    dataset = Dataset(get_dataset(dataset_id, auth).json())
    print(Dataset)

    # get variable count (find all variables, limit of 1, then get the total hits count)
    variable_count = get_variables(dataset_id, 1, "en", auth).json()[
        "variableResultDto"
    ]["totalHits"]

    # get all variables
    variables = get_variables(dataset_id, variable_count, "en", auth).json()[
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
    study_id = dataset.get_study_id()
    print(study_id)

    # get the study
    study = Study(get_study(study_id, auth).json())
    print(Study)

    # output the data
    with open(f"output/{dataset_id}.json", "w") as f:
        f.write(
            json.dumps(
                {
                    "dataset": dataset.data,
                    "study": study.data,
                    "variables": cleaned_variables,
                },
                indent=4,
            )
        )


if __name__ == "__main__":
    main()
