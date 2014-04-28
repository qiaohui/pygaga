# coding=gbk
from email.mime.text import MIMEText
import smtplib

class gmail (object):
    def __init__ (self, account, password, domain='gmail.com'):
        self.account="%s@%s" % (account, domain)
        self.password=password

    def send (self,to,title,content):
        server = smtplib.SMTP('smtp.gmail.com' )
        server.docmd("EHLO server" )
        server.starttls()
        server.login(self.account,self.password)

        msg = MIMEText(content,'html','GBK')
        msg['Content-Type']='text/html; charset="GBK"'
        msg['Subject'] = title
        msg['From'] = self.account
        for tomail in to.replace(',',' ').split():
            msg['To'] = tomail
            server.sendmail(self.account, tomail,msg.as_string())
        server.close()

if __name__ == "__main__":
    gmail("jcn.mail.sender", "jcn123456").send('huan.yu@langtaojin.com',
            '这是一封测试邮件',
            '''托尔斯泰 测试''')
