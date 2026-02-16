"""Login Page Object - Sample test file for Loctor Builder audit."""

from selenium.webdriver.common.by import By


class LoginPage:
    """Page Object for the Heroku App Login Page."""

    PAGE_HEADING = (By.CSS_SELECTOR, "h2")
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button.radius")
    SUBHEADER_TEXT = (By.CSS_SELECTOR, "h4.subheader")

    def __init__(self, driver):
        self.driver = driver

    def enter_username(self, username):
        self.driver.find_element(*self.USERNAME_INPUT).send_keys(username)

    def enter_password(self, password):
        self.driver.find_element(*self.PASSWORD_INPUT).send_keys(password)

    def click_login(self):
        self.driver.find_element(*self.LOGIN_BUTTON).click()

    def get_heading_text(self):
        return self.driver.find_element(*self.PAGE_HEADING).text
