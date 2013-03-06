from pylons import config

import requests


def subscribe_lists(listnames, data):
    errors = []
    for listname in listnames:
        url = config.get('openspending.subscribe_{0}'.format(listname), False)
        if url and data.get('subscribe_{0}'.format(listname)):
            if not subscribe(url, data):
                errors.append(listname)
    return errors


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
    try:
        response = requests.post(listserver, data=data)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException:
        return False
