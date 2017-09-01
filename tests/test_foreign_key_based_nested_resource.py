#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_django-rest-framework-nested-resource
------------

Tests for `django-rest-framework-nested-resource` models module.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse

from rest_framework import status

from drf_nested_resource.mixins import NestedResourceMixin

from tests.models import (
    TargetModel,
    ForeignKeySourceModel,
)


class NestedForeignKeyRelationshipTest(TestCase):
    def test_list_is_filtered_correctly(self):
        """
        Test that the list api view has it's queryset correctly filtered to
        only the `ForeignKeySourceModel` instances that are related to the
        `TargetModel` designated by the url.
        """
        # Generate an instance of `TargetModel`
        target_a = TargetModel.objects.create()

        # Generate some instances of `ForeignKeySourceModel` that are related
        # to `TargetModel`.
        for i in range(5):
            ForeignKeySourceModel.objects.create(target=target_a)

        # Generate another instance of `TargetModel` as well as a related
        # instance of `ForeignKeySourceModel` to ensure that they do not show
        # up in the list view.
        target_b = TargetModel.objects.create()
        ForeignKeySourceModel.objects.create(target=target_b)

        url = reverse('nested-sources-list', kwargs={'target_pk': target_a.pk})
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, msg=response.data,
        )
        self.assertEqual(len(response.data), 5)

    def test_detail_is_filtered_correctly(self):
        """
        Test that the nested detail view of a `ForeignKeySourceModel` returns
        the correct data.
        """
        target_a = TargetModel.objects.create()
        source = ForeignKeySourceModel.objects.create(target=target_a)

        url = reverse(
            'nested-sources-detail',
            kwargs={'target_pk': target_a.pk, 'pk': source.pk},
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, msg=response.data,
        )
        self.assertEqual(response.data.get('id'), source.pk, msg=response.data)

    def test_404_on_detail_request_for_non_related_instances(self):
        """
        Test that a 404 is returned if we try to retrieve an instance that is
        not related to the `TargetModel` instance.
        """
        target_a = TargetModel.objects.create()
        source = ForeignKeySourceModel.objects.create(target=target_a)

        target_b = TargetModel.objects.create()
        url = reverse(
            'nested-sources-detail',
            kwargs={'target_pk': target_b.pk, 'pk': source.pk},
        )
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND, msg=response.data,
        )

    def test_creation_with_correct_parent_relationship(self):
        """
        Test that creation via the nested endpoint allows inclusion of the
        parent field if it matches that of the parent declared by the url.
        """
        target_a = TargetModel.objects.create()

        # sanity check
        self.assertFalse(target_a.sources.exists())

        url = reverse('nested-sources-list', kwargs={'target_pk': target_a.pk})

        response = self.client.post(url, {'target': target_a.pk})
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED, msg=response.data,
        )

        self.assertTrue(target_a.sources.exists())

    def test_create_endpoint_forces_relationship_to_parent(self):
        """
        Test that creation via the nested endpoint validates that the instance
        of `ForeignKeySourceModel` being created must be related to the target.
        """
        target_a = TargetModel.objects.create()
        target_b = TargetModel.objects.create()

        url = reverse('nested-sources-list', kwargs={'target_pk': target_a.pk})

        # Try to create an instance pointed to `target_b` with the url that
        # relates to `target_a`
        response = self.client.post(url, {'target': target_b.pk})
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data,
        )
        self.assertIn(
            NestedResourceMixin.default_error_messages['parent_reference_mismatch'][:25],
            response.data.get('detail', ''),
        )
