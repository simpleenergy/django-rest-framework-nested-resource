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
    ManyToManyTargetModel,
    ManyToManySourceModel,
)


class NestedManyToManyRelationshipTest(TestCase):
    """
    Test nested resources when the nested model has the ManyToMany relationship
    declared on it.
    """
    def test_list_view_filtered_correctly(self):
        """
        Test that the list view /m2m-targets/<target_pk>/m2m-sources/ is
        filtered correctly to only show objects related to the
        `ManyToManyTargetModel` designated by the url.
        """
        # Generate the primary model for the url
        target_a = ManyToManyTargetModel.objects.create()
        url = reverse('nested-m2m-sources-list', kwargs={'target_pk': target_a.pk})

        # Generate another `ManyToManyTargetModel` instance to ensure instances
        # that are only associated with it are not shown.
        target_b = ManyToManyTargetModel.objects.create()

        source_a = ManyToManySourceModel.objects.create()
        source_b = ManyToManySourceModel.objects.create()
        source_c = ManyToManySourceModel.objects.create()

        # `target_a` is linked to only `source_a` and `source_b`
        target_a.sources.add(source_a)
        target_a.sources.add(source_b)

        # `target_b` is linked to only `source_b` and `source_c`
        target_b.sources.add(source_b)
        target_b.sources.add(source_c)

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=response.data,
        )
        self.assertEqual(len(response.data), 2)

        returned_pks = set([obj['id'] for obj in response.data])
        self.assertIn(source_a.pk, returned_pks)
        self.assertIn(source_b.pk, returned_pks)

    def test_detail_view_filtered_correctly(self):
        """
        Test that the nested detail view allows accessing related
        `ManyToManySourceModel` instances.
        """
        # Generate the a target and source, and link them through the m2m
        # relationship.
        target = ManyToManyTargetModel.objects.create()
        source = ManyToManySourceModel.objects.create()
        target.sources.add(source)

        url = reverse(
            'nested-m2m-sources-detail',
            kwargs={'target_pk': target.pk, 'pk': source.pk})

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=response.data,
        )
        self.assertEqual(response.data.get('id'), source.pk)


class NestedReverseManyToManyRelationshipTest(TestCase):
    """
    Test nested resources when the parent model has the ManyToMany relationship
    declared on it.
    """
    def test_list_view_filtered_correctly(self):
        """
        Test that the list view /m2m-sources/<source_pk>/m2m-targets/ is
        filtered correctly to only show objects related to the
        `ManyToManyTargetModel` designated by the url.
        """
        # Generate the primary model for the url
        source_a = ManyToManySourceModel.objects.create()
        url = reverse('nested-m2m-targets-list', kwargs={'source_pk': source_a.pk})

        # Generate another `ManyToManySourceModel` instance to ensure instances
        # that are only associated with it are not shown.
        source_b = ManyToManySourceModel.objects.create()

        target_a = ManyToManyTargetModel.objects.create()
        target_b = ManyToManyTargetModel.objects.create()
        target_c = ManyToManyTargetModel.objects.create()

        # `target_a` is linked to only `source_a` and `source_b`
        source_a.targets.add(target_a)
        source_a.targets.add(target_b)

        # `target_b` is linked to only `source_b` and `source_c`
        source_b.targets.add(target_b)
        source_b.targets.add(target_c)

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=response.data,
        )
        self.assertEqual(len(response.data), 2)

        returned_pks = set([obj['id'] for obj in response.data])
        self.assertIn(target_a.pk, returned_pks)
        self.assertIn(target_b.pk, returned_pks)

    def test_detail_view_filtered_correctly(self):
        """
        Test that the nested detail view allows accessing related
        `ManyToManyTargetModel` instances.
        """
        # Generate the a source and target, and link them through the m2m
        # relationship.
        source = ManyToManySourceModel.objects.create()
        target = ManyToManyTargetModel.objects.create()
        source.targets.add(target)

        url = reverse(
            'nested-m2m-targets-detail',
            kwargs={'source_pk': target.pk, 'pk': source.pk})

        response = self.client.get(url)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg=response.data,
        )
        self.assertEqual(response.data.get('id'), target.pk)
