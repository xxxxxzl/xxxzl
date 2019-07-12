import requests
from scrapy.selector import Selector
import time
import html2text as ht
import os
from selenium import webdriver
import pdfkit
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# 小专栏基础地址
xzl = 'https://xiaozhuanlan.com'

# 设置等待时长
seconds = 5

# 文件标题是否添加文章编写时间
hasTime = True

# 是否以MarkDown格式导出, 导出pdf需先下载![wkhtmltopdf](https://wkhtmltopdf.org/downloads.html)
# mac可以直接通过 `brew install Caskroom/cask/wkhtmltopdf` 进行安装
markdown = True

# 当为小书时，且`markdown=False`，是否将所有章节进行拼接为一个pdf
xs_pdf = True

driver = webdriver.Safari()


def xxxzl():
    global driver
    driver.implicitly_wait(20)
    driver.get(xzl+'/login')
    github = driver.find_element_by_class_name('wechat-login-btn')
    github.click()
    k = input('是否已使用微信登录，回车键确认, q退出')
    if k == 'q':
        driver.quit()
        exit()
    else:
        driver.get(xzl + '/me/subscribes')
        get_all_html()
        get_all_subscribes()


# 采集订阅列表
def get_all_subscribes():
    titles = driver.find_elements_by_class_name('zl-title')
    size = len(titles)
    print('采集完成， 共找到%d条记录\n' % size)
    for idx, title in enumerate(titles):
        print(str(idx) + ': ' + title.text.replace(' ', '').replace('\n', ''))
    serial_number = select_zl(titles, size)
    if serial_number == size:
        for i in range(size):
            element = driver.find_elements_by_class_name('streamItem-cardInner')[i]
            c_title = driver.find_elements_by_class_name('zl-title')[i].text.replace(' ', '').replace('\n', '')
            book = True
            try:
                element.find_element_by_class_name('zl-bookContent')
            except NoSuchElementException:
                book = False
            except TimeoutException:
                book = False
            if book:
                print('将要导出的类型为: 小书\n')
                get_xs(element, c_title, True)
            else:
                print('将要导出的类型为: 专栏\n')
                get_zl(element, c_title, True)
            driver.back()
            time.sleep(seconds)
        print('全部订阅已采集完成, 即将退出程序!!!')
        driver.quit()
        exit()
    else:
        element = driver.find_elements_by_class_name('streamItem-cardInner')[serial_number]
        c_title = titles[serial_number].text.replace(' ', '').replace('\n', '')
        book = True
        try:
            element.find_element_by_class_name('zl-bookContent')
        except NoSuchElementException:
            book = False
        except TimeoutException:
            book = False
        if book:
            print('将要导出的类型为: 小书\n')
            get_xs(element, c_title)
        else:
            print('将要导出的类型为: 专栏\n')
            get_zl(element, c_title)
    driver.back()
    time.sleep(seconds)
    get_all_subscribes()


# 采集小书目录
def get_xs(element, xs_title, xzl_path=False):
    el = element.find_element_by_tag_name('a')
    el.click()
    ims = driver.find_elements_by_class_name('book-cata-item')
    imss = driver.find_elements_by_class_name('cata-sm-item')
    print('目录采集完成, 共找到: ' + str(len(ims)) + '大节, ' + str(len(imss)) + '小节')
    html = ''
    xp = ''
    if xzl_path:
        xp = '小专栏/'
    xs_path = os.path.join(os.path.expanduser("~"), 'Desktop') + '/' + \
               xp + xs_title + '/'
    for idx, item in enumerate(ims):
        href = item.find_element_by_tag_name('a').get_property('href')
        path = xs_path + item.text.replace('\n', '').replace(' ', '').replace('/', '-') + '/'
        if xs_pdf and not markdown:
            path = xs_path
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            xjs = item.find_elements_by_class_name('cata-sm-item')
            html += get_xs_detail(href, path)
            for idx2, xj in enumerate(xjs):
                href = xj.find_element_by_tag_name('a').get_property('href')
                html += get_xs_detail(href, path)
        except NoSuchElementException:
            print('当前章节未发现小节内容')
    if xs_pdf and not markdown:
        # 在html中加入编码， 否则中文会乱码
        html = driver.find_element_by_id('a4').get_attribute('innerHTML') + html
        html = "<html><head><meta charset='utf-8'></head> " + html + "</html>"
        pdfkit.from_string(html, path + xs_title + '.pdf')
    print('小书: ' + xs_title + ' 采集完成, 文件存储路径为: ' + xs_path + '\n')


# 获取小书详情
def get_xs_detail(href, path):
    text_maker = ht.HTML2Text()
    response = requests.get(url=href, headers={'cookie': '_xiaozhuanlan_session=' + driver.get_cookies()[0]['value']})
    selector = Selector(text=response.text)
    html = selector.css(u'.cata-book-content').extract_first()
    zj_title = selector.css(u'.cata-sm-title ::text').extract_first().replace('\n', '').replace(' ', '').replace('/', '-')
    print('当前采集章节为: ' + zj_title)
    file_name = zj_title
    if markdown:
        md = text_maker.handle(html)
        with open(path + file_name + '.md', 'w') as f:
            f.write(md)
    else:
        if not xs_pdf:
            # 在html中加入编码， 否则中文会乱码
            html = "<html><head><meta charset='utf-8'></head> " + html + "</html>"
            pdfkit.from_string(html, path + file_name + '.pdf')
        else:
            return html
    print(zj_title + '采集完成\n')
    return ''


# 采集专栏列表
def get_zl(element, zl_title, xzl_path=False):
    el = element.find_element_by_tag_name('a')
    el.click()
    get_all_html()
    items = driver.find_elements_by_class_name('topic-body-link')
    size = len(items)
    print('目录采集完成， 共找到%d条记录\n'%size)
    xp = ''
    if xzl_path:
        xp = '小专栏/'
    path = os.path.join(os.path.expanduser("~"), 'Desktop') + '/' + xp + zl_title + '/'
    for idx, item in enumerate(items):
        href = item.get_property('href')
        if not os.path.exists(path):
            os.makedirs(path)
        get_zl_detail(href, path)
    print('专栏: ' + zl_title + ' 采集完成, 文件存储路径为: ' + path + '\n')


# 获取专栏详情
def get_zl_detail(href, path):
    response = requests.get(url=href, headers={'cookie': '_xiaozhuanlan_session=' + driver.get_cookies()[0]['value']})
    selector = Selector(text=response.text)
    text_maker = ht.HTML2Text()
    create_time = selector.css(u'.time abbr::attr(title)').extract_first()
    html = selector.css(u'.xzl-topic-body-content').extract_first()
    zj_title = selector.css(u'.topic-title ::text').extract_first().replace('\n', '').replace(' ', '').replace('/', '-')
    print('当前采集章节为: ' + zj_title)
    file_name = zj_title
    if hasTime:
        file_name = create_time + ' ' + zj_title
    if markdown:
        md = text_maker.handle(html)
        with open(path + file_name + '.md', 'w') as f:
            f.write(md)
    else:
        # 在html中加入编码， 否则中文会乱码
        html = "<html><head><meta charset='utf-8'></head> " + html + "</html>"
        pdfkit.from_string(html, path + file_name + '.pdf')
    print(zj_title + '采集完成\n')


# 选择导出内容
def select_zl(titles, size):
    ss = input('请输入想要导出的专栏序号, all:全部, q:退出\n')
    if ss.isdigit():
        serial_number = int(ss)
        if int(serial_number) < size:
            title = titles[serial_number].text.replace(' ', '').replace('\n', '')
            print('是否确认导出: ' + title + '')
            yn = input('y/n\n')
            if yn == 'y':
                print('即将为您导出: ' + title + '\n')
                return serial_number
            else:
                return select_zl(titles, size)
        else:
            print('未查询到该序号对应的专栏\n')
            return select_zl(titles, size)
    elif ss == 'all':
        print('是否确认导出全部订阅内容')
        yn = input('y/n\n')
        if yn == 'y':
            return size
        else:
            return select_zl(titles, size)
    elif ss == 'q':
        print('退出程序!!!')
        driver.quit()
        exit()
    else:
        return select_zl(titles, size)


# 获取完整html内容
def get_all_html():
    style = ''
    while not style == 'display: block;':
        print('正在采集。。。\n')
        time.sleep(seconds)
        # 此处模拟浏览器滚动， 以采集更多数据
        js = "window.scrollTo(0, document.documentElement.scrollHeight)"
        driver.execute_script(js)
        style = driver.find_element_by_class_name('xzl-topic-list-no-topics').get_attribute('style')


if __name__ == '__main__':
    print('开始')
    xxxzl()