from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import unittest
import time


class NewVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_list_and_retrieve_it_later(self):
        # Zhangsan hears about a cool new online to-do app.
        # He goes to check out its homepage.
        self.browser.get('http://localhost:8000')

        # He notices the page title and header mention To-Do lists.
        self.assertIn('To-Do', self.browser.title,
                      "Browser title was: " + self.browser.title)

        header_text = self.browser.find_element_by_tag_name('h1').text
        self.assertIn('To-Do', header_text)

        # He is invited to enter a to-do item straight away.
        inputbox = self.browser.find_element_by_id('id_new_item')
        self.assertEqual(
            inputbox.get_attribute('placeholder'),
            'Enter a to-do item'
        )

        # He types "Buy flowers" into a text box.
        inputbox.send_keys('Buy flowers')

        # When he hits enter, the page updates, and now the page lists
        # "1: Buy flowers" as an item in a to-do list table.
        inputbox.send_keys(Keys.ENTER)
        time.sleep(1)

        table = self.browser.find_element_by_id('id_list_table')
        rows = table.find_elements_by_tag_name('tr')
        self.assertIn('1: Buy flowers', [row.text for row in rows])


if __name__ == '__main__':
    unittest.main()
