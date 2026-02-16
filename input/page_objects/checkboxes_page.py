"""Checkboxes Page Object - Sample test file for Loctor Builder audit."""

from selenium.webdriver.common.by import By


class CheckboxesPage:
    PAGE_HEADING = (By.CSS_SELECTOR, "h3")
    CHECKBOX_FORM = (By.ID, "checkboxes")

    def __init__(self, driver):
        self.driver = driver

    def get_heading_text(self):
        return self.driver.find_element(*self.PAGE_HEADING).text

    def get_checkbox_container(self):
        return self.driver.find_element(*self.CHECKBOX_FORM)
