"""Dropdown Page Object - Sample test file for Loctor Builder audit."""

from selenium.webdriver.common.by import By


class DropdownPage:
    PAGE_HEADING = (By.CSS_SELECTOR, "h3")
    DROPDOWN_SELECT = (By.ID, "dropdown")

    def __init__(self, driver):
        self.driver = driver

    def get_heading_text(self):
        return self.driver.find_element(*self.PAGE_HEADING).text

    def select_option(self, value):
        from selenium.webdriver.support.select import Select
        select = Select(self.driver.find_element(*self.DROPDOWN_SELECT))
        select.select_by_value(value)
