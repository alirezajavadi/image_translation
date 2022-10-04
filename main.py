from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import requests
import os
import json
import time


def send_request(lang, image):
    payload = {'isOverlayRequired': False,
               'apikey': api_key,
               'language': lang,
               'base64Image': image
               }
    request = requests.post("https://api.ocr.space/parse/image", data=payload)
    return request.content.decode()


def open_browser():
    options = Options()
    options.add_argument("--log-level=3")  # fatal error
    browser = webdriver.Firefox(service=Service(driver_path), options=options)
    try:
        # open browser with https://translate.google.com/ url
        browser.get("https://translate.google.com/")

        # read our header (image selector)
        file = open("assets/imageForm.html", "r")
        form = file.read().replace("\r", "")
        form = form.replace("\n", "")
        file.close()

        # add our form in browser
        script = f"var elements = '{form}',body = document.evaluate('/html/body/c-wiz/div/div[2]', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;;body.insertAdjacentHTML( 'beforebegin', elements );"
        browser.execute_script(script=script)

        while True:
            time.sleep(1)
            # user selected image
            if browser.find_element(By.ID, "uploadImg").get_attribute("value") != "":
                browser.execute_script("""
                                    document.getElementById("translateLabel").setAttribute("disabled","false");
                                """)
            else:
                continue

            # user clicked on Translate button
            if browser.find_element(By.ID, "translate").is_selected():
                browser.execute_script("""
                        document.getElementById('translateLabel').innerHTML="Translating...";
                        
                        var oFReader = new FileReader();
                        oFReader.readAsDataURL(document.getElementById("uploadImg").files[0]);
    
                        oFReader.onload = function (oFREvent) {
                            document.getElementById("base64image").src = oFREvent.target.result;
                        };
                    """)

                # send image to ocr space
                language = browser.find_element(By.ID, "lang").get_attribute("value")
                image = browser.find_element(By.ID, "base64image").get_attribute("src")
                result = json.loads(send_request(lang=language, image=image))

                if result == "The API key is invalid":
                    print("First you most paste your ocr.space API Key in \"api_key.txt\", then try again!")
                    browser.quit()
                    exit(0)

                # check result
                if result['OCRExitCode'] == 1:
                    textarea = browser.find_element(By.XPATH,
                                                    "/html/body/c-wiz/div/div[3]/c-wiz/div[2]/c-wiz/div[1]/div[2]/div[3]/c-wiz[1]/span/span/div/textarea")
                    textarea.clear()
                    result = str(result['ParsedResults'][0]['ParsedText'])
                    result = result.replace("\n", "")
                    result = result.replace("\r", " ")
                    textarea.send_keys(result)

                else:
                    browser.execute_script(f"""
                                                document.getElementById('error').innerHTML="{str(result['ErrorMessage'][0])}";
                                                document.getElementById('error').style.display = 'block';
                                            """)

                browser.execute_script("""
                        document.getElementById("translate").checked = false;
                        document.getElementById('translateLabel').innerHTML="Translate";
                    """)

    except requests.exceptions.ConnectionError:
        print("Connection Error!")
        browser.quit()


if __name__ == '__main__':
    driver_path = 'assets'
    if os.name == 'posix':
        driver_path = os.path.join(driver_path, 'geckodriver_linux64')
    else:
        print("This program can't run in your OS, Sorry!")
        exit(0)

    try:
        with open("api_key.txt", "r") as api_key_file:
            api_key = api_key_file.read()
    except FileNotFoundError:
        api_key = "helloworld"

    open_browser()
