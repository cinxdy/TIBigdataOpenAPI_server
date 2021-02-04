
from pymongo import MongoClient
from bson.objectid import ObjectId
from secrets import token_urlsafe 
from passlib.hash import pbkdf2_sha512
from datetime import datetime
from dateutil.relativedelta import relativedelta
#import logging

client = MongoClient('localhost',27017)
db = client.user
trafficLimit = 3

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
        "reporting_date" : today,
        "expiration_date" : (today+relativedelta(years=1)),
        "traffic":0
    }

    db.apiUser.insert_one(post)
    #app.logger.debug('registerAPI():'+'email_logined:'+email_logined+'post:'+str(post)+'key:'+key)
    return key

def reissue(_id):
    today = datetime.today()
    key, hashKey = generateCode()

    post = {
        "app_name" : "testtesttest",
        "veri_code" : hashKey,
        "reporting_date" : today,
        "expiration_date" : (today+relativedelta(years=1)),
        }

    db.apiUser.update({"_id": ObjectId(_id)}, {'$set': post})
    print("reissue> app_name", post['app_name'],"key", key)
    #app.logger.debug('reissue():'+'_id:'+_id+'post:'+str(post)+'key:'+key)
    return key

def getDocByEmail():
    docList = db.apiUser.find({"user_email": email_logined})
    #app.logger.debug('getInform():'+'email_logined:'+email_logined+'doc:'+str(doc))
    return docList

def getDocById(_id):
    doc = db.apiUser.find_one({"_id": ObjectId(_id)})
    #app.logger.debug('getInform():'+'email_logined:'+email_logined+'doc:'+str(doc))
    return doc

def findHash():
    doc = getDocByEmail()
    hashKeyList = [item['veri_code'] for item in doc]
    #app.logger.debug('findHash():'+'email_logined:'+email_logined+'hashKeyList:'+str(hashKeyList))
    return hashKeyList

def verification(serviceKey):
    hashKeyList = findHash()
    for hashKey in hashKeyList:
        if(pbkdf2_sha512.verify(serviceKey, hashKey)):
            doc = db.apiUser.find_one({"veri_code": hashKey})
            return doc['_id']
    return False

def limitTraffic(_id):
    doc = getDocById(_id)
    if doc['traffic'] > trafficLimit:
        return False
    
    post = {"traffic" : doc['traffic']+1}
    db.apiUser.update({"_id": ObjectId(_id)}, {'$set':post})
    doc = getDocById(_id)
    print(doc)
    return True

def limitDate(_id):
    doc = getDocById(_id)
    if doc['expiration_date'] < datetime.today():
        return False
    return True