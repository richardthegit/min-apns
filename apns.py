"""
Token-auth APNs support.

For setup:

    https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/establishing_a_token-based_connection_to_apns

Sending details:

    https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/sending_notification_requests_to_apns

Dependencies:

    pip install cryptography pyjwt "httpx[http2]"
"""
import time, uuid, jwt, httpx

# Load your Key (from the Apple certificates portal) into a string.
with open('path to your .p8 file') as f:
    key_string = f.read()

# Configuration.
CONF = {
    'url': 'https://api.push.apple.com',
    'key': key_string,
    'key_id': None, # ID of your key in the Apple portal
    'team_id': None, # ID of your Apple developer team
    'topic': None, # Your App ID
}

def get_jwt():
    """
    Return a new JWT to authorize the request. Apple won't accept any older than
    one hour, so we just create a new one for every request.
    """
    payload = {
        'iss': CONF['team_id'],
        'iat': time.time(),
    }
    return jwt.encode(payload = payload, key = CONF['key'], algorithm = 'ES256',
                      headers = {'kid': CONF['key_id']})


def send_message(token, message, badge_count = None, extra = None):
    """
    Send a message to an Apple device via APNs. Returns True on success,
    False if the token is bad, and raise an exception otherwise.

    NOTE: Apple want us to hold a persistent connection for notifications, but
    if your volume is low why bother.
    """
    # Check the doc link above for more configuration options.
    headers = {
        'apns-push-type': 'alert',
        'apns-id': str(uuid.uuid4()),
        'apns-topic': CONF['topic'],
        'authorization': f'bearer {get_jwt()}',
    }
    args = {
        'aps': {
            'alert': message,
            'badge': badge_count,
        }
    }
    # Application-specific data is just added to the top-level dictionary and
    # will be passed on to the recipient.
    if extra:
        args.update(extra)

    # Requests *must* use HTTP/2.
    with httpx.Client(http2 = True, headers = headers) as client:
        r = client.post(f'{CONF["url"]}/3/device/{token}', json = args)

    # Response doc:
    # https://developer.apple.com/documentation/usernotifications/setting_up_a_remote_notification_server/handling_notification_responses_from_apns
    if r.status_code == 200:
        # All good; the response will be empty in this case.
        return True

    if r.status_code == 410:
        # Inactive token; it happens.
        return False

    # Some other error - maybe the config is bad? Raise it.
    raise Exception(f'APNs push failed ({r.status_code}): {r.text}')


# Example usage
if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: <token>')
        exit(1)

    token = sys.argv[1]
    try:
        r = send_message(token, 'A test message', 99, {
            'some': 'test data',
        })
        print('Okay' if r else 'Bad token')
    except Exception as e:
        print(f'Big trouble: {e}')
