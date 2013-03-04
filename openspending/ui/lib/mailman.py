import requests


def subscribe(listserver, data):
    data = {
        'email': data['email'],
        'fullname': data['fullname'],
        'pw': '',
        'pw-conf': '',
        'language': 'en',
        'digest': '1',
        'email-button': 'Subscribe'
    }
    requests.post(listserver, data=data)
