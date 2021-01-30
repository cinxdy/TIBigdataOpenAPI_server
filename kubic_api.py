from flask import request
from datetime import datetime
from dateutil.relativedelta import relativedelta
from kubic_user import *
from elasticsearch import Elasticsearch
import esAccount as esAcc

def makeRequest():
    kubic_request = {
        'serviceKey': request.args.get('serviceKey') ,
        'numOfCnt': request.args.get('numOfCnt', 100),
        'rank': request.args.get('rank', 1),
        'keyword': request.args.get('keyword',""),
        'keyInTitle': request.args.get('keyInTitle',""),
        'keyInBody': request.args.get('keyInBody',""),
        'writer': request.args.get('writer',""),
        'startDate': request.args.get('startDate',(datetime.today()-relativedelta(years=1)).strftime("%Y%m%d")),
        'endDate': request.args.get('endDate',datetime.today().strftime("%Y%m%d")),
        'institution': request.args.get('institution',""),
        'category': request.args.get('category',""),
    }

    if kubic_request['serviceKey']=="":
        resultCode = 400
        resultMSG = 'Bad Request: No serviceKey'
    elif kubic_request['keyword']=="" and kubic_request['keyInTitle'] == "":
        resultCode = 400
        resultMSG = 'Bad Request: No KeyInTitle'
    else:
        resultCode = 200
        resultMSG = 'OK'
    
    print("request:",kubic_request,'resultCode:',resultCode)
    return kubic_request, resultCode, resultMSG

def esSearch(request):
    #Connect to DB
    ES = Elasticsearch([{'host': esAcc.host, 'port': esAcc.port}], http_auth=(esAcc.id, esAcc.password))

    # ES = Elasticsearch(host = host, port=9200)

    # print(ES.cat.indices())

    #search the document
#     response = ES.search(index=index, body={    
#     "size": request['numOfCnt'],
#     "query": {
#       "multi_match": {
#         "query": request['keyword'],
#         "fields": ["post_title", "post_body", "fileName", "fileContent"]
#       }
#     }
#   })

    query = {
    "size": request['numOfCnt'],
    "query": {
        "bool": {
            "must":[
                {"wildcard": {"post_title": "*"+request['keyInTitle']+"*" }},
            ],
            # "sort": [{"post_date": {"order" : "desc" #오름차순: asc, 내림차순: desc 
            # }}]    
            "filter": {"range": { "post_date": { "gte": request['startDate'], "lte": request['endDate'] }}}
        },
    }
    }

    if not request['keyInBody'] == "":
        query['query']['bool']['must'].append({"wildcard": {"post_body": "*"+request['keyInBody']+"*" }})
    if not request['writer'] == "":
        query['query']['bool']['must'].append({"wildcard": {"post_writer": "*"+request['writer']+"*" }})
    if not request['institution'] == "":
        query['query']['bool']['must'].append({"wildcard": {"published_institution": "*"+request['institution']+"*" }})
    
    print("query: ",query)
    response = ES.search(index=esAcc.index, body=query)

    print("response:",str(response)[:30])
    return response
    
def raiseError(response, resultCode, resultMSG):
    response['header']['resultCode'] = resultCode
    response['header']['resultMSG'] = resultMSG
    return response

def makeResponse(request, resultCode, resultMSG):
    response = {
            "header":{
                "resultCode": resultCode,
                "resultMSG": resultMSG,
            },
            "body": {}
        }
    if resultCode > 300:
        return response

    if not verification(request['serviceKey']):
        return raiseError(response, 401,'Unauthorized')

    try: data = esSearch(request)
    except Exception as e:
        print(e)
        return raiseError(response, 502,'Bad Gateway')
    # print('origin data from ES:',data)

    if data['hits']['total']['value']==0:
        return raiseError(response, 204,'No Content')

    response['body'] = {
                "numOfCnt": request['numOfCnt'],
                "totalCnt": data['hits']['total']['value'],
                "rank" : request['rank'],
                "contents":[{
                    "title": content['_source']['post_title'],
                    "body": content['_source']['post_body'],
                    #' '.join(content['_source']['post_body'].split())[:400],
                    "writer": content['_source']['post_writer'],
                    "date": content['_source']['post_date'] if 'post_date' in content['_source'] else None,
                    "institution": content['_source']['published_institution'],
                    "institutionURL": content['_source']['published_institution_url'],
                    "category": content['_source']['top_category'],
                    "fileURL": content['_source']['file_download_url'] if 'file_download_url' in content['_source'].keys() else None,
                    "fileName": content['_source']['file_name'] if 'file_name' in content['_source'].keys() else None,
                    #content['_source']['file_download_url'],
                }for content in data['hits']['hits']]
                }
    print("response:", response['header']['resultCode'])
    return response
