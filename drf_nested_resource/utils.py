import re
import itertools

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.fields.related import (
    ManyRelatedObjectsDescriptor,
    RelatedObject,
)
from django.contrib.contenttypes import generic
from django.core.exceptions import ImproperlyConfigured

from drf_nested_resource.compat import singular_noun


def is_generic_relationship_pair(parent_field, child_field):
    """
    Given a field from the parent model and a field from the child model
    """
    if not isinstance(child_field, generic.GenericForeignKey):
        return False

    if not isinstance(parent_field, generic.GenericRelation):
        return False

    child_model = child_field.model

    ct_field = child_model._meta.get_field(child_field.ct_field)
    fk_field = child_model._meta.get_field(child_field.fk_field)

    expected_ct_field = child_model._meta.get_field(
        parent_field.content_type_field_name,
    )
    expected_fk_field = child_model._meta.get_field(
        parent_field.object_id_field_name,
    )

    return (
        ct_field == expected_ct_field and fk_field == expected_fk_field
    )


def find_child_to_parent_accessor_name(parent_model, child_model):
    # ForeignKey relationship
    for field in child_model._meta.fields:
        if isinstance(field, models.ForeignKey) and field.rel.to is parent_model:
            return field.name

    # ManyToMany relationship where the field is declared on the `child_model`
    for field in child_model._meta.many_to_many:
        if field.rel.to is parent_model:
            return field.attname

    # ManyToMany relationship where the field is declared on the `parent_model`
    for field in parent_model._meta.many_to_many:
        if field.rel.to is child_model:
            return field.rel.related_name

    # GenericForeignKey relationship
    for parent_field, child_field in itertools.product(parent_model._meta.virtual_fields, child_model._meta.virtual_fields):
        if is_generic_relationship_pair(parent_field, child_field):
            return child_field.name

    raise ImproperlyConfigured(
        "Parent model '{0}' cannot be found for model '{1}'.".format(
            parent_model._meta.model_name, child_model._meta.model_name)
    )


def find_child_to_parent_serializer_field(serializer_class, parent_accessor_name):
    """
    Given a serializer class (for the child model) and the name of the
    attribute on the child model which references the parent model, find the
    name of the serializer field that *likely* references the parent model.
    """
    serializer = serializer_class()

    def is_serializer_field(name):
        return name in serializer.get_fields()

    # keep track of the values that were checked for nice error message reporting.
    checked = [parent_accessor_name]

    # there may be a serializer field by the exact name of the child to
    # parent accessor attribute.
    if is_serializer_field(parent_accessor_name):
        return parent_accessor_name

    # it may be something like a ForeignKey whech has the `_id` suffix.
    child_model = serializer.Meta.model
    try:
        field = child_model._meta.get_field(parent_accessor_name)
        checked.append(field.attname)
        if is_serializer_field(field.attname):
            return field.attname
    except FieldDoesNotExist:
        pass

    raise ImproperlyConfigured(
        "Unable to find field on serializer that parent model.  Checked {0}. "
        "You may need to declare `parent_serializer_field` on your view if the "
        "field is not in one of these locations.".format(
            checked,
        )
    )


def get_virtual_field(model, field_name):
    matched_fields = filter(
        lambda f: f.name == field_name,
        model._meta.virtual_fields,
    )

    if len(matched_fields) == 1:
        return matched_fields[0]
    raise FieldDoesNotExist(
        "{!r} has no virtual field named {!r}".format(
            model,
            field_name,
        )
    )


def camel_case_to_snake_case(value):
    """
    source: http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
    """
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', value)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def compute_default_url_kwarg_for_parent(parent_model, child_model):
    """
    Given a `parent_model` and a `child_model` which
    """
    parent_accessor_name = find_child_to_parent_accessor_name(
        parent_model=parent_model,
        child_model=child_model,
    )

    # ForeignKey and ManyToManyField strategies
    try:
        field = child_model._meta.get_field(parent_accessor_name)
    except FieldDoesNotExist:
        pass
    else:
        if isinstance(field, models.ManyToManyField):
            # this isn't generic enough as it only accounts for fields that
            # are named with the pluralization of the other model that ends
            # with an `s`.
            return '{0}_{1}'.format(singular_noun(field.name), 'pk')
        elif isinstance(field, models.ForeignKey):
            return '{0}_{1}'.format(field.name, 'pk')
        else:
            raise ImproperlyConfigured(
                "No known strategy for computing url kwarg for field of type {!r}".format(
                    type(field),
                )
            )

    # GenericForeignKey strategy
    try:
        field = get_virtual_field(child_model, parent_accessor_name)
    except FieldDoesNotExist:
        pass
    else:
        return '{0}_{1}'.format(
            camel_case_to_snake_case(parent_model._meta.object_name),
            'pk',
        )

    # ManyToManyField from *other* side of the relationship.
    child_to_parent_accessor = getattr(child_model, parent_accessor_name, None)
    if isinstance(child_to_parent_accessor, ManyRelatedObjectsDescriptor):
        return '{0}_{1}'.format(
            singular_noun(parent_accessor_name),
            'pk',
        )

    raise ImproperlyConfigured(
        "No known strategy found for computing the url parameter for model "
        "{!r}.  You may need to declare `parent_url_kwarg` on your "
        "view.".format(
            parent_model,
        )
    )


def get_all_virtual_relations(model):
    generic_relations = filter(
        lambda f: isinstance(f, generic.GenericRelation),
        model._meta.virtual_fields,
    )
    return [field.rel for field in generic_relations]


def find_parent_to_child_manager(parent_obj, child_model):
    def is_relation_to_child_model(rel):
        if isinstance(rel, generic.GenericRel):
            return issubclass(rel.to, child_model)
        if isinstance(rel, RelatedObject):
            if issubclass(rel.model, child_model):
                return True
            # reverse
            if issubclass(rel.parent_model, child_model):
                if isinstance(parent_obj, rel.model):
                    return True
        else:
            assert False, "This code path should not be possible"

    related_objects = filter(
        is_relation_to_child_model,
        itertools.chain(
            # ForeignKey relations
            parent_obj._meta.get_all_related_objects(),
            # GenericForeignKey relations
            get_all_virtual_relations(parent_obj),
            # ManyToMany relations
            parent_obj._meta.get_all_related_many_to_many_objects(),
            # ManyToMany relations (from the other model)
            child_model._meta.get_all_related_many_to_many_objects(),
        )
    )
    if len(related_objects) != 1:
        raise ImproperlyConfigured(
            "Unable to find manager from {!r} to {!r}.  You may need to declare "
            "`parent_to_child_manager_attr` on your view if the manager is in a "
            "custom location.".format(
                parent_obj.__class__, child_model,
            )
        )

    rel = related_objects[0]

    if isinstance(rel, generic.GenericRel):
        return getattr(parent_obj, rel.field.attname)
    elif issubclass(rel.model, child_model):
        return getattr(parent_obj, rel.get_accessor_name())
    elif isinstance(parent_obj, rel.model):
        return getattr(parent_obj, rel.field.attname)
