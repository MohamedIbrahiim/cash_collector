from django.shortcuts import render

# Create your views here.
from rest_framework import serializers


class ReadTaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    description = serializers.CharField()
    amount = serializers.FloatField()
    due_date = serializers.DateTimeField()
    collected_at = serializers.DateTimeField()
    remaining_amount = serializers.IntegerField()


class EmptySerializer(serializers.Serializer):
    pass


class IsFrozenSerializer(serializers.Serializer):
    is_frozen = serializers.BooleanField()


class PaySomeCollectedSerializer(serializers.Serializer):
    collected = serializers.FloatField()
