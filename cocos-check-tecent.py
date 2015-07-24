import requests
import os
import json
import zipfile, os.path
import shutil
from sys import stdout
import datetime
import BeautifulSoup

keywords = ['cocos2d', 'luaengine', 'libunity', 'unityengine', 'spidermonkey', 'jsb_']


def download_file(url, filename, totalsize):
    # NOTE the stream=True parameter
    if os.path.isfile(filename):
        return filename
    r = requests.get(url, stream=True)
    with open(filename, 'wb') as f:
        downloadsize = 0
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                f.write(chunk)
                f.flush()
                downloadsize += 1024
                #print str(stats) + 'k',
                stdout.write("\r%.1f%%" % (downloadsize * 100 / totalsize))
                stdout.flush()
    stdout.write("\n")
    return filename

def check_engine(filename, chunksize=8192):
    _engine = []
    for keyword in keywords:
        i = filename.lower().find(keyword)
        #print keyword
        #print i
        if i > 0:
            print filename
            _detected = keyword
            if(keyword == 'libunity' or keyword == 'unityengine'):
                _detected = 'unity'
            if(_engine.count(_detected) == 0):
                #print 'detected in name:' + keyword
                _engine.append(_detected)
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                #print chunk
                for keyword in keywords:
                    i = chunk.lower().find(keyword)
                    if i > 0:
                        print chunk[i:i + 48]
                        _detected_ = keyword
                        if(keyword == 'libunity' or keyword == 'unityengine'):
                            print keyword
                            _detected_ = 'unity'
                        if(_engine.count(_detected_) == 0):
                            print 'detected in file:' + _detected_
                            _engine.append(_detected_)
            else:
                break
    return _engine

def scan(path):
    _engine2 = []
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(".so"):
                print file
                fPath = os.path.join(root, file)
                check = check_engine(fPath)
                #print check
                for item in check:
                    #print 'check:'+item
                    #print _engine2.count(item)
                    if(_engine2.count(item) == 0):
                        #print '_engine2 add:' + item
                        _engine2.append(item)
    return _engine2

# def unzip(source_filename, dest_dir):
#     print source_filename
#     with zipfile.ZipFile(source_filename) as zf:
#         for member in zf.infolist():
#             # Path traversal defense copied from
#             # http://hg.python.org/cpython/file/tip/Lib/http/server.py#l789
#             words = member.filename.split('/')
#             path = dest_dir
#             for word in words[:-1]:
#                 drive, word = os.path.splitdrive(word)
#                 head, word = os.path.split(word)
#                 if word in (os.curdir, os.pardir, ''): continue
#                 path = os.path.join(path, word)
#             zf.extract(member, path)

def unzip(source_filename, dest_dir):
    if os.path.exists(dest_dir):
        shutil.rmtree(dest_dir)
    os.mkdir(dest_dir)
    execCmd = u"unzip %s -d %s " % (source_filename, dest_dir)
    execCmd = execCmd.encode("utf-8")
    ret = os.system(execCmd)
    if ret != 0:
        os.remove(source_filename)
        return False
    else:
        return True

def get_app_list_html(url):
    applist = []
    r = requests.get(url)

    if(r.status_code is not 200):
        print 'http reqeust error, please check your network connections'

    #diagnose(r.text)
    print r.text
    soup = BeautifulSoup(r.text)
    i = 0
    for a in soup.find_all('a', attrs={'class': 'name ofh'}):
        app_data = {}
        print a.text
        app_data['name'] = a.text
        ref = a['href']
        pkg = ref.split('=')[1]
        print pkg
        app_data['pkg'] = pkg
        tag_size = a.next_sibling.next_sibling
        print tag_size.text
        app_data['size'] = tag_size.text
        tag_download = tag_size.next_sibling.next_sibling
        print tag_download.text
        app_data['download'] = tag_download.text
        tag_link = tag_download.next_sibling.next_sibling
        print tag_link['ex_url']
        app_data['url'] = tag_link['ex_url']
        print '+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++'
        applist.append(app_data)
        i = i + 1
    print i
    return applist

def get_app_list_json(url):
    applist = []
    r = requests.get(url)
    if(r.status_code is not 200):
        print 'http reqeust error, please check your network connections'
    #print r.json()
    payload = r.json()
    for item in payload['obj']:
        app_data = {}
        app_data['pkg'] = item['pkgName']
        app_data['name'] = item['appName']
        app_data['size'] = item['fileSize']
        msize = int(app_data['size']) / (1024.0 * 1024.8)
        app_data['msize'] = "%.2f" % msize
        app_data['appId'] = item['appId']
        app_data['url'] = item['apkUrl']
        app_data['download'] = str(item['appDownCount'])
        applist.append(app_data)
    return applist

def collect_stats(url):
    detected = []
    app_list = get_app_list_json(url)
    for item in app_list:
        _filename = './apks/' + item['pkg'] + '.apk'
        print 'Download ' + item['pkg'] + ' start...'
        ok = False
        unzip_root = './unzip/'
        if not os.path.exists(unzip_root):
            os.makedirs(unzip_root)
        while ok is not True:
            download_file(item['url'], _filename, int(item['size']))
            unzip_folder = unzip_root + item['pkg'] + '/'
            ok = unzip(_filename, unzip_folder)
        engine_list = scan(unzip_folder)
        for n, i in enumerate(engine_list):
            if i == 'cocos2d':
                engine_list[n] = 'cocos2d-x'
        if(len(engine_list) == 0):
            item['engine'] = 'others'
        else:
            item['engine'] = ' '.join(engine_list)
        detected.append(item)
    return detected

#print collect_stats('http://sj.qq.com/myapp/category.htm?orgame=2')
url2 = 'http://sj.qq.com/myapp/cate/appList.htm?orgame=2&categoryId=0&pageSize=20&pageContext=0'

cocos2d_game = collect_stats(url2)
rank = 1
now = datetime.datetime.now()
csv = "/Users/guanghui/Downloads/cocos-check-tecent/cocos2d-stats-tencent-" + now.strftime("%Y%m%d-%H%M%S") + ".csv"
with open(csv, "w") as stats_file:
    stats_file.write('rank,game-name               ,download-count           ,detected-engine       ,size\n')
    for game in cocos2d_game:
        stats_file.write(str(rank))
        stats_file.write(',')
        stats_file.write(game['name'].encode('gb2312', 'ignore'))
        stats_file.write(',')
        stats_file.write(game['download'].encode('gb2312', 'ignore'))
        stats_file.write(',')
        stats_file.write(game['engine'])

        stats_file.write(',')
        stats_file.write(str(game['msize']))
        stats_file.write('\n')
        rank = rank + 1
