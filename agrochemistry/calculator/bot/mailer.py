import smtplib


class Mailer:
    def __init__(self, gmail, password):
        self.gmail = gmail
        self.gmail_password = password

    def send_mail(self, to, text):
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(self.gmail, self.gmail_password)
            server.sendmail(self.gmail, to, text)
            server.close()
        except:
            pass
