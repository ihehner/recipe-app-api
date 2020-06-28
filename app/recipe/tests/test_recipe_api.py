from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def sample_tag(user, name='Main course'):
    """Create and return a sample tag"""
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Salt'):
    """Create and return sample ingredient"""
    return Ingredient.objects.create(user=user, name=name)


def detail_url(recipe_id):
    """Return url for detail Recipe"""
    return reverse('recipe:recipe-detail', args=[recipe_id])


def create_user(**params):
    return get_user_model().objects.create_user(**params)


def sample_recipe(user, **params):
    """Create and return sample recipe"""
    defaults = {
        'title': 'Sample Recipe',
        'time': 10
    }
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


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
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.all().order_by('-id')
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_limited_to_user(self):
        """Test that recipes are limited by user"""
        user2 = get_user_model().objects.create_user(
            'other@blah.com'
            'testother123'
        )
        sample_recipe(user=user2, title='Green Eggs', time=5)
        recipe = sample_recipe(user=self.user, title='Omelette')

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['title'], recipe.title)

    def test_view_recipe_detail(self):
        """Test retrieving recipe detail"""
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
