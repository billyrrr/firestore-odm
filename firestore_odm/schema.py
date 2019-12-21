import warnings

from firestore_odm.errors import PropertyEvalError
from firestore_odm.utils import attr_name_to_firestore_key, \
    firestore_key_to_attr_name
from firestore_odm.utils import obj_type_serialize, obj_type_deserialize
from . import fields
import marshmallow
from marshmallow import post_dump, pre_load, post_load, EXCLUDE


class SchemaMixin:

    f = staticmethod(attr_name_to_firestore_key)
    g = staticmethod(firestore_key_to_attr_name)

    def on_bind_field(self, field_name, field_obj):
        """Hook to modify a field when it is bound to the `Schema`.

        No-op by default.
        """

        if field_obj.attribute is None:
            field_obj.attribute = field_name

        if field_obj.data_key is None:
            default_data_key = self.f(field_obj.attribute)
            field_obj.data_key = default_data_key

        # if field_obj.attribute in self.f_mapping:
        #     raise ValueError
        # else:
        #     self.f_mapping[field_obj.attribute] = field_obj.data_key
        #
        # if field_obj.data_key in self.g_mapping:
        #     raise ValueError
        # else:
        #     self.g_mapping[field_obj.data_key] = field_obj.attribute

    def __init__(self, *args, **kwargs):
        if "unknown" not in kwargs:
            # The assumption made is that if-condition on existence of
            #   key in kwargs is a better design than explicit kwarg = None,
            #   since, as an example, `EXCLUDE is None` may be True, as it
            #   is from an external dependency.
            # TODO: note that unknown passed by positional arg is not caught
            unknown = EXCLUDE
        else:
            unknown = kwargs["unknown"]
        super().__init__(
            *args,
            unknown=unknown,
            **kwargs)
        #
        # self.f_mapping = dict()
        # self.g_mapping = dict()


class BusinessPropertyStoreSchemaMixin():
    pass


class BoilerProperty(object):
    """
    Ref: https://blog.csdn.net/weixin_43265804/article/details/82863984
        content under CC 4.0
    """

    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        self.__doc__ = doc

    def __get__(self, instance, owner):
        if instance is None:
            return self
        else:
            try:
                return self.fget(instance)
            except Exception as exception:
                """
                Otherwise AttributeError will be swallowed 
                """
                raise PropertyEvalError from exception

    def __set__(self, instance, value):
        self.fset(instance, value)

    def __delete__(self, instance):
        self.fdel(instance)

    def getter(self, fget):
        return BoilerProperty(fget, self.fset, self.fdel, self.__doc__)

    def setter(self, fset):
        return BoilerProperty(self.fget, fset, self.fdel, self.__doc__)

    def deleter(self, fdel):
        return BoilerProperty(self.fget, self.fset, fdel, self.__doc__)


class SchemaBase(SchemaMixin, marshmallow.Schema):

    @classmethod
    def _get_reserved_fieldnames(cls):
        return set()


class BasicSchema(SchemaBase):
    pass


class Schema(SchemaBase):
    """
    Attributes:
    ============
    obj_type: fields.Function
        Exports and imports class name of an instance for differentiating
            different subclasses of PrimaryObject in the same collection.
    doc_id: firestore document id
        Caution: probable pitfall; doc_id won't be valid if obj is
            not a subclass of firestore object; watch out for strange
            behaviors such as doc_id being setted twice.
            A possible mistake can be setting doc_id after doc_id is
            read, since two doc_id for the same object can be observed.
    """

    obj_type = fields.Function(
        attribute="obj_type",
        data_key="obj_type",
        dump_only=True,
        serialize=obj_type_serialize,
        deserialize=obj_type_deserialize)

    doc_id = fields.Str(
        attribute="doc_id",
        dump_only=True,
        data_key="doc_id",
        required=False
    )

    doc_ref = fields.Str(
        attribute="doc_ref_str",
        dump_only=True,
        data_key="doc_ref",
        required=False
    )

    @classmethod
    def _get_reserved_fieldnames(cls):
        """ Returns a list of fieldnames to hide when calling
            "to_view_dict" on view model

        :return:
        """
        return {"obj_type", "doc_id", "doc_ref"}


def _get_field(variable_key) -> fields.Field:
    warnings.warn("_get_field is returning wildcard field")
    return fields.Raw(
            load_from=attr_name_to_firestore_key(variable_key)
        )


def _get_field_vars(var_names, fd) -> dict:
    """

    :param var_names: A list of (instance) variable names
    :param fd:
    :return:
    """
    field_vars = dict()
    for var_name in var_names:
        if var_name in fd:
            field_vars[var_name] = _get_field(var_name)
    return field_vars


def _get_instance_variables(obj_cls) -> list:
    """
    Returns a dict of instance variable name: default value
    Note that this method does not work for now
    :param obj_cls:
    :return:
    """
    # init_func: function = obj_cls.__init__
    res = obj_cls.__init__.__code__.co_names
    return list(res)


def generate_schema(obj_cls) -> Schema:
    """
    Generates
    :param obj:
    :return:
    """

    def constructor(self, obj_cls):
        Schema.__init__(self)
        self.obj_cls = obj_cls

    # A list of all fields to serialize and deserialize
    fd = obj_cls.get_fields()

    @post_load
    def make_temp_obj(self, data: dict, **kwargs):
        obj = self.obj_cls()
        for k, v in data.items():
            key, value = firestore_key_to_attr_name(k), v
            if key in fd:
                setattr(obj, key, value)
        return obj

    instance_vars = _get_instance_variables(obj_cls)
    field_vars = _get_field_vars(instance_vars, fd)

    TempSchema = type("TempSchema", (Schema,),
                      {
                          "__init__": constructor,
                          "make_temp_obj": make_temp_obj,
                          **field_vars
                      }
    )

    return TempSchema(obj_cls)
