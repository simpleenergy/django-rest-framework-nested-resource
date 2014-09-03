import django
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

    # We have to add a Meta class with all this dodgy permissions stuff to keep Django 1.7 from
    # complaining loudly about the name of the generated permission for this model being too long.
    class Meta:
        if tuple(int(e) for e in django.get_version().split(".")) >= (1, 7):
            default_permissions = ()


class ManyToManyTargetModel(models.Model):
    pass


class ManyToManySourceModel(models.Model):
    targets = models.ManyToManyField(ManyToManyTargetModel, related_name='sources')


class ManyToManySourceNoRelatedNameModel(models.Model):
    targets = models.ManyToManyField(ManyToManyTargetModel)

    # We have to add a Meta class with all this dodgy permissions stuff to keep Django 1.7 from
    # complaining loudly about the name of the generated permission for this model being too long.
    class Meta:
        if tuple(int(e) for e in django.get_version().split(".")) >= (1, 7):
            default_permissions = ()
