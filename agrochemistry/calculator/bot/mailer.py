from django.core.mail import EmailMessage


def send_mail(text: str, sent_from: str, to: str, subject='', attach_path=''):
    email = EmailMessage(
        subject,
        text,
        sent_from,
        to,
    )
    if attach_path:
        email.attach_file(attach_path)
    email.send()
