import os
import shutil # 但即使copy2也不能保证保留所有metadata
import time
from datetime import datetime
import uuid
import pathlib
from send2trash import send2trash
from bs4 import (BeautifulSoup, Comment)
import lxml # 不一定用，但与bs4解析网页时相关模块有联系，作为模块预装的提示吧
import pandas as pd

def getDir(basedir, newdir):
    d = os.path.abspath(os.path.join(basedir, newdir))
    if not os.path.exists(d):
        os.mkdir(d)
    return d

def getParentDir(path):
    return os.path.split(os.path.dirname(path))[1]

def getNewPath(basedir, basename):
    name_s = os.path.splitext(basename)
    i = 0
    path = os.path.join(basedir, "".join(name_s))
    while os.path.exists(path):
        i += 1
        path = os.path.join(basedir, "({})".format(i).join(name_s))
    return os.path.abspath(path)
   
class NoteIndex:
    def __init__(self, dir, tbname, cols, note_root_dir):
        super().__init__()
        self.dir = getDir(dir, "")
        self.name = tbname
        self.cols = cols
        #
        self.note_root_dir = note_root_dir
    
    def getUpdateTime(self):
        return datetime.fromtimestamp(os.path.getmtime(self.path))
    
    def create(self):
        self.note_dir = {}
        for t in ["Draft", "Archive", "Trash"]:
            self.note_dir[t] = getDir(self.note_root_dir, t)
        self.path = os.path.abspath(os.path.join(self.dir, "{}_index.json".format(self.name)))
        if not os.path.exists(self.path):
            self.data = pd.DataFrame(columns=self.cols)
            self.save()
            print("数据表不存在，那就新建一个吧~~~",self.path)
        else:
            self.read()
            print("这个表已经存在啦，我就不新建咯~~~",self.path)
         
    def update(self, flag, item):
        new_item = pd.Series([item.type, item.title, item.path, item.ctime, item.mtime, item.atime
                             ,item.url, item.content_ext, item.cat, item.keywords, item.summary] # , item.att_list
                             ,index=self.cols) 
        if flag is "add":
            new_frame = new_item.to_frame(item.id).T # 由列转行
            self.data = self.data.append(new_frame) #,ignore_index=True)
        elif flag is "update":
            self.data.loc[item.id] = new_item
        elif flag is "delete":
            self.data = self.data.drop(item.id)
        else:
            print("输入的标记有误：", flag)
        self.save()
        # self.read()
        
    def save(self):
        try:
            self.data.to_json(self.path)
        except Exception as e:
            print("数据表保存出错：", e)
            # ?????? 然后做点啥呢？
    
    def read(self):
        try:
            self.data = pd.read_json(self.path, convert_dates=["atime","ctime","mtime"])
        except Exception as e:
            print("数据表读取出错：", e)
            # ?????? 然后做点啥呢？

    def archive(self):
        archive_dir = getDir(self.dir, "{}_archive".format(self.name))
        tstmp = str(datetime.timestamp(datetime.now()))
        archive_name = "({})".format(tstmp).join(os.path.splitext(os.path.basename(self.path)))
        self.create() # 万一索引表被误删除时增加鲁棒性
        shutil.move(self.path, os.path.join(archive_dir, archive_name))  
    
    def getAllDate(self):
        tb = self.data.copy()
        dateset = set([])
        if tb.empty:
            pass
        else:
            for col in ["atime", "ctime", "mtime"]:#["mtime"]: # 
                dateset |= set(tb[col].dt.date.unique())
                #[QDate(2019,2,15),QDate(2019,2,18)]
        return dateset
       
class NotePack:
    def __init__(self, tb):
        super().__init__()
        self.index_tb = tb
        self.content_ext = ".html"
        self.info_ext = ".info"
        self.att_dir_name = "附件"

# 增        
    def create(self, file_path=None):
        self.id = str(uuid.uuid1())
        self.type = "Draft" # 默认只有在draft才可以新建
        # 还剩path, title, url, keywords, time(a,c,m), content
        if os.path.exists(os.path.join(self.index_tb.note_root_dir, self.type, self.id)):
            print("千古奇观啊!居然出现了重复的id", self.id)
            self.load()
            self.index_tb.update(flag="update", item=self)
        else:
            self.cat = "未分类"
            self.path = getDir(os.path.join(self.index_tb.note_root_dir, self.type), self.id)
            if file_path: # 结合了update的内容，只是不想重复建立空白再覆盖了。           
                self.parse(file_path)
            else:
                self.genContent()
            self.keywords = ";".join([self.cat])
            self.summary = "" # 基本就是个冗余项，可以以新建附件的形式完成 
            self.genInfo()
            self.getAtt()
            self.getTime()
            self.index_tb.update(flag="add", item=self)
            
            # print("新加入笔记：",self.title)
        
    def parse(self, file_path):
        file_fullname = os.path.basename(file_path)
        file_ext = os.path.splitext(file_fullname)
        name_s = file_fullname.split("(")[0] # 这个和singleFile保存的文件名格式有关
        if name_s: # != ""
            self.title = name_s  
        else:
            print("真的出现了？",file_fullname)
            self.title = file_ext[0] 
        self.content = os.path.join(self.path, file_fullname)
        shutil.copy2(file_path, self.content)
        self.content_ext = file_ext[1]
        self.url = pathlib.Path(os.path.abspath(self.content)).as_uri()          
        if (self.content_ext == ".html"):# 注意目前只对html有解析
            contents = ""
            codecs= ("utf-8", "gb18030", "ASCII")
            for codec in codecs:
                try:
                    f = open(self.content, "r", encoding=codec)
                except UnicodeDecodeError:
                    print("按{}读取错误".format(codec))
                else:
                    contents = f.read()
                    # print("按{}读取成功".format(codec)
                    break
            if not contents:
                print("未能成功读取HTML文件:", self.content)
            else:
                soup = BeautifulSoup(contents, 'lxml')
                # 摘取标题
                try:
                    self.title = soup.find('h2',{"class":"rich_media_title"}).string.strip()
                except:
                    pass            
                # 摘取URL
                try:
                    comments = soup.findAll(text=lambda text:isinstance(text, Comment))
                    url_p = comments[0].split("url:")[1].split("saved date:")[0].strip()
                except:
                    pass
                else:
                    if url_p[:4] == "http": # 修正部分以前一些本地笔记重新用singleFile保存的链接为file://开头
                        self.url = url_p
                # 摘取分类
                try:
                    self.cat = soup.title.string.strip()
                except:
                    pass # self.cat = "未分类"
                else:
                    if (self.cat == self.title) | (self.cat == None):
                        self.cat = "未分类"
        else: # 对于可能是图片或者pdf格式的各类非html笔记
            pass

    def genContent(self):
        self.title = "新的笔记"
        html_template = '<!DOCTYPE html><html><meta charset="utf-8"><head><title>{}</title></head>'.format(self.title)
        html_template += '<body>文件生成于{}，请开始记录吧</body></html>'.format(datetime.now().strftime("%Y-%m-%d_%H:%M:%S"))
        self.content = os.path.join(self.path, self.title+self.content_ext)
        with open(self.content, "w", encoding="utf-8") as f:
            f.write(html_template)
        self.url = pathlib.Path(os.path.abspath(self.content)).as_uri()
    
    def genInfo(self):
        info = pd.Series()
        info["title"] = self.title
        # info["type"] = self.type
        info["url"] = self.url
        info["cat"] = self.cat
        info["keywords"] = self.keywords
        info["summary"] = self.summary
        infoJSON = os.path.splitext(os.path.basename(self.content))[0]
        try:
            info.to_json(os.path.join(self.path, infoJSON+self.info_ext))
        except Exception as e:
            print("笔记信息写入出错：",e)
    
    def getAtt(self):
        self.att_dir = getDir(self.path, self.att_dir_name)
        self.att_list = os.listdir(self.att_dir)
    
    def getTime(self, path=None):
        # print(self.path)
        if path:
            pass
        else:
            path = self.content
        self.atime = datetime.fromtimestamp(os.path.getatime(path))
        self.ctime = datetime.fromtimestamp(os.path.getctime(path))  # ctime 在unix和win上表示的意义不全相同，不一定是create time也可能是change time
        self.mtime = datetime.fromtimestamp(os.path.getmtime(path)) 

# 删    
    def delete(self):
        try:
            send2trash(os.path.abspath(self.path)) # send2trash version1.5版本因为 \ / 符号的问题必须abspath一下, 不然后果很严重！！！
            self.index_tb.update(flag="delete", item=self) 
        except Exception as e:
            print("笔记删除出错",e)

# 改 
    def update(self, content=None):
        if content:
            try:
                with open(self.content, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                print("笔记写入出错",e)
        self.genInfo()     
        self.getAtt()
        self.getTime()
        self.index_tb.update(flag="update", item=self) 
        
    def move(self, dest):        
        # 移动笔记实体啦~~~~~~~~~~~~~~~~~~~~~
        if dest in ["Draft", "Archive", "Trash"]:
            self.type = dest
            # self.genInfo()
            old_path = self.path
            new_path = os.path.join(self.index_tb.note_root_dir, self.type, os.path.basename(self.path))
            try:
                shutil.move(old_path, new_path)
                self.path = new_path
            except Exception as e:
                print("文件夹移动中出错：",e)
        else:
            print("移动目标有误",dest)
        self.getAtt()    
        self.getTime(self.path)
        self.index_tb.update(flag="update", item=self)        
                   
    def addAtt(self, file_path):
        try:
            new_path = os.path.join(self.att_dir, os.path.basename(file_path))
            i = 0
            while os.path.exists(new_p):
                i += 1
                new_path = "({})".format(i).join(os.path.splitext(new_p))
            shutil.copy2(file_path, new_path)
        except Exception as e:
            print("添加附件失败",e)
        
    def delAtt(self, file_path):
        try:
            send2trash(os.path.abspath(file_path))
        except Exception as e:
            print("删除附件失败",e)

# 查
    def load(self, index=None):
        if index: 
            # 给index的则从table里先找，生成listWidget更快
            # 可以认为title,url,keywords,summary在table和infoJSON文件中相互冗余
            # table精炼信息并索引加快了查询速度
            # infoJSON保证了信息存储的独立可靠
            self.getFromIndex(index)
        else:
            self.getFromInfo()
            
    def getFromIndex(self, index):
            # 给index的则从table里先找，生成listWidget更快
            # 可以认为title,url,keywords,summary在table和infoJSON文件中相互冗余
            # table精炼信息并索引加快了查询速度
            # infoJSON保证了信息存储的独立可靠
            info = self.index_tb.data.loc[index]
            self.id = index
            self.path = info["path"]
            self.title = info["title"]
            self.type = getParentDir(info["path"])
            self.url = info["url"]
            self.cat = info["cat"]
            self.keywords = info["keywords"]
            self.summary = info["summary"]
            # type ext content att可以随后loadNote时再获得 
            
    def getFromInfo(self):
        if os.path.exists(self.path):
        # 万一有文件夹被无意删除了就会出错跳出的。。。
            self.id = os.path.basename(self.path)
            self.type = getParentDir(self.path)
            for f in os.listdir(self.path):
                path = os.path.join(self.path, f)
                if os.path.splitext(f)[1] == self.info_ext:
                    info = pd.read_json(path, typ="Series") 
                    self.title = info["title"]
                    self.url = info["url"]
                    self.cat = info["cat"]
                    self.keywords = info["keywords"]
                    self.summary = info["summary"]
                elif f == self.att_dir_name:
                    self.getAtt()
                else:
                    self.content = path           
                    self.content_ext = os.path.splitext(path)[1]
            self.getAtt()
            self.getTime()
            # self.getTime()
            self.index_tb.update(flag="update", item=self) 
            print("笔记解析完成:",self.title)
        else:
            print("读取错误，{}找不到了".format(self.path))
        
     