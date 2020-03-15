import json
import re
import sys
from os import listdir
from time import sleep
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from tqdm import tqdm
driver = None
CONFIG_FILE = "config.json"

URL_LOGIN = 'https://login.didattica.polito.it/secure/ShibLogin.php'
URL_INTERNAL_LOGIN_PUSH = "https://idp.polito.it/idp/x509mixed-login"
URL_INTERNAL_REDIRECT = "https://idp.polito.it/idp/profile/SAML2/Redirect/SSO"
URL_INTERNAL_LOGIN_REQUIRED = "https://idp.polito.it/idp/Authn/X509Mixed/UserPasswordLogin"
URL_DIDATTICA_LANDING = "https://didattica.polito.it/portal/page/portal/home/Studente"
URL_VIDEO_DEFAULT = "https://elearning.polito.it/gadgets/video/template_video.php"
XPATH_MATERIA = "//a[@class = 'policorpolink' and upper-case(normalize-space(text()))='{0}']"
FIELD_USERNAME = 'j_username'
FIELD_PASSWORD = 'j_password'
XPATH_VIDEOLEZIONI_LINKS = "//li[@class = 'h5']/a"
XPATH_DOWNLOAD_LINK = "//a[normalize-space(text()) = 'Video']"
XPATH_DOWNLOAD_LINK_LQ = "//a[normalize-space(text()) = 'iPhone']"
SLEEP_T = 0.01



class Configuration (object):

    def __init__(self):
        with open(CONFIG_FILE, "r") as fp:
            info = json.load(fp)
        if "username" not in info:
            print ("username non valido")
            return
        if "password" not in info:
            print ("password non valida")
            return
        if "url" not in info:
            print ("url non valido")
            return
        self.username = info["username"]
        self.password = info["password"]
        self.URL_LESS = info["url"]
        self.options = Options()
        self.options.add_argument("--use-fake-ui-for-media-stream")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--disable-notifications")
        self.options.add_argument("--lang=en")
        self.options.add_argument("--incognito")
        self.driver = webdriver.Chrome(ChromeDriverManager().install(), options = self.options)


    def login(self):
        wait = WebDriverWait(self.driver, 40)
        self.driver.get(URL_LOGIN)
        #Login
        wait.until(EC.element_to_be_clickable((By.ID, FIELD_USERNAME))).send_keys(self.username)
        wait.until(EC.element_to_be_clickable((By.ID, FIELD_PASSWORD))).send_keys(self.password)
        wait.until(EC.element_to_be_clickable((By.ID, 'login'))).submit()

        if self.driver.current_url == URL_DIDATTICA_LANDING:
            print("Login successful.")
            dict_link_lessons = self.videolezioni()

            if dict_link_lessons is not False:
                for name in tqdm(dict_link_lessons):
                    for errors in range (0,5):
                        answer=self.download(name, dict_link_lessons[name])
                        if answer:
                            break
                self.driver.close()
            else:
                return self.driver.close()

        else:
            print("Login failed.")
            return None
        return False

    def videolezioni(self):
        try:
            self.driver.get(self.URL_LESS)
            #list_link_lessons = []
            elems = self.driver.find_elements_by_xpath("//a[@href]")
            dict_video = {}
            for elem in elems:
                if URL_VIDEO_DEFAULT in elem.get_attribute("href"):
                    dict_video[elem.text] = elem.get_attribute("href")
            return dict_video
        except Exception as e:
            print ("Impossibile recuperare le videolezioni")
            return False

    def download(self, name, link):
        try:
            import requests
            requests.packages.urllib3.disable_warnings()
            self.driver.get(link)
            wait = WebDriverWait(self.driver, 40)
            wait.until(EC.element_to_be_clickable((By.ID, 'video1'))).click()
            elem = self.driver.find_elements_by_xpath("/html/body/video/source")
            link_video = elem[0].get_attribute("src")
            cookies = self.driver.get_cookies()
            s = requests.Session()
            for cookie in cookies:
               s.cookies.set(cookie['name'], cookie['value'])
            response = s.get(link_video, verify = False, stream = True)
            with open("{}.mp4".format(name), "wb") as handle:
                for chunk in tqdm(response.iter_content(chunk_size=512)):
                    if chunk:
                        handle.write(chunk)
            return True
        except Exception as e:
            return False
def main():
    config = Configuration()
    config.login()


if __name__ == "__main__":
    main()
