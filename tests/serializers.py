from rest_framework import serializers

from tests.models import (
    GenericForeignKeySourceModel,
    TargetModel,
    ForeignKeySourceModel,
    OneToOneSourceModel,
    ManyToManyTargetModel,
    ManyToManySourceModel,
)


class GenericForeignKeySourceModelSerializer(serializers.ModelSerializer):
    object = serializers.WritableField()

    def validate_object(self, attrs, source):
        value = attrs['source']
        attrs['source'] = TargetModel.objects.get(pk=value)
        return attrs

    class Meta:
        model = GenericForeignKeySourceModel
        fields = ('id', 'object')


class TargetModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = TargetModel


class ForeignKeySourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ForeignKeySourceModel
        fields = ('id', 'target')


class OneToOneSourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = OneToOneSourceModel
        fields = ('id', 'target')


class ManyToManyTargetModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManyTargetModel
        fields = ('id', 'sources')


class ManyToManySourceModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManyToManySourceModel
        fields = ('id', 'targets')
