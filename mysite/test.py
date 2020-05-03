from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from myapp import models

class WineListViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create user
        test_user1 = User.objects.create_user(username='testuser1', password='1X<ISRUkw+tuK')
        test_user1.save()

        # Create 13 wines for pagination tests
        number_of_wines = 13
        for wine_id in range(number_of_wines):
            models.Wine.objects.create(
                title=f'Wine {wine_id}',
                winery=f'Winery {wine_id}',
                country=f'Country {wine_id}',
                province=f'Province {wine_id}',
                variety=f'Variety {wine_id}',
            )
    
    def test_view_url_exists_at_desired_location(self):
        login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
        response = self.client.get('/search/')
        self.assertEqual(response.status_code, 200)
        
    # def test_pagination_is_twelve(self):
    #     login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
    #     response = self.client.get('/search/')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue('is_paginated' in response.context)
    #     self.assertTrue(response.context['is_paginated'] == True)
    #     self.assertTrue(len(response.context['wine_list']) == 12)

    # def test_lists_all_wines(self):
    #     # Get second page and confirm it has (exactly) remaining 1 item
    #     login = self.client.login(username='testuser1', password='1X<ISRUkw+tuK')
    #     response = self.client.get('/search/?page=2')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertTrue('is_paginated' in response.context)
    #     self.assertTrue(response.context['is_paginated'] == True)
    #     self.assertTrue(len(response.context['wine_list']) == 1)