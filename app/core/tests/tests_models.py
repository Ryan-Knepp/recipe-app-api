from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

from core import models


def sample_user(email="test@test.com", password="testpass"):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    def test_create_user_with_email_successfully(self):
        """Test creating a new user with an email is successful"""

        email = "test.dev.com.net"
        password = "test123"
        user = get_user_model().objects.create_user(email=email, password=password)

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        email = "test@CAPS.COM"
        user = get_user_model().objects.create_user(email, "123")

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating a user with no email causes an error"""
        with self.assertRaises(ValueError):
            user = get_user_model().objects.create_user(None, "123")

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser("super@user.com", "123")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_tag_str(self):
        """Test the tag string representation"""
        tag = models.Tag.objects.create(user=sample_user(), name="Meat")

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_str(self):
        ingredient = models.Ingredient.objects.create(user=sample_user(), name="Bacon")

        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_str(self):
        recipe = models.Recipe.objects.create(
            user=sample_user(), title="Smashburger", time_minutes=5, price=5.00
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch("uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):
        """Test that image is saved in the correct location"""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "myImage.jpg")

        exp_path = f"uploads/recipe/{uuid}.jpg"
        self.assertEqual(file_path, exp_path)
