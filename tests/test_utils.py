from django.test import TestCase
from django.db.models.manager import Manager
from django.core.exceptions import ImproperlyConfigured

from rest_framework import serializers

from drf_nested_resource.utils import (
    find_child_to_parent_accessor_name,
    find_child_to_parent_serializer_field,
    compute_default_url_kwarg_for_parent,
    find_parent_to_child_manager,
)

from tests.models import (
    TargetModel,
    ForeignKeySourceModel,
    ForeignKeySourceNoRelatedNameModel,
    GenericForeignKeySourceModel,
    ManyToManyTargetModel,
    ManyToManySourceModel,
    ManyToManySourceNoRelatedNameModel,
    SelfReferencingManyToManyModel,
    ManyToManyTowardsSelfReference,
)


class FindRelationshipFieldTest(TestCase):
    def test_raises_integrity_error_when_no_relationship_found(self):
        with self.assertRaises(ImproperlyConfigured):
            find_child_to_parent_accessor_name(
                parent_model=ForeignKeySourceModel,
                child_model=TargetModel,
            )

    def test_on_foreign_key_relationship(self):
        """
        Test finding the field that represents the parent/child relationship in
        a normal `ForeignKey` backed relationship.
        """
        attname = find_child_to_parent_accessor_name(
            parent_model=TargetModel,
            child_model=ForeignKeySourceModel,
        )
        self.assertEqual(attname, 'target')

    def test_on_generic_foreign_key_relationship(self):
        """
        Test finding the field that represents the parent/child relationship in
        a `GenericForeignKey` backed relationship.
        """
        attname = find_child_to_parent_accessor_name(
            parent_model=TargetModel,
            child_model=GenericForeignKeySourceModel,
        )
        self.assertEqual(attname, 'object')

    def test_on_many_to_many_relationship(self):
        """
        Test finding the field that represents the parent/child relationship in
        a `ManyToManyField` backed relationship when the child model is the one
        which has the `ManyToManyField` declared on it.
        """
        attname = find_child_to_parent_accessor_name(
            parent_model=ManyToManyTargetModel,
            child_model=ManyToManySourceModel,
        )
        self.assertEqual(attname, 'targets')

    def test_on_many_to_many_relationship_from_other_side(self):
        """
        Test finding the field that represents the parent/child relationship in
        a `ManyToManyField` backed relationship when the parent model is the one
        which has the `ManyToManyField` declared on it.
        """
        attname = find_child_to_parent_accessor_name(
            parent_model=ManyToManySourceModel,
            child_model=ManyToManyTargetModel,
        )
        self.assertEqual(attname, 'sources')


#
# Test Serializers for testing `find_child_to_parent_serializer_field`
#
class NoSuffixSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySourceModel
        fields = ('id', 'target')


class WithSuffixSerializer(serializers.ModelSerializer):
    target_id = serializers.Field()

    class Meta:
        model = ForeignKeySourceModel
        fields = ('id', 'target_id')


class BaseInheritedSerializer(serializers.ModelSerializer):
    target = serializers.PrimaryKeyRelatedField()

    class Meta:
        model = ForeignKeySourceModel
        fields = ('id', 'target')


class InheritedSerializer(BaseInheritedSerializer):
    pass


class FindSerializerFieldTest(TestCase):
    def test_on_non_suffixed_field_name(self):
        """
        Test that the serializer field can be found when it is the same name as
        the child to parent accessor attribute name.
        """
        field_name = find_child_to_parent_serializer_field(
            NoSuffixSerializer,
            'target',
        )
        self.assertEqual(field_name, 'target')

    def test_on_suffixed_field_name(self):
        """
        Test that the serializer field can be found when the serializer field
        has the `_id` suffix as is sometimes the case with `ForeignKey` fields.
        """
        field_name = find_child_to_parent_serializer_field(
            WithSuffixSerializer,
            'target',
        )
        self.assertEqual(field_name, 'target_id')

    def test_on_inherited_serializer(self):
        """
        Test that a field declared on a base class of the serializer is still
        found.  Just in case there is something fishy going on with
        `serializer.base_fields`.
        """
        field_name = find_child_to_parent_serializer_field(
            InheritedSerializer,
            'target',
        )
        self.assertEqual(field_name, 'target')


class ComputeURLKwargForParentTest(TestCase):
    """
    Test the `compute_default_url_kwarg_for_parent` function is able to come up
    with sensable defaults for what the url kwarg *should* be when representing
    various relationships for `/parents/<url_kwarg>/children/`
    """
    def test_foreign_key_relationship_kwarg_computation(self):
        """
        For the relationship where ChildParent.parent is a ForeignKey field
        which points to the ParentModel
        """
        url_kwarg = compute_default_url_kwarg_for_parent(
            parent_model=TargetModel,
            child_model=ForeignKeySourceModel,
        )
        self.assertEqual(url_kwarg, 'target_pk')

    def test_generic_foreign_key_relationship_kwarg_computation(self):
        url_kwarg = compute_default_url_kwarg_for_parent(
            parent_model=TargetModel,
            child_model=GenericForeignKeySourceModel,
        )
        self.assertEqual(url_kwarg, 'target_model_pk')

    def test_many_to_many_relationship(self):
        url_kwarg = compute_default_url_kwarg_for_parent(
            parent_model=ManyToManyTargetModel,
            child_model=ManyToManySourceModel,
        )
        self.assertEqual(url_kwarg, 'target_pk')

    def test_many_to_many_from_other_side_of_relationship(self):
        url_kwarg = compute_default_url_kwarg_for_parent(
            parent_model=ManyToManySourceModel,
            child_model=ManyToManyTargetModel,
        )
        self.assertEqual(url_kwarg, 'source_pk')


class GetParentToChildManagerTest(TestCase):
    """
    Test that the `find_parent_to_child_manager` function is able to find the
    manager from the parent object to the child objects for all supported
    relationships.
    """
    def assertManagersEqual(self, manager_a, manager_b):
        """
        The manager class that django uses for reverse relationships is
        constructed dynamically using code generation so this is an
        approximation guaranteeing they are the same.
        """
        self.assertIsInstance(manager_a, Manager)
        self.assertIsInstance(manager_b, Manager)
        self.assertEqual(manager_a.model, manager_b.model)
        self.assertEqual(
            str(manager_a.all().query),
            str(manager_b.all().query),
        )

    def test_foreign_key_relationship_with_declared_related_name(self):
        parent_obj = TargetModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=ForeignKeySourceModel,
        )
        self.assertManagersEqual(manager, parent_obj.sources)

    def test_foreign_key_relationship_without_related_name(self):
        parent_obj = TargetModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=ForeignKeySourceNoRelatedNameModel,
        )
        self.assertManagersEqual(manager, parent_obj.foreignkeysourcenorelatednamemodel_set)

    def test_generic_foreign_key_relationship(self):
        parent_obj = TargetModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=GenericForeignKeySourceModel,
        )
        self.assertManagersEqual(manager, parent_obj.generic_sources)

    def test_many_to_many_relationship_with_declared_related_name(self):
        parent_obj = ManyToManyTargetModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=ManyToManySourceModel,
        )
        self.assertManagersEqual(manager, parent_obj.sources)

    def test_many_to_many_relationship_from_other_side_with_declared_related_name(self):
        parent_obj = ManyToManySourceModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=ManyToManyTargetModel,
        )
        self.assertManagersEqual(manager, parent_obj.targets)

    def test_many_to_many_relationship_without_related_name(self):
        parent_obj = ManyToManyTargetModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=ManyToManySourceNoRelatedNameModel,
        )

        self.assertManagersEqual(
            manager,
            parent_obj.manytomanysourcenorelatednamemodel_set,
        )

    def test_many_to_many_relationship_from_other_side_without_related_name(self):
        parent_obj = ManyToManySourceNoRelatedNameModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=ManyToManyTargetModel,
        )
        self.assertManagersEqual(manager, parent_obj.targets)

    def test_many_to_many_relationship_with_self(self):
        parent_obj = SelfReferencingManyToManyModel.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=SelfReferencingManyToManyModel,
        )
        self.assertManagersEqual(manager, parent_obj.targets)

    def test_m2m_towards_self_referencing_model(self):
        parent_obj = ManyToManyTowardsSelfReference.objects.create()
        manager = find_parent_to_child_manager(
            parent_obj=parent_obj,
            child_model=SelfReferencingManyToManyModel,
        )
        self.assertManagersEqual(manager, parent_obj.targets)
