"""Form Authentication Page Object - Sample test file."""

from selenium.webdriver.common.by import By


class FormAuthPage:
    LOGIN_FORM = (By.ID, "login")
    USERNAME_LABEL = (By.XPATH, "//label[@for='username']")

    def __init__(self, driver):
        self.driver = driver

    def get_form(self):
        return self.driver.find_element(*self.LOGIN_FORM)

    def get_username_label(self):
        return self.driver.find_element(*self.USERNAME_LABEL).text
