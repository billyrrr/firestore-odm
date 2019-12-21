import pytest
from firestore_odm import fields
from firestore_odm.primary_object import PrimaryObject
from firestore_odm.schema import Schema
from .utils import _delete_all


class DomainModel(PrimaryObject):
    """
    Domain model is intended for handling business logic.
    """
    pass


class CitySchema(Schema):
    city_name = fields.Raw()

    country = fields.Raw()
    capital = fields.Raw()


class MunicipalitySchema(CitySchema):
    pass


class StandardCitySchema(CitySchema):
    city_state = fields.Raw()
    regions = fields.Raw(many=True)


class City(DomainModel):
    class Meta:
        schema_cls = CitySchema
        collection_name = "City"


class Municipality(City):
    class Meta:
        schema_cls = MunicipalitySchema


class StandardCity(City):
    class Meta:
        schema_cls = StandardCitySchema


@pytest.fixture
def setup_cities(request, CTX):

    def fin():
        _delete_all(collection_name="City", CTX=CTX)

    request.addfinalizer(fin)

    sf = StandardCity.new(doc_id="SF")
    sf.city_name, sf.city_state, sf.country, sf.capital, sf.regions = \
        'San Francisco', 'CA', 'USA', False, ['west_coast', 'norcal']
    sf.save()

    la = StandardCity.new(doc_id="LA")
    la.city_name, la.city_state, la.country, la.capital, la.regions = \
        'Los Angeles', 'CA', 'USA', False, ['west_coast', 'socal']
    la.save()

    dc = Municipality.new(doc_id="DC")
    dc.city_name, dc.country, dc.capital = 'Washington D.C.', 'USA', True
    dc.save()

    tok = Municipality.new(doc_id="TOK")
    tok.city_name, tok.country, tok.capital = 'Tokyo', 'Japan', True
    tok.save()

    beijing = Municipality.new(doc_id="BJ")
    beijing.city_name, beijing.country, beijing.capital = \
        'Beijing', 'China', True
    beijing.save()
