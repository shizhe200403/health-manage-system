from rest_framework import serializers

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at"]


class FoodImageAnalysisRequestSerializer(serializers.Serializer):
    image = serializers.ImageField()


class FoodImageIngredientSerializer(serializers.Serializer):
    ingredient_name = serializers.CharField()
    amount = serializers.FloatField(required=False, allow_null=True)
    unit = serializers.CharField(required=False, allow_blank=True)
    is_main = serializers.BooleanField(required=False)


class FoodImageNutritionSerializer(serializers.Serializer):
    energy = serializers.FloatField(required=False, allow_null=True)
    protein = serializers.FloatField(required=False, allow_null=True)
    fat = serializers.FloatField(required=False, allow_null=True)
    carbohydrate = serializers.FloatField(required=False, allow_null=True)


class FoodImageAnalysisDataSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    meal_type = serializers.ChoiceField(choices=["breakfast", "lunch", "dinner", "snack"], required=False)
    servings = serializers.FloatField(required=False, allow_null=True)
    portion_size = serializers.CharField(required=False, allow_blank=True)
    ingredients = FoodImageIngredientSerializer(many=True, required=False)
    steps = serializers.ListField(child=serializers.CharField(), required=False)
    nutrition = FoodImageNutritionSerializer(required=False)
    confidence_notes = serializers.CharField(required=False, allow_blank=True)
    warning = serializers.CharField(required=False, allow_blank=True)


class FoodImageAnalysisResponseSerializer(serializers.Serializer):
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = FoodImageAnalysisDataSerializer()
