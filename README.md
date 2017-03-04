# 买房/租房 爬虫

+ 可自定义小区黑名单（用于过滤掉商住两用房）
+ 每个抓取源需要自己更新下抓取的数据映射规则
+ 在fangspider/spiders/数据源.py里直接写符合抓取的页码条件的URL
+ *加入代理IP，防止被屏蔽*



# 使用
```shell
# 查看数据源
scrapy list

# 抓取数据源
scrapy crawl 数据源名称

# 检查数据源
scrapy check [-l] 数据源名称

# 测试下载地址
scrapy fetch URL
```