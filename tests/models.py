from django.db import models
from django.contrib.contenttypes import generic


class GenericForeignKeySourceModel(models.Model):
    content_type = models.ForeignKey('contenttypes.ContentType')
    object_id = models.PositiveIntegerField()

    object = generic.GenericForeignKey('content_type', 'object_id')


class TargetModel(models.Model):
    generic_sources = generic.GenericRelation(GenericForeignKeySourceModel)


class ForeignKeySourceModel(models.Model):
    target = models.ForeignKey(TargetModel, related_name='sources')


class ForeignKeySourceNoRelatedNameModel(models.Model):
    target = models.ForeignKey(TargetModel)


class ManyToManyTargetModel(models.Model):
    pass


class ManyToManySourceModel(models.Model):
    targets = models.ManyToManyField(ManyToManyTargetModel, related_name='sources')


class ManyToManySourceNoRelatedNameModel(models.Model):
    targets = models.ManyToManyField(ManyToManyTargetModel)


class SelfReferencingManyToManyModel(models.Model):
    targets = models.ManyToManyField('self')
