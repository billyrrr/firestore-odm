from typing import TypeVar

from marshmallow.utils import is_iterable_but_not_string

from firestore_odm.helpers import EmbeddedElement
from .model_registry import BaseRegisteredModel, ModelRegistry


# from abc import ABC, abstractmethod


class SchemedBase:

    @property
    def schema_obj(self):
        raise NotImplementedError

    @property
    def schema_cls(self):
        raise NotImplementedError


class Schemed(SchemedBase):
    """
    A mixin class for object bounded to a schema for serialization
        and deserialization.
    """

    _schema_obj = None
    _schema_cls = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self._schema_obj = self._schema_cls()

    @classmethod
    def get_schema_cls(cls):
        """ Returns the Schema class associated with the model class.
        """
        return cls._schema_cls

    @classmethod
    def get_schema_obj(cls):
        """ Returns an instantiated object for Schema associated
                with the model class
        """
        if cls._schema_obj is None:
            cls._schema_obj = cls._schema_cls()
        return cls._schema_obj

    @property
    def schema_cls(self):
        """ Returns the Schema class associated with the model object.
        """
        return self.get_schema_cls()

    @property
    def schema_obj(self):
        """ Returns an instantiated object for Schema associated
                with the model object.
        """
        return self.get_schema_obj()

    @classmethod
    def _get_fields(cls):
        fd = cls.get_schema_obj().fields
        return {
            key: val for key, val in fd.items() if key not in {"doc_id", }
        }

    #     """ TODO: find ways of collecting fields without reading
    #                 private attribute on Marshmallow.Schema
    #
    #     :return:
    #     """
    #     res = dict()
    #     for name, declared_field in cls.get_schema_obj().fields.items():
    #         if not declared_field.dump_only:
    #             res[name] = declared_field
    #     return res


class Importable:
    """
    When object subclass this mixin class, the object has the ability to
        be deserialized/loaded/set from a dictionary.
    """

    def _import_val(self, val, to_get=False):

        def embed_element(val: EmbeddedElement):
            d = val.d
            obj_type = d["obj_type"]
            obj_cls = BaseRegisteredModel.get_cls_from_name(obj_type)
            data = {key: val for key, val in d.items() if key != "obj_type"}
            obj = obj_cls()
            obj._import_properties(data)
            return obj

        if isinstance(val, EmbeddedElement):
            return embed_element(val)
        elif isinstance(val, dict) and "obj_type" in val:
            # Deserialize nested object
            obj_type = val["obj_type"]
            # TODO: check hierarchy
            #   (_registry is a singleton dictionary and flat for now)
            obj_cls = BaseRegisteredModel.get_cls_from_name(obj_type)

            obj = obj_cls.new(
                with_dict=val,
                to_get=to_get,
                doc_id=val.get("doc_id", None),
                transaction=self.transaction
            )
            raise NotImplementedError

        elif is_iterable_but_not_string(val):
            if isinstance(val, list):
                val_list = [self._import_val(elem, to_get) for elem in val]
                return val_list
            elif isinstance(val, dict):
                val_d = dict()
                for k, v in val.items():
                    val_d[k] = self._import_val(v, to_get)
                return val_d
            else:
                raise NotImplementedError

        else:
            return val

    def _import_properties(self, d: dict, to_get=False) -> None:
        """ TODO: implement iterable support
        TODO: test
        TODO: note that this method is not well-tested and most likely
                will fail for nested structures
        :param d:
        :return:
        """
        d = self.schema_obj.load(d)

        for key, val in d.items():
            # if key not in self.__get_dump_only_fields__():
            setattr(self, key, self._import_val(val, to_get=to_get))

    def update_vals(self, with_dict=None):
        if with_dict is None:
            with_dict = dict()
        for key, val in with_dict.items():
            setattr(self, key, self._import_val(val, to_get=False))

    @classmethod
    def from_dict(cls, d, to_get=False, **kwargs):
        instance = cls.new(**kwargs)  # TODO: fix unexpected arguments
        instance._import_properties(d, to_get=to_get)
        return instance


class Exportable:
    """
    When object subclass this mixin class, the object has the ability to
        be serialized/dumped/output into a dictionary.
    """

    def _export_val(self, val, to_save=False):
        """
        Private method for serializing an instance variable of the object.
        TODO: test nested

        :param val:
        :param to_save: If set to True, the changes made to an
                    object referenced by master object in
                    a relationship field will be saved. Otherwise,
                    changes are not saved, and the
                    TODO: Add support for atomicity
        :return:
        """

        def embed_element(val: EmbeddedElement):
            obj = val.obj
            return self._export_val(obj)

        if isinstance(val, Serializable):
            return val._export_as_dict(to_save=to_save)
        elif isinstance(val, EmbeddedElement):
            return embed_element(val)
        elif is_iterable_but_not_string(val):
            if isinstance(val, list):
                val_list = [self._export_val(elem, to_save) for elem in val]
                return val_list
            elif isinstance(val, dict):
                val_d = dict()
                for k, v in val.items():
                    val_d[k] = self._export_val(v, to_save)
                return val_d
            else:
                raise NotImplementedError
        else:
            return val

    def _export_as_dict(self, to_save=False) -> dict:
        """ Map/dict is only supported at root level for now
        TODO: implement iterable support
        :return:
        """
        d = self.schema_obj.dump(self)

        # print("----")
        # print(d)

        res = dict()
        for key, val in d.items():
            res[key] = self._export_val(val, to_save=to_save)

        return res

    def _export_val_view(self, val):

        def embed_element(val: EmbeddedElement):
            obj = val.obj
            return obj._export_as_view_dict()

        if isinstance(val, Serializable):
            return val._export_as_view_dict()
        if isinstance(val, EmbeddedElement):
            return embed_element(val)
        elif is_iterable_but_not_string(val):
            if isinstance(val, list):
                val_list = [self._export_val_view(elem) for elem in val]
                return val_list
            elif isinstance(val, dict):
                val_d = dict()
                for k, v in val.items():
                    val_d[k] = self._export_val_view(v)
                return val_d
            else:
                raise NotImplementedError
        else:
            return val

    def _export_as_view_dict(self) -> dict:
        """
        TODO: implement iterable support
        :return:
        """

        d = self.schema_obj.dump(self)

        res = dict()
        for key, val in d.items():
            if key not in self.schema_cls._get_reserved_fieldnames():
                res[key] = self._export_val_view(val)

        return res

    def to_dict(self):
        return self._export_as_dict()


class NewMixin:
    """
    Mixin class for initializing instance variable on creation.
    """

    @classmethod
    def new(cls, allow_default=True, **kwargs):
        """ Instantiates a new instance to the model.
                This is similar to the use of "new" in Java.
                It is recommended that you use "new" to initialize
                    an object, rather than the native initializer.

        :param allow_default: if set to False, an error will be
            raised if value is not provided for a field.
        :param kwargs: keyword arguments to pass to the class
            initializer.
        :return:
        """

        fd = cls._get_fields()  # Calls classmethod

        field_keys = {key for key, field in fd.items() if not field.dump_only}
        kwargs_keys = set(kwargs.keys())

        required_keys = {val for key, val in fd.items() if val.required}

        # Keys to set value from keyword arguments
        keys_to_set = kwargs_keys & field_keys
        # Keys to set to default value read from Field object from schema
        keys_default = field_keys - keys_to_set
        if not allow_default and len(keys_default) != 0:
            raise ValueError("{} are not set".format(keys_default))
        keys_super = kwargs_keys - keys_to_set - keys_default

        d_val_default = {key: field.default_value
                for key, field in fd.items() if key in keys_default}
        d_val_provided = {key: kwargs[key] for key in keys_to_set}
        d_super = {key: kwargs[key] for key in keys_super}

        return cls(_with_dict={**d_val_default, **d_val_provided}, **d_super)

    def __init__(self, _with_dict=None, **kwargs):
        """ Private initializer; do not call directly.
            Use "YourModelClass.new(...)" instead.

        :param _with_dict:
        :param kwargs:
        """
        if _with_dict is None:
            _with_dict = dict()

        for key, val in _with_dict.items():
            if key not in dir(self):
                setattr(self, key, val)

        super().__init__(**kwargs)


class SerializableMeta(ModelRegistry):
    """
    Metaclass for serializable models.
    """

    def __new__(mcs, name, bases, attrs):
        klass = super().__new__(mcs, name, bases, attrs)
        if hasattr(klass, "Meta"):
            # Moves Model.Meta.schema_cls to Model._schema_cls
            meta = klass.Meta
            if hasattr(meta, "schema_cls"):
                klass._schema_cls = meta.schema_cls
        return klass


class Mutable(BaseRegisteredModel,
              Schemed, Importable, NewMixin, Exportable):
    pass


class Immutable(BaseRegisteredModel, Schemed, NewMixin, Exportable):
    pass


class Serializable(Mutable, metaclass=SerializableMeta):

    # class Meta:
    #     """
    #     Options object for a Serializable model.
    #     """
    #     schema_cls = None

    pass


T = TypeVar('T')
U = TypeVar('U')
