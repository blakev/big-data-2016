# big-data-2016
Vivint's team repository for the Qubole Big Data 2016 competition.

## Objective

*Team objective goes here.*

## Getting Started
### Requirements

- Python 3.5+ (https://python.org)


### Installation

**Database**:

```bash
$ docker run --name bigdata-mariadb  -e MYSQL_ROOT_PASSWORD=bigdata2016 -d -p 3306:3306 mariadb:latest
$ mysql -u root -h 0.0.0.0 -P 3306 -p bigdata2016
mysql> create database ratemyprofessor;
mysql> exit
```

**Linux**:

```bash
$ sudo apt install python3.5

$ mkdir big-data && cd big-data

$ pip install --upgrade virtualenv pip

$ virtualenv -p python3.5 ./bigdata

$ ./bigdata/bin/activate

(bigdata) $ pip install -r requirements.txt

(bigdata) $ python
Python 3.5.0 (default, Oct 19 2015, 16:36:23)
[GCC 4.9.2] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import vivint
>>>
```

**Windows**:

```bash
```

## Links
- [Vivint, inc.](http://vivint.com)

## Attribution