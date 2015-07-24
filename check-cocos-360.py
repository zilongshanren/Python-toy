from sys import stdout
import requests
import re
import os
import json
import zipfile, os.path
import shutil
import datetime
import BeautifulSoup

keywords = ['cocos2d', 'libunity', 'unityengine', 'luaengine', 'spidermonkey', 'cccrypto', 'ccnative', 'ccnetwork', 'anysdk', 'xinmei365']


def download_file(url, filename, totalsize):
    # NOTE the stream=True parameter
    if os.path.exists(filename):
        return filename
    r = requests.get(url, stream=True)
    with open(filename, 'w+') as f:
        downloadsize = 0
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
                f.flush()
                #print len(chunk)
                downloadsize += 1024
                #print str(stats) + 'k',
                #stdout.write("\r%.1f%%" %(downloadsize*100/totalsize))
                #stdout.flush()
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
                        #print chunk[i:i+48]
                        _detected_ = keyword
                        if(keyword == 'libunity' or keyword == 'unityengine'):
                            #print keyword
                            _detected_ = 'unity'
                        if(_engine.count(_detected_) == 0):
                            #print 'detected in file:' + _detected_
                            _engine.append(_detected_)
            else:
                break
    return _engine

def scan(path):
    _engine2 = []
    for root, dirs, files in os.walk(path.encode('utf-8')):
        for file in files:
            if file.endswith(".so"):
                #print file
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

def get_app_list(url):
    r = requests.get(url)

    if(r.status_code is not 200):
        print 'http reqeust error, please check your network connections'

    #diagnose(r.text)
    print r.text
    soup = BeautifulSoup(r.text)
    app_data = {}
    applist = []

    for script in soup.find_all('script'):
        #print script.get_text()
        values = re.findall(r'var G_appData =\s*(.*?);', script.get_text(), re.DOTALL | re.MULTILINE)
        for value in values:
            app_data = json.loads(value)

    for tag in soup.find_all('div', attrs={'class': 'app-rank'}):
        appitem = {}
        appitem['rank'] = tag.span.text
        app = tag.parent.parent
        for child in app.descendants:
            if child.name == 'p':
                appitem['desc'] = child.span.string
        appitem['pname'] = app['data-pname']
        appitem['id'] = app['data-sid']
        for data in app_data:
            if data['id'] == app['data-sid']:
                appitem['name'] = data['name']
                appitem['size'] = data['size']
                appitem['down_url'] = data['down_url']
                break
        applist.append(appitem)

    return applist


def get_app_list_json(url):
    r = requests.get(url)
    if(r.status_code is not 200):
        print 'http reqeust error, please check your network connections'
    payload = r.json()
    print payload
    applist = []
    rank = 1
    for item in payload['result']:
        app = {}
        app['name'] = item['name']
        app['id'] = item['id']
        app['down_url'] = item['market']['360market']['download_url']
        app['pname'] = item['package_name']
        size = item['market']['360market']['size']
        app['size'] = size
        msize = int(size) / (1024.0 * 1024.0)
        app['msize'] = "%.2f" % (msize)
        app['desc'] = str(item['week_total'])
        app['rank'] = str(rank)
        rank = rank + 1
        applist.append(app)
    return applist

def collect_stats(url):
    detected = []
    app_list = get_app_list_json(url)
    idx = 0
    for item in app_list:
        idx += 1
        print idx
        _filename = './apks/' + item['id'] + '.apk'
        print 'Download ' + item['pname'] + ' start...'
        ok = False
        unzip_root = './unzip/'
        if os.path.exists(unzip_root):
            shutil.rmtree(unzip_root)
        else:
            os.mkdir(unzip_root)

        retry = 0
        while ok is not True:
            if(retry > 3):
                break
            download_file(item['down_url'], _filename, int(item['size']))
            print item['size']
            _size = os.path.getsize(_filename)
            print _size
            if str(_size) == item['size']:
                unzip_folder = unzip_root + item['id'] + '/'
                if os.path.exists(unzip_root):
                    shutil.rmtree(unzip_root)
                os.mkdir(unzip_root)
                ok = unzip(_filename, unzip_folder)
            else:
                print 'remove ' + _filename
                os.remove(_filename)
                ok = False
            retry += 1
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


top_url = 'http://openbox.mobilem.360.cn/app/list/cid/2/order/weekpure/start/1/num/100/format/json'
cocos2d_game = collect_stats(top_url)
print cocos2d_game

# settings.configure()


# template = """
# <html>
# <head>
# <title>Cocos2d popularity in Top 50 games (by download) in 360 platform</title>
# </head>
# <table>
# {% for item in game_list %}
# {% if forloop.counter0|divisibleby:4 %}<tr>{% endif %}
# <td>{{ item }}</td>
# {% if forloop.counter|divisibleby:4 or forloop.last %}</tr>{% endif %}
# {% endfor %}
# </table>
# </html>
# """

# t = Template(template)

# c = Context({"game_list": cocos2d_game})
# stats = t.render(c)
# #print stats
now = datetime.datetime.now()
csv = "/home/cocos/www/cocos-check-360/cocos2d-stats-360-" + now.strftime("%Y%m%d-%H%M%S") + ".csv"
with open(csv, "w") as stats_file:
    stats_file.write('rank,game-name               ,weekly-download        ,detected-engine         ,size\n')
    for game in cocos2d_game:
        stats_file.write(game['rank'])
        stats_file.write(',')
        stats_file.write(game['name'].encode('gb2312', 'ignore'))
        stats_file.write(',')
        stats_file.write(game['desc'].encode('gb2312', 'ignore'))
        stats_file.write(',')
        stats_file.write(game['engine'])
        stats_file.write(',')
        stats_file.write(game['msize'])
        stats_file.write('\n')
