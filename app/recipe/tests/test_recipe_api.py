from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicRecipesApiTest(TestCase):
    """Test publicly availabale API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is reqiured for retieving recipes"""
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipesApiTest(TestCase):
    """Test that authorisation is required"""

    def setUp(self):
        self.user = create_user(
            email='test@blah.com',
            password='test123',
            name='Test'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipe_list(self):
        """Test retrieving recipe list"""
        Recipe.objects.create(user=self.user, title='Dinner Salad', time=10)
        Recipe.objects.create(user=self.user, title='Scrambled eggs', time=15)

        res = self.client.get(RECIPE_URL)

        recipe = Recipe.objects.all().order_by('-title')
        serializer = RecipeSerializer(recipe, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        """Test that recipes are limited by user"""
        user2 = get_user_model().objects.create_user(
            'other@blah.com'
            'testother123'
        )
        Recipe.objects.create(user=user2, title='Green Eggs', time=5)
        recipe = Recipe.objects.create(user=self.user,
                                       title='Omelette',
                                       time=10)

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], recipe.title)
