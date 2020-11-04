import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPES_URL = reverse("recipe:recipe-list")


def detail_url(recipe_id):
    """return recipe detail url"""
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id):
    """return url for recipe image upload"""
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


def sample_recipe(user, **params):
    defaults = {"title": "Sample Recipe", "time_minutes": 10, "price": 5.00}

    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


def sample_tag(user, name="Sample"):
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name="Bacon"):
    return Ingredient.objects.create(user=user, name=name)


class PublicRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """login is required for creating recipes"""

        res = self.client.get(RECIPES_URL)
        self.assertEqual(res.status_code, 401)


class PrivateRecipeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("test@test.com", "pass123")
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):

        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by("-id")
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        user2 = get_user_model().objects.create_user("other@test.com", "pass123")
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        payload = {"title": "Bacon Bacon", "time_minutes": 10, "price": 7.00}

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, 201)

        recipe = Recipe.objects.get(id=res.data["id"])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        tag1 = sample_tag(user=self.user, name="Meat")
        tag2 = sample_tag(user=self.user, name="Bacon")

        payload = {
            "title": "More Bacon",
            "time_minutes": 12,
            "price": 11.00,
            "tags": [tag1.id, tag2.id],
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, 201)
        recipe = Recipe.objects.get(id=res.data["id"])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        ingredient1 = sample_ingredient(user=self.user, name="Candy")
        ingredient2 = sample_ingredient(user=self.user, name="Bacon")

        payload = {
            "title": "More Bacon",
            "time_minutes": 12,
            "price": 11.00,
            "ingredients": [ingredient1.id, ingredient2.id],
        }

        res = self.client.post(RECIPES_URL, payload)

        self.assertEqual(res.status_code, 201)
        recipe = Recipe.objects.get(id=res.data["id"])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)


class RecipeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user("test@test.com", "pass123")
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(url, {"image": ntf}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, 200)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)

        res = self.client.post(url, {"image": "noimage"}, format="multipart")

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, 400)
