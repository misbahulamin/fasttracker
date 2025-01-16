from firebase_admin import messaging

def send_push_notification(title, body, topic):
    print(title)
    print(body)
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        topic=topic,
    )
    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except Exception as e:
        print(f"An error occurred: {e}")