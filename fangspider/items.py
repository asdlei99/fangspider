# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class FangspiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    source = scrapy.Field()                             # 来源
    title = scrapy.Field()                              # 标题
    money = scrapy.Field()                              # 总价
    price = scrapy.Field()                              # 单价
    area = scrapy.Field()                               # 面积
    room_type = scrapy.Field()                          # 房型
    layer = scrapy.Field()                              # 楼层
    year = scrapy.Field()                               # 建成年代
    plot = scrapy.Field()                               # 小区
    address = scrapy.Field()                            # 地址
    link = scrapy.Field()                               # 链接
    img = scrapy.Field()                                # 图片地址
    flags = scrapy.Field()                              # 附加信息
    toward = scrapy.Field()                             # 朝向
    publisher = scrapy.Field()                          # 发布人
    deal_count = scrapy.Field()                         # 发布人成交量
    publish_count = scrapy.Field()                      # 发布人发布量
    location = scrapy.Field()                           # 位置坐标
    driving_distance = scrapy.Field()                   # 到预设中心区域开车距离
    driving_duration = scrapy.Field()                   # 到预设中心区域开车时间
    integrated_distance = scrapy.Field()                # 到预设中心区域公交距离
    integrated_duration = scrapy.Field()                # 到预设中心区域公交时间
