#自动捡漏选课脚本
自动捡漏选课脚本 for GUET (base on python3.5, requests)  

#Usage
```
usage: python3 selectCourse.py [-h] [-t {0,1}] [-i INTERVAL]
                    username password courses [courses ...]

positional arguments:
  username
  password
  courses

optional arguments:
  -h, --help            show this help message and exit
  -t {0,1}, --select_type {0,1}
                        0: 正常(默认), 1: 重修
  -i INTERVAL, --interval INTERVAL
                        interval (second)
```

例如：
```
python3 selectCourse.py 学号 密码 课号1 课号2
```