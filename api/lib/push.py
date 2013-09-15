from apnsclient import Session, Message, APNs


def change_badge_number(user):
    push(user.device_token, None, user.badge_num, None, None)


def alert_and_change_badge_number(from_user, to_user, item_type):

    from_user_name = from_user.fullname
    message = "{} shared a {} with you".format(from_user_name,
                                               item_type)

    push(to_user.device_token,
         message,
         to_user.badge_num,
         from_user_name,
         item_type)


def push(token, message, badge_num, name, item_type):
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
