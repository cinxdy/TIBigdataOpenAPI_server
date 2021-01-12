
from pymongo import MongoClient
from secrets import token_urlsafe 
from passlib.hash import pbkdf2_sha512
from datetime import datetime
#import logging

client = MongoClient('localhost',27017)
db = client.user

def getEmail():
    email_logined = "cindy@handong.edu"
    #app.logger.debug('getEmail():'+'email_logined:'+email_logined)
    return email_logined


email_logined = getEmail()

def countAPI():
    count = db.apiUser.count({"user_email": email_logined})
    return count

def generateCode():
    key = token_urlsafe(16)
    hashKey = pbkdf2_sha512.hash(key)
    #app.logger.debug('generateCode:'+"key"+key+"hashKey"+hashKey)
    return key, hashKey

def registerAPI(app_name, app_purpose):
    today = datetime.today()
    key, hashKey = generateCode()

    post = {
        "app_name" : app_name,
        "app_purpose" : app_purpose,
        "user_email" : email_logined,
        "veri_code" : hashKey,
        "reporting_date" : {
            'year': int(today.year),
            'month': int(today.month),
            'date': int(today.day)
            },
        "expiration_date" : {
            'year': int(today.year)+1,
            'month': int(today.month),
            'date': int(today.day)

            },
        "traffic":0
    }

    db.apiUser.insert_one(post)
    #app.logger.debug('registerAPI():'+'email_logined:'+email_logined+'post:'+str(post)+'key:'+key)
    return key

def reissue(_id):
    now = datetime.datetime.now().date()
    key, hashKey = generateCode()

    post = {
        "veri_code" : hashKey,
        "reporting_date" : {
            'year': int(now.strftime('%y')),
            'month': int(now.strftime('%m')),
            'date': int(now.strftime('%d'))
            },
        "expiration_date" : {
            'year': int(now.strftime('%y'))+1,
            'month': int(now.strftime('%m')),
            'date': int(now.strftime('%d'))
            },
    }

    db.apiUser.update({'_id':_id}, post)
    #app.logger.debug('reissue():'+'_id:'+_id+'post:'+str(post)+'key:'+key)
    return key

def getInform():
    doc = db.apiUser.find({"user_email": email_logined})
    #app.logger.debug('getInform():'+'email_logined:'+email_logined+'doc:'+str(doc))
    return doc

def findHash():
    doc = getInform()
    hashKeyList = [item['veri_code'] for item in doc]
    #app.logger.debug('findHash():'+'email_logined:'+email_logined+'hashKeyList:'+str(hashKeyList))
    return hashKeyList

def verification(serviceKey, hashKeyList=findHash()):
    for hashKey in hashKeyList:
        if(pbkdf2_sha512.verify(serviceKey, hashKey)):
            return True
    return False

