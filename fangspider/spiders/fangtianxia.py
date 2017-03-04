# -*- coding: utf-8 -*-
import re
import scrapy
import scrapy.crawler

from  fangspider.items import FangspiderItem

FTECH_URL_ROOT = "http://esf.sh.fang.com"
# 二手房地址(按时间排序): http://esf.sh.fang.com/house/h316-i3页码/
# 价格区间 http://esf.sh.fang.com/house/c2起始价格（万）-d2结束价格（万）-h316-i3页码-l3100/
# 价格区间 http://esf.sh.fang.com/house/c2起始价格（万）-d2结束价格（万）-h316-i3页码-l3100/


PUBLISHER_CACHE = dict()

PICK_SEGMENT = re.compile('[^\\s\\r\\n]+')
PICK_NUMBER = re.compile('[\\d\\.]+')
DEAL_NUMBER = re.compile('成交总量[^\\d]*(\\d+)')

class FangtianxiaSpider(scrapy.Spider):
    name = 'fangtianxia'
    label = '房天下'
    allowed_domains = [".fang.com"]
    start_urls = []
    custom_settings = {
        'FETCH_PAGES': 3
    }

    def start_requests(self):
        # load settings
        fang_conf = self.settings.getdict('FANGSPIDER_CONF')
        for i in range(1, self.settings.getint('FETCH_PAGES') + 1):
            self.start_urls.append("http://esf.sh.fang.com/house/c2{0}-d2{1}-h316-g22-i3{2}-l3100/".format(fang_conf['FETCH_PRICE_L'], fang_conf['FETCH_PRICE_R'], i))

        return super().start_requests()

    def pick_link(self, url):
        if url[0:1] == '/':
            return FTECH_URL_ROOT + url
        return url

# <dl id="list_D03_01" onmouseout="mouseOutStyle(this)" onmouseover="mouseOverStyle(this)" class="list rel">
#     <dt class="img rel floatl">
#         <a href="/chushou/3_282179620.htm"  target="_blank">
#             <img width="180" height="135" src="http://img.soufun.com/secondhouse/image/esfnew/search2014/images/loading160_120.gif" src2="http://cdnsfb.soufunimg.com/viewimage/0/2017_2/23/M12/23/cd5320c686dc4d1c9dec979349774d90/220x165c.jpg" onerror="imgiserror(this,'http://cdnsfb.soufunimg.com/0/2017_2/23/M12/23/cd5320c686dc4d1c9dec979349774d90.jpg')" /></a>
#         <p class="txtBg"></p>
#         <p class="txt"><span class="iconImg">9</span></p>
#     </dt>
#     <dd class="info rel floatr">
#         <p class="title"><a href="/chushou/3_282179620.htm"  target="_blank" title="地铁6/7/8/13号线世博上南四村15万精装全送诚售">地铁6/7/8/13号线世博上南四村15万精装全送诚售</a>
#         </p>
#         <p class="mt12">
#             1室1厅
#             <span class="line">|</span>中层(共6层)
#             <span class='line'>|</span>南向
#             <span class='line'>|</span>建筑年代：1983
#         </p>
#         <p class="mt10">
#             <a target="_blank" href="/house-xm1210283224/" title="上南四村"><span>上南四村</span></a>
#             <span class="iconAdress ml10 gray9" title="世博-上南路1251弄">世博-上南路1251弄</span>
#         </p>
#         <p class="gray6 mt10"><a  rel="nofollow"  href='/a/luohuo9876'title="访问[罗辉]的个人网上店铺，查看更多房源" target='_blank' >罗辉</a><span class="ml10 gray9">2小时前发布</span></p>
#         <div class="mt8 clearfix">
#             <div class="pt4 floatl">
#                  <span class="colorPink note">满五唯一</span><span class="colorPink note">优质教育</span><span class="train note">距8号线成山路站约236米</span>
#                   </div>
#             <div class="floatl note-img"></div>
#         </div>
#         <div class="area alignR">
#             <p>35㎡</p>
#             <p class="tag">建筑面积</p>
#         </div>
#         <div class="moreInfo">
#             <p class="mt5 alignR"><span class="price">193</span><span class="YaHei ml5">万</span></p>
#             <p class="danjia alignR mt5">55143元<span class="Arial">/</span>㎡</p>
#         </div>
#          
#         
#     </dd>
#     <div class="clear"></div>
# </dl>

    def pick_string(self, arr, idx):
        if arr is None:
            return ''
        if len(arr) <= idx:
            return ''
        return arr[idx]

    def pick_number(self, arr, idx):
        if arr is None:
            return 0
        if len(arr) <= idx:
            return 0
        res = PICK_NUMBER.search(arr[idx])
        if res is not None:
            return float(res.group(0))
        return 0

    def pick_number_from_str(self, strin):
        if strin is None:
            return 0
        if len(strin) <= 0:
            return 0
        res = PICK_NUMBER.search(strin)
        if res is not None:
            return float(res.group(0))
        return 0

    def parse_publisher(self, response):
        pub_info = {
            'deal_count': 0,
            'publish_count': 0
        }
        pub_dom = response.css('#allhousecount')
        pub_str = (''.join(pub_dom.xpath('text()').extract())).strip()

        if len(pub_str) > 0:
            pub_info['publish_count'] = int(pub_str)

        deal_str = (''.join(response.css('.about *').xpath('text()').extract())).strip()
        res = DEAL_NUMBER.search(deal_str)
        if res is not None:
            pub_info['deal_count'] = int(res.group(1))

        item = response.meta['item']
        url = response.url
        PUBLISHER_CACHE[url] = pub_info
        item['deal_count'] = pub_info['deal_count']
        item['publish_count'] = pub_info['publish_count']

        yield item

    def parse(self, response):
        item_doms = response.css('.houseList > .list')
        #items = []
        for element in item_doms:
            item = FangspiderItem()
            item['source'] = self.label
            item['title'] = (''.join(element.css('.floatr > .title').xpath('a/text()').extract())).strip()
            item['money'] = (''.join(element.css('.floatr .price').xpath('text()').extract())).strip()
            item['price'] = str(self.pick_number_from_str((''.join(element.css('.floatr .danjia').xpath('text()').extract())).strip())) + u'/㎡'
            item['area'] = str(self.pick_number_from_str((''.join(element.css('.floatr > .area').xpath('p[1]/text()').extract())).strip()))
            item['plot'] = (''.join(element.css('.floatr').xpath('p[3]/a/span/text()').extract())).strip()
            item['address'] = (''.join(element.css('.floatr').xpath('p[3]/span/text()').extract())).strip()
            item['link'] = self.pick_link((''.join(element.css('.floatr > .title').xpath('a/@href').extract())).strip())
            item['img'] = self.pick_link((''.join(element.css('.img img').xpath('@src2').extract())).strip())
            flags = []
            for flag_dom in element.css('.floatr > .mt8 > .pt4 > span'):
                flags.append((''.join(flag_dom.xpath('text()').extract())).strip())
            if len(flags) > 0:
                item['flags'] = (','.join(flags)).strip()
            else:
                item['flags'] = ''
            mt12 = PICK_SEGMENT.findall((''.join(element.css('.floatr').xpath('p[2]/text()').extract())).strip())
            item['room_type'] = self.pick_string(mt12, 0)
            item['layer'] = self.pick_string(mt12, 1)
            item['toward'] = self.pick_string(mt12, 2)
            item['year'] = self.pick_number(mt12, 3)
            item['publisher'] = self.pick_link((''.join(element.css('.floatr').xpath('p[4]/a/@href').extract())).strip())
            #self.fetch_publisher_deal_count(item['publisher'], item)

            publisher_info = PUBLISHER_CACHE.get(item['publisher'])
            if publisher_info is not None:
                item['deal_count'] = publisher_info['deal_count']
                item['publish_count'] = publisher_info['publish_count']
                yield item

            if len(item['publisher']) <= 0:
                item['deal_count'] = 0
                item['publish_count'] = 0
                yield item

            # fetch publisher info
            yield scrapy.Request(item['publisher'], callback=self.parse_publisher, meta={'item' : item}, dont_filter=True)
