# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os
import time
import math
import requests
import sqlite3
import random
import msgpack
from scrapy.exceptions import DropItem

BUY_TABLE_NAME = 'buy'
PLOT_TABLE_NAME = 'plot'

DATA_PATH = 'data'
DATABASE_FILENAME = 'collection.sqlite'

class FangspiderPipeline(object):
    files = dict()
    plots_cache = dict()
    time_dir = ''
    dbconn = None
    dbcursor = None

    def __init__(self):
        if not os.path.exists(DATA_PATH):
            os.makedirs(DATA_PATH, 0o777)
        self.dbconn = sqlite3.connect(os.path.join(DATA_PATH, DATABASE_FILENAME))
        self.dbconn.text_factory = str
        self.dbcursor = self.dbconn.cursor()

        has_buy = False
        has_plot = False
        for row in self.dbcursor.execute("select name from sqlite_master where type='table' order by name"):
            if row[0] == BUY_TABLE_NAME:
                has_buy = True
            elif row[0] == PLOT_TABLE_NAME:
                has_plot = True

        # 初始化表和索引
        if not has_buy:
            self.dbcursor.execute("create table {0}(url TEXT PRIMARY KEY, data BLOB, create_date TEXT)".format(BUY_TABLE_NAME))
            self.dbcursor.execute("create index date_index on {0}(create_date)".format(BUY_TABLE_NAME))
        if not has_plot:
            self.dbcursor.execute(("create table {0}(name TEXT PRIMARY KEY, location TEXT, address TEXT, " +
                                  "driving_distance INTEGER, driving_duration INTEGER, " +
                                  "integrated_distance INTEGER, integrated_duration INTEGER " + ")").format(PLOT_TABLE_NAME))

    def has_url_in_db(self, url):
        self.dbcursor.execute("select create_date from {0} where url=:url".format(BUY_TABLE_NAME), {'url': url})
        return self.dbcursor.fetchone() is not None

    def insert_url_into_db(self, url, data):
        if not self.has_url_in_db(url):
            self.dbcursor.execute("insert into {0}(url, data, create_date) values(:url, :data, :create_date)".format(BUY_TABLE_NAME), {
                'url': url,
                'data': data,
                'create_date': self.time_dir
            })
            print('[INFO] {0} row inserted'.format(self.dbcursor.rowcount))
        else:
            self.dbcursor.execute("update {0} set data=:data where url=:url".format(BUY_TABLE_NAME), {
                'url': url,
                'data': data
            })
            print('[INFO] {0} row updated'.format(self.dbcursor.rowcount))


    def open_spider(self, spider):
        self.time_dir = time.strftime('%F')

    def process_item(self, item, spider):
        if 'title' in item:
            item_dict = dict(item)
            self.process_item_gis_info(item_dict, spider)
            self.insert_url_into_db(item['link'], msgpack.packb(item_dict, encoding='utf-8'))
            return item
        else:
            raise DropItem("Missing")

    def close_spider(self, spider):
        # commit and save into database
        self.dbconn.commit()

    def process_item_gis_info(self, item, spider):
        if 'plot' not in item or len(item['plot']) == 0:
            return item
        gis_data = self.find_plot_gis(item['plot'], spider)
        if gis_data is not None:
            item['location'] = gis_data['location']
            item['driving_distance'] = gis_data['driving_distance']
            item['driving_duration'] = gis_data['driving_duration']
            item['integrated_distance'] = gis_data['integrated_distance']
            item['integrated_duration'] = gis_data['integrated_duration']
        return item

    def request_get_json(self, url, url_params=None):
        response = requests.get(url, params=url_params)
        return response.json()

    def request_post_json(self, url, all_params=None):
        response = requests.post(url, data=all_params)
        return response.json()

    def get_gis_conf_gaode_api_key(self, spider):
        fang_conf = spider.settings.getdict('FANGSPIDER_CONF')
        if fang_conf is None or 'GIS' not in fang_conf:
            return None
        if 'gaode_api' not in fang_conf['GIS']:
            return None
        keys = fang_conf['GIS']['gaode_api']
        if len(keys) == 0:
            return None
        if len(keys) == 1:
            return keys[0]
        return keys[random.randint(0, len(keys) - 1)]

    def find_plot_gis(self, plot_name, spider):
        if plot_name in self.plots_cache:
            return self.plots_cache[plot_name]

        # first find in db
        ret = self.select_plot_gis_from_db(plot_name)
        if ret is not None:
            self.plots_cache[ret['name']] = ret
            return ret

        gis_gaode_api = self.get_gis_conf_gaode_api_key(spider)
        if gis_gaode_api is None:
            return None
        fang_conf = spider.settings.getdict('FANGSPIDER_CONF')
        if fang_conf is None or 'GIS' not in fang_conf:
            return None
        gaode_center = fang_conf['GIS']['gaode_center']
        gaode_search_api = fang_conf['GIS']['gaode_search_api']
        gaode_path_driving_api = fang_conf['GIS']['gaode_path_driving_api']
        gaode_path_integrated_api = fang_conf['GIS']['gaode_path_integrated_api']
        gaode_city = fang_conf['GIS']['gaode_city']
        if len(gis_gaode_api) == 0 or len(gaode_center) == 0 or len(gaode_search_api) == 0:
            return None

        ret = {
            'name': plot_name,
            'location': '',
            'address': '',
            'driving_distance': [],
            'driving_duration': [],
            'integrated_distance': [],
            'integrated_duration': []
        }
        plot_loc_data = self.request_get_json(gaode_search_api, {
            'key': gis_gaode_api,
            'keywords': plot_name,
            'city': gaode_city,
            'children': 1,
            'offset': 5,
            'page': 1
        })

        # use empty dataset templorary
        if 'pois' not in plot_loc_data:
            self.plots_cache[ret['name']] = ret
            return ret

        for pois in plot_loc_data['pois']:
            ret['location'] = pois['location']
            ret['address'] = pois['address']
            if len(ret['location']) > 0:
                break

        # do not configure center location
        if gaode_center is None or len(gaode_center) <= 0:
            self.plots_cache[ret['name']] = ret
            self.insert_plot_gis_into_db(ret)
            return ret

        if len(gaode_path_driving_api) > 0:
            for destination in gaode_center:
                plot_driving_path_data = self.request_get_json(gaode_path_driving_api, {
                    'key': gis_gaode_api,
                    'origin': ret['location'],
                    'destination': destination,
                    'extensions': 'base',
                    'strategy': 0
                })
                if 'route' in plot_driving_path_data:
                    route = plot_driving_path_data['route']
                    if 'paths' in route:
                        for path in route['paths']:
                            dis = float(path['distance'])
                            ret['driving_distance'].append(dis)
                            ret['driving_duration'].append(float(path['duration']) / 60)
                            if dis > 0:
                                break

        if len(gaode_path_integrated_api) > 0:
            for destination in gaode_center:
                plot_driving_path_data = self.request_get_json(gaode_path_integrated_api, {
                    'key': gis_gaode_api,
                    'origin': ret['location'],
                    'destination': destination,
                    'city': gaode_city,
                    'cityd': gaode_city,
                    'nightflag': 0,
                    'strategy': 0
                })
                if 'route' in plot_driving_path_data:
                    route = plot_driving_path_data['route']
                    if 'transits' in route:
                        for transit in route['transits']:
                            dis = float(transit['distance'])
                            ret['integrated_distance'].append(dis)
                            ret['integrated_duration'].append(float(transit['duration']) / 60)
                            if dis > 0:
                                break

        self.plots_cache[ret['name']] = ret
        self.insert_plot_gis_into_db(ret)
        return ret


    def has_plot_in_db(self, plot_name):
        self.dbcursor.execute("select name from {0} where name=:name".format(PLOT_TABLE_NAME), {'name': plot_name})
        return self.dbcursor.fetchone() is not None

    def insert_plot_gis_into_db(self, data):
        data = data.copy()
        for (k, v) in data.items():
            if isinstance(v, list):
                data[k] = ','.join(list(map(str, v)))
        self.dbcursor.execute(("insert into {0}(name, location, address, driving_distance, driving_duration, integrated_distance, integrated_duration) " +
                               "values(:name, :location, :address, :driving_distance, :driving_duration, :integrated_distance, :integrated_duration)")
                              .format(PLOT_TABLE_NAME), data)

    def select_plot_gis_from_db(self, plot_name):
        self.dbcursor.execute("select name, location, address, driving_distance, driving_duration, integrated_distance, integrated_duration " +
                              " from {0} where name=:name".format(PLOT_TABLE_NAME), {'name': plot_name})
        res = self.dbcursor.fetchone()
        if res is None:
            return None
        return {
            'name': res[0],
            'location': res[1],
            'address': res[2],
            'driving_distance': list(map(float, res[3].split(','))),
            'driving_duration': list(map(float, res[4].split(','))),
            'integrated_distance': list(map(float, res[5].split(','))),
            'integrated_duration': list(map(float, res[6].split(',')))
        }
