from typing import Union
from pydantic import BaseModel, Field
from datetime import datetime


class Identifier(BaseModel):
    identifier: str
    identifierType: str


class Creator(BaseModel):
    name: str
    affiliation: str


class Title(BaseModel):
    title: str
    titleType: str = None


class Subject(BaseModel):
    subject: str
    subjectScheme: str
    schemeURI: str
    valueURI: str


class Contributor(BaseModel):
    name: str
    affiliation: str
    contributorType: str


class Date(BaseModel):
    date: str
    dateType: str
    dateInformation: str = None


class Description(BaseModel):
    description: str
    descriptionType: str


class GeoLocation(BaseModel):
    geoLocationPlace: str = None
    geoLocationPoint: str = None
    geoLocationBox: str = None
    geoLocationPolygon: str = None


class Right(BaseModel):
    rightURI: str
    rightsIdentifier: str
    rightsIdentifierScheme: str
    schemeURI: str


class RelatedIdentifier(BaseModel):
    relatedIdentifier: str
    relatedIdentifierType: str
    relationType: str


class DataciteModel(BaseModel):
    """
    Datacite submission model
    """

    # required
    prefix: str
    suffix: str
    url: str
    identifiers: list[Identifier]
    creators: list[Creator]
    titles: list[Title]
    publisher: str
    publicationYear: int
    resourceTypeGeneral: str
    resourceType: str

    # recommended
    subjects: list[Subject]
    contributors: list[Contributor] = None
    dates: list[Date]
    RelatedIdentifiers: list[RelatedIdentifier] = None
    descriptions: list[Description]
    geoLocations: list[GeoLocation]

    # optional
    language: str = None
    rights: list[Right] = None
    formats: list[str] = None
    version: str = None


class DataAttributesDTO(BaseModel):
    type: str = "dois"
    attributes: DataciteModel


class CreateDOIDTO(BaseModel):
    data: DataAttributesDTO


# MICA


class Named(BaseModel):
    lang: str
    value: str


class Timestamps(BaseModel):
    created: datetime
    updated: datetime = None


class CollectedDatasetDtoStudyTable(BaseModel):
    project: str
    table: str
    studyId: str
    populationId: str
    dataCollectionEventId: str
    dceId: str
    weight: int


class CollectedDatasetDto(BaseModel):
    studyTable: CollectedDatasetDtoStudyTable


class EntityStateDto(BaseModel):
    revisionsAhead: int
    revisionStatus: str


class MicaDatasetModel(BaseModel):
    """
    Mica submission model
    """

    id: str
    name: list[Named]
    acronym: list[Named]
    description: list[Named]
    entityType: str
    published: bool
    timestamps: Timestamps
    variableType: str
    content: Union[str, dict]
    obiba_mica_CollectedDatasetDto_type: CollectedDatasetDto = Field(
        alias="obiba.mica.CollectedDatasetDto.type"
    )
    obiba_mica_EntityStateDto_datasetState: EntityStateDto = Field(
        alias="obiba.mica.EntityStateDto.datasetState"
    )


class DataCollectionEvent(BaseModel):
    # id: str
    # name: str
    startDate: str = None
    content: Union[str, dict]
    weight: int


class Population(BaseModel):
    id: str
    name: list[Named]
    description: list[Named]
    entityType: str = None
    dataCollectionEvents: list[DataCollectionEvent]
    content: Union[str, dict]
    weight: int


class MicaStudyModel(BaseModel):
    """
    Mica submission model
    """

    id: str
    timestamps: Timestamps
    name: list[Named]
    acronym: list[Named]
    objectives: list[Named]
    populations: list[Population]
    content: Union[str, dict]
    published: bool
    studyResourcePath: str


class MicaRootDataModel(BaseModel):
    metadata: dict
    dataset: MicaDatasetModel
    study: MicaStudyModel


# configuration
class MicaConfigurationModel(BaseModel):
    prefix: str
    suffix: str
    language: str
    version: str
    publisher: str
    resourceTypeGeneral: str
    resourceType: str
    subjects: list[Subject]
    creators: list[Creator]
    dates: list[Date]
    geoLocations: list[GeoLocation]


class ConfigurationModel(BaseModel):
    """
    Configuration model
    """

    mica: MicaConfigurationModel
