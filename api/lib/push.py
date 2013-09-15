from apnsclient import Session, Message, APNs


def notify(token, message=None, badge_num=0, name=None, item_type=None):

    con = Session.new_connection(
        ("gateway.push.apple.com",
         2195),
        cert_file="cert.pem",
        passphrase="this is the queue push key")

    message_packet = Message(
        token,
        alert=message,
        badge=badge_num,
        user=name,
        sound="default",
        itemType=item_type)

    srv = APNs(con)
    res = srv.send(message_packet)

    # Check failures. Check codes in APNs reference docs.
    for token, reason in res.failed.items():
        code, errmsg = reason

    if res.needs_retry():
        retry_message = res.retry()
        res = srv.send(retry_message)
