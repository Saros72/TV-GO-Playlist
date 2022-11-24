#-*-coding:utf8;-*-
#v1.17.0


# přihlašovací údaje
user = ""
password = ""

# jazyk (cz/sk)
lng = "cz"

# zařízení
if lng == "cz":
    dev_type = "OTT_LINUX_4302"
    dev_type = "OTT_ANDROID"
    dev_name = "Xiaomi Mi 11"
else:
    dev_type = "OTT_STB"
    dev_name = "KSTB6077"

# Seznam vlastních kanálů
# Seznam id kanálů oddělené čárkou (např.: "6054,6053,20,29")
# Pro všechny kanály ponechte prázdné
CHANNEL_IDS = ""

# EPG
# vygenerovat EPG
# ano = 1, ne = 0
epg_enabled = 1

# Počet dní (1-15)
days = 3

# Počet dní zpětně (0-7)
days_back = 1


import time, random, requests, os, json, sys, time, unicodedata, uuid, xmltv
from urllib.parse import urlparse
from datetime import datetime, timedelta, date
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry


save_path = os.path.dirname(os.path.realpath(__file__))
fu = os.path.join(save_path,"uuid")
fp = os.path.join(save_path,"playlist.m3u")
fe = os.path.join(save_path,"epg.xml")
UA = "okhttp/3.12.12"
now = datetime.now()
local_now = now.astimezone()
TS = " " + str(local_now)[-6:].replace(":", "")
if not os.path.exists(fu):
    dev_id = str(uuid.uuid4())
    f = open(fu, "w")
    f.write(dev_id)
    f.close()
else:
    dev_id = open(fu, "r").read()


def encode(string):
    string = str(unicodedata.normalize('NFKD', string).encode('ascii', 'ignore'), "utf-8")
    return string


class TV_GO:

    def __init__(self):
        self.refreshtoken = self.login()
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

    def login(self):
        print("Login:", end="", flush=True)
        params={"dsid": dev_id, "deviceName": dev_name, "deviceType": dev_type, "osVersion": "0.0.0", "appVersion": "0.0.0", "language": lng.upper()}
        headers={"Host": lng + "go.magio.tv", "User-Agent": UA}
        req = requests.post("https://" + lng + "go.magio.tv/v2/auth/init", params=params, headers=headers).json()
        accessToken = req["token"]["accessToken"]
        params = {"loginOrNickname": user, "password": password}
        headers = {"Content-type": "application/json", "authorization": "Bearer " + accessToken, "Host": lng + "go.magio.tv", "User-Agent": UA, "Connection": "Keep-Alive"}
        req = requests.post("https://" + lng + "go.magio.tv/v2/auth/login", json = params, headers = headers).json()
        if req["success"] == True:
            accesstoken = req["token"]["accessToken"]
            refreshtoken = req["token"]["refreshToken"]
            print(" OK\n")
            return refreshtoken
        else:
            print("\n" + req["errorMessage"])
            return None

    def playlist(self):
        refreshtoken = self.refreshtoken
        if refreshtoken is not None:
            print("Generuji playlist:")
            params={"refreshToken": refreshtoken}
            headers = {"Content-type": "application/json", "Host": lng + "go.magio.tv", "User-Agent": UA, "Connection": "Keep-Alive"}
            req = self.session.post("https://" + lng + "go.magio.tv/v2/auth/tokens", json = params, headers = headers).json()
            if req["success"] == True:
                accesstoken = req["token"]["accessToken"]
            else:
                os.system('cls||clear')
                print("Chyba:\n" + req["errorMessage"])
                return
            params={"list": "LIVE", "queryScope": "LIVE"}
            headers = {"Content-type": "application/json", "authorization": "Bearer " + accesstoken, "Host": lng + "go.magio.tv", "User-Agent": UA, "Connection": "Keep-Alive"}
            req = self.session.get("https://" + lng + "go.magio.tv/v2/television/channels", params = params, headers = headers).json()
            channels = []
            channels2 = []
            ids = ""
            reqq = requests.get("https://" + lng + "go.magio.tv/home/categories?language=" + lng, headers = headers).json()["categories"]
            categories = {}
            for cc in reqq:
                for c in cc["channels"]:
                    categories [c["channelId"]] = cc["name"]
            for n in req["items"]:
                name = n["channel"]["name"]
                logo = str(n["channel"]["logoUrl"])
                idd = n["channel"]["channelId"]
                ids = ids + "," + str(idd)
                id = "tm-" + str(idd) + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-")
                if CHANNEL_IDS == "":
                    channels2.append(({"display-name": [(name, u"cs")], "id": str(id), "icon": [{"src": logo}]}))
                    channels.append((name, idd, logo))
                else:
                    if str(idd) in CHANNEL_IDS.split(","):
                        channels2.append(({"display-name": [(name, u"cs")], "id": str(id), "icon": [{"src": logo}]}))
                        channels.append((name, idd, logo))
            f = open(fp, "w", encoding="utf-8")
            f.write("#EXTM3U\n")
            for ch in channels:
                id = "tm-" + str(ch[1]) + "-" + encode(ch[0]).replace(" HD", "").lower().replace(" ", "-")
                if ch[1] == 5000:
                    id = "tm-6016-eurosport-1"
                group = categories[ch[1]]
                print(ch[0])
                params={"service": "LIVE", "name": dev_name, "devtype": dev_type, "id": ch[1], "prof": "p5", "ecid": "", "drm": "verimatrix"}
                headers = {"Content-type": "application/json", "authorization": "Bearer " + accesstoken, "Host": lng + "go.magio.tv", "User-Agent": UA, "Connection": "Keep-Alive"}
                req = self.session.get("https://" + lng + "go.magio.tv/v2/television/stream-url", params = params, headers = headers)
                if req.json()["success"] == True:
                    url = req.json()["url"]
                else:
                    if req.json()["success"] == False and req.json()["errorCode"] == "NO_PACKAGE":
                        url = None
                    else:
                        os.system('cls||clear')
                        print("Chyba:\n" + req.json()["errorMessage"].replace("exceeded-max-device-count", "Překročen maximální počet zařízení"))
                        if "DEVICE_MAX_LIMIT" in str(req.json()):
                            ut = input("\nOdebrat zařízení? a/n ")
                            if ut == "a":
                                self.delete_device()
                            else:
                                os.system('cls||clear')
                        return
                if lng == "sk" or lng == "cz":
                    if url is not None:
                        headers = {"Host": urlparse(url).netloc, "User-Agent": "ReactNativeVideo/3.13.2 (Linux;Android 10) ExoPlayerLib/2.10.3", "Connection": "Keep-Alive"}
                        req = self.session.get(url, headers = headers, allow_redirects=False)
                        url = req.headers["location"]
                if url is not None:
                    f.write('#EXTINF:-1 group-title="' + group + '" tvg-id="' + id +  '",' +str(ch[0])+"\n" + url + '\n')
            f.close()
            if epg_enabled == 1:
                self.epg(accesstoken, channels2, ids)
            else:
                print("\nHotovo\n")
                input("Pro ukončení stiskněte libovolnou klávesu")


    def epg(self, accesstoken, channels, tm_ids):
        print("\nStahuji data pro EPG:")
        programmes = []
        headers = {"Content-type": "application/json", "authorization": "Bearer " + accesstoken, "Host": lng + "go.magio.tv", "User-Agent": UA, "Connection": "Keep-Alive"}
        now = datetime.now()
        for i in range(days_back*-1, days):
            next_day = now + timedelta(days = i)
            back_day = (now + timedelta(days = i)) - timedelta(days = 1)
            date_to = next_day.strftime("%Y-%m-%d")
            date_from = back_day.strftime("%Y-%m-%d")
            date_ = next_day.strftime("%d.%m.%Y")
            print(date_, end="", flush=True)
            req = self.session.get("https://" + lng + "go.magio.tv/v2/television/epg?filter=channel.id=in=(" + str(tm_ids[1:]) + ");endTime=ge=" + date_from + "T23:00:00.000Z;startTime=le=" + date_to + "T23:59:59.999Z&limit=" + str(len(channels)) + "&offset=0&lang=" + lng.upper(), headers=headers).json()["items"]
            for x in range(0, len(req)):
                for y in req[x]["programs"]:
                    id = y["channel"]["id"]
                    name = y["channel"]["name"]
                    channel = "tm-" + str(id) + "-" + encode(name).replace(" HD", "").lower().replace(" ", "-")
                    start_time = y["startTime"].replace("-", "").replace("T", "").replace(":", "")
                    stop_time = y["endTime"].replace("-", "").replace("T", "").replace(":", "")
                    title = y["program"]["title"]
                    desc = y["program"]["description"]
                    year = y["program"]["programValue"]["creationYear"]
                    try:
                        subgenre = y["program"]["programCategory"]["subCategories"][0]["desc"]
                    except:
                        subgenre = ''
                    try:
                        genre = [(y["program"]["programCategory"]["desc"], u''), (subgenre, u'')]
                    except:
                        genre = None
                    try:
                        icon = y["program"]["images"][0]
                    except:
                        icon = None
                    epi = y["program"]["programValue"]["episodeId"]
                    if epi != None:
                        title = title + " (" + epi + ")"
                    try:
                        programm = {'channel': str(channel), 'start': start_time + TS, 'stop': stop_time + TS, 'title': [(title, u'')],  'desc': [(desc, u'')]}
                        if year != None:
                            programm['date'] = year
                        if genre != None:
                            programm['category'] = genre
                        if icon != None:
                            programm['icon'] = [{"src": icon}]
                    except:
                        pass
                    if programm not in programmes:
                        programmes.append(programm)
            print("  OK")
        self.session.close()
        print("\nGeneruji EPG")
        w = xmltv.Writer(encoding="utf-8", source_info_url="http://www.funktronics.ca/python-xmltv", source_info_name="Funktronics", generator_info_name="python-xmltv", generator_info_url="http://www.funktronics.ca/python-xmltv")
        for c in channels:
            w.addChannel(c)
        for p in programmes:
            w.addProgramme(p)
        w.write(fe, pretty_print=True)
        print("Hotovo\n")
        input("Pro ukončení stiskněte libovolnou klávesu")


    def delete_device(self):
        params={"refreshToken": self.refreshtoken}
        headers = {"Content-type": "application/json", "Host": lng + "go.magio.tv", "User-Agent": UA, "Connection": "Keep-Alive"}
        req = requests.post("https://" + lng + "go.magio.tv/v2/auth/tokens", json = params, headers = headers).json()
        if req["success"] == True:
            accesstoken = req["token"]["accessToken"]
        else:
            os.system('cls||clear')
            print("Chyba:\n" + req["errorMessage"])
            return
        headers = {"Content-type": "application/json", "authorization": "Bearer " + accesstoken, "Host": lng + "go.magio.tv", "User-Agent": UA, "Connection": "Keep-Alive"}
        req = requests.get("https://" + lng + "go.magio.tv/v2/home/my-devices", headers = headers).json()
        devices = []
        try:
            devices.append((req["thisDevice"]["name"] + " (Toto zařízení)", req["thisDevice"]["id"]))
        except:
            pass
        try:
            for d in req["smallScreenDevices"]:
                devices.append((d["name"], d["id"]))
        except:
            pass
        try:
            for d in req["stbAndBigScreenDevices"]:
                devices.append((d["name"], d["id"]))
        except:
            pass
        os.system('cls||clear')
        i = 0
        for x in devices:
            print('{:30s} {:1s} '.format(x[0], str(i)))
            i+=1
        try:
            l = int(input("\nVyberte zařízení:\n"))
            dev_id = devices[l][1]
            req = requests.get("https://" + lng + "go.magio.tv/home/deleteDevice?id=" + str(dev_id), headers = headers).json()
            if req["success"] == True:
                os.system('cls||clear')
                print("Odebráno\n")
                self.playlist()
            else:
                os.system('cls||clear')
                print("Chyba:\n" + req["errorMessage"])
        except:
            os.system('cls||clear')
            print("Chyba")
        return


if __name__ == "__main__":
    TV_GO().playlist()