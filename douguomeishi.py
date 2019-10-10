import json
import re
import time

import pymongo
import requests


class Dgou(object):
    def __init__(self):
        self.Getheaders = {
            "client": "4",
            "version": "6922.2",
            "device": "SM-G955N",
            "sdk": "19,4.4.2",
            "imei": "863064010140236",
            "channel": "zhuzhan",
            # "mac": "D8:9C:67:02:08:17",  # 可注释掉--会定位mac地址封掉后手机不能请求
            "resolution": "720*1280",
            "dpi": "1.5",
            # "android-id": "8cec4b9ed5b65985",  # 可注释掉
            # "pseudo-id": "b9ed5b659858cec4",  # 可注释掉
            "brand": "samsung",
            "scale": "1.5",
            "timezone": "28800",
            "language": "zh",
            "cns": "3",
            "carrier": "CMCC",
            # "imsi": "460071402367515",  # 可注释掉
            "user-agent": "Mozilla/5.0 (Linux; Android 4.4.2; SM-G955N Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/30.0.0.0 Mobile Safari/537.36",
            "reach": "1",
            "newbie": "0",
            # "lon": "101.564822",  # 可注释掉
            # "lat": "38.001318",  # 可注释掉
            # "cid": "620700",  # 可注释掉
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "Keep-Alive",
            "Host": "api.douguo.net",
            # "Content-Length": "68",
        }
        t = time.time()
        self.get_data = {
            "client": "4",
            # "_session": "1556242851606863064010140236",
            "v": str(int(t)),
            "_vs": "2305",
        }

        self.host = ''  # 数据库IP
        self.mongodb = 'Cate'  # 库
        self.mongo_table = 'Dgms'  # 集合 --豆果美食app--菜谱分类-菜谱
        self.client = pymongo.MongoClient(host=self.host, port=27017)  # 建立连接

        self.db = self.client[self.mongodb]  # 操作库
        self.tb = self.db[self.mongo_table]  # 操作集合

    # 请求菜谱分类源码
    def get_html(self, url):
        response = requests.post(url, data=self.get_data, headers=self.Getheaders)
        if response.status_code == 200:
            return response.text
        else:
            return 'Get_food_list code is False: %d ' % response.status_code

    # 获取总列表名称，源码
    def get_food_list(self, html):
        F = {}
        content = json.loads(html)
        content = content['result']['cs']
        for cont in content:
            Fname = cont['name']  # 总列表名称
            F['name'] = Fname
            second_cont = cont['cs']  # 列表源码
            yield Fname, second_cont

    # 获取三级列表名称， 并放入字典Sec
    def get_th_list(self, Fname, second_cont):
        Sec = {}
        for i, cont2 in enumerate(second_cont):
            th_cont = cont2['cs']  # 三级列表 具体到每个细类  例：蔬菜-时令蔬菜-土豆，茄子，香椿
            for i, sec in enumerate(th_cont):
                Sec[i] = sec['name']
            self.th_list(Sec)  # 调用函数th_cont()处理请求

    # 遍历三级列表，请求三级列表源码(三级列表下下一级列表-即做法)
    def th_list(self, Sec):
        for val in Sec.values():
            url = 'http://api.douguo.net/recipe/v2/search/0/20'  # 可以翻页---暂时未翻页
            data = {
                "client": "4",
                # "_session": "1556415243078863064010140236",
                "keyword": str(val),
                "order": "0",
                "_vs": "400",
            }
            #  请求三级列表-内容
            response = requests.post(url, data=data, headers=self.Getheaders)
            if response.status_code == 200:
                th = response.text
                self.th_cont(th)  # 调用函数th_cont处理kw, id, idx
            else:
                print('Get th_list code is False:%d' % response.status_code)

    # 请求三级列表内容，获取所需kw, id, idx
    def th_cont(self, th):
        html = json.loads(th)
        content = html['result']['list']  # 作者，id
        kw = html['result']['sts']
        for i, cont in enumerate(content):
            if 'dsp' not in cont.keys():
                cont = cont['r']
                id = cont['id']
                idx = i+1
                url = 'http://api.douguo.net/recipe/detail/{}'.format(id)
                data = {
                    "client": "4",
                    "_session": "1556419851044863064010140236",
                    "author_id": "0",
                    "_vs": "2801",
                    "_ext": {"query": {"id": id, "kw": kw, "idx": idx, "src": "2801", "type": "13"}},
                }
                response = requests.post(url, data=data, headers=self.Getheaders)
                if response.status_code == 200:
                    forth = response.text
                    self.parse_forth(forth)  # 调用函数parse_forth解析菜谱详情
                else:
                    print('Get th_cont code is False:%d' % response.status_code)

    # 解析菜谱最终做法
    def parse_forth(self, forth):
        Menu = {}
        forth = json.loads(forth)
        try:
            content = forth['result']['recipe']
            title = content['title']  # 标题
            image = content['original_photo_path']  # 图片
            image2 = content['photo_path']  # 图片2 与上面相同
            tips = content['tips']  # 建议
            cookstory = content['cookstory']  # 厨房小记--厨房小趣事
            cookstep = content['cookstep']  # 烹饪步骤--附带图片
            major = content['major']  # 配料
            user = content['user']['nickname']  # 作者
            if title and cookstep and major and user:
                Menu['title'] = title
                Menu['user'] = user
                if image:
                    Menu['image'] = image
                else:
                    if image2:
                        Menu['image'] = image2
                    else:
                        Menu['image'] = ''
                if tips:
                    Menu['tips'] = tips
                else:
                    Menu['tips'] = ''
                if cookstory:
                    Menu['cookstory'] = cookstory
                else:
                    Menu['cookstory'] = ''
                Menu['major'] = major
                Menu['cookstep'] = cookstep
            self.save_mongo(Menu)
        except:
            pass

    def save_mongo(self, Menu):
        self.tb.insert_one(Menu)
        print('存储入库中...')

    def run(self):
        url = 'http://api.douguo.net/recipe/flatcatalogs'
        html = self.get_html(url)
        for Fname, second_cont in self.get_food_list(html):
            self.get_th_list(Fname, second_cont)


if __name__ == '__main__':

    dgms = Dgou()
    dgms.run()


