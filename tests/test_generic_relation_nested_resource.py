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

from tests.models import (
    TargetModel,
    GenericForeignKeySourceModel,
)


class GenericRelationshipNestedResourceTest(TestCase):
    """
    Funcitonal test to ensure that generic relationships can be used with
    `NestedResourceMixin`
    """
    def test_list_view_filtered_correctly(self):
        """
        Test that the list view /targets/<target_pk>/generic-sources/ is
        filtered correctly to only show objects related to the
        `TargetModel` designated by the url.
        """
        # Generate the primary model for the url
        target_a = TargetModel.objects.create()
        url = reverse(
            'nested-generic-sources-list',
            kwargs={'target_model_pk': target_a.pk},
        )

        # Generate another `TargetModel` instance to test instances that are
        # only associated with it are not shown.
        target_b = TargetModel.objects.create()

        # Generate two `GenericForeignKeySourceModel` instances that reference
        # `target_a`
        generic_source_a = GenericForeignKeySourceModel.objects.create(
            object=target_a,
        )
        generic_source_b = GenericForeignKeySourceModel.objects.create(
            object=target_a,
        )

        # Generate another `GenericForeignKeySourceModel` instance that reference
        # `target_b` and should not show up in the list view.
        GenericForeignKeySourceModel.objects.create(
            object=target_b,
        )

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=response.data,
        )
        self.assertEqual(len(response.data), 2)

        returned_pks = set([obj['id'] for obj in response.data])
        self.assertIn(generic_source_a.pk, returned_pks)
        self.assertIn(generic_source_b.pk, returned_pks)

    def test_detail_view_filtered_correctly(self):
        """
        Test that the nested detail view allows accessing related
        `ManyToManySourceModel` instances.
        """
        # Generate the a target and source, and link them through the m2m
        # relationship.
        target = TargetModel.objects.create()
        generic_source = GenericForeignKeySourceModel.objects.create(object=target)

        url = reverse(
            'nested-generic-sources-detail',
            kwargs={'target_model_pk': target.pk, 'pk': generic_source.pk})

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=response.data,
        )
        self.assertEqual(response.data.get('id'), generic_source.pk)
