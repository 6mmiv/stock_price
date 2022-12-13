import requests
import pandas as pd
import time
import datetime

def get_today_kospi_pure_buying_quantity() :
    startday = str(datetime.datetime.now().date()).replace('-', '')
    endday = str(datetime.datetime.now().date()).replace('-', '')


    gen_req_url = 'https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'

    query_str_parms = {'locale' : 'ko_KR',
                       'inqTpCd' : '2',
                       'trdVolVal' : '2',
                       'askBid' : '3',
                       'mktId' : 'STK', # 코스피 : STK, 코스닥 : KSQ, 코넥스 : KNX, 전부다 : ALL
                       'etf' : 'EF',
                       'etn' : 'EN',
                       'elw' : 'EW',
                       'strtDd' : startday,
                       'endDd' : endday,
                       'money' : '3',
                       'csvxls_isNo' : 'false',
                       'name' : 'fileDown',
                       'url': 'dbms/MDC/STAT/standard/MDCSTAT02202'}

    header = {'accept' : 'text/plain, */*; q=0.01',
              'accept-encoding' : 'gzip, deflate, br',
              'accept-language' : 'ko-KR,ko;q=0.9',
              'content-length' : '193',
              'content-type' : 'application/x-www-form-urlencoded; charset=UTF-8',
              'cookie' : '__smVisitorID=5KhkUoGOGDX; JSESSIONID=dIW57DY81aBll8S3EnyehxiAhrlB5LIUGg0zf0zFPXY5uanLbl6wzm71rLBuvcTP.bWRjX2RvbWFpbi9tZGNvd2FwMi1tZGNhcHAxMQ==',
              'origin' : 'https://data.krx.co.kr',
              'referer' : 'https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201',
              'sec-ch-ua' : '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
              'sec-ch-ua-mobile' : '?0',
              'sec-ch-ua-platform' : '"Windows"',
              'sec-fetch-dest' : 'empty',
              'sec-fetch-mode' : 'cors',
              'sec-fetch-site' : 'same-origin',
              'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
              'x-requested-with' : 'XMLHttpRequest'
              }

    r = requests.get(gen_req_url, query_str_parms, headers = header)

    gen_req_url = 'https://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'

    form_data = {'code' : r.content}

    r = requests.post(gen_req_url, form_data, headers = header)

    data1 = str(r.content).split('n')
    data1 = data1[1].split('"')

    return 'kospi    ' + str(data1[1]) + '    ' + str(data1[3]) + '    ' + str(data1[5]) + '    ' + str(data1[7]) + '    ' + str(data1[9])

def get_today_kosdaq_pure_buying_quantity() :
    startday = str(datetime.datetime.now().date()).replace('-', '')
    endday = str(datetime.datetime.now().date()).replace('-', '')

    gen_req_url = 'https://data.krx.co.kr/comm/fileDn/GenerateOTP/generate.cmd'

    query_str_parms = {'locale' : 'ko_KR',
                       'inqTpCd' : '2',
                       'trdVolVal' : '2',
                       'askBid' : '3',
                       'mktId' : 'KSQ', # 코스피 : STK, 코스닥 : KSQ, 코넥스 : KNX, 전부다 : ALL
                       'etf' : 'EF',
                       'etn' : 'EN',
                       'elw' : 'EW',
                       'strtDd' : startday,
                       'endDd' : endday,
                       'money' : '3',
                       'csvxls_isNo' : 'false',
                       'name' : 'fileDown',
                       'url': 'dbms/MDC/STAT/standard/MDCSTAT02202'}

    header = {'accept' : 'text/plain, */*; q=0.01',
              'accept-encoding' : 'gzip, deflate, br',
              'accept-language' : 'ko-KR,ko;q=0.9',
              'content-length' : '150',
              'content-type' : 'application/x-www-form-urlencoded; charset=UTF-8',
              'cookie' : '__smVisitorID=5KhkUoGOGDX; JSESSIONID=dIW57DY81aBll8S3EnyehxiAhrlB5LIUGg0zf0zFPXY5uanLbl6wzm71rLBuvcTP.bWRjX2RvbWFpbi9tZGNvd2FwMi1tZGNhcHAxMQ==',
              'origin' : 'https://data.krx.co.kr',
              'referer' : 'https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201',
              'sec-ch-ua' : '"Google Chrome";v="105", "Not)A;Brand";v="8", "Chromium";v="105"',
              'sec-ch-ua-mobile' : '?0',
              'sec-ch-ua-platform' : '"Windows"',
              'sec-fetch-dest' : 'empty',
              'sec-fetch-mode' : 'cors',
              'sec-fetch-site' : 'same-origin',
              'user-agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
              'x-requested-with' : 'XMLHttpRequest'
              }

    r = requests.get(gen_req_url, query_str_parms, headers = header)

    gen_req_url = 'https://data.krx.co.kr/comm/fileDn/download_csv/download.cmd'

    form_data = {'code' : r.content}

    r = requests.post(gen_req_url, form_data, headers = header)

    data1 = str(r.content).split('n')
    data1 = data1[1].split('"')

    return 'kosdaq    ' + str(data1[1]) + '    ' + str(data1[3]) + '    ' + str(data1[5]) + '    ' + str(data1[7]) + '    ' + str(data1[9])

