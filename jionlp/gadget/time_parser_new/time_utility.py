# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com

import re
import time
import datetime

from jionlp.rule.rule_pattern import *
from ..money_parser import MoneyParser


class TimeUtility(object):
    """
    时间解析的助手类，主要包括时间比较函数，等等。
    """

    @staticmethod
    def _compare_handler(first_handler, second_handler):
        """ 比较两个 handler 的时间先后

        Args:
            first_handler: 第一个 handler
            second_handler: 第二个 handler

        Returns:
            若第一个时间和第二个时间相同，返回 0
            若第一个时间早于第二个时间，返回 -1
            若第一个时间晚于第二个时间，返回 1
        """
        for f, s in zip(first_handler, second_handler):
            if f == -1 or s == -1:
                break
            if f == s:
                continue
            elif f > s:
                return 1
            elif f < s:
                return -1

        return 0

    @staticmethod
    def _cut_zero_key(dict_obj):
        # 删除其中值为 0 的 key
        return dict([item for item in dict_obj.items() if item[1] > 0])

    @property
    def time_unit_names(self):
        return ['year', 'month', 'day', 'hour', 'minute', 'second']

    def __call__(self):
        # 实际上是父类的初始化，为了避免 jionlp 初次加载耗时，而放入 __call__ 方法
        chinese_num = '零〇一二三四五六七八九'
        arabic_num = '00123456789'
        self.chinese_num_2_arabic_num = str.maketrans(chinese_num, arabic_num)

        self.single_num_pattern = re.compile(SINGLE_NUM_STRING)

        self.money_parser = MoneyParser()

    @staticmethod
    def parse_pattern(time_string, pattern):
        """ 公共解析函数 """
        searched_res = pattern.search(time_string)
        if searched_res:
            # logging.info(''.join(['matched: ', searched_res.group(),
            #                       '\torig: ', time_string]))
            return searched_res.group()
        else:
            return ''

    def _char_num2num(self, char_num):
        """ 将 三十一 转换为 31，用于月、日、时、分、秒的汉字转换

        :param char_num:
        :return: float 类型的数字
        """
        res_num = self.money_parser(char_num, ret_format='str')
        if res_num is None:
            return 0
        else:
            return float(res_num[:-1])

    def chinese_year_char_2_arabic_year_char(self, char_year):
        """ 将 二零一九 年份转化为 2019 """
        arabic_year_char = char_year.translate(self.chinese_num_2_arabic_num)
        return arabic_year_char

    @staticmethod
    def time_completion(time_handler, time_base_handler):
        """根据时间基，补全 time_handler，即把 time_handler 前部 -1 部分补齐

        :param time_handler:
        :param time_base_handler:
        :return:
        """
        if time_handler in ['inf', '-inf']:
            return time_handler

        for i in range(len(time_handler)):
            if time_handler[i] > -1:
                break
            time_handler[i] = time_base_handler[i]

        return time_handler

    @staticmethod
    def check_handler(time_handler):
        """
        字符串合法校验，形如 [-1, 11, 29, -1, 23, -1] ，即中间部位有未指明时间，为非法时间字符串，
        左侧未指明时间须根据 base_time 补充完整，右侧未指明时间可省略，或按时间段补全
        """
        if time_handler in ['inf', '-inf']:
            return True

        assert len(time_handler) == 6
        # 未识别出任何时间串，即全部为 -1：[-1, -1, -1, -1, -1, -1]
        if set(time_handler) == {-1}:
            return False

        first = False
        second = False
        for i in range(5):
            if time_handler[i] > -1 and time_handler[i + 1] == -1:
                first = True
            if time_handler[i] == -1 and time_handler[i + 1] > -1:
                if first:
                    second = True

        if first and second:
            return False
        return True

    @staticmethod
    def _convert_time_base2handler(time_base):
        """将 time_base 转换为 handler,"""

        # if type(time_base) is arrow.arrow.Arrow:
        #     time_base_handler = [
        #         time_base.year, time_base.month, time_base.day,
        #         time_base.hour, time_base.minute, time_base.second]
        if type(time_base) in [float, int]:
            # 即 timestamp
            time_array = datetime.datetime.fromtimestamp(time_base)
            time_base_handler = [
                time_array.year, time_array.month, time_array.day,
                time_array.hour, time_array.minute, time_array.second]
        elif type(time_base) is datetime.datetime:
            time_base_handler = [
                time_base.year, time_base.month, time_base.day,
                time_base.hour, time_base.minute, time_base.second]
        elif type(time_base) is list:
            assert len(time_base) <= 6, 'length of time_base must be less than 6.'
            for i in time_base:
                assert type(i) is int, 'type of element of time_base must be `int`.'
            if len(time_base) < 6:
                time_base.extend([-1 for _ in range(6 - len(time_base))])
            time_base_handler = time_base
        elif type(time_base) is dict:
            time_base_handler = [
                time_base.get('year', -1), time_base.get('month', -1),
                time_base.get('day', -1), time_base.get('hour', -1),
                time_base.get('minute', -1), time_base.get('second', -1)]
        elif type(time_base) is str:
            time_array = time.strptime(time_base, "%Y-%m-%d %H:%M:%S")
            time_base_handler = [
                time_array.tm_year, time_array.tm_mon, time_array.tm_mday,
                time_array.tm_hour, time_array.tm_min, time_array.tm_sec]
        elif time_base is None:
            time_base_handler = None
        else:
            raise ValueError('the given time_base is illegal.')

        return time_base_handler

    @staticmethod
    def _convert_handler2datetime(handler):
        """将 time handler 转换为 datetime 类型

        :param handler:
        :return:
        """
        new_handler = []
        for idx, i in enumerate(handler):
            if i > -1:
                new_handler.append(i)
            else:
                if idx in [0, 1, 2]:
                    new_handler.append(1)  # 月、日 从 1 开始计数
                elif idx in [3, 4, 5]:
                    new_handler.append(0)  # 时分秒从 0 开始计数

        return datetime.datetime(*new_handler)

    @staticmethod
    def _cleansing(time_string):
        return time_string.strip()  # .replace(' ', '')
