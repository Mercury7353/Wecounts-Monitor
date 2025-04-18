#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime

def load_config(config_path="config.json"):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_gmail_connection():
    """测试Gmail连接"""
    print("开始测试Gmail连接...")
    
    # 加载配置
    config = load_config()
    if not config:
        print("配置加载失败，请检查config.json文件")
        return False
    
    email_config = config.get('email', {})
    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port')
    username = email_config.get('username')
    password = email_config.get('password')
    recipients = email_config.get('recipients', [])
    
    print(f"SMTP服务器: {smtp_server}")
    print(f"SMTP端口: {smtp_port}")
    print(f"用户名: {username}")
    print(f"密码: {'*' * len(password) if password else 'Not set'}")
    print(f"收件人: {', '.join(recipients)}")
    
    # 创建测试邮件
    msg = MIMEMultipart()
    msg['From'] = formataddr(["微信监控系统", username])
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = "测试邮件 - Gmail连接测试"
    
    body = f"""
    这是一封测试邮件，用于验证Gmail邮件发送功能是否正常。
    
    如果您收到这封邮件，说明Gmail配置正确。
    
    时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    """
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print("尝试连接到Gmail SMTP服务器...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("连接成功，启用TLS...")
        server.starttls()
        print(f"尝试登录 ({username})...")
        server.login(username, password)
        print("登录成功，尝试发送邮件...")
        server.sendmail(username, recipients, msg.as_string())
        print("邮件发送成功！")
        server.quit()
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Gmail邮件发送测试 ===")
    result = test_gmail_connection()
    
    if result:
        print("\n测试成功！Gmail邮件配置正确。")
    else:
        print("\n测试失败。请检查以下几点:")
        print("1. 确保您已开启Gmail的两步验证")
        print("2. 确保您使用的是正确的应用专用密码")
        print("3. 确保您的网络环境允许连接到Gmail SMTP服务器") 