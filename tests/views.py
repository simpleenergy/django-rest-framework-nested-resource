from rest_framework import viewsets

from drf_nested_resource.mixins import NestedResourceMixin

from .models import (
    TargetModel,
    ForeignKeySourceModel,
    ManyToManyTargetModel,
    ManyToManySourceModel,
    GenericForeignKeySourceModel,
)


class NestedForeignKeySourceModelViewSet(NestedResourceMixin, viewsets.ModelViewSet):
    """
    /targets/<target_pk>/sources/
    """
    parent_model = TargetModel
    model = ForeignKeySourceModel


class NestedGenericForeignKeySourceModelViewSet(NestedResourceMixin,
                                                viewsets.ModelViewSet):
    """
    /targets/<target_pk>/generic-sources/
    """
    parent_model = TargetModel
    model = GenericForeignKeySourceModel


class NestedManyToManySourceModelViewSet(NestedResourceMixin,
                                         viewsets.ReadOnlyModelViewSet):
    """
    /m2m-targets/<target_pk>/m2m-sources/
    """
    parent_model = ManyToManyTargetModel
    model = ManyToManySourceModel


class NestedManyToManyTargetModelViewSet(NestedResourceMixin,
                                         viewsets.ReadOnlyModelViewSet):
    """
    /m2m-sources/<source_pk>/m2m-targets/
    """
    parent_model = ManyToManySourceModel
    model = ManyToManyTargetModel
