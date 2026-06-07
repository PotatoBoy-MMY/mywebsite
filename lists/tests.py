from django.test import TestCase
from django.core.urlresolvers import resolve
from lists.views import home_page


class HomePageTest(TestCase):

    def test_root_url_resolves_to_home_page_view(self):
        found = resolve('/')
        self.assertEqual(found.func, home_page)

    def test_home_page_returns_correct_html(self):
        response = self.client.get('/')

        self.assertTrue(response.content.startswith(b'<html>'))
        self.assertIn(b'<title>To-Do lists</title>', response.content)
        self.assertIn(b'<h1>To-Do</h1>', response.content)
        self.assertIn(b'<input id="id_new_item" placeholder="Enter a to-do item" />', response.content)
        self.assertIn(b'<table id="id_list_table">', response.content)
        self.assertTrue(response.content.endswith(b'</html>'))
