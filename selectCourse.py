import requests
import argparse
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
from time import sleep
from enum import IntEnum
from datetime import datetime
from sys import argv

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
URL_LOGIN = 'http://bkjw.guet.edu.cn/student/public/login.asp'
URL_SELECT_COURSE = 'http://bkjw.guet.edu.cn/student/select.asp'
HEADERS = {'User-Agent': USER_AGENT}


class RtnSelectCourse(IntEnum):
    FULL = -2
    LOGIN_EXPIRED = -1
    UNKNOWN = 0
    SUCCESS = 1
    SELECTED = 2


def data_dict2str(data_dict):
    return '&'.join('%s=%s' % (k, v) for k, v in data_dict.items())


def retry_wrapper(func):
    from functools import wraps

    @wraps(func)
    def wrapper(*args, **kwargs):
        failed_times = 0
        timeout = 1
        # while failed_times < 3:
        while True:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                print(e)
                print('failed times:', failed_times + 1, ' next try:', timeout << 1, 'second(s) later.')
                sleep(timeout)
                failed_times += 1
                timeout <<= 1
                continue

    return wrapper


@retry_wrapper
def login(usn, pwd):
    session = requests.session()
    data = {'username': usn, 'passwd': pwd, 'login': '%B5%C7%A1%A1%C2%BC'}
    str_data = data_dict2str(data)
    r = session.post(URL_LOGIN, data=str_data,
                     headers={'User-Agent': USER_AGENT, 'Content-Type': 'application/x-www-form-urlencoded'},
                     allow_redirects=False)
    # print(r.content.decode(r.apparent_encoding))
    assert r.status_code == 302, 'pwd incorrect!'
    return session


@retry_wrapper
def select_course(session, select_type, course):
    course = str(course)
    assert course.isdigit() and len(course) == 7, 'course无效!'

    """
    requests.post()，使用dict作为data时，遇到非ascii码时，实践发现使用了两次url编码，
    (比如将'登　录'变成'%B5%C7%A1%A1%C2%BC'(gbk编码)，然后再将'%'编码成%25，变成'%25B5%25C7%25A1%25A1%25C2%25BC')，
    如果不需要转义，则要使用str类型的data，并且修改header，将Content-Type设置为：application/x-www-form-urlencoded。
    """
    data = {
        'selecttype': select_type,
        'course': course,
        'textbook{}'.format(course): 0,
        'lwBtnselect': '%CC%E1%BD%BB'
    }
    str_data = '&'.join('%s=%s' % (k, v) for k, v in data.items())
    r = session.post(URL_SELECT_COURSE, data=str_data,
                     headers={'User-Agent': USER_AGENT, 'Content-Type': 'application/x-www-form-urlencoded'},
                     # proxies={'http':'http://127.0.0.1:8080'}
                     )
    content_length = int(r.headers['Content-Length'])
    # print(r.status_code, content_length, r.content.decode('gbk'))

    assert not (r.status_code == 500 and content_length == 391), 'course无效!'

    if r.status_code == 500 and content_length == 315:
        return RtnSelectCourse.SUCCESS
    elif r.status_code == 200 and content_length == 254:
        return RtnSelectCourse.SELECTED
    elif r.status_code == 302:
        return RtnSelectCourse.LOGIN_EXPIRED
    elif r.status_code == 200 and content_length == 256:
        return RtnSelectCourse.FULL
    else:
        print('response: status_code:', r.status_code, 'content-length', content_length)
        return RtnSelectCourse.UNKNOWN


def start(username, password, select_type, courses, interval):
    session = login(username, password)

    params = [(session, select_type, course) for course in courses]
    pool = ThreadPool(len(courses))
    while len(params) > 0:
        results = pool.starmap(select_course, params)
        print(str(datetime.now())[:-7], end=' ')
        for i, result in enumerate(results):
            print(params[i][2], ':', result, end='. ')
        print()

        selected_courses = []
        for i, result in enumerate(results):
            # 删除成功课程
            if result > 0:
                course = params[i][2]
                print(str(datetime.now())[:-7], 'course select succeed:', course)
                selected_courses.append(course)
            # 登录超时重新登录
            elif result == RtnSelectCourse.LOGIN_EXPIRED or result == RtnSelectCourse.UNKNOWN:
                session = login(username, password)
                params = [(session, select_type, param[2]) for param in params]
        params = list(filter(lambda param: param[2] not in selected_courses, params))
        if len(params) == 0:
            break
        sleep(interval)
    print('==============all done.==============')
    pool.close()
    pool.join()


if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser('selectCourse')
    parser.add_argument('username')
    parser.add_argument('password')
    parser.add_argument('courses', nargs='+')
    parser.add_argument('-t', '--select_type', type=int, default=0, choices=range(0, 2), help='0: 正常(默认), 1: 重修')
    parser.add_argument('-i', '--interval', default=3, type=int, help='interval (second)')

    if len(argv) == 1:
        parser.print_help()
        exit(1)

    args = parser.parse_args()
    print(args)

    select_type = ['%D5%FD%B3%A3', '%D6%D8%D0%DE'][args.select_type]

    try:
        start(args.username, args.password, select_type, args.courses, args.interval)
    except KeyboardInterrupt:
        pass
