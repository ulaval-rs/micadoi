from jsonmodels import models, fields, validators
import requests
import click
import json
import mica

DOI_REGEX = r"/^10.\d{4,9}/[-._;()/:A-Z0-9]+$/i"
DOI_PREFIX_REGEX = r"^10.\d{4,9}$/i"


class DOICreator(models.Base):
    name = fields.StringField()
    affiliation = fields.ListField(str)
    nameIdentifiers = fields.ListField(str)


class DOITitle(models.Base):
    title = fields.StringField(required=True)


class DOIAttributes(models.Base):
    doi = fields.StringField()
    prefix = fields.StringField()
    event = fields.StringField()
    suffix = fields.StringField()
    identifiers = fields.ListField()
    alternateIdentifiers = fields.ListField()
    creators = fields.ListField(DOICreator)
    titles = fields.ListField(DOITitle)
    publisher = fields.StringField()
    container = fields.DictField()
    publicationYear = fields.IntField()
    contributors = fields.ListField()
    dates = fields.ListField()
    language = fields.StringField()
    types = fields.DictField()
    relatedIdentifiers = fields.ListField()
    sizes = fields.ListField()
    version = fields.StringField()
    rightsList = fields.ListField()
    descriptions = fields.ListField()
    geoLocations = fields.ListField()
    fundingReferences = fields.ListField()
    url = fields.StringField()
    contentUrl = fields.StringField()
    metadataVersion = fields.IntField()
    schemaVersion = fields.StringField()
    # isActive = fields.BoolField() # readonly
    # state = fields.StringField() # readonly
    # relationships (client ulaval.pulsar)
    # provider (ulaval)
    # media
    # references
    # citations
    # parts
    # partOf
    # versions
    # versionsOf


class PostDTO(models.Base):
    """
    Send an attribute package and a type of "dois" at POST /dois/
    Note that this DTO should be wrapped inside a {"data":<dto>} object

    DOIAttributes required:
        prefix (or doi, but prefix will auto-generate a suffix)
        creators
        titles
        publisher
        publicationYear
        types
            resourceTypeGeneral
        url
        schemaVersion

    """

    type = fields.StringField(default="dois")
    attributes = fields.EmbeddedField(DOIAttributes)


class UpdateDTO(models.Base):
    """
    Send an attribute package at PUT /dois/{prefix}/{suffix}
    Note that this DTO should be wrapped inside a {"data":<dto>} object
    """

    attributes = fields.EmbeddedField(DOIAttributes)


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


@click.command()
@click.option("--datacite-host", help="DataCite host")
@click.option("--datacite-user", help="DataCite user")
@click.option("--datacite-password", help="DataCite password")
@click.argument("doi")
def get_doi(datacite_host, datacite_user, datacite_password, doi):
    """
    Get a DOI
    """
    url = f"{datacite_host}/dois/{doi}"

    if datacite_user and datacite_password:
        auth = DataciteAuth(datacite_host, datacite_user, datacite_password)
        response = requests.get(
            url,
            auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
        )
    else:
        response = requests.get(
            url,
        )

    if response.status_code != 200:
        raise Exception(f"Error getting doi {doi}: {response.status_code}")
    click.echo(json.dumps(response.json(), indent=2))


@click.command()
@click.option("--datacite-host", help="DataCite host")
@click.option("--datacite-user", help="DataCite user")
@click.option("--datacite-password", help="DataCite password")
@click.option("--datacite-prefix", help="DataCite DOI prefix")
@click.option("--creator-path", help="DataCite Creator json file")
@click.argument("mica_data_path")
def generate_mica_doi(
    datacite_host,
    datacite_user,
    datacite_password,
    datacite_prefix,
    creator_path,
    mica_data_path,
):
    auth = DataciteAuth(datacite_host, datacite_user, datacite_password)
    url = f"{auth.url}/dois/"

    # load the mica json file
    data = None
    with open(mica_data_path, "r") as f:
        data = mica.load(json.load(f))

    # mica data
    mica_metadata = data["metadata"]
    mica_dataset = data["dataset"]
    mica_study = data["study"]
    mica_variables = data["variables"]

    dto = PostDTO()

    # Populate all attributes
    attributes = DOIAttributes()
    dto.attributes = attributes
    attributes.prefix = datacite_prefix
    # attributes.event = "publish"

    # load the creator object
    with open(creator_path, "r") as f:
        creator = DOICreator(**json.load(f))
    attributes.creators = [creator]

    # create the title object
    title = DOITitle(title=mica_dataset.name)
    attributes.titles = [title]

    attributes.publisher = mica_study.name
    attributes.publicationYear = mica_study.timestamps["created"].year

    attributes.url = mica_metadata["url"]
    attributes.schemaVersion = "http://datacite.org/schema/kernel-4"
    attributes.types = {
        "resourceTypeGeneral": "Dataset",
    }

    response = requests.post(
        url,
        json={"data": dto.to_struct()},
        auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
    )
    if response.status_code != 201:
        raise Exception(f"Error creating doi: {response.status_code}")

    click.echo(json.dumps(response.json(), indent=2))


@click.command()
@click.option("--datacite-host", help="DataCite host")
@click.option("--datacite-user", help="DataCite user")
@click.option("--datacite-password", help="DataCite password")
@click.argument("doi")
@click.argument("attributes_path")
def update_doi(
    datacite_host,
    datacite_user,
    datacite_password,
    doi,
    attributes_path,
):
    auth = DataciteAuth(datacite_host, datacite_user, datacite_password)
    url = f"{auth.url}/dois/{doi}"

    dto = UpdateDTO()

    # Populate all attributes
    with open(attributes_path, "r") as f:
        attributes = DOIAttributes(**json.load(f))
    dto.attributes = attributes

    response = requests.put(
        url,
        json={"data": dto.to_struct()},
        auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
    )
    if response.status_code != 200:
        raise Exception(f"Error updating doi: {response.status_code}")

    click.echo(json.dumps(response.json(), indent=2))


@click.command()
@click.option("--datacite-host", help="DataCite host")
@click.option("--datacite-user", help="DataCite user")
@click.option("--datacite-password", help="DataCite password")
@click.argument("doi")
def publish_doi(datacite_host, datacite_user, datacite_password, doi):
    auth = DataciteAuth(datacite_host, datacite_user, datacite_password)
    url = f"{auth.url}/dois/{doi}"

    dto = UpdateDTO()

    attributes = DOIAttributes(event="publish")
    dto.attributes = attributes

    response = requests.put(
        url,
        json={"data": dto.to_struct()},
        auth=requests.auth.HTTPBasicAuth(auth.username, auth.password),
    )
    if response.status_code != 200:
        raise Exception(f"Error updating doi: {response.status_code}")

    click.echo(json.dumps(response.json(), indent=2))
