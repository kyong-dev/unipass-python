# /package/customs_id_number.py
import configparser
from typing import List
import requests
import xml.etree.ElementTree as ET
from utils.mobile_number_format import addHyphen, removeHyphen

config = configparser.ConfigParser()
config.read('unipass.ini')
UNIPASS_API_KEY = config['DEFAULT']['UNIPASS_API_KEY']


def api_request(customsIdNumber: str, name: str, phone: str):
    errors = []
    if len(name) < 2:
        errors.append('납세의무자 성명은(는) 필수입력입니다.')
    if len(phone) < 9:
        errors.append('납세의무자 휴대전화번호은(는) 필수입력입니다.')
    if len(errors) > 0:
        return {'success': False, 'errors': errors}
    requestURL = f'https://unipass.customs.go.kr:38010/ext/rest/persEcmQry/retrievePersEcm?crkyCn={UNIPASS_API_KEY}&persEcm={customsIdNumber}&pltxNm={name}&cralTelno={removeHyphen(phone)}'
    try:
        response = requests.get(requestURL)
    except Exception as e:
        str(e)
    response_element = ET.fromstring(response.text)
    resultString = response_element.find('tCnt').text
    errors = []
    if resultString == '1':
        return {'success': True, 'errors': []}
    else:
        for reason in response_element.findall(
                'persEcmQryRtnErrInfoVo'):
            errors.append(reason.find('errMsgCn').text)
        return {'success': False, 'errors': errors}


def validate(customsIdNumber: str, names: List[str], phones: List[str]):

    finalName = names[0]
    finalPhone = phones[0]
    if len(customsIdNumber) != 13:
        return {'success': False, 'customsIdNumber': customsIdNumber, 'name': finalName, 'phone': addHyphen(finalPhone), 'errors': ['납세의무자 개인통관고유부호가 존재하지 않습니다.']}
    result = {}
    for name in names:
        for phone in phones:
            result = api_request(customsIdNumber, name, phone)
            if result['success']:
                return {'success': True, 'customsIdNumber': customsIdNumber, 'name': name, 'phone': addHyphen(phone), 'errors': result['errors']}
            else:
                # 입력된 성명 중에 개인통관부호에 등록된 명의와 일치된 이름이 없을 경우 가장 우선으로 입력된 2글자 이상인 이름이 finalName으로 결정된다.
                if '성명' not in ' '.join(result['errors']):
                    finalName = name
                # 입력된 번호 중에 개인통관부호에 등록된 번호와 일치된 휴대전화번호가 없을 경우 가장 우선으로 입력된 01로 시작하는 휴대폰 번호가 finalPhone으로 결정된다.
                if '휴대전화번호' not in ' '.join(result['errors']) or (not finalPhone.startswith('01') and phone.startswith('01')):
                    finalPhone = phone

    result = api_request(customsIdNumber, finalName, finalPhone)
    return {'success': False, 'customsIdNumber': customsIdNumber, 'name': finalName, 'phone': addHyphen(finalPhone), 'errors': result['errors']}


print(validate("P123", ['공경섭'], ['010-6878-3628']))
print(validate("P220003429872", ['', '공경섭'], ['010-878-3628', '']))
print(validate("P220003429872", ['고경저', '김진숙', ''], [
      '0503-123-1234', '010-4524-7873', '0503-123-1234']))
print(validate("P220003429872", ['김진', '김진숙'], ['010-4524-7875']))
print(validate("P220003429872", ['김진'], [
      '010-4524-7873', '0503-123-1234', '010-4524-7875']))
