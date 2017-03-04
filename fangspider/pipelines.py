# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json, os, time
import codecs
from scrapy.exceptions import DropItem

class FangspiderPipeline(object):
    files = dict()
    time_dir = ''

    def __init__(self):
        pass

    def get_spider_file_path(self, spider):
        return os.path.join('data', self.time_dir, '{0}.json'.format(spider.name))

    def open_spider(self, spider):
        self.time_dir = time.strftime('%F')
        self.get_spider_file_path(spider)

    def get_file(self, path):
        if path in self.files:
            return self.files[path]
        # make parent directory
        if not os.path.exists(path) or os.path.getsize(path) < 10:
            data_dirname = os.path.dirname(path)
            if not os.path.exists(data_dirname):
                os.makedirs(data_dirname, 0o777, True)
            # open a new file
            file = codecs.open(path, mode="ab", encoding='utf-8')
            file.write('[\n')
        else:
            # open a old file
            file = codecs.open(path, mode="wb", encoding='utf-8')
            file.seek(-2, os.SEEK_END)
            file.write(",\n")
            file.close()
            file = codecs.open(path, mode="ab", encoding='utf-8')
        self.files[path] = file
        return file

    def process_item(self, item, spider):
        data_path = self.get_spider_file_path(spider)
        data_file = self.get_file(data_path)
        if 'title' in item:
            line = json.dumps(dict(item), ensure_ascii=False) + ',\n'
            data_file.write(line)
            return item
        else:
            raise DropItem("Missing")

    def close_spider(self, spider):
        data_path = self.get_spider_file_path(spider)
        if data_path in self.files.keys():
            print('===================== close data file {0}'.format(data_path))
            file = self.files.get(data_path)
            file.close()
            file = codecs.open(data_path, mode="r+b", encoding='utf-8')
            file.seek(-2, os.SEEK_END)
            file.write('\n]')
            file.close()
            self.files.pop(data_path)
