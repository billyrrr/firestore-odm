"""
Note that test setup is UNRELIABLE.
Class may persist in registry (of metaclass) across tests.

"""
import json

import pytest as pytest
from functools import lru_cache

from firestore_odm import factory, serializable
from firestore_odm import schema, fields


@pytest.fixture
@lru_cache(maxsize=1)
def ModelASchema():
    class ModelASchema(schema.Schema):
        int_a = fields.Integer(load_from="intA", dump_to="intA")
        int_b = fields.Integer(load_from="intB", dump_to="intB")
    return ModelASchema

@pytest.fixture
@lru_cache(maxsize=1)
def ModelA(ModelASchema):

    class ModelA(serializable.Serializable):
        _schema_cls = ModelASchema

    return ModelA


def test_create_model():

    class ModelKSchema(schema.Schema):
        int_a = fields.Integer(load_from="intA", dump_to="intA")
        int_b = fields.Integer(load_from="intB", dump_to="intB")

    class ModelK(serializable.Serializable):
        class Meta:
            schema_cls = ModelKSchema

    obj: ModelK = ModelK.new()

    assert obj.int_a == 0
    assert obj.int_b == 0

    assert obj.to_dict() == {
        "intA": 0,
        "intB": 0,
        "obj_type": "ModelK",
    }


def test_cls_factory(ModelA):
    obj: ModelA = ModelA.new()

    assert obj.int_a == 0
    assert obj.int_b == 0

    obj.int_a = 1
    obj.int_b = 2

    assert obj.int_a == 1
    assert obj.int_b == 2

    assert obj.to_dict() == {
        "intA": 1,
        "intB": 2,
        "obj_type": "ModelA",
    }


def test_from_dict(ModelA):

    obj = ModelA.from_dict({
        "intA": 1,
        "intB": 2,
        "obj_type": "ModelA",
    })

    assert isinstance(obj, ModelA)
    assert obj.int_a == 1
    assert obj.int_b == 2


def test__additional_fields(ModelASchema, ModelA):

    class ModelAASchema(ModelASchema):
        int_aa = fields.Integer(load_from="intAA", dump_to="intAA")

    obj_a = ModelA.new()

    assert hasattr(obj_a, "int_a")
    assert not hasattr(obj_a, "int_aa")

    ModelAA = factory.ClsFactory.create(
        name="ModelAA",
        schema=ModelAASchema
    )
    obj_aa = ModelAA.new()
    assert hasattr(obj_aa, "int_a")
    assert hasattr(obj_aa, "int_aa")


def test_default_value(ModelA):

    obj_a = ModelA.new()

    assert obj_a.int_a == 0


def test_property_fields():
    class ModelAPSchema(schema.Schema):
        some_property = fields.Function(dump_only=True)

    def fget(self):
        return 8

    sp = property(fget=fget)

    class ModelAP(serializable.Serializable):
        _schema_cls = ModelAPSchema

    ModelAP.some_property = sp

    obj_a = ModelAP.new()

    assert obj_a.some_property == 8


def test_multiple_inheritance(ModelASchema):

    class ModelBSchema(schema.Schema):
        int_b = fields.Integer(load_from="intB", dump_to="intB")

    class ModelABSchema(ModelASchema, ModelBSchema):
        pass

    ModelAB = factory.ClsFactory.create(
        name="ModelAB",
        schema=ModelABSchema
    )

    ab = ModelAB.new()
    ab.int_a = 1
    ab.int_b = 2

    assert ab.int_a == 1
    assert ab.int_b == 2

    assert ab._export_as_dict().items() >= {
        "intA": 1,
        "intB": 2
    }.items()


def test__export_as_dict(ModelA):

    a = ModelA.new()
    a.int_a = 1
    a.int_b = 2

    assert a._export_as_dict() == {
        "intA": 1,
        "intB": 2,
        "obj_type": "ModelA",
    }


def test__import_properties(ModelA):

    a = ModelA.new()
    a._import_properties({
        "intA": 1,
        "intB": 2,
    })

    assert a.int_a == 1
    assert a.int_b == 2


def test_separate_class():
    """
    Tests experimental code for decorator pattern implementation

    :return:
    """

    class SModelASchema(schema.Schema):
        int_a = schema.fields.Integer(load_from="intA", dump_to="intA")
        int_b = schema.fields.Integer(load_from="intB", dump_to="intB")

    class SModelASerializable(serializable.Serializable):
        _schema_cls = SModelASchema

        def __init__(self, **kwargs):
            super().__init__(**kwargs)

    class SModelAModel(object):

        def __init__(self):
            self.int_a = 0
            self.int_b = 0

    class SModelA(SModelAModel, SModelASerializable):

        def __init__(self, **kwargs):
            super().__init__()
            super(SModelASerializable, self).__init__(**kwargs)

    a = SModelA.new()
    a.int_a = 1
    a.int_b = 2

    assert a._export_as_dict() == {
        "intA": 1,
        "intB": 2,
        "obj_type": "SModelA",
    }


def test_embedded():
    class TargetSchema(schema.Schema):
        earliest = fields.Raw()
        latest = fields.Raw()

    class Target(serializable.Serializable):
        _schema_cls = TargetSchema

    t = Target()
    t.earliest = 10
    t.latest = 20

    class PlanSchema(schema.Schema):
        target = fields.Embedded()
        name = fields.Str()

    class Plan(serializable.Serializable):
        _schema_cls = PlanSchema

    k = Plan.from_dict({
        "target": t.to_dict(),
        "name": "my plan"
    })

    assert k.name == "my plan"
    assert isinstance(k.target, Target)
    assert k.target.earliest == 10
    assert k.target.latest == 20

    assert k.to_dict() == {
        "name": "my plan",
        "target": {
            "earliest": 10,
            "latest": 20,
            "obj_type": "Target",
        },
        "obj_type": "Plan",
    }


def test_embedded_many_with_dict():
    class SpeciesSchema(schema.Schema):
        scientific_name = fields.Str()
        weight = fields.Str()
        habitats = fields.Embedded(many=True)
        related_species = fields.Embedded(many=True)

    class Species(serializable.Serializable):
        _schema_cls = SpeciesSchema

    class EndangeredSpeciesSchema(SpeciesSchema):
        pass

    class EndangeredSpecies(serializable.Serializable):
        _schema_cls = EndangeredSpeciesSchema

    class HabitatSchema(schema.Schema):
        habitat_name = fields.Str()

    class Habitat(serializable.Serializable):
        _schema_cls = HabitatSchema

    forests = Habitat.new(habitat_name="Forests")
    grasslands = Habitat.new(habitat_name="Grasslands")

    jaguar = Species.new(
        scientific_name="Panthera onca",
        habitats=[forests, grasslands]
    )

    cold_high_mountains = Habitat.new(
        habitat_name="cold high mountains")

    snow_leopard = Species.new(
        scientific_name="Panthera uncia",
        habitats=[cold_high_mountains]
    )

    temperate = Habitat.new(habitat_name="Temperate")
    broadleaf = Habitat.new(habitat_name="Broadleaf")
    mixed_forests = Habitat.new(habitat_name="Mixed Forests")

    amur_leopard = EndangeredSpecies.new(
        scientific_name="Panthera pardus orientalis",
        weight="70 - 105 pounds",
        habitats=[temperate, broadleaf, mixed_forests],
        related_species={
            "jaguar": jaguar,
            "snow leopard": snow_leopard
        }
    )

    d = {
        "obj_type": "EndangeredSpecies",
        "relatedSpecies": {
            "jaguar": {
                "obj_type": "Species",
                "relatedSpecies": [],
                "scientificName": "Panthera onca",
                "weight": "",
                "habitats": [
                    {
                        "obj_type": "Habitat",
                        "habitatName": "Forests"
                    },
                    {
                        "obj_type": "Habitat",
                        "habitatName": "Grasslands"
                    }
                ]
            },
            "snow leopard": {
                "obj_type": "Species",
                "relatedSpecies": [],
                "scientificName": "Panthera uncia",
                "weight": "",
                "habitats": [
                    {
                        "obj_type": "Habitat",
                        "habitatName": "cold high mountains"
                    }
                ]
            }
        },
        "scientificName": "Panthera pardus orientalis",
        "weight": "70 - 105 pounds",
        "habitats": [
            {
                "obj_type": "Habitat",
                "habitatName": "Temperate"
            },
            {
                "obj_type": "Habitat",
                "habitatName": "Broadleaf"
            },
            {
                "obj_type": "Habitat",
                "habitatName": "Mixed Forests"
            }
        ]
    }

    assert d == amur_leopard.to_dict()

    amur_leopard_deserialized = EndangeredSpecies.from_dict(d)

    assert amur_leopard_deserialized.to_dict() == d
