import argparse
from fp_files_conf import fp_files_conf as conf
import lib_fingerprint_files
import lib_helper_functions
import logging
import multiprocessing
import sys
import time

logger = logging.getLogger()

def get_commandline_parameters():
    """
    >>> sys.argv.append('--fp_dir=./testfiles/')
    >>> sys.argv.append('--resultfile=./testresults/fp_files_result1.csv')
    >>> sys.argv.append('--batchmode')
    >>> sys.argv.append('--no_admin')
    >>> sys.argv.append('--no_hashing')
    >>> sys.argv.append('--no_mp')
    >>> get_commandline_parameters()
    >>> conf.fp_files_dir
    './testfiles/'
    >>> conf.interactive
    False
    >>> conf.exit_if_not_admin
    False

    """
    parser = argparse.ArgumentParser(description='create fingerprint of the files under --fp_files_dir ')
    parser.add_argument('positional_ignored', type=str, nargs='*', help='Positional Arguments are ignored')
    parser.add_argument('--fp_dir', type=str, required=False, default='', help='path to the directory to fingerprint, e.g. c:\\test\\')
    parser.add_argument('--resultfile', type=str, required=False, default='', help='path to the result file, e.g. c:\\results\\fp_files_result1.csv')
    parser.add_argument('--batchmode', dest='batchmode', default=False, action='store_true', help='no user interactions')
    parser.add_argument('--no_admin', dest='no_admin', default=False, action='store_true', help='run with limited rights, not recommended')
    parser.add_argument('--no_hashing', dest='no_hashing', default=False, action='store_true', help='do not calculate file hashes, not recommended')
    parser.add_argument('--no_mp', dest='no_mp', default=False, action='store_true', help='no multiprocessing - preserves ordering of files in the result')
    args = parser.parse_args()
    conf.fp_files_dir = args.fp_dir
    conf.fp_result_filename = args.resultfile
    conf.interactive = not args.batchmode
    conf.exit_if_not_admin = not args.no_admin
    conf.hash_files = not args.no_hashing
    conf.multiprocessing = not args.no_mp

def main():
    """
    >>> import test
    >>> import lib_doctest
    >>> lib_doctest.setup_doctest_logger()
    >>> timestamp = time.time()
    >>> test.create_testfiles_fingerprint_1(timestamp)
    >>> sys.argv.append('--fp_dir=./testfiles/')
    >>> sys.argv.append('--resultfile=./testresults/fp_files_result1.csv')
    >>> sys.argv.append('--batchmode')
    >>> sys.argv.append('--no_admin')
    >>> get_commandline_parameters()
    >>> logger.level=logging.ERROR
    >>> main()  # +ELLIPSIS, +NORMALIZE_WHITESPACE

    >>> test.modify_testfiles_fingerprint_2(timestamp)
    >>> sys.argv.append('--resultfile=./testresults/fp_files_result2.csv')
    >>> get_commandline_parameters()
    >>> logger.level=logging.ERROR
    >>> main()  # +ELLIPSIS, +NORMALIZE_WHITESPACE

    >>> sys.argv.append('--no_mp')
    >>> get_commandline_parameters()
    >>> logger.level=logging.ERROR
    >>> main()  # +ELLIPSIS, +NORMALIZE_WHITESPACE

    >>> sys.argv.append('--no_hashing')
    >>> get_commandline_parameters()
    >>> logger.level=logging.ERROR
    >>> main()  # +ELLIPSIS, +NORMALIZE_WHITESPACE


    """

    lib_helper_functions.config_console_logger()
    lib_helper_functions.inform_if_not_run_as_admin(exit_if_not_admin=conf.exit_if_not_admin, interactive=conf.interactive)
    logger.info('create files fingerprint {}'.format(conf.version))

    check_fp_files_dir()
    check_fp_result_filename()

    conf.logfile_fullpath = lib_helper_functions.strip_extension(conf.fp_result_filename) + '.log'
    lib_helper_functions.config_file_logger(logfile_fullpath=conf.logfile_fullpath)

    logger.info('fingerprinting directory : {}'.format(conf.fp_files_dir))
    logger.info('results filename         : {}'.format(conf.fp_result_filename))
    logger.info('file hashing             : {}'.format(conf.hash_files))
    logger.info('multiprocessing          : {}'.format(conf.multiprocessing))

    with lib_fingerprint_files.FingerPrintFiles() as fingerprint_files:
        if conf.multiprocessing:                # test c:\windows : 66 seconds
            fingerprint_files.create_fp_mp()
        else:
            fingerprint_files.create_fp()       # test c:\windows : 124 seconds

    logger.info('Finished\n\n')
    lib_helper_functions.logger_flush_all_handlers()
    if conf.interactive:
        input('enter for exit, check the logfile')

def check_fp_result_filename(test_input:str= ''):
    """
    >>> conf.interactive = False
    >>> conf.fp_result_filename='./testresults/fp_files_result1.csv'
    >>> check_fp_result_filename()

    >>> conf.fp_result_filename='x:/testresults/fp_files_result_test'
    >>> check_fp_result_filename()  # +ELLIPSIS, +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    SystemExit: 1
    >>> conf.interactive = True
    >>> check_fp_result_filename(test_input='./testresults/fp_files_result1.csv')

    can not write to x:/testresults/fp_files_result_test.csv, probably access rights

    """
    conf.fp_result_filename = lib_helper_functions.strip_extension(conf.fp_result_filename) + '.csv'
    while not is_fp_result_filename_ok(f_path=conf.fp_result_filename):
        if conf.interactive:
            if test_input:
                conf.fp_result_filename = test_input
            else:
                conf.fp_result_filename = input('result filename (e.g. c:\\results\\fingerprint1.csv ): ')
            conf.fp_result_filename = lib_helper_functions.strip_extension(conf.fp_result_filename) + '.csv'
            if not is_fp_result_filename_ok(f_path=conf.fp_result_filename):
                logger.info('can not write to {}, probably access rights'.format(conf.fp_result_filename))
            else:
                break
        else:
            logger.info('can not write to {}, probably access rights'.format(conf.fp_result_filename))
            sys.exit(1)

def check_fp_files_dir(test_input:str= ''):
    """
    >>> conf.interactive = False
    >>> conf.fp_files_dir = './testfiles/'
    >>> check_fp_files_dir()
    >>> conf.fp_files_dir = './not_exist/'
    >>> check_fp_files_dir()  # +ELLIPSIS, +NORMALIZE_WHITESPACE
    Traceback (most recent call last):
        ...
    SystemExit: None
    >>> conf.interactive = True
    >>> check_fp_files_dir(test_input='./testfiles/')  # +ELLIPSIS, +NORMALIZE_WHITESPACE

    can not read directory ./not_exist/

    """
    while not is_fp_files_dir_ok():
        if conf.interactive:
            if test_input:
                conf.fp_files_dir = test_input
            else:
                conf.fp_files_dir = input('directory to fingerprint (e.g. c:\\test\\ ): ')
            if not is_fp_files_dir_ok():
                logger.info('can not read directory {}, try again'.format(conf.fp_files_dir))
                lib_helper_functions.logger_flush_all_handlers()
            else:
                break
        else:
            logger.info('can not read directory {}'.format(conf.fp_files_dir))
            lib_helper_functions.logger_flush_all_handlers()
            sys.exit(1)

def is_fp_files_dir_ok()->bool:
    """
    >>> conf.fp_files_dir = './testfiles/'
    >>> is_fp_files_dir_ok()
    True
    >>> conf.fp_files_dir = './testfiles'
    >>> is_fp_files_dir_ok()
    True
    >>> conf.fp_files_dir = './not_exist/'
    >>> is_fp_files_dir_ok()
    False
    """
    # noinspection PyBroadException
    try:
        lib_fingerprint_files.format_fp_files_dir()
        return True
    except Exception:
        return False

def is_fp_result_filename_ok(f_path:str)->bool:
    """
    >>> is_fp_result_filename_ok(f_path='./testresults/fp_files_result_test.csv')
    True
    >>> is_fp_result_filename_ok(f_path='./testresults/fp_files_result_test')
    True
    >>> is_fp_result_filename_ok(f_path='x:/testresults/fp_files_result_test')
    False
    """
    # noinspection PyBroadException
    try:
        lib_helper_functions.touch_file_create_directory(f_path=f_path)
        return True
    except Exception:
        return False

def set_logfile_fullpath():
    """
    >>> conf.fp_result_filename = './testresults/fp_files_result_test'
    >>> set_logfile_fullpath()
    >>> conf.logfile_fullpath
    './testresults/fp_files_result_test.log'
    """
    conf.logfile_fullpath = lib_helper_functions.strip_extension(conf.fp_result_filename) + '.log'


if __name__ == '__main__':
    # Hack for multiprocessing.freeze_support() to work from a
    # setuptools-generated entry point.
    multiprocessing.freeze_support()
    get_commandline_parameters()
    main()