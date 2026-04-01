from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, RecipeBulkActionView, RecipeViewSet

router = DefaultRouter()
router.register(r"ingredients", IngredientViewSet, basename="ingredient")
router.register(r"recipes", RecipeViewSet, basename="recipe")

urlpatterns = router.urls + [
    path("recipes/admin/bulk/", RecipeBulkActionView.as_view(), name="recipe-bulk"),
]

