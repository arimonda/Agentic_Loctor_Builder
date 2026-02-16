"""Login Page Object - WITH BROKEN LOCATORS for healing demo."""

from selenium.webdriver.common.by import By


class LoginPageBroken:
    """Page Object with intentionally broken locators."""

    PAGE_HEADING = (By.CSS_SELECTOR, "h2")
    USERNAME_INPUT = (By.ID, "txt_username_BROKEN")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.XPATH, "//button[@id='btn-submit-BROKEN']")

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
