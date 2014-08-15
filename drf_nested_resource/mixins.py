import copy
import collections

from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import get_object_or_404

from rest_framework import exceptions

from drf_nested_resource import utils


class NestedResourceMixin(object):
    """
    Allows to use nested resource url and pass the url kwars for parent object lookup to the serializer
    This enforce a proper use of the serializer for db integrity constraints
    For many-to-many relationships, it must only be used for read only endpoints
    """
    _parent_lookup_field = None
    _parent_url_kwarg = None
    _parent_serializer_field = None

    parent_to_child_manager_attr = None

    default_error_messages = {
        "parent_reference_mismatch": "The reference value for the parent model (`{key}: {value}`) does not match that of the parent instance (`{parent_reference_value}`) for the parent instance designated by this url",
    }

    #
    # Core Serializer methods.
    #
    def get_parent_object(self):
        """
        Returns the instance of `self.parent_model` as designated by the url.
        """
        try:
            parent_lookup_value = self.kwargs[self.parent_url_kwarg]
        except KeyError:
            raise ImproperlyConfigured(
                "'{0}' not found in the URL kwargs.  If this is not the value "
                "you have used for your url, please set `parent_url_kwarg` on "
                "your view to overide this value".format(self.parent_url_kwarg)
            )
        return get_object_or_404(
            self.parent_model,
            **{self.parent_lookup_field: parent_lookup_value}
        )

    def get_serializer(self, instance=None, data=None,
                       files=None, many=False, partial=False):
        """
        Wrapper around the default `get_serializer` logic that enforces the
        child object is associated with the parent_object for `create/update`
        style operations.
        """
        parent_obj = self.get_parent_object()

        if data is not None and self.parent_serializer_field in data:
            # Casting to a string because everything that comes out of the post
            # data is a string.
            if not data[self.parent_serializer_field] == str(getattr(parent_obj, self.parent_lookup_field)):
                raise exceptions.ParseError(
                    self.default_error_messages['parent_reference_mismatch'].format(
                        key=data.get(self.parent_serializer_field),
                        value=data.get(self.parent_serializer_field),
                        parent_reference_value=parent_obj.pk,
                    )
                )

        if isinstance(data, collections.Mapping):
            # In the case where data is being posted in that does not include
            # the value to tie the object to it's parent, set it gracefully.
            data = copy.deepcopy(data)
            data.setdefault(self.parent_serializer_field, parent_obj.pk)

        serializer = super(NestedResourceMixin, self).get_serializer(
            instance=instance,
            data=data,
            files=files,
            many=many,
            partial=partial,
        )
        return serializer

    def get_queryset(self):
        """
        Return a queryset of `self.model` objects that are related to the
        parent object.
        """
        parent_obj = self.get_parent_object()
        manager = self.get_parent_to_child_manager(parent_obj)
        return manager.all()

    #
    # getter functions
    #
    def get_child_to_parent_accessor_name(self):
        """
        Find the field on the child model that represents the relationship to
        the parent model.
        """
        return utils.find_child_to_parent_accessor_name(
            parent_model=self.parent_model,
            child_model=self.model,
        )

    def get_parent_serializer_field_name(self):
        """
        Given the name of the attribute on the child model which references the
        parent, return the name of the serializer field which represents the
        child to parent relationship.
        """
        return utils.find_child_to_parent_serializer_field(
            serializer_class=self.get_serializer_class(),
            parent_accessor_name=self.get_child_to_parent_accessor_name(),
        )

    def get_parent_url_kwarg(self):
        return utils.compute_default_url_kwarg_for_parent(
            parent_model=self.parent_model,
            child_model=self.model,
        )

    def get_parent_to_child_manager(self, parent_obj):
        if self.parent_to_child_manager_attr is not None:
            return getattr(parent_obj, self.parent_to_child_manager_attr)
        else:
            return utils.find_parent_to_child_manager(
                parent_obj=parent_obj,
                child_model=self.model,
            )

    #
    # Properties
    #
    @property
    def parent_model(self):
        raise ImproperlyConfigured(
            "'parent_model' has to be set for this view."
        )

    @property
    def parent_lookup_field(self):
        """
        Return the field name that should be used to lookup the parent object
        based on the value pulled out of the url kwargs.
        """
        if not self._parent_lookup_field:
            # making sure we can find an attribute on the child model that
            # references the parent model.
            self.get_child_to_parent_accessor_name()
            self.parent_lookup_field = 'pk'

        if not self._parent_lookup_field:
            assert False, "This should not be possible"
        return self._parent_lookup_field

    @parent_lookup_field.setter
    def parent_lookup_field(self, value):
        self._parent_lookup_field = value

    @property
    def parent_url_kwarg(self):
        if not self._parent_url_kwarg:
            self._parent_url_kwarg = self.get_parent_url_kwarg()

        return self._parent_url_kwarg

    @parent_url_kwarg.setter
    def parent_url_kwarg(self, value):
        self._parent_url_kwarg = value

    @property
    def parent_serializer_field(self):
        if not self._parent_serializer_field:
            self.parent_serializer_field = self.get_parent_serializer_field_name()

        return self._parent_serializer_field

    @parent_serializer_field.setter
    def parent_serializer_field(self, value):
        self._parent_serializer_field = value

