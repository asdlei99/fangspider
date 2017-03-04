# 买房/租房 爬虫

+ 可自定义小区黑名单（用于过滤掉商住两用房）
+ 每个抓取源需要自己更新下抓取的数据映射规则
+ 在fangspider/spiders/数据源.py里直接写符合抓取的页码条件的URL
+ 如果链家或者房天下的页面布局变化了可能要修改spiders里的匹配规则
+ 可以每小时跑一次，最后执行 ```python gen_summary.py -d 年-月-日``` 会汇总在Excel里
+ 可以修改配置来变更模拟浏览器访问的UserAgent

# 环境准备
+ [python](https://www.python.org/downloads/) 或 [Anaconda](https://www.continuum.io/downloads)
+ [爬虫引擎: scrapy](https://scrapy.org)，安装方式见下文
+ [Excel读写器: openpyxl](https://bitbucket.org/openpyxl/openpyxl)
+ [序列化工具: msgpack-python](https://github.com/msgpack/msgpack-python)
+ [HTTP请求: requests](http://docs.python-requests.org/en/master/)

## Linux 
```shell
sudo apt-get install python3 python3-dev
python -m pip install scrapy
python -m pip install openpyxl msgpack-python requests

sudo apt-get install python-dev python-pip libxml2-dev libxslt1-dev zlib1g-dev libffi-dev libssl-dev
pip install Scrapy 
pip install openpyxl msgpack-python requests
```

## OSX
```shell
xcode-select --install

export PATH=/usr/local/bin:/usr/local/sbin:$PATH

brew install python3
brew update; brew upgrade python3
python -m pip install scrapy
python -m pip install openpyxl msgpack-python requests

brew install python
brew update; brew upgrade python
pip install Scrapy
pip install openpyxl msgpack-python requests
```

## Windows
Windows下只支持python2，并且要额外安装[pywin32](http://sourceforge.net/projects/pywin32/)
```bat
c:\python27\python.exe c:\python27\tools\scripts\win_add2path.py
pip install Scrapy
pip install openpyxl msgpack-python requests
```

## Anaconda
```shell
conda install -c conda-forge scrapy
conda install openpyxl msgpack-python requests
```

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

# 生成某天的Excel数据表格
python gen_summary.py -d 年-月-日
```

### 配置
见 [fangspider/settings.py](fangspider/settings.py)

+ 必须配置抓取的房源的价格上限和下限
+ 最好配置城市名称，防止可能名称在多个城市中都有导致位置查询错误
+ GIS字段用于配置地理位置信息抓取的Key和路径规划的目标点
> * GIS信息使用高德的开放平台API，可以配置多个token以解决每日调用次数限制问题
> * 由于个人版高德API每日每个API的频次限制是1000次，所以可以可以配置多个key，每次查询的时候会随机选一个
> * 查询的小区坐标和到目标位置的路径规划信息会存入sqlite数据库，如果修改目标需要手动删除一下数据库里的plot表
> * 路径规划目标点可以通过 http://restapi.amap.com/v3/place/text?key=[KEY]&keywords=[目标名称]&city=[城市名称]&children=1&offset=5&page=1 查询，一般使用pois离第一个数据的location字段即可
> * 高德地图API的key申请参见[高德地图开放平台](http://lbs.amap.com/)