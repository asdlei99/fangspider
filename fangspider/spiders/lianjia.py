# -*- coding: utf-8 -*-
import re
import sys
import scrapy

from  fangspider.items import FangspiderItem

FTECH_URL_ROOT = "http://sh.lianjia.com"

# 价格区间 http://sh.lianjia.com/ershoufang/a2b起始价格（万）to结束价格（万）d页码l2s7
PUBLISHER_CACHE = dict()

PICK_SEGMENT = re.compile('[^\\s\\|\\r\\n]+')
PICK_NUMBER = re.compile('[\\d\\.]+')
DEAL_NUMBER = re.compile('成交[^\\d]*(\\d+)')
YEAR_NUMBER = re.compile('(\\d+)\\s*年')

class LianjiaSpider(scrapy.Spider):
    name = 'lianjia'
    label = '链家'
    allowed_domains = [".lianjia.com"]
    start_urls = []
    custom_settings = {
        'FETCH_PAGES': 3
    }

    def start_requests(self):
        # load settings
        fang_conf = self.settings.getdict('FANGSPIDER_CONF')
        for i in range(1, self.settings.getint('FETCH_PAGES') + 1):
            self.start_urls.append("http://sh.lianjia.com/ershoufang/a2b{0}to{1}d{2}l2s7".format(fang_conf['FETCH_PRICE_L'], fang_conf['FETCH_PRICE_R'], i))

        if 2 == sys.version_info[0]:
            return super(LianjiaSpider, self).start_requests()
        else:
            return super().start_requests()

    def pick_link(self, url):
        if url[0:1] == '/':
            return FTECH_URL_ROOT + url
        return url
		#		<li>
		#			<div class="pic-panel">
		#				<a name="selectDetail"  gahref="results_click_order_1" key="sh4549577" target="_blank" href="/ershoufang/sh4549577.html"><img onerror="this.src='http://cdn7.dooioo.com/static/img/new-version/default_block.png'; this.onerror=null;" src="http://cdn7.dooioo.com/static/img/new-version/default_block.png"  data-img-real="http://cdn1.dooioo.com/fetch/vp/fy/gi/20160507/dd495ab8-d4a4-4b42-a9b6-6508dec49aaa.jpg_200x150.jpg" data-img-layout="http://cdn1.dooioo.com/fetch/vp/fy/gi/20160514/58dfbeca-d389-485f-93ab-d0028e812bf3.jpg_200x150.jpg" data-original="http://cdn1.dooioo.com/fetch/vp/fy/gi/20160507/dd495ab8-d4a4-4b42-a9b6-6508dec49aaa.jpg_200x150.jpg" class="lj-lazy" alt="城北新村，高清大图，满五年少税，配套完善" />
		#					<!-- 如果有视频 加上这个div  否则不用 -->
		#				</a>
		#				<!-- 如果有小区推荐标签 加上这个div  否则不用 -->
		#			</div>
		#			<div class="info-panel">
		#				<h2><a name="selectDetail"  gahref="results_click_order_1" key="sh4549577" target="_blank" href="/ershoufang/sh4549577.html" title="城北新村，高清大图，满五年少税，配套完善">城北新村，高清大图，满五年少税，配套完善</a>
		#					<i class="new-label"></i>
		#				</h2>
		#				<div class="col-1">
		#					<div class="where">
		#						<a class="laisuzhou" href="/xiaoqu/5011000000927.html"><span class="nameEllipsis" title="城北新村">城北新村</span></a>&nbsp;&nbsp;
		#						<span>2室1厅&nbsp;&nbsp;</span>
		#						<span>59.12平&nbsp;&nbsp;</span>
		#					</div>
		#					<div class="other">
		#						<div class="con">
		#							<a href="/ershoufang/qingpu/">青浦</a>
		#							<span>| </span>高区/6层
		#							<span>| </span>朝南
		#							<span>| </span>1982年建
		#						</div>
		#					</div>
		#					<div class="chanquan">
		#						<div class="left agency">
		#							<div class="view-label left">
		#								<span class="taxfree"></span>
		#								<span class="taxfree-ex"><span>满五</span></span>
		#							</div>
		#						</div>
		#					</div>
		#				</div>
		#				<div class="col-3">
		#					<div class="price">
		#						<span class="num">190</span>万
		#					</div>
		#					<div class="price-pre">32138元/平</div>
		#				</div>
		#				<div class="col-2">
		#					<div class="square"><div>
		#						<span class="num">0</span>人
		#					</div>
		#					<div class="col-look">看过此房</div>
		#				</div>
		#			</div>
		#			</div>
		#		</li>
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

        # 现在抓不到发布数量
        deal_str = (''.join(response.css('.jjr_card_wrapper .card_left .card .userinfo .detail').xpath('p[4]/text()').extract())).strip()
        res = DEAL_NUMBER.search(deal_str)
        if res is not None:
            pub_info['deal_count'] = int(res.group(1))

        item = response.meta['item']
        url = response.url
        PUBLISHER_CACHE[url] = pub_info
        item['deal_count'] = pub_info['deal_count']
        item['publish_count'] = pub_info['publish_count']

        yield item

    def parse_detail(self, response):
        item = response.meta['item']
        # url = response.url
        item['address'] = (''.join(response.css('.addrEllipsis').xpath('text()').extract())).strip()

        # publisher
        item['publisher'] = self.pick_link((''.join(response.css('.brokerInfoText .brokerName').xpath('a[1]/@href').extract())).strip())

        # check year again
        if item['year'] == 0:
            year_str = (''.join(response.css('.content > .aroundInfo > tr').xpath('td/text()').extract())).strip()
            res = YEAR_NUMBER.search(year_str)
            if res is not None:
                item['year'] = int(res.group(1))

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

    def parse(self, response):
        item_doms = response.css('ul > li')
        #items = []
        for element in item_doms:
            item_title = (''.join(element.css('.info > .prop-title').xpath('a/text()').extract())).strip()
            item_link = (''.join(element.css('.info > .prop-title').xpath('a/@href').extract())).strip()
            if len(item_link) == 0 or len(item_title) == 0:
                continue
            item = FangspiderItem()
            item['source'] = self.label
            item['title'] = item_title
            item['money'] = (''.join(element.css('.info > .info-table .total-price').xpath('text()').extract())).strip()
            item['price'] = str(self.pick_number_from_str((''.join(element.css('.info > .info-table .minor').xpath('text()').extract())).strip())) + u'/㎡'
            item['link'] = self.pick_link(item_link)
            item['img'] = self.pick_link((''.join(element.css('a.img').xpath('img/@data-original').extract())).strip())
            flags = []
            for flag_dom in element.css('.info .property-tag-container > span'):
                flags.append((''.join(flag_dom.xpath('text()').extract())).strip())
            if len(flags) > 0:
                item['flags'] = (','.join(flags)).strip()
            else:
                item['flags'] = ''
            mt12 = PICK_SEGMENT.findall((''.join(element.css('.info > .info-table').xpath('div[1]/span[1]/text()').extract())).strip())
            item['room_type'] = self.pick_string(mt12, 0)
            item['area'] = str(self.pick_number_from_str(self.pick_string(mt12, 1)))
            item['layer'] = self.pick_string(mt12, 2)
            item['toward'] = self.pick_string(mt12, 3)
            mt13 = PICK_SEGMENT.findall((''.join(element.css('.info > .info-table').xpath('div[2]/span[1]/text()').extract())).strip())
            item['year'] = self.pick_number(mt13, 0)
            item['plot'] = (''.join(element.css('.info > .info-table').xpath('div[2]/span[1]/a[1]/span/text()').extract())).strip()
            # request detail
            # print(item)
            yield scrapy.Request(item['link'], callback=self.parse_detail, meta={'item' : item}, dont_filter=True)
