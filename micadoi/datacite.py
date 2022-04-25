from pydantic import BaseModel
import requests
import click
import json
import mica
import models

DOI_REGEX = r"/^10.\d{4,9}/[-._;()/:A-Z0-9]+$/i"
DOI_PREFIX_REGEX = r"^10.\d{4,9}$/i"


class DataciteAuth:
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


def build_doi_attributes_from_mica(
    dataset: models.MicaDatasetModel,
    study: models.MicaStudyModel,
    metadata: dict,
):
    config = models.ConfigurationModel.parse_file("config.json")

    mica_config = config.mica

    model = models.DataciteModel(
        # required parameters
        prefix=mica_config.prefix,
        suffix=mica_config.suffix,
        url=metadata["url"],
        identifiers=[
            models.Identifier(
                identifier=f"https://doi.org/{mica_config.prefix}/{mica_config.suffix}",
                identifierType="DOI",
            ),
        ],
        creators=mica_config.creators,
        titles=[
            models.Title(title=dataset.name[0].value),
            models.Title(
                title=study.acronym[0].value,
                titleType="AlternativeTitle",
            ),
        ],
        publisher=mica_config.publisher,
        publicationYear=dataset.timestamps.created.year,
        resourceTypeGeneral=mica_config.resourceTypeGeneral,
        resourceType=mica_config.resourceType,
        # recommended parameters
        subjects=mica_config.subjects,
        # model.contributors
        dates=mica_config.dates,
        # model.RelatedIdentifiers
        descriptions=[
            models.Description(
                description=dataset.description[0].value,
                descriptionType="Abstract",
            ),
        ],
        geoLocations=mica_config.geoLocations,
        # optional parameters
        language=mica_config.language,
        version=mica_config.version,
    )

    return model


@click.command()
@click.option("--datacite-host", help="DataCite host")
@click.option("--datacite-user", help="DataCite user")
@click.option("--datacite-password", help="DataCite password")
@click.argument("mica_data_path")
def generate_mica_doi(
    datacite_host,
    datacite_user,
    datacite_password,
    mica_data_path,
):
    auth = DataciteAuth(datacite_host, datacite_user, datacite_password)
    url = f"{auth.url}/dois/"

    # load the mica json file
    data = models.MicaRootDataModel.parse_file(mica_data_path)

    doi_request = build_doi_attributes_from_mica(
        data.dataset, data.study, data.metadata
    )

    dto = models.CreateDOIDTO(
        data=models.DataAttributesDTO(type="dois", attributes=doi_request)
    )

    click.echo(dto.json())

    response = requests.post(
        url,
        json=dto.dict(),
        auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
    )
    if response.status_code != 201:
        click.echo(json.dumps(response.json(), indent=2))
        raise Exception(f"Error creating doi: {response.status_code}")

    click.echo(json.dumps(response.json(), indent=2))
