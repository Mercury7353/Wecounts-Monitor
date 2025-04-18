#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import os
import smtplib
import traceback
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

def load_config(config_path="config.json"):
    """加载配置文件"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_email_connection():
    """测试邮件连接"""
    print("开始测试邮件连接...")
    
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
    recipient = email_config.get('recipient')
    
    print(f"检查点 1: 配置信息")
    print(f"SMTP服务器: {smtp_server}")
    print(f"SMTP端口: {smtp_port}")
    print(f"用户名: {username}")
    print(f"密码: {'*' * len(password) if password else 'Not set'}")
    print(f"收件人: {recipient}")
    
    if not all([smtp_server, smtp_port, username, password, recipient]):
        print("检查点 2: 配置不完整，请检查config.json中的email部分")
        return False
    
    # 创建测试邮件
    msg = MIMEMultipart()
    msg['From'] = formataddr(["微信监控系统", username])
    msg['To'] = recipient
    msg['Subject'] = "测试邮件 - 微信监控系统"
    
    body = """
    这是一封测试邮件，用于验证微信监控系统的邮件发送功能是否正常。
    
    如果您收到这封邮件，说明邮件配置正确。
    
    时间: {}
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        print(f"检查点 3: 尝试连接到SMTP服务器 {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        print("检查点 4: 连接成功")
        
        print("检查点 5: 尝试启用TLS加密")
        server.starttls()
        print("检查点 6: TLS加密启用成功")
        
        print(f"检查点 7: 尝试登录 ({username})")
        server.login(username, password)
        print("检查点 8: 登录成功")
        
        print(f"检查点 9: 尝试发送邮件到 {recipient}")
        server.sendmail(username, recipient, msg.as_string())
        print("检查点 10: 邮件发送成功")
        
        server.quit()
        print("检查点 11: SMTP连接已关闭")
        return True
    except Exception as e:
        print(f"邮件发送失败: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        return False

def test_qq_email_specific():
    """专门测试QQ邮箱的连接"""
    print("\n开始专门测试QQ邮箱连接...")
    
    # 加载配置
    config = load_config()
    if not config:
        return False
    
    email_config = config.get('email', {})
    username = email_config.get('username')
    password = email_config.get('password')
    recipient = email_config.get('recipient')
    
    # QQ邮箱特定设置
    smtp_server = "smtp.qq.com"
    
    # 尝试不同的端口
    ports_to_try = [587, 465, 25]
    
    for smtp_port in ports_to_try:
        print(f"\n尝试QQ邮箱端口: {smtp_port}")
        
        try:
            if smtp_port == 465:
                print("使用SSL连接")
                server = smtplib.SMTP_SSL(smtp_server, smtp_port)
            else:
                print("使用普通连接")
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
            
            print(f"尝试登录 ({username})")
            server.login(username, password)
            print("登录成功")
            
            # 创建测试邮件
            msg = MIMEMultipart()
            msg['From'] = formataddr(["微信监控系统", username])
            msg['To'] = recipient
            msg['Subject'] = f"测试邮件 - 端口{smtp_port}"
            
            body = f"""
            这是一封测试邮件，使用端口 {smtp_port}。
            
            时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            print(f"尝试发送邮件到 {recipient}")
            server.sendmail(username, recipient, msg.as_string())
            print(f"使用端口 {smtp_port} 发送邮件成功!")
            
            server.quit()
            return True
        except Exception as e:
            print(f"使用端口 {smtp_port} 失败: {str(e)}")
    
    print("所有端口都尝试失败")
    return False

if __name__ == "__main__":
    print("=== 邮件发送测试 ===")
    result = test_email_connection()
    
    if not result:
        print("\n=== 尝试QQ邮箱特定测试 ===")
        qq_result = test_qq_email_specific()
        
        if qq_result:
            print("\n建议更新config.json中的SMTP端口设置") 