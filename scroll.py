from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import sys, os
import config_, twitter

def init():
    ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
    options = Options()
    options.add_argument('--disable-extensions')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent="{0}"'.format(ua))
    options.add_argument('--no-sandbox')
    #options.add_argument('--blink-settings=imagesEnabled=false')
    try:
        driver = webdriver.Chrome(chrome_options=options)
    except Exception as e:
        print(e)
        sys.exit()
        
    driver.implicitly_wait(10)
    #driver.delete_all_cookies()

    return driver

def write_links(driver,url):
    # links = driver.find_elements_by_xpath("//div[contains(@class,'tweet') and boolean(@data-permalink-path)]")
    links = driver.find_elements_by_tag_name("a")
    count = 0
    with open("txt/id-statuses-{0}-{1}.txt".format(url.split("/")[-2],url.split("/")[-1]), "w") as f:
        for link in links:
            status_id = link.get_attribute("href")
            if status_id != None and "/status/" in status_id:
                f.write("{0}\n".format(status_id))
                count = count + 1
    # with open("scroll.html", "w") as f:
    #     f.write(driver.page_source)
    return count

def login(driver):
    driver.get('https://twitter.com/login')
    time.sleep(3)
    username = driver.find_element_by_xpath('// *[ @ id = "page-container"] / div / div[1] / form / fieldset / div[1] / input')
    # username = driver.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div[1]/form/fieldset/div[1]/input")
    username.send_keys(config_.id)
    password = driver.find_element_by_xpath('// *[ @ id = "page-container"] / div / div[1] / form / fieldset / div[2] / input')
    # password = driver.find_element_by_xpath("/html/body/div[1]/div[2]/div/div/div[1]/form/fieldset/div[2]/input")
    password.send_keys(config_.pw)
    print("SUBMIT")
    password.submit()

    time.sleep(3)


def scroll(url):
    print("init()")
    driver = init()
    print("login()")
    login(driver)
    # driver.save_screenshot("login.png")
    print("open({0})".format(url))
    driver.get(url)
    # driver.save_screenshot("url.png")
    time.sleep(3)
    count = 0
    num = write_links(driver,url)
    old_num = num

    while True:
        for i in range(60):
            print("count_{0}-sec_{1}: links_{2}".format(count, i, num))
            # driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            body = driver.find_element_by_css_selector('body')
            body.send_keys(Keys.PAGE_DOWN)
            time.sleep(1)
        num = write_links(driver,url)
        if num == old_num:
            count = count + 1
        else:
            count = 0
        old_num = num
        if count == 3: # count[min]
            break

    driver.quit()


if __name__ == '__main__':
    if sys.argv[1].isdigit():
        screen_name = twitter.db.users.find_one({"_id_str":sys.argv[1]})["screen_name"]
    else:
        screen_name = sys.argv[1]
    scroll("https://twitter.com/{0}/media".format(screen_name))
    #scroll("https://twitter.com/{0}/with_replies".format(screen_name))

