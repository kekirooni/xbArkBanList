import urllib.request, time, sys, threading, pyperclip, webbrowser, urllib, json, requests, os, socket, platform
from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from tkinter import *
import base64, sqlite3, shutil
from datetime import timezone, datetime, timedelta
from PIL import Image, ImageTk
import io
import tkinter

import os, re, requests, json

from urllib.parse import urlencode, unquote, parse_qs, urlparse


MESSAGE_TEXT = 0
MESSAGE_GIF = 1

GROUP_NOTI_NONE = 0
GROUP_NOTI_AT_ONLY = 1
GROUP_NOTI_ALL = 2

ARK_TITLE_ID = 983730484
CLUB_ID = 3379889510460425

gamertag= None
new =None
gcID = 29184405409504205
gcIDc: int = 0

logged = False
count = 0
api_timeout = 0
email = ""
password = ""
groupID = "27954743249869781"
size = 0
clipboard = True

class AuthFailed(Exception):
    pass
class InvalidRequest(Exception):
    pass
class InvalidReportReason(Exception):
    pass
class InvalidReportType(Exception):
    pass

# 32bit only (no prefix) e.g. 000003f3(_hexstr) -> 1011(eax, return)
def todec(
    _hexstr:str) -> int:
    bedian:str
    # big edian
    for id, c in enumerate(_hexstr):
        if "0" in c:
            continue
        bedian = _hexstr[id:]       #   000003f3 -> 3f3
        break
    # correcting pythons auto byte->string
    for idx, x in enumerate(bedian):
        if not x.isalnum() and not x.isdigit():     #   catch } (7d)
            for z in bytes(x, "utf-8"):             #   } -> 0x7d
                bedian = bedian.replace(x, hex(z).replace("0x", ""))        #   000001} -> 0000017d

    return int(f"0x{bedian}", 16)

class Client(object):
    
    def __init__(
        self: object
        ):
        self.session = requests.session()
        self.AUTHORIZATION_HEADER: str
        self.authenticated = False

    def _raise_for_status(
        self: object,
        response: requests.Request
        ):
        if response.status_code > 400:
            try:
                description = f"Error {response.status_code}: {response.json()['errorMessage']}"
            except:
                description = 'Invalid request' if response.status_code != 429 else "Rate limited"
            raise InvalidRequest(f"{response.status_code} Invalid Request ({description})")
        
    def _put_json(
        self: object,
        url: str,
        data: dict,
        headers: dict
        ):
        resp = self.session.request("PUT", url, data=json.dumps(data), headers=headers)
        self._raise_for_status(resp)
        return resp
    
    def _post(
        self: object,
        url: str,
        **kw: object
        ):
        '''
        Makes a POST request, setting Authorization
        header by default
        '''
        headers = kw.pop('headers', {})
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        kw['headers'] = headers
        resp = self.session.post(url, **kw)
        self._raise_for_status(resp)
        return resp
        
    def _post_json(
        self: object,
        url: str,
        data: dict,
        **kw: object
        ):
        '''
        Makes a POST request, setting Authorization
        and Content-Type headers by default
        '''
        data = json.dumps(data)
        headers = kw.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        headers.setdefault('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36')

        kw['headers'] = headers
        kw['data'] = data
        return self._post(url, **kw)
    
    def _get(
        self: object,
        url: str,
        **kw: object
        ):
        '''
        Makes a GET request, setting Authorization
        header by default
        '''
        headers = kw.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')
        headers.setdefault('Accept', 'application/json')
        headers.setdefault('Authorization', self.AUTHORIZATION_HEADER)
        kw['headers'] = headers
        resp = self.session.get(url, **kw)
        return resp
    
    def auth(
        self: object,
        sLogin: str,
        sPassword: str
        ):
        """
            https = urllib3.PoolManager(ca_certs=certifi.where()) # creating SSL certified pool (allows HTTPS connection)
            resp = https.request("GET", "https://login.live.com/oauth20_authorize.srf?", fields={
            'client_id': '0000000048093EE3',
            'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
            'response_type': 'token',
            'display': 'touch',
            'scope': 'service::user.auth.xboxlive.com::MBI_SSL',
            'locale': 'en'
                }) # get auth tokens from successful SSL HTTPS connection"""
        login = sLogin
        base_url = 'https://login.live.com/oauth20_authorize.srf?'

            # if the query string is percent-encoded the server
            # complains that client_id is missing
        qs = unquote(urlencode({
                'client_id': '0000000048093EE3',
                'redirect_uri': 'https://login.live.com/oauth20_desktop.srf',
                'response_type': 'token',
                'display': 'touch',
                'scope': 'service::user.auth.xboxlive.com::MBI_SSL',
                'locale': 'en',
            }))
        resp = self.session.get(base_url + qs)
        url_re = b'urlPost:\\\'([A-Za-z0-9:\?_\-\.&/=]+)'
        ppft_re = b'sFTTag:\\\'.*value="(.*)"/>'
        login_post_url = re.search(url_re, resp.content).group(1)
        post_data = {
                'login': sLogin,
                'passwd': sPassword,
                'PPFT': re.search(ppft_re, resp.content).groups(1)[0],
                'PPSX': 'Passpor',
                'SI': 'Sign in',
                'type': '11',
                'NewUser': '1',
                'LoginOptions': '1',
                'i3': '36728',
                'm1': '768',
                'm2': '1184',
                'm3': '0',
                'i12': '1',
                'i17': '0',
                'i18': '__Login_Host|1',
            }
        resp = self.session.post(
                login_post_url, data=post_data, allow_redirects=False,
            )
        if 'Location' not in resp.headers:
            # we can only assume the login failed
            msg = 'Could not log in with supplied credentials'
            raise AuthFailed(msg)

        # the access token is included in fragment of the location header
        location = resp.headers['Location']
        parsed = urlparse(location)
        fragment = parse_qs(parsed.fragment)
        access_token = fragment['access_token'][0]

        url = 'https://user.auth.xboxlive.com/user/authenticate'
        resp = self.session.post(url, data=json.dumps({
            "RelyingParty": "http://auth.xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "AuthMethod": "RPS",
                "SiteName": "user.auth.xboxlive.com",
                "RpsTicket": access_token,
            }
        }), headers={'Content-Type': 'application/json'})

        json_data = resp.json()
        user_token = json_data['Token']
        uhs = json_data['DisplayClaims']['xui'][0]['uhs']

        url = 'https://xsts.auth.xboxlive.com/xsts/authorize'
        resp = self.session.post(url, data=json.dumps({
            "RelyingParty": "http://xboxlive.com",
            "TokenType": "JWT",
            "Properties": {
                "UserTokens": [user_token],
                "SandboxId": "RETAIL",
            }
        }), headers={'Content-Type': 'application/json'})

        response = resp.json()
        self.AUTHORIZATION_HEADER = 'XBL3.0 x=%s;%s' % (uhs, response['Token'])
        self.user_xid = response['DisplayClaims']['xui'][0]['xid']
        self.user_gtg = response['DisplayClaims']['xui'][0]['gtg']
        self.authenticated = True
        print(f"{self.user_gtg} successfully logged in ({self.user_xid})\n")
        return self

    def get_title_stats(
        self: object,
        xuid: int,
        titleId:int = ARK_TITLE_ID
    ):
        url = "https://userstats.xboxlive.com/batch"    #   URI WebApi
        resp = self._post_json(url, data =  {
                                        "arrangebyfield": "xuid",       #   get fields for XUID
                                        "groups": [{
                                            "name": "Hero",             #   Hero field, containing a group of StatList containers
                                            "titleId": titleId          #   the title index of the game
                                            }],
                                        "stats": [{
                                            "name": "MinutesPlayed",    #   ask to return minutes played
                                            "titleId": titleId          #   of the title
                                           }],
                                        "xuids": [xuid]                 #   list of xuids, > 1 will return a vector json
                                        }, headers={"x-xbl-contract-version": b"2", #   required
                                                    "accept-language": "en-GB"})    #   not sure if required, probably not
        #   post-get response formatted into JSON
        raw_json = resp.json()
        stats: dict = {}
        """
        example payload response:
                    'groups': [{
                                'name': 'Hero',
                                'titleid': '983730484',
                                'statlistscollection': [{
                                        'arrangebyfield': 'xuid',
                                        'arrangebyfieldid': '2533274905367855',
                                        'stats': [{
                                                'groupproperties': {
                                                    'Ordinal': '3',
                                                    'SortOrder': 'Descending',
                                                    'DisplayName': 'Creatures Tamed',
                                                    'DisplayFormat': 'Integer',
                                                    'DisplaySemantic': 'Cumulative'
                                                },
                                                'xuid': '2533274905367855',
                                                'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                                'name': 'CreatureTamed',
                                                'type': 'Integer',
                                                'properties': {
                                                    'DisplayName': 'Creatures Tamed'
                                                }
                                            }, {
                                                'groupproperties': {
                                                    'Ordinal': '7',
                                                    'SortOrder': 'Descending',
                                                    'DisplayName': 'Survivors Killed',
                                                    'DisplayFormat': 'Integer',
                                                    'DisplaySemantic': 'Cumulative'
                                                },
                                                'xuid': '2533274905367855',
                                                'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                                'name': 'KilledSurvivor',
                                                'type': 'Integer',
                                                'properties': {
                                                    'DisplayName': 'Survivors Killed'
                                                }
                                            }, {
                                                'groupproperties': {
                                                    'Ordinal': '10',
                                                    'SortOrder': 'Ascending',
                                                    'DisplayName': 'Player Deaths',
                                                    'DisplayFormat': 'Integer',
                                                    'DisplaySemantic': 'Cumulative'
                                                },
                                                'xuid': '2533274905367855',
                                                'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                                'name': 'PlayerDied',
                                                'type': 'Integer',
                                                'properties': {
                                                    'DisplayName': 'Player Deaths'
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ],
                        'statlistscollection': [{
                                'arrangebyfield': 'xuid',
                                'arrangebyfieldid': '2533274905367855',
                                'stats': [{
                                        'groupproperties': {},
                                        'xuid': '2533274905367855',
                                        'scid': 'c1000100-ccd3-4685-bb6c-83ca3aa28934',
                                        'titleid': '983730484',
                                        'name': 'MinutesPlayed',
                                        'type': 'Integer',
                                        'value': '205763',
                                        'properties': {}
                                    }
                                ]
                            }
                        ]
                    }
        
        """
        #   going through each instance of a group StatList object
        for stat in raw_json["groups"][0]["statlistscollection"][0]["stats"]:
            try:
                #   storing the name:value into a directionary (key:value)
                stats[stat["name"]] = stat["value"]
            except (KeyError, IndexError):
                #   if stat doesnt have a value (0) skip adding the stat and avoid exception
                continue
        try:
            #   store the minuted played stat we requested in the POST JSON
            stats["MinutesPlayed"] = int(raw_json["statlistscollection"][0]["stats"][0]["value"])
        except (KeyError, IndexError):
            #   if value doesnt exist, aka 0, set a None object for error handling 
            stats["MinutesPlayed"] = None

        return stats

    def change_group_notification_status(
        self: object,
        groupID: int,
        statusID: int
    ) -> int:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/channels/0/notification"
        noti_options = [ "None",  "DirectMentions", "All" ]
        data = { "notificationOptions": noti_options[statusID] }
        return self._put_json(url, data=data, headers={"content-type": "application/json", "authorization": self.AUTHORIZATION_HEADER, "x-xbl-contract-version": b"1"})
    
    def add_friend(
        self: object,
        xuid: int
    ):
        url = f"https://social.xboxlive.com/users/xuid({self.user_xid})/people/xuid({xuid})?app_name=xbox_on_windows&app_ctx=user_profile"
        return self.session.request("PUT", url, headers={"authorization": self.AUTHORIZATION_HEADER,
                                                         "x-xbl-contract-version": b"2"}).status_code
    
    def delete_friend(
        self: object,
        xuid: int
    ):
        url = f"https://social.xboxlive.com/users/xuid({self.user_xid})/people/xuid({xuid})"
        return self.session.request("DELETE", url, headers={"authorization": self.AUTHORIZATION_HEADER,
                                                            "x-xbl-contract-version": b"2"}).status_code
    
    def get_blocked_users(
        self: object
    ):
        url = "https://privacy.xboxlive.com/users/me/people/never"
        resp = self._get(url).json()
        data = None
        try:
            data = resp["users"][0] #   there are blocked XUIDs
            data = resp["users"][:]
        except IndexError:
            pass
        return data
                   
    def change_group_name(
        self: object,
        groupID: int,
        new_name: str
    ) -> str:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/name"
        return self._post_json(url, data = {
                                    "name": new_name 
                                    }).status_code
    
    def block_user(
        self: object,
        xuid: int
    ):
        url = "https://privacy.xboxlive.com/users/me/people/never"
        return self._put_json(url, data = {
                                    "xuid": xuid
                                            }, headers={"authorization": self.AUTHORIZATION_HEADER,
                                                        "x-xbl-contract-version": b"4",
                                                        "content-type": "application/json",
                                                        "accept": "application/json"}).status_code
    
    def unblock_user(
        self: object,
        xuid: int
    ):
        url = "https://privacy.xboxlive.com/users/me/people/never"
        return self.session.request("DELETE", url, data=json.dumps({"xuid": xuid}),
                                    headers={"x-xbl-contract-version": b"4",
                                             "authorization": self.AUTHORIZATION_HEADER,
                                             "content-type": "application/json",
                                             "accept": "application/json"}).status_code
    
    def invite_to_group(
        self: object,
        groupID: int, # 29184405409504205
        xuid: int
    ) -> int:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/participants"
        resp = self._post_json(url, data = {
                                "participants": [ xuid ]
                                })
        return resp.status_code
    
    def message_to_group(
        self: object,
        groupID: int, # 29184405409504205
        message: str
    ) -> int:
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/channels/0/messages"
        resp = self._post_json(url, data={
                                     "parts": [{
                                             "contentType": "text",
                                             "version": 0,
                                             "text": message
                                          }]
                                     })
        return resp.status_code
    
    def image_to_group(
        self: object,
        groupID: int = 29184048534909958,
        _dir: str = "",
        message: str = ""
    ):
        #   get upload attachment ID and upload URI link
        url = { "upload_info":
                "https://xblmessaging.xboxlive.com/network/xbox/users/me/upload/png" }
        resp = self._get(url["upload_info"], headers={"x-xbl-contract-version": b"1"})

        url["uploadUri"] = resp.json()["uploadUri"]
        attachmentId = resp.json()["attachmentId"]

        # need to get image data

        name = tkinter.filedialog.askopenfilename(title="Choose an Image to Send",filetypes=[("PNG","*.png"), ("JPEG", "*.jpeg")]) if _dir == "" else _dir
        with open(name, "rb") as f:
            imgdata = f.read()
            width = todec(str(imgdata[0x10:0x14]).replace("b'", "").replace("'", "").replace("\\x", ""))
            height = todec(str(imgdata[0x14:0x18]).replace("b'", "").replace("'", "").replace("\\x", ""))
            print(len(imgdata))
            

        # upload image to attachment servers, after 200 response, attachmentId represents our image
        # and response header contains the MD5 hash for our image
        
        md5 = self.session.put(url["uploadUri"],data=imgdata,
                                         headers = {
                                            "x-xbl-contract-version": b"3",
                                            "Content-Type": "application/octet-stream",
                                            "x-ms-blob-type": "BlockBlob"
                                             }).headers["Content-MD5"]

        # send the uploaded image attachment into the group chat, with a fixed 500x500 size
        
        url["messageUri"] = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/groups/{groupID}/channels/0/messages"

        resp = self._post_json(url["messageUri"],
                               data = {
                                    "parts": [{

                                             "attachmentId": attachmentId,
                                             "contentType": "image",
                                             "filetype": "png",
                                             "hash": md5,
                                             "height": height,
                                             "sizeInBytes": len(imgdata),
                                             "version": 0,
                                             "width": width
                                    
                                        }]
                                   })
        if message == "":
            return resp.status_code
        return [self.message_to_group(groupID, message), resp.status_code]
    
    def gamertag_from_xuid(
        self: object, xuid:int
        ) -> str:
        url = f"https://profile.xboxlive.com/users/xuid({xuid})/profile/settings"
        return self.fetch(url)["settings"][3]["value"]

    def xuid_from_gamertag(
        self: object, gt: str
        ) -> str:
        url = f'https://profile.xboxlive.com/users/gt({gt})/profile/settings'
        return self.fetch(url)["id"]

    def report_user(
        self: object,
        xuid: int,
        _type: str = "UserContentGamertag",
        reason: str = "cheating"
        ) -> requests.Request:
        url = f"https://reputation.xboxlive.com/users/xuid({xuid})/feedback"
        type_check = [
                        "UserContentGamertag",              #   Player name or Gamertag
                        "UserContentGamerpic",              #   Player Picture
                        "CommsVoiceMessage",                #   Voice Communication
                        "UserContentPersonalInfo"           #   Bio or Location
                     ]
        reason_check = [
                        "sexuallyInappropirate",            #   Sexually inappropriate
                        "violenceOrGore",                   #   Violence or gore
                        "harassment",                       #   Harassment
                        "spamOrAdvertising",                #   Spam or advertising
                        "terroristOrViolentExtremist",      #   Terrorist or violent extremist content
                        #   v   "under Something Else"    v
                        "imminentHarmPersonsOrProperty",    #   Imminent harm to persons or property
                         "hateSpeech",                      #   Hate speech
                         "fraud",                           #   Fraud
                         "cheating",                        #   Cheating
                         "csam",                            #   Child sexual exploitation or abuse
                         "drugsOrAlcohol",                  #   Drugs or alcohol
                         "profanity",                       #   Profanity
                         "selfHarmOrSuicide",               #   Self-harm or suicide
                         "other"                            #   Other
                        ]
        if reason not in reason_check:
            raise InvalidReportReason("incorrect report reason. please see: {reason_check}")
        if _type not in type_check:
            raise InvalidReportType("incorrect report type. please see: {type_check}")
        response = self._post_json(url, data = { "evidenceId": "(null)",
                                            "feedbackContext": "User",
                                            "feedbackType": _type,
                                            "textReason": f"{reason};" },
                              headers={"x-xbl-contract-version": "101"})
        return response

    def get_user_presence(
        self:object,
        xuid:int,
        level:str="all",
        is_group:bool = False
    ):
        presence_level = [ "user", "device", "title", "all" ]
        if level not in presence_level:
            Exception(f"Incorrect presence level. Try using: {presence_level}")
        url = f"https://userpresence.xboxlive.com/users/xuid({xuid})/groups/People?level={level}" \
              if is_group else f"https://userpresence.xboxlive.com/users/xuid({xuid})?level={level}"
        return self.session.get(url, headers={"x-xbl-contract-version": b"3",
                                              "accept": "application/json",
                                              "accept-language": "en-US",
                                              "authorization": self.AUTHORIZATION_HEADER
                                              }).json()
    
    def message_user(
        self: object, xuid: str, _type: int, text:str
        )-> int:
        """
                Author: kek/bitwise/kyza

                Makes a POST JSON request, with a message packet

                Conversation has to already exist for the other end to recieve (returns 200 SUCCESS regardless)

        """
        url = f"https://xblmessaging.xboxlive.com/network/xbox/users/me/conversations/users/xuid({xuid})"
        """match _type:
            case 0:     #       TEXT
                response = self._post_json(url, data={
                                     "parts": [{
                                             "contentType": "text",
                                             "version": 0,
                                             "text": text
                                          }]
                                     })
            case 1:     #       GIF
                response = self._post_json(url, data={
                                    "parts": [{
                                            "contentType": "weblinkMedia",
                                            "mediaType": "gif",
                                            "mediaUrl": text,
                                            "text": text,
                                            "version": 0
                                            }]
                                    }, headers={"x-xbl-contract-version": b"1"})"""
        response = self._post_json(url, data = {
                                        "parts": [{

                                            "contentType": "text",
                                            "version": 0,
                                            "text": text

                                            }]
                                                })
        return response.status_code
    
    def fetch(self, url):
        settings = [
                'AppDisplayName',
                'DisplayPic',
                'Gamerscore',
                'Gamertag',
                'PublicGamerpic',
                'XboxOneRep',
                "RealNameOverride",
                "ModernGamertagSuffix"
            ]
        qs = '?settings=%s' % ','.join(settings)
        headers = {'x-xbl-contract-version': b'3',}
        resp = self._get(url + qs, headers=headers)
        if resp.status_code == 404:
            print("No such user\n")

            # example payload:
            # {
            #     "profileUsers": [{
            #         "id": "2533274812246958",
            #         "hostId": null,
            #         "settings": [{
            #             "id": "AppDisplayName",
            #             "value": "JoeAlcorn"
            #         }, {
            #             "id": "DisplayPic",
            #             "value": "http://compass.xbox.com/assets/70/52/7052948b-c50d-4850-baff-abbcad07b631.jpg?n=004.jpg"
            #         }, {
            #             "id": "Gamerscore",
            #             "value": "22786"
            #         }, {
            #             "id": "Gamertag",
            #             "value": "JoeAlcorn"
            #         }, {
            #             "id": "PublicGamerpic",
            #             "value": "http://images-eds.xboxlive.com/image?url=z951ykn43p4FqWbbFvR2Ec.8vbDhj8G2Xe7JngaTToBrrCmIEEXHC9UNrdJ6P7KIFXxmxGDtE9Vkd62rOpb7JcGvME9LzjeruYo3cC50qVYelz5LjucMJtB5xOqvr7WR"
            #         }, {
            #             "id": "XboxOneRep",
            #             "value": "GoodPlayer"
            #         }],
            #         "isSponsoredUser": false
            #     }]
            # }

        
        raw_json = resp.json()
        try:
            user = raw_json['profileUsers'][0]
        except KeyError:
            self._raise_for_status(resp)    #   rate limited
            print(raw_json)
        return user

def dumpXUID():
    xuidList = session.get("http://arkdedicated.com/xboxbanlist.txt").content.decode()
    return xuidList.replace("b'", "").replace("'", "").split()    

def listXUID():
    global count, api_timeout, pb, status, size, client, gt
    amount=int(tc.get())
    while(count < amount):
        pb.start()
        try:
            Lb.insert(count, "{0}: {1} ({2})\n".format(count+1, client.gamertag_from_xuid(gt[(len(gt)-1)-count]), gt[(len(gt)-1)-count]))
            time.sleep(0.5)
            #client.invite_to_group(29184405409504205, int(gt[(len(gt)-1)-count]))
            if api_timeout > 0 and api_timeout < 300:
                print("timeout lasted {0}s at index {1}\n".format(api_timeout, count))
                api_timeout = 0
            count=count+1
            status.config(text="Status: Working..")
        except GamertagNotFound:
            status.config(text="Status: API Timeout...elapsed for {0} seconds".format(api_timeout+1))
            api_timeout = api_timeout+1
            time.sleep(1)
            continue
            
    pb.stop()
    status.config(text="Status: Done!")
    size = Lb.size()

def threadlistXUID():
    threading.Thread(target=listXUID).start()

def copyselect():
    global Lb, status
    txt = ""
    for i in Lb.curselection():
       txt += "".join(Lb.get(i))
    pyperclip.copy(txt)
    status.config(text="Status: Copied selection into clipboard")
    
def copyall(_return: bool = False):
    global Lb, status, clipboard
    count = 0
    listt = []
    while(count < Lb.size()):
        listt.append(Lb.get(count))
        count=count+1
    if clipboard and _return == False:
        pyperclip.copy(str("".join(listt).rstrip("\n")))
        status.config(text="Status: Copied all to clipboard")
    return str("".join(listt).rstrip("\n"))

def clearAll():
    global Lb, status, count, api_timeout, tc, gt
    Lb.delete(0,END)
    status.config(text="Status: Idle")
    count = 0
    api_timeout = 0
    gt = dumpXUID()

def saveXUID():
    global status
    f = open("banlist.txt", "w")
    f.write(copyall(True))
    f.close()
    status.config(text="Status: Saved to banlist.txt")

def banCheckGT():
    global gamertag
    xuid: str = ""
    xuidList = session.get("http://arkdedicated.com/xboxbanlist.txt").content.decode()
    print(gamertag.get())
    try:
        xuid = client.xuid_from_gamertag(gamertag.get())
    except InvalidRequest:
        m = f"{gamertag.get()} does not exist"
        messagebox.showerror(title=m, message=m)
        return
    mb = messagebox.showerror if xuid in xuidList else messagebox.showinfo
    mb(title=f"{gamertag.get()} is {'not' if xuid not in xuidList else ''} banned",
       message=f"{gamertag.get()} is {'not' if xuid not in xuidList else ''} globally banned")

def banCheck(event):
    global top, gamertag
    new = Toplevel(top)
    new.title("ban check")
    #new.tk.call("wm", "iconphoto", top._w, PhotoImage(file='logo\\banlistlogo.ico'))
    new.geometry("250x100+{0}+{0}".format(int((top.winfo_screenwidth() / 2) - (400 / 2)), int((top.winfo_screenheight() / 2) - (300 / 2))))
    new.resizable(False, False)
    name = Label(new, text="Gamertag: ")
    name.place(x=95, y=15)
    gamertag = Entry(new)
    gamertag.place(x=65, y=35)
    c = Button(new, text="Check", command=banCheckGT)
    c.place(x=100, y=55)
    new.mainloop()

def threadselectClip():
    threading.Thread(target=selectClip).start()

def selectClip():
    global top, Lb, status
    gt = ""
    for i in Lb.curselection():
        if Lb.get(i)[1] != ":":
            gt = "".join(Lb.get(i)).split("{0}: ".format(Lb.get(i)[0:2]))[1].split("(", 1)[0].rstrip()
        else:
            gt = "".join(Lb.get(i)).split("{0}: ".format(Lb.get(i)[0]))[1].split("(", 1)[0].rstrip()
    if " " in gt:
        gt = gt.replace(" ", "%20")
    os.system(f"start \"\" https://www.xboxreplay.net/en-us/player/{gt}/clips")

def addAllGC():
    global gcID, gcIDc, status, client

    url = "https://xblmessaging.xboxlive.com/network/xbox/users/me/groups"
    resp = client._get(url, headers={"x-xbl-contract-version": b"1"})
    gName = resp.json()["groups"][0]["groupName"]
    if "CHEATERS GET BANNED" not in gName:
        client.change_group_name(29184405409504205, "CHEATERS GET BANNED")
    xid: list = []
    name = str(copyall(True).encode("utf-8")).replace("b", "").replace("'","").split("\\n")
    status.config(text="Status: Working...")
    if(gcIDc): # rate limit happened
        for gcIDc in range(len(name)):
            xuid = name[gcIDc][name.index("(")+1:name.index(")")]
            time.sleep(10)
            xid.append(xuid)
            #client.invite_to_group(gcID, xuid)
        gcIDc = 0
        return
    for idx, y in enumerate(name):
        xuid = int(y[y.index("(")+1:y.index(")")])
        time.sleep(5)
        try:
            client.invite_to_group(gcID, xuid)
            status.config(text=f"Status: Adding ({idx+1}/{len(name)})...")
        except InvalidRequest:
            print("rate limited...saving index and bailing...try again in 10 minutes")
            gcIDc = idx
            return
        print(f"{xuid} added to group chat...\n")
    status.config(text="Status: Done!")
    client.image_to_group(gcID, "C:\\Users\\User\\Desktop\\xbArkBanList\\logo\\banned.png", "Network Failure Message: You have been globally banned.")
    
def gcThread(event):
    threading.Thread(target=addAllGC).start()

if __name__ == "__main__":
    try:
        client = Client().auth(email, password)
    except AuthFailed:
        messagebox.showerror("Incorrect Email or Password", "email or password incorrect, force closing now.")
        time.sleep(1.5)
        exit()
    except IndexError:
        messagebox.showerror("Incorrect format", "please use the correct format specified (email:password), force closing\n\n")
        time.sleep(1.5)
        exit()
    session = requests.session()
    gt = dumpXUID()
    top = Tk()
    top.title("xbArkBanList - ||kek||")
    top.geometry("450x250+{0}+{1}".format(int((top.winfo_screenwidth() / 2) - (400 / 2)), int((top.winfo_screenheight() / 2) - (300 / 2))))
    top.resizable(False, False)
    top.grid_rowconfigure(0, weight=1)
    top.grid_columnconfigure(0, weight=3)
    Lb = Listbox(top,height=20, width=40, selectmode="multiple")
    Lb.grid(row=0, column=0, sticky="nsew")
    txt = Label(top, text="Amount to dump:")
    txt.place(x=350, y=10)
    tc = Spinbox(top, from_=1.0, to=float(len(gt)), width=10)
    tc.place(x=363,y=35)
    _call = Button(top, text="Dump", command=threadlistXUID)
    _call.place(x=374,y=55)
    saveA = Button(top, text="Save to File", command=saveXUID)
    saveA.place(x=362, y=75)
    clip = Button(top, text="Selected Clips", command=threadselectClip)
    clip.place(x=354, y=121)
    clr = Button(top, text="Clear All", command=clearAll)
    clr.place(x=368, y=147)
    
    _copys = Button(top, text="Copy Selected", command=copyselect)
    _copys.place(x=354, y=172)
    _copya = Button(top, text="Copy All", command=copyall)
    _copya.place(x=368, y=198)
    
    check = Label(top, text="Ban Check", fg="#00008B", font="Helvetica 8 bold")
    check.place(x=285, y=228)
    check.bind("<Button-1>", banCheck)
    
    pb = ttk.Progressbar(top, orient="horizontal", length=100, mode="indeterminate")
    pb.grid(row=3, column=2, sticky="n")

    gc = Label(top, text="Add all to Group Chat", fg="#006600", font="Helvetica 8 bold")
    gc.place(x=122, y=228)
    gc.bind("<Button-1>", gcThread)
    
    status = Label(top, text="Status: Idle")
    status.place(x=0, y=228)
    top.mainloop()
