import datetime
import json
import os, subprocess, threading
import sys
import time
# https://www.runoob.com/python3/python3-date-time.html
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from optparse import OptionParser

import requests


def target(arg_t):
    count_t = arg_t[0]
    cmd_t = arg_t[1]
    dexDir = arg_t[2]

    print("start ", count_t, dexDir)
    print(cmd_t)
    process = subprocess.Popen(cmd_t, shell=True)
    (out, err) = process.communicate()
    print("end ", count_t, dexDir)


if __name__ == "__main__":
    usage = "usage: python3 %prog -d <apk_cat_root_dir> -l <logDir> -i <libdir> -b <blackList>"
    parser = OptionParser(usage=usage)
    parser.add_option('-d', '--dir', action='store', type='string', dest='dir',
                      help='The dir of apk files.')
    parser.add_option('-b', '--blackfile', action='store', type='string', dest='blackFile', help='Black list')
    parser.add_option('-l', '--log', action='store', type='string', dest='log', help='The log dir')
    parser.add_option('-i','--lib',action='store', type='string', dest='lib',help='the lib dir')
    (options, args) = parser.parse_args()
    SLEEPTIME = 2
    currentPath = os.getcwd()
    matching = "LibScan.py"
    apk_cat_root_dir = "NoDIR"
    logDir = "NoLogDir"
    blackFile = "NoListFile"
    list_limit = False  # if we need to limit the range of each category
    output_root_dir = "Output"
    lib_root_dir = "Input"

    # i = 0
    all_query = True
    queryNum = None
    allQuery = True
    if not options.dir:
        parser.error('-d <apk_cat_dir> is mandatory')
        # print("Wrong args!")
        exit(0)
    else:
        apk_cat_root_dir = options.dir
        if apk_cat_root_dir.endswith('/'):
            apk_cat_root_dir = apk_cat_root_dir[:-1]
    if options.blackFile:
        blackFile = options.blackFile

    if options.log:
        logDir = options.log
        if logDir.endswith('/'):
            logDir = logDir[:-1]
        if not os.path.exists(logDir):
            os.makedirs(logDir)
    if options.lib:
        lib_root_dir = options.lib
        if lib_root_dir.endswith('/'):
            lib_root_dir = lib_root_dir[:-1]
    lib_dir = os.path.join(lib_root_dir,"libs")
    lib_dex_dir = os.path.join(lib_root_dir,"libs_dex")
    if not (os.path.exists(lib_dir) and os.path.exists(lib_dex_dir) ):
        parser.error(f'{lib_dir} or {lib_dex_dir} not exist!')
        # print("Wrong args!")
        exit(0)

    blackList = []
    if os.path.exists(blackFile):
        with open(blackFile, "r") as file1:
            for line in file1:
                line = line.strip()
                blackList.append(line)

    cat_dir_list = os.listdir(apk_cat_root_dir)
    count = 0
    cat_dir_list.sort()
    for category in cat_dir_list:
        count += 1
        if category in blackList:
            print("Skip", category)
            continue
        # # remove this if want to handle GAME
        # if category.startswith("GAME_"):
        #     continue
        cat_long_dir = os.path.join(apk_cat_root_dir, category)
        # apk_path_list = []

        localtime = time.asctime(time.localtime(time.time()))
        formatTime = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        timeList = formatTime.split("-")
        month = timeList[1]
        day = timeList[2]
        hour = timeList[3]
        minute = timeList[4]
        logFile = os.path.join(logDir,
                               "LibScan_" + category + "_" + month + day + "_" + hour + minute + ".txt")
        logErrorFile = os.path.join(logDir,
                                    "LibScan_" + category + "_error_" + month + day + "_" + hour + minute + ".txt")

        pool = ThreadPoolExecutor(max_workers=1)
        starttime = time.time()
        allTask = []
        output_dir = os.path.join(output_root_dir, category)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        arg = (count, 'python3 ython3 %s detect_all -o %s -p 4 -af %s -lf %s -ld %s' %\
               (matching, output_dir, cat_long_dir, lib_dir, lib_dex_dir), category)
        if logDir != "NoLogDir":
            arg = (count, 'python3 %s detect_all -o %s -p 4 -af %s -lf %s -ld %s 1> %s 2>%s' %\
                   (matching, output_dir, cat_long_dir, lib_dir, lib_dex_dir, logFile, logErrorFile), category)
        allTask.append(pool.submit(target, arg))

        wait(allTask, return_when=ALL_COMPLETED)
        endtime = time.time()

        print(category, str(round(endtime - starttime, 2)) + "s")
        with open(blackFile, "a") as file2:
            file2.write(category + "\n")

    #send wechat message if finished
    current_time = datetime.datetime.now()
    result = "finished"
    programname = __file__

    # wxpusher
    headers = {'content-type': "application/json"}
    body = {
        "appToken": "AT_yuSiBxUV7ymmaWI1FI8E5W47DbFoy8T3",
        "content": "Finished work: " + " ".join([programname, str(current_time)]),
        "summary": "Finished work: " + " ".join([programname, str(current_time)]),
        "contentType": 1,
        "topicIds": [],
        "uids": ["UID_adrAb8zuLwrHd8ZApL0eqhJ8mXLJ"]
    }

    ret = requests.post('http://wxpusher.zjiecode.com/api/send/message', data=json.dumps(body), headers=headers)