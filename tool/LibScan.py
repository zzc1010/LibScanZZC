# 程序启动入口
import os
import argparse
import datetime
import sys
import zipfile
sys.path.append(os.getcwd() + "/module")
from module.config import LOGGER
from module.analyzer import search_lib_in_app,search_libs_in_app

# 用户命令行输入参数解析
def parse_arguments():
    parser = argparse.ArgumentParser(description='Process some integers')
    subparsers = parser.add_subparsers(
        help='sub-command help', dest='subparser_name')

    parser_one = subparsers.add_parser(
        'detect_one', help='Detection mode (Single): detect if multiple apps contain a specific TPL version')
    parser_one.add_argument(
        '-o',
        metavar='FOLDER',
        type=str,
        default='outputs',
        help='Specify directory of detection results (containing result in .TXT per app)')
    parser_one.add_argument(
        '-p',
        metavar='num_processes',
        type=int,
        default=None,
        help='Specify maximum number of processes used in detection (default=#CPU_cores)'
    )
    parser_one.add_argument(
        '-af',
        metavar='FOLDER',
        type=str,
        help='Specify directory of apps'
    )
    parser_one.add_argument(
        '-lf',
        metavar='FOLDER',
        type=str,
        help='Specify directory of TPL versions'
    )
    parser_one.add_argument(
        '-ld',
        metavar='FOLDER',
        type=str,
        help='Specify directory of TPL versions in DEX files'
    )

    parser_specific = subparsers.add_parser(
        'detect_all', help='Detection mode (Multiple): detect if multiple apps contain multiple TPL versions')
    parser_specific.add_argument(
        '-o',
        metavar='FOLDER',
        type=str,
        default='outputs',
        help='Specify directory of detection results (containing result in .TXT per app)')
    parser_specific.add_argument(
        '-p',
        metavar='num_processes',
        type=int,
        default=None,
        help='Specify maximum number of processes used in detection (default=#CPU_cores)'
    )
    parser_specific.add_argument(
        '-af',
        metavar='FOLDER',
        type=str,
        help='Specify directory of apps')
    parser_specific.add_argument(
        '-lf',
        metavar='FOLDER',
        type=str,
        help='Specify directory of TPL versions'
    )
    parser_specific.add_argument(
        '-ld',
        metavar='FOLDER',
        type=str,
        help='Specify directory of TPL versions in DEX files'
    )

    return parser.parse_args()

# 使用dex2jar工具将待检测的jar文件转换为dex文件
def jar_to_dex(libs_folder, lib_dex_folder):
    for file in os.listdir(libs_folder):
        file_name = file[:file.rfind(".")]
        if sys.platform.find("win") != -1:
            cmd = "module/dex2jar/d2j-jar2dex.bat " + libs_folder + "/" + file + " -o " + lib_dex_folder + "/" + file_name + ".dex"
        else:
            cmd = "module/dex2jar/d2j-jar2dex.sh " + libs_folder + "/" + file + " -o " + lib_dex_folder + "/" + file_name + ".dex"
        os.system(cmd)

# 将aar文件转换为jar文件
def arr_to_jar(libs_folder):
    for file in os.listdir(libs_folder):
        if file.endswith(".aar"):
            os.rename(libs_folder + "/" + file, libs_folder + "/" + file[:file.rfind(".")] + ".zip")

    for file in os.listdir(libs_folder):
        if file.endswith(".zip"):
            zip_file = zipfile.ZipFile(libs_folder + "/" + file)
            zip_file.extract("classes.jar", ".")
            for f in os.listdir(libs_folder):
                if f == "classes.jar":
                    os.rename(libs_folder + "/" + f, libs_folder + "/" + file[:file.rfind(".")] + ".jar")
            zip_file.close()
            os.remove(libs_folder+ "/" + file)

def main(lib_folder = 'libs',
         lib_dex_folder = 'libs_dex',
         apk_folder = 'apks',
         output_folder = 'outputs',
         processes = None,
         model = 'multiple'):
    # 将库目录下所有的arr、jar文件转化为dex文件，并放入libs_dex目录下
    if len(os.listdir(lib_dex_folder)) == 0:
        arr_to_jar(lib_folder)
        jar_to_dex(lib_folder, lib_dex_folder)

    if model == "multiple": # 在库级别并行分析
        search_libs_in_app(os.path.abspath(lib_dex_folder),
                          os.path.abspath(apk_folder),
                          os.path.abspath(output_folder),
                          processes)
    elif model == "one": #在apk级别并行分析
        search_lib_in_app(os.path.abspath(lib_dex_folder),
                           os.path.abspath(apk_folder),
                           os.path.abspath(output_folder),
                           processes)

if __name__ == '__main__':
    args = parse_arguments()

    LOGGER.debug("args: %s", args)

    if args.subparser_name == 'detect_one':
        main(lib_folder = args.lf, lib_dex_folder = args.ld, apk_folder=args.af, output_folder= args.o, processes=args.p, model="one")
    elif args.subparser_name == 'detect_all':
        main(lib_folder = args.lf, lib_dex_folder = args.ld, apk_folder=args.af, output_folder= args.o, processes=args.p, model="multiple")
    else:
        LOGGER.debug("检测模式输入错误!")
