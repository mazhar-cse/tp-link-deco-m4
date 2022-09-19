import os
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as Options_Chrome
from selenium.webdriver.firefox.options import Options as Options_FireFox
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait

LOG_FILE = os.path.dirname(os.path.abspath(__file__)) + '/tp-link-Deco-M4-scheduler.log'

logger = logging.getLogger('')
logger.setLevel(logging.DEBUG)
fh = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=100000, backupCount=10)
sh = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - [%(name)s.%(funcName)s:%(lineno)d] - %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
sh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(sh)
loglevel_allowed = ['debug', 'info', 'warning', 'error', 'critical']

os.chdir(os.path.dirname(os.path.abspath(__file__)))
with open('config/tp-link-Deco-M4.json', 'r') as file:
    properties_data = json.loads(file.read())

log_level = logging.getLevelName('DEBUG')
if properties_data[0]['log_level'].lower() in loglevel_allowed:
    log_level = logging.getLevelName(properties_data[0]['log_level'].upper())
else:
    logging.debug("Switch back to Debug Level as user used a unexpected value in log level")
logger.setLevel(log_level)

browser_display = properties_data[0]['browser_display'].lower()

if properties_data[0]['browser'].lower() == "chrome":
    # Chrome
    chrome_options = Options_Chrome()
    if not browser_display == "yes":
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
elif properties_data[0]['browser'].lower() == "firefox":
    # Firefox
    options = Options_FireFox()
    options.headless = True
    if browser_display == "yes":
        options.headless = False
    profile = webdriver.FirefoxProfile()
    driver = webdriver.Firefox(options=options, firefox_profile=profile, executable_path='geckodriver')
else:
    logging.exception("Browser selected that is not supported [firefox|chrome]")
    exit(9)


#logging.info(f"Password:{properties_data[0]['password']}")
logging.info(f"Password:****xx*****xxxx*****xxx******")
try:

    url = f"http://{properties_data[0]['ip']}"
    wait = WebDriverWait(driver, 10)

    # open browser and login
    logging.info(f"Browser [{properties_data[0]['browser']}] now open on ip:{properties_data[0]['ip']}")
    driver.get(url)
    # wait for the login field
    wait.until(ec.visibility_of_element_located((By.ID, "local-login-pwd")))
    # find the password element and pass the password from JSON
    driver.find_element(By.CSS_SELECTOR, 'input.text-text:nth-child(1)').send_keys(properties_data[0]['password'])
    # wait for fading overlay to disappear
    sleep(3)
    # click on the login button
    logging.info(f"Clicking now on login button")
    driver.find_element(By.LINK_TEXT, "LOG IN").click()

    # wait for first page loaded
    wait = WebDriverWait(driver, 60)
    wait.until(ec.visibility_of_element_located((By.CLASS_NAME, "folder-tree-folder-node-text")))
    logging.info("Logged in successful")

    # navigate to the reboot page
    driver.get(f'{url}/webpages/index.html#reboot')

    # for the list to be displayed / assumption is that all devices show up at the same time
    logging.info("Wait for all devices to show up in list")
    wait = WebDriverWait(driver, 60)
    wait.until(ec.visibility_of_element_located((By.XPATH, f"//div[contains(@class, 'content') "
                                                           f"and text()='{properties_data[0]['text_model']}']")))

    # prepare reboot
    logging.info("Ready to Reboot")
    try:
        logging.info("Going to click on reboot_all button")
        # bring the 'REBOOT ALL' button in the visible area
        driver.execute_script("document.querySelector('#reboot-button > div.widget-wrap-outer.button-wrap-outer > div.widget-wrap.button-wrap > a').scrollIntoView();")
        # wait until the 'REBOOT ALL' button becomes clickable
        button = WebDriverWait(driver, 10).until(ec.element_to_be_clickable((By.CSS_SELECTOR, "a[type='button'][title='REBOOT ALL']")))
        button.click()

    except Exception as ex:
        logging.error("'REBOOT ALL' button not found or not become clickable")
    # wait for the reboot overlay
    wait = WebDriverWait(driver, 8)
    wait.until(ec.visibility_of_element_located((By.XPATH, f"//span[contains(@class, 'text button-text') "
                                                           f"and text()='{properties_data[0]['text_reboot']}']")))
    sleep(15)
    if properties_data[0]['execute_reboot'].lower() == "yes":
        # reboot finally
        logging.info("Rebooting...(may take 45s to 90s)")
        driver.find_element(By.XPATH, (f"//span[contains(@class, 'text button-text') "
                                     f"and text()='{properties_data[0]['text_reboot']}']")).click()
        sleep(10)
    else:
        logging.info("aborting for test - no reboot triggered")
except Exception:
    logging.error("Something went wrong/failed - check the scheduler log", Exception)
finally:
    driver.quit()
    exit()