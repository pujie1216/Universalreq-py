import sys
import time
try:
  import requests
except (ImportError, ModuleNotFoundError):
  print("请先安装 requests 模块哦,5秒后自动退出")
  time.sleep(5)
  sys.exit()
import os
import json
import linecache
import re
import datetime

requests.packages.urllib3.disable_warnings()

def requestExit():
  print("\n程序5秒后自动退出")
  time.sleep(5)
  sys.exit()

class Notification():
  def getWorkwxtoken(self, corpid, corpsecret, noticpath):
    resp = requests.get(
      "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=%s&corpsecret=%s" % (corpid, corpsecret),
      timeout=5).json()
    if resp["errcode"] == 0:
      access_token = resp["access_token"]
      with open(noticpath + "/workwx.token", "w") as token:
        token.write(access_token)
        print("企业微信的token已本地记录")
        return access_token
    else:
      print("企业微信的token获取失败: " + resp["errmsg"])
      time.sleep(10)
      return False

  def sendWorkwxmsg(self, agentid, access_token, message):
    workwxdata = '{"touser":"@all",' \
                 '"msgtype":"text",' \
                 '"agentid":"%s",' \
                 '"text":{"content":"%s"}}' % (agentid, message)
    resp = requests.post("https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=%s" % (access_token),
                         data=workwxdata.encode("utf-8"), timeout=5).json()
    if resp["errcode"] == 0:
      print("企业微信的推送消息发送成功")
    else:
      print("企业微信的推送消息发送失败: " + resp["errmsg"])

  def WorkwxnoticMain(self, noticpath, message):
    noticsetpath = noticpath + "/notic.set"
    workwxtkpath = noticpath + "/workwx.token"
    workwxidl = linecache.getline(noticsetpath, 8).strip().split(".")
    corpid = workwxidl[0]
    corpsecret = workwxidl[1]
    agentid = workwxidl[2]
    if os.path.isfile(workwxtkpath):
      tokengettime = int(os.path.getmtime(workwxtkpath))
      tokenexptime = tokengettime + 7200
      if tokenexptime < int(time.time()):
        print("企业微信的本地token可能已过期,正在自动重新获取")
        access_token = self.getWorkwxtoken(corpid, corpsecret, noticpath)
      else:
        print("企业微信的本地token还在有效期内,继续使用")
        access_token = linecache.getline(workwxtkpath, 1).strip()
    else:
      access_token = self.getWorkwxtoken(corpid, corpsecret, noticpath)
    if access_token:
      self.sendWorkwxmsg(agentid, access_token, message)

  def BarknoticMain(self, noticsetpath, message):
    try:
      barkey = linecache.getline(noticsetpath, 11).strip()
      requests.get("https://api.day.app/%s/%s" % (barkey, message), timeout=5)
      print("Bark的推送消息发送成功")
    except Exception:
      self.BarknoticMain(noticsetpath, message)

  def DingtalknoticMain(self, noticsetpath, message):
    keyword = linecache.getline(noticsetpath, 14).strip()
    access_token = linecache.getline("notic.set", 15).strip()
    dingtalkdata = '{"msgtype":"text",' \
                   '"text":{"content": "%s\n%s"}}' % (keyword, message)
    resp = requests.post("https://oapi.dingtalk.com/robot/send?access_token=%s" % (access_token),
                         headers={"Content-Type": "application/json;charset=UTF-8"},
                         data=dingtalkdata.encode("utf-8"), timeout=5).json()
    if resp["errcode"] == 0:
      print("钉钉的推送消息发送成功")
    else:
      print("钉钉的推送消息发送失败: " + resp["errmsg"])

  def NoticMain(self, noticpath, message):
    noticsetpath = noticpath + "/notic.set"
    notictype = linecache.getline(noticsetpath, 5).strip()
    if notictype == "0":
      print("推送通知没有开启哦\n")
    else:
      message = "%s %s" % (time.strftime("%H{}%M{}%S{}").format("时", "分", "秒"), message)
      if notictype == "1":
        print("当前使用 企业微信 推送通知")
        self.WorkwxnoticMain(noticpath, message)
      elif notictype == "2":
        print("当前使用 Bark 推送通知")
        self.BarknoticMain(noticsetpath, message)
      elif notictype == "3":
        print("当前使用 钉钉 推送通知")
        self.DingtalknoticMain(noticsetpath, message)

def requestUrlp():
  if os.path.isfile("request.urlp"):
    with open("request.urlp", encoding="utf-8") as urlp:
      for i in urlp.readlines():
        i = i.strip()
        if not len(i) or i.startswith("#"):
          continue
        urlp = i
  else:
    urlp = input("当前目录没有 request.urlp 文件,需要自行填写Url\n:")
  return urlp

def requestHeaders():
  if os.path.isfile("request.headers"):
    headersd = {}
    with open("request.headers", encoding="utf-8") as headers:
      for i in headers.readlines():
        i = i.strip()
        if not len(i) or i.startswith("#"):
          continue
        kv = i.split(":", 1)
        headersd[kv[0].strip()] = kv[1].strip()
    return headersd
  else:
    headers = input("当前目录没有 request.headers 文件,需要自行填写字典格式的headers\n:")
    if not headers.startswith("{"):
      ask = input("格式错误,是否重新输入\n是 输入 y 后按确定继续,否 直接按确定并退出:")
      if ask.lower() == "y":
        return requestHeaders()
      else:
        requestExit()
    else:
      headersd = json.loads(headers)
      return headersd

def requestData():
  if os.path.isfile("request.data"):
    with open("request.data", encoding="utf-8") as data:
      for i in data.readlines():
        i = i.strip()
        if not len(i) or i.startswith("#"):
          continue
        data = i.encode(linecache.getline("request.data", 4).strip().replace("#", ""))
  else:
    data = input("当前目录没有 request.data 文件,需要自行填写data\n没有data的直接按确定键:")
    if data == "":
      data = "None"
  return data

def requestTiming():
  requesttime = linecache.getline("request.set", 5).strip()
  if requesttime == "0":
    pass
  elif datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3] < requesttime:
    print("已开启定时,请勿关闭,程序将在 %s 开抢" % (requesttime))
    while True:
      nowtime = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
      if requesttime < nowtime:
        break
      print("当前本地时间为: %s " % (nowtime), end="\r")
      time.sleep(0.01)

def requestGo(requesturlp, requestheaders, requestdata, requesttimeout, requestlooptime, noticpath):
  try:
    while True:
      if requestdata == "None":
        response = requests.get(requesturlp, headers=requestheaders, verify=False, timeout=requesttimeout)
      else:
        response = requests.post(requesturlp, headers=requestheaders, data=requestdata, verify=False,
                                 timeout=requesttimeout)
      if response.status_code == requests.codes.ok:
        webencode = requests.utils.get_encodings_from_content(response.text)
        if len(webencode) != 0:
          responset = response.content.decode(webencode[0])
        else:
          responset = response.content.decode(linecache.getline("request.set", 14).strip())
        print(time.strftime("%H:%M:%S ") + responset)
        stopresponse = linecache.getline("request.set", 17).strip()
        if stopresponse == "0":
          pass
        elif stopresponse == "1" and re.findall(linecache.getline("request.set", 20).strip(), responset,
                                                flags=re.I) == []:
          print("\n已根据设置的结果停止刷新")
          if noticpath != "false":
            Notification().NoticMain(noticpath, responset.replace('"', "'"))
          time.sleep(30)
          break
        elif stopresponse == "2" and re.findall(linecache.getline("request.set", 23).strip(), responset,
                                                flags=re.I) != []:
          print("\n已根据设置的结果停止刷新")
          if noticpath != "false":
            Notification().NoticMain(noticpath, responset.replace('"', "'"))
          time.sleep(30)
          break
      else:
        print("请求的网址 %s 了" % (response.status_code))
        response.raise_for_status()
      time.sleep(requestlooptime)
  except requests.exceptions.HTTPError:
    print("%s 秒后重新访问" % (requestlooptime))
    time.sleep(requestlooptime)
    requestGo(requesturlp, requestheaders, requestdata, requesttimeout, requestlooptime, noticpath)
  except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
    print("%s 访问网址出错了, %s 秒后重新访问" % (time.strftime("%H:%M:%S "), requestlooptime))
    time.sleep(requestlooptime)
    requestGo(requesturlp, requestheaders, requestdata, requesttimeout, requestlooptime, noticpath)
  except Exception as err:
    print(err)
    ask = input("未知错误,是否继续访问,是 直接按确定键继续,否 输入 n 后按确定键退出:")
    if ask.lower() == "n":
      requestExit()
    else:
      requestGo(requesturlp, requestheaders, requestdata, requesttimeout, requestlooptime, noticpath)

def requestMain():
  if os.path.isfile("request.set") and len(open("request.set", errors="ignore", encoding="utf-8").readlines()) == 26:
    noticpath = linecache.getline("request.set", 26).strip()
    noticsetpath = noticpath + "/notic.set"
    try:
      noticlines = len(open(noticsetpath, errors="ignore", encoding="UTF-8").readlines())
      if noticlines != 15:
        print("出错了, notic.set 的行数不对,将无法开启推送通知哦")
        noticsetpath = "false"
    except FileNotFoundError:
      print("指定目录下没有 notic.set 文件,将无法开启推送通知哦")
      noticpath = "false"
    if noticpath != "false":
      linecache.updatecache(noticsetpath)
    requesttimeout = linecache.getline("request.set", 8).strip()
    requestlooptime = linecache.getline("request.set", 11).strip()
  else:
    print("当前目录没有 request.set 文件或文件行数不对,需要自行填写 连接超时 和 间隔刷新时间 且无法开启推送通知哦")
    noticsetpath = "false"
    requesttimeout = input("输入连接超时的时间(秒,仅数字或小数):")
    requestlooptime = input("输入间隔刷新时间(秒,仅数字或小数):")
  try:
    requesttimeout = float(requesttimeout)
  except ValueError:
    input("检测到 连接超时 为非数字或小数,重新修改或输入仅数字或小数!\n按确定键继续...")
    requestMain()
  try:
    requestlooptime = float(requestlooptime)
  except ValueError:
    input("检测到 间隔刷新时间 为非数字或小数,重新修改或输入仅数字或小数!\n按确定键继续...")
    requestMain()
  requesturlp = requestUrlp()
  requestheaders = requestHeaders()
  requestdata = requestData()
  requestTiming()
  requestGo(requesturlp, requestheaders, requestdata, requesttimeout, requestlooptime, noticpath)
  requestExit()

try:
  codedatenow = datetime.datetime.strptime("2021-5-13 19:30", "%Y-%m-%d %H:%M")
  codeversionj = requests.get("https://raw.githubusercontent.com/pujie1216/Universalreq-py/main/codeversion.json",
                              timeout=5).json()
  codedatenew = datetime.datetime.strptime(codeversionj["codedate"], "%Y-%m-%d %H:%M")
  if codedatenew > codedatenow:
    print("检测到有比较新的代码,更新内容为:\n\n%s" % (codeversionj["changelog"]))
    updateask = input("是否去GitHub更新代码,是 直接按确定键 继续,否 输入 n 后按确定键继续:")
    if updateask == "":
      if sys.platform == "win32":
        os.system("start https://github.com/pujie1216/Universalreq-py")
      elif sys.platform == "darwin":
        os.system("open https://github.com/pujie1216/Universalreq-py &")
      else:
        os.system("xdg-open https://github.com/pujie1216/Universalreq-py &")
      requestExit()
except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, ValueError) as err:
  print(err)
  print("\n访问GitHub出错,跳过检测更新\n")
requestMain()
