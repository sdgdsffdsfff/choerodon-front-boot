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
centerContent = {}
baseDirs = os.path.abspath(os.path.join(os.path.dirname("__file__")))
pathDir = {
    "menuDirs": '{baseDirs}/{value}/src/app/{value}/config/Menu.yml',
    "deployDirs": '{baseDirs}/.deploy.yml',
    "languageEnDir": '{baseDirs}/{value}/src/app/{value}/config/language/en.yml',
    "languagezhDir": '{baseDirs}/{value}/src/app/{value}/config/language/zh.yml',
}
newPathDir = {
    "wholeConfig": '{baseDirs}/menu.yml',
    "dirConfig": '{baseDirs}/dirMenu.yml'
}
levelArray = ["site","organization", "project", "user"]
serviceCode = 'choerodon.code'
serviceGroup = 'choerodon-front'
serviceKind = 'choerodon-front'

def writeYml(modules, newPathDir, language=None):
    whole = {
        "group": serviceGroup,
        "code": serviceCode,
        "kind": serviceKind,
        "language": {
            "English": languageYml(modules, pathDir["languageEnDir"]),
            "Chinese": languageYml(modules, pathDir["languagezhDir"]),
        },
        "menu": menuYml(modules, pathDir["menuDirs"])
    }
    ymlString = newPathDir.format(baseDirs = baseDirs, language = language)
    logging.info("Begin write menu data into: " + ymlString)
    ymlFile = open(ymlString, 'w+')
    ymlFile.write(json.dumps(whole))
    ymlFile.close()
    logging.info("End write menu data into: " + ymlString)
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

# 读取中英yml文件
def languageYml(modules, languageDir):
    logging.info("Loading menu language data from modules: " + "".join(modules))
    centerObj = {}
    languageContent = adjustContent(modules, languageDir)
    for i in modules:
        for k in languageContent[i].keys():
            centerArray = '{code}.{module}'.format(code = serviceCode, module = k)
            centerObj[centerArray] = languageContent[i][k]
            centerContent.update(centerObj)
    return centerObj

# 读取menuYml数据文件
def menuYml(modules, path):
    logging.info("Loading menu data from modules: " + "".join(modules))
    centerObj = {}
    menuYmlContent = adjustContent(modules, path)
    for i in modules:
        for k in menuYmlContent[i].keys():
            centerArray = '{code}.{module}'.format(code = serviceCode, module = k)
            if centerArray not in centerObj.keys():
                centerObj[centerArray] = menuYmlContent[i][k]
            centerLevel = []
            for level in levelArray:
                for saveLevel in menuYmlContent[i][k].keys():
                    if saveLevel == level:
                        centerLevel.append(saveLevel)
            for level in centerLevel:
                subMenu = menuDirYml(menuYmlContent[i][k][level], centerArray)
                if type(centerObj[centerArray][level]) == list:
                    centerObj[centerArray][level] = subMenu
                else:
                    centerObj[centerArray][level].update(subMenu)
                centerContent.update(centerObj)
    return centerObj

def menuDirYml(menuYmlContent, moduleDir):
    centerLevel = {}
    for (n,index) in zip(menuYmlContent,range(0,len(menuYmlContent))):
        for j in n.keys():
            centerMenuDir = '{codeModule}.{menu}'.format(codeModule = moduleDir,menu = j)
            centerLevel[centerMenuDir] = menuYmlContent[index][j]
    return centerLevel

if __name__ == '__main__':
    logging.basicConfig(format='[%(levelname)s] %(asctime)s [%(threadName)s:%(thread)d] [%(pathname)s:%(funcName)s:%(lineno)d] -- %(message)s', level=logging.DEBUG)
    
    parser = argparse.ArgumentParser()
    parser.add_argument('-o','--options', help='option name: yml / sql / dir', required=True)
    parser.add_argument('-m','--modules', nargs='+', help='module name')
    parser.add_argument('-i','--ip', help='databse host', dest="host", default="localhost")
    parser.add_argument('-p','--port', type=int, help='databse port', dest="port", default=3306)
    parser.add_argument('-u','--user', help='databse user', dest="user", default="choerodon")
    parser.add_argument('-s','--secret', help='databse password', dest="passwd", default="123456")
    parser.add_argument('-a','--attrs', help='enable update attrs, it can include sort & parent_id, you can use "port,parent_id" to update menu attrs', dest="attrs", default="")
    parser.add_argument('-d','--delete', type=bool, help='enable delete menu', dest="delete", default=False)
    parser.add_argument('-t','--type', help='mysql/oracle', dest="dbType", default="mysql")
    parser.add_argument('-x', '--debug', type=bool, help='enable debug log', dest="debug", default=False)
    args = parser.parse_args()

    options = os.environ.get('MENU_OPTIONS') if os.environ.get('MENU_OPTIONS') else args.options
    host = os.environ.get('DB_HOST') if os.environ.get('DB_HOST') else args.host
    port = os.environ.get('DB_PORT') if os.environ.get('DB_PORT') else args.port
    user = os.environ.get('DB_USER') if os.environ.get('DB_USER') else args.user
    passwd = os.environ.get('DB_PASS') if os.environ.get('DB_PASS') else args.passwd
    attrs = os.environ.get('UP_ATTRS') if os.environ.get('UP_ATTRS') else args.attrs
    delete = os.environ.get('ENABLE_DELETE') if os.environ.get('ENABLE_DELETE') else args.delete
    dbType = os.environ.get('DB_TYPE') if os.environ.get('DB_TYPE') else args.dbType
    debug = os.environ.get('ENABLE_DEBUG') if os.environ.get('ENABLE_DEBUG') else args.debug

    if cmp(options, "yml") == 0:
        logging.info("Begin parsing yaml")
        modules = args.modules
        logging.info("Contains the following modules: " + "".join(modules))
        writeYml(modules, newPathDir["wholeConfig"])
    elif (cmp(options, "sql") == 0) :
        logging.info("Begin init menu config")
        try:
            wholeConfig = newPathDir["wholeConfig"].format(baseDirs=baseDirs)
            logging.info("Begin parsing menu yaml from: " + wholeConfig)
            ymlFile = open(wholeConfig)
            logging.info("Begin Loading menu data")
            contentConfig = yaml.load(ymlFile)
        except:
            logging.error("Parsing menu yaml error!")
            logging.error("No such file or directory:" + newPathDir["wholeConfig"].format(baseDirs=baseDirs))
            sys.exit(1)

        if dbType == "mysql":
            logging.info("The db driver is mysql")
            config = {
                'host': host,
                'port': int(port),
                'user': user,
                'passwd': passwd
            }
            operate = __import__('menuMysql')
            menuOperate = operate.MenuMysql(config, os.getenv("DB_NAME", "iam_service"), attrs, debug)
        elif dbType == "oracle":
            logging.info("The db driver is oracle")
            config = {
                'host': host,
                'port': int(port),
                'user': user,
                'password': passwd,
                'sid':'xe'
            }
            operate = __import__('menuOracle')
            menuOperate = operate.MenuOracle(config, os.getenv("DB_NAME", "iam_service"), attrs, debug)
        
        logging.info("Db driver load success")

        logging.info("Insert into IAM_MEUN")
        menuOperate.insertMenuTable('IAM_MENU', contentConfig)

        logging.info("Insert into IAM_MEUN_TL")
        menuOperate.insertMenuTlTable('IAM_MENU_TL', contentConfig)
        menuOperate.insertServiceTlTable('IAM_MENU_TL', contentConfig)

        logging.info("Insert into IAM_MENU_PERMISSION")
        menuOperate.insertMenuPermission('IAM_MENU_PERMISSION', contentConfig)

        if delete == True:
            logging.info("Delete invalid menus")
            menuOperate.deleteMenu(contentConfig)
        menuOperate.close()
        ymlFile.close()
        logging.info("End init menu config")
    elif (cmp(options, "dir") == 0) :
        logging.info("Begin init dir config")
        try:
            dirConfig = newPathDir["dirConfig"].format(baseDirs=baseDirs)
            logging.info("Begin parsing dir yaml from: " + dirConfig)
            ymlFile = open(dirConfig)
            logging.info("Begin Loading dir data")
            contentConfig = yaml.load(ymlFile)
        except:
            logging.error("Parsing dir yaml error!")
            logging.error("No such file or directory:" + newPathDir["dirConfig"].format(baseDirs=baseDirs))
            sys.exit(1)
        if dbType == "mysql":
            logging.info("The db driver is mysql")
            config = {
                'host': host,
                'port': int(port),
                'user': user,
                'passwd': passwd
            }
            operate = __import__('menuMysql')
            menuOperate = operate.MenuMysql(config, os.getenv("DB_NAME", "iam_service"), attrs, debug)
        
        logging.info("Db driver load success")

        logging.info("Insert dir data into database")        
        menuOperate.insertDir(contentConfig)
        if delete == True:
            logging.info("Delete invalid dir data")
            menuOperate.deleteDir(contentConfig)
        menuOperate.close()
        ymlFile.close()
        logging.info("End init dir config")
    else:
        logging.error("Argument -o/--options must be yml, sql or dir")