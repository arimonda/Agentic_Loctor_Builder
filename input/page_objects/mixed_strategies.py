"""Mixed Strategy Page Object - Tests different locator types."""

from selenium.webdriver.common.by import By


class MixedStrategiesPage:
    """Uses ID, CSS, XPath, and Name locators on the login page."""

    USERNAME_BY_ID = (By.ID, "username")
    PASSWORD_BY_NAME = (By.NAME, "password")
    BUTTON_BY_CSS = (By.CSS_SELECTOR, "button[type='submit']")
    HEADING_BY_XPATH = (By.XPATH, "//h2")
    FORM_BY_ID = (By.ID, "login")

    def __init__(self, driver):
        self.driver = driver

    def get_username_field(self):
        return self.driver.find_element(*self.USERNAME_BY_ID)

    def get_password_field(self):
        return self.driver.find_element(*self.PASSWORD_BY_NAME)

    def get_submit_button(self):
        return self.driver.find_element(*self.BUTTON_BY_CSS)

    def get_heading(self):
        return self.driver.find_element(*self.HEADING_BY_XPATH)

    def get_form(self):
        return self.driver.find_element(*self.FORM_BY_ID)
