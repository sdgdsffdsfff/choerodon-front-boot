#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import os
import yaml
import sys
import argparse
import logging
reload(sys)
sys.setdefaultencoding('utf8')

__author__="fan@choerodon.io"

content = {}
baseDirs = os.path.abspath(os.path.join(os.path.dirname("__file__")))
pathDir = {
    "dashboardDirs": '{baseDirs}/{value}/src/app/{value}/config/dashboard/dashboard.yml',
    "languageEnDir": '{baseDirs}/{value}/src/app/{value}/config/dashboard/language/en.yml',
    "languagezhDir": '{baseDirs}/{value}/src/app/{value}/config/dashboard/language/zh.yml',
}
newPathDir = {
    "wholeConfig": '{baseDirs}/dashboard.yml'
}

# write dashboard yml file
def writeYml(modules, newPathDir, language=None):
    whole = {
        "dashboard": dashboardYml(modules, pathDir["dashboardDirs"]),
        "language": {
            "English": languageYml(modules, pathDir["languageEnDir"]),
            "Chinese": languageYml(modules, pathDir["languagezhDir"]),
        }
    }
    ymlString = newPathDir.format(baseDirs = baseDirs, language = language)
    logging.info("Begin write dashboard data into: " + ymlString)
    ymlFile = open(ymlString, 'w+')
    ymlFile.write(json.dumps(whole))
    ymlFile.close()
    logging.info("End write dashboard data into: " + ymlString)

# get dir
def adjustString(dirString, value=None):
    endString = dirString.format(baseDirs = baseDirs, value = value)
    return endString

# get yml data
def adjustContent(modules, dirName):
    for i in modules:
        ymlFile = open(adjustString(dirName, i))
        content[i] = yaml.load(ymlFile)
    return content
# get dashboard yml data
def dashboardYml(modules, path):
    logging.info("Loading dashboard data from modules: " + "".join(modules))
    centerObj = {}
    dashboardContent = adjustContent(modules, path)
    for i in modules:
        for k in dashboardContent[i]["dashboard"]:
            code = '{namespace}/{code}'.format(namespace = i, code = k["code"])
            k["namespace"] = i
            centerObj[code] = k
    return centerObj

# get dashboard tl yml data
def languageYml(modules, languageDir):
    centerObj = {}
    languageContent = adjustContent(modules, languageDir)
    for i in modules:
        for k in languageContent[i].keys():
            code = '{namespace}/{code}'.format(namespace = i, code = k)
            centerObj[code] = languageContent[i][k]
    return centerObj

if __name__ == '__main__':
    logging.basicConfig(format='[%(levelname)s] %(asctime)s [%(threadName)s:%(thread)d] [%(pathname)s:%(funcName)s:%(lineno)d] -- %(message)s', level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('-o','--options', help='option name: yml / sql', required=True)
    parser.add_argument('-m','--modules', nargs='+', help='module name')
    parser.add_argument('-i','--ip', help='databse host', dest="host", default="localhost")
    parser.add_argument('-p','--port', type=int, help='databse port', dest="port", default=3306)
    parser.add_argument('-u','--user', help='databse user', dest="user", default="choerodon")
    parser.add_argument('-s','--secret', help='databse password', dest="passwd", default="123456")
    parser.add_argument('-t','--type', help='mysql/oracle', dest="dbType", default="mysql")
    parser.add_argument('-d','--delete', type=bool, help='enable delete menu', dest="delete", default=True)
    parser.add_argument('-x', '--debug', type=bool, help='enable debug log', dest="debug", default=False)
    args = parser.parse_args()

    options = os.environ.get('DASHBOARD_OPTIONS') if os.environ.get('DASHBOARD_OPTIONS') else args.options
    if cmp(options, "yml") == 0:
        logging.info("Begin parsing yaml")
        modules = args.modules
        logging.info("Contains the following modules: " + "".join(modules))
        writeYml(modules, newPathDir["wholeConfig"])
    elif (cmp(options, "sql") == 0) :
        logging.info("Begin init dashboard config")
        try:
            wholeConfig = newPathDir["wholeConfig"].format(baseDirs=baseDirs)
            logging.info("Begin parsing dashboard yaml from: " + wholeConfig)
            ymlFile = open(wholeConfig)
            logging.info("Begin Loading dashboard data")
            contentConfig = yaml.load(ymlFile)
        except:
            logging.error("Parsing menu yaml error!")
            logging.error("No such file or directory:" + newPathDir["wholeConfig"].format(baseDirs=baseDirs))
            sys.exit(1)
        
        host = os.environ.get('DB_HOST') if os.environ.get('DB_HOST') else args.host
        port = os.environ.get('DB_PORT') if os.environ.get('DB_PORT') else args.port
        user = os.environ.get('DB_USER') if os.environ.get('DB_USER') else args.user
        passwd = os.environ.get('DB_PASS') if os.environ.get('DB_PASS') else args.passwd
        dbType = os.environ.get('DB_TYPE') if os.environ.get('DB_TYPE') else args.dbType
        delete = os.environ.get('ENABLE_DELETE') if os.environ.get('ENABLE_DELETE') else args.delete
        debug = os.environ.get('ENABLE_DEBUG') if os.environ.get('ENABLE_DEBUG') else args.debug

        if dbType == "mysql":
            logging.info("The db driver is mysql")

            config = {
                'host': host,
                'port': int(port),
                'user': user,
                'passwd': passwd
            }
            operate = __import__('dashboardMysql')
            dashboardOperate = operate.DashboardMysql(config, os.getenv("DB_NAME", "iam_service"), debug)

        elif dbType == "oracle":
            logging.info("The db driver is oracle")

            config = {
                'host': host,
                'port': int(port),
                'user': user,
                'password': passwd,
                'sid':'xe'
            }
            operate = __import__('dashboardOracle')
            dashboardOperate = operate.DashboardOracle(config, os.getenv("DB_NAME", "iam_service"), debug)

        logging.info("Db driver load success")

        logging.info("Insert into IAM_DASHBOARD")
        dashboardOperate.insertDashboard(contentConfig)

        logging.info("Insert into IAM_DASHBOARD_TL")
        dashboardOperate.insertDashbaordTl(contentConfig)

        logging.info("Insert into IAM_DASHBOARD_ROLE")
        dashboardOperate.insertDashboardRole(contentConfig)

        if delete == True:
            logging.info("Delete invalid dashboards")
            dashboardOperate.deleteDashboard(contentConfig)
        dashboardOperate.close()
        ymlFile.close()

    else:
        logging.error("Argument -o/--options must be yml or sql")