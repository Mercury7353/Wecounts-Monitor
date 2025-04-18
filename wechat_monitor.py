#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import os
import random
import re
import smtplib
import time
import base64
import asyncio
import aiosmtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.utils import formataddr
import traceback
import pandas as pd
import requests
import schedule
from lxml import etree

from wechat_crawler import WeChatCrawler


class WeChatMonitor:
    def __init__(self, config_path="config.json"):
        """初始化微信监控器"""
        self.config = self.load_config(config_path)
        self.data_dir = "data"
        self.log_dir = "logs"
        self.ensure_dirs_exist()
        
        # 初始化微信爬虫
        self.crawler = WeChatCrawler()
        
        # 初始化已经检查过的文章URL缓存
        self.checked_articles_file = os.path.join(self.data_dir, "checked_articles.json")
        self.checked_articles = self.load_checked_articles()
        
        # 创建事件循环
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        self.logger("WeChatMonitor initialized")
        self.logger(f"Monitoring accounts: {', '.join(self.config['accounts'])}")
        self.logger(f"Watching for keywords: {', '.join(self.config['keywords'])}")
        self.logger(f"Email accounts configured: {len(self.config['email']['accounts'])}")

    def load_config(self, config_path):
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            exit(1)
    
    def ensure_dirs_exist(self):
        """确保所需目录存在"""
        for directory in [self.data_dir, self.log_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    def load_checked_articles(self):
        """加载已检查过的文章列表"""
        if os.path.exists(self.checked_articles_file):
            try:
                with open(self.checked_articles_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger(f"Error loading checked articles: {e}")
                return {}
        return {}
    
    def save_checked_articles(self):
        """保存已检查过的文章列表"""
        try:
            with open(self.checked_articles_file, 'w', encoding='utf-8') as f:
                json.dump(self.checked_articles, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger(f"Error saving checked articles: {e}")
    
    def logger(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        log_file = os.path.join(self.log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    
    def fetch_account_articles(self, account_name):
        """获取公众号最新文章列表"""
        self.logger(f"Fetching latest article for: {account_name}")
        
        # 使用微信爬虫获取最新一篇文章
        articles = self.crawler.get_articles(account_name, count=1)
        
        if articles:
            self.logger(f"Found {len(articles)} article for {account_name}")
            # 打印文章信息检查点
            for article in articles:
                self.logger(f"Article title: {article['title']}")
                self.logger(f"Article URL: {article['link']}")
                self.logger(f"Publish time: {article['create_time']}")
        else:
            self.logger(f"No articles found for {account_name}")
        
        return articles
    
    def fetch_article_content(self, article_url):
        """获取文章内容"""
        try:
            # 使用微信爬虫获取文章内容
            html_content = self.crawler.get_article_content(article_url)
            
            if not html_content:
                self.logger(f"Failed to fetch content for {article_url}")
                return None
            
            # 使用lxml解析文章内容
            html = etree.HTML(html_content)
            title = ''.join(html.xpath("//*[@id=\"activity-name\"]/text()")).strip()
            author = ''.join(html.xpath("//*[@id=\"js_name\"]/text()")).strip()
            content = '\n'.join(html.xpath("//*[@id=\"js_content\"]//text()")).strip()
            
            # 打印内容检查点
            self.logger(f"Parsed article title: {title}")
            self.logger(f"Parsed article author: {author}")
            self.logger(f"Content length: {len(content)} characters")
            
            # 打印内容摘要
            content_preview = content[:200] + "..." if len(content) > 200 else content
            self.logger(f"Content preview: {content_preview}")
            
            return {
                "title": title or "未获取到标题",
                "author": author or "未获取到作者",
                "content": content,
                "url": article_url
            }
        except Exception as e:
            self.logger(f"Error fetching article content: {e}")
            return None
    
    def check_keywords(self, text):
        """检查文本中是否包含关键词"""
        if not text:
            return []
        
        found_keywords = []
        for keyword in self.config['keywords']:
            if keyword in text:
                found_keywords.append(keyword)
        
        return found_keywords
    
    async def send_email_async(self, msg, recipient):
        """异步发送邮件，含失败自动切换备用邮箱机制"""
        email_config = self.config['email']
        
        # 尝试每个配置的邮箱账号
        for i, account in enumerate(email_config['accounts']):
            try:
                self.logger(f"Trying to send email to {recipient} using account {account['username']} (attempt {i+1}/{len(email_config['accounts'])})")
                
                # 更新邮件发件人
                msg.replace_header('From', formataddr(["WecountsMonitor", account['username']]))
                
                async with aiosmtplib.SMTP(
                    hostname=email_config['smtp_server'],
                    port=email_config['smtp_port'],
                    use_tls=True
                ) as smtp:
                    await smtp.login(account['username'], account['password'])
                    await smtp.send_message(msg)
                    self.logger(f"Email alert sent to {recipient} using {account['username']}")
                    return True
            except Exception as e:
                self.logger(f"Failed to send email to {recipient} using {account['username']}: {e}")
                if i < len(email_config['accounts']) - 1:
                    self.logger(f"Trying next email account...")
                    continue
                else:
                    self.logger(f"All email accounts failed when sending to {recipient}")
                    return False
        
        return False

    async def send_email_alert_async(self, article_data, keywords):
        """异步发送邮件提醒到所有接收者"""
        try:
            email_config = self.config['email']
            recipients = email_config['recipients']
            
            # 默认使用第一个账号作为发件人
            default_username = email_config['accounts'][0]['username']
            
            # 读取图片文件
            try:
                with open("img.jpg", "rb") as img_file:
                    img_data = img_file.read()
                image_found = True
            except Exception as e:
                self.logger(f"Error reading image file: {e}")
                image_found = False
            
            # 创建所有邮件的任务
            tasks = []
            for recipient in recipients:
                msg = MIMEMultipart()
                msg['From'] = formataddr(["WecountsMonitor", default_username])
                msg['To'] = recipient
                msg['Subject'] = f"关键词提醒: {', '.join(keywords)} - {article_data['title']}"
                
                # 如果图片存在，添加图片作为内联附件
                img_cid = None
                if image_found:
                    img = MIMEImage(img_data)
                    img.add_header('Content-ID', '<attached_image>')
                    img.add_header('Content-Disposition', 'inline', filename='img.jpg')
                    msg.attach(img)
                    img_cid = 'attached_image'
                
                # 构建邮件内容
                html_content = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                        .header {{ background-color: #f8f9fa; padding: 10px; border-bottom: 1px solid #e9ecef; }}
                        .footer {{ margin-top: 20px; font-size: 12px; color: #6c757d; }}
                        .highlight {{ background-color: yellow; font-weight: bold; }}
                        .image-container {{ text-align: center; margin: 20px 0; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>{article_data['title']}</h2>
                            <p>作者: {article_data['author']}</p>
                        </div>
                        <div class="content">
                            <p>在文章《{article_data['title']}》中发现关键词: <span class="highlight">{', '.join(keywords)}</span></p>
                            <p>文章链接: <a href="{article_data['url']}">{article_data['url']}</a></p>
                            <p>监控时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                            <p>有疑问扫码咨询</p>
                            {f'<div class="image-container"><img src="cid:{img_cid}" alt="附图" style="max-width:100%;"></div>' if img_cid else ''}
                        </div>
                        <div class="footer">
                            <p>此邮件由WecountsMonitor自动发送，请勿回复。</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(html_content, 'html', 'utf-8'))
                
                # 创建发送任务
                task = asyncio.create_task(self.send_email_async(msg, recipient))
                tasks.append(task)
            
            # 等待所有邮件发送完成
            results = await asyncio.gather(*tasks)
            success_count = sum(1 for r in results if r)
            self.logger(f"Email sending completed. Success: {success_count}/{len(recipients)}")
            return success_count > 0
            
        except Exception as e:
            self.logger(f"Failed to send emails: {e}")
            return False

    def send_email_alert(self, article_data, keywords):
        """同步发送邮件提醒的包装函数"""
        return self.loop.run_until_complete(self.send_email_alert_async(article_data, keywords))
    
    def process_registrations(self):
        """处理注册CSV文件，更新收件人列表并发送欢迎邮件"""
        self.logger("Processing registration file...")
        reg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reg.csv")
        
        if not os.path.exists(reg_file):
            self.logger(f"Registration file not found: {reg_file}")
            return
        
        try:
            # 读取CSV文件
            df = pd.read_csv(reg_file)
            if '邮箱' not in df.columns:
                self.logger("CSV file does not contain '邮箱' column")
                return
            
            # 清理邮箱数据：去除空值和无效值
            emails = df['邮箱'].dropna().tolist()
            valid_emails = [email.strip() for email in emails if email.strip() and '@' in email]
            
            if not valid_emails:
                self.logger("No valid emails found in registration file")
                return
            
            # 加载当前配置
            current_recipients = set(self.config['email']['recipients'])
            
            # 找出新添加的邮箱
            new_emails = [email for email in valid_emails if email not in current_recipients]
            
            if not new_emails:
                self.logger("No new emails to add")
                return
            
            # 更新配置
            self.config['email']['recipients'] = list(current_recipients.union(set(new_emails)))
            
            # 保存更新后的配置
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            
            self.logger(f"Added {len(new_emails)} new emails to recipients list")
            
            # 发送欢迎邮件给新添加的收件人
            self.send_welcome_emails(new_emails)
            
        except Exception as e:
            self.logger(f"Error processing registration file: {e}")
    
    async def send_welcome_email_async(self, recipient):
        """异步发送欢迎邮件"""
        try:
            email_config = self.config['email']
            default_username = email_config['accounts'][0]['username']
            
            # 读取图片文件
            try:
                img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "img.jpg")
                with open(img_path, "rb") as img_file:
                    img_data = img_file.read()
                image_found = True
            except Exception as e:
                self.logger(f"Error reading image file: {e}")
                image_found = False
            
            msg = MIMEMultipart()
            msg['From'] = formataddr(["WecountsMonitor", default_username])
            msg['To'] = recipient
            msg['Subject'] = "WecountsMonitor注册成功"
            
            # 如果图片存在，添加图片作为内联附件
            img_cid = None
            if image_found:
                img = MIMEImage(img_data)
                img.add_header('Content-ID', '<attached_image>')
                img.add_header('Content-Disposition', 'inline', filename='img.jpg')
                msg.attach(img)
                img_cid = 'attached_image'
            
            # 构建邮件内容
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #f8f9fa; padding: 10px; border-bottom: 1px solid #e9ecef; }}
                    .content {{ padding: 20px 0; }}
                    .footer {{ margin-top: 20px; font-size: 12px; color: #6c757d; }}
                    .image-container {{ text-align: center; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>WecountsMonitor注册成功</h2>
                    </div>
                    <div class="content">
                        <p>致 RUCer，</p>
                        <p><strong>收到该邮件证明您的邮箱已加入WecountsMonitor的提醒列表。</strong></p>
                        <p>欢迎大家使用免费开源的WecountsMonitor，该服务主要是为了方便大家火速报名形势与政策讲座 & 志愿活动，帮助高年级同学顺利毕业写的！</p>
                        <p>🌟 如果任何bug / 接收不到邮件 / 改进建议，欢迎扫描附件二维码加入反馈群进行吐槽。如果有其他开发建议或insights，也欢迎加入"WecountsMonitor"群聊进行讨论～ 🌟</p>
                        <p>来自WecountsMonitor开发组</p>
                        {f'<div class="image-container"><img src="cid:{img_cid}" alt="二维码" style="max-width:100%;"></div>' if img_cid else ''}
                    </div>
                    <div class="footer">
                        <p>（此邮件由WecountsMonitor自动发送，请勿回复）</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_content, 'html', 'utf-8'))
            
            # 使用带备用邮箱机制的发送函数
            return await self.send_email_async(msg, recipient)
            
        except Exception as e:
            self.logger(f"Failed to create welcome email for {recipient}: {e}")
            return False

    def send_welcome_emails(self, recipients):
        """发送欢迎邮件给新注册的用户"""
        if not recipients:
            return
        
        self.logger(f"Sending welcome emails to {len(recipients)} new recipients")
        
        try:
            # 创建异步任务
            async def send_all_welcome_emails():
                tasks = [self.send_welcome_email_async(recipient) for recipient in recipients]
                results = await asyncio.gather(*tasks)
                success_count = sum(1 for r in results if r)
                self.logger(f"Welcome email sending completed. Success: {success_count}/{len(recipients)}")
                return success_count > 0
            
            # 运行异步任务
            return self.loop.run_until_complete(send_all_welcome_emails())
            
        except Exception as e:
            self.logger(f"Failed to send welcome emails: {e}")
            return False
    
    def process_articles(self, account_name, articles):
        """处理文章列表，检查新文章中的关键词"""
        for article in articles:
            article_url = article['link']
            
            # 跳过已经检查过的文章
            if article_url in self.checked_articles:
                self.logger(f"Skipping already checked article: {article['title']}")
                continue
            
            self.logger(f"Checking new article: {article['title']} - {article_url}")
            
            # 检查文章发布时间，如果超过8小时则跳过
            try:
                # 将字符串时间转换为datetime对象
                publish_time = datetime.strptime(article['create_time'], "%Y-%m-%d %H:%M:%S")
                current_time = datetime.now()
                time_diff = current_time - publish_time
                
                if time_diff.total_seconds() > 8 * 3600:  # 8小时 = 8 * 3600秒
                    self.logger(f"Skipping article older than 8 hours: {article['title']}")
                    # 标记为已检查，避免下次再处理
                    self.checked_articles[article_url] = {
                        "title": article['title'],
                        "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "skipped": "too old"
                    }
                    continue
            except Exception as e:
                self.logger(f"Error parsing article time: {e}, using current time instead")
                # 如果时间解析失败，使用当前时间作为发布时间，继续处理文章
                publish_time = datetime.now()
            
            # 获取文章内容
            article_data = self.fetch_article_content(article_url)
            if not article_data:
                self.logger(f"Failed to fetch content for {article_url}")
                continue
            
            # 标记为已检查
            self.checked_articles[article_url] = {
                "title": article['title'],
                "check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # 检查标题和内容中是否包含关键词
            title_keywords = self.check_keywords(article_data['title'])
            content_keywords = self.check_keywords(article_data['content'])
            all_keywords = list(set(title_keywords + content_keywords))
            
            if all_keywords:
                self.logger(f"Found keywords in article: {', '.join(all_keywords)}")
                self.send_email_alert(article_data, all_keywords)
            else:
                self.logger(f"No keywords found in article")
    
    def run_once(self):
        """运行一次监控流程"""
        self.logger("Starting monitoring process...")
        
        for account in self.config['accounts']:
            try:
                self.logger(f"Fetching latest article for: {account}")
                # 获取公众号最新文章
                articles = self.fetch_account_articles(account)
                if articles:
                    self.process_articles(account, articles)
                else:
                    self.logger(f"No articles found for {account}")
                
                # 每处理完一个公众号后休眠1分钟
                if account != self.config['accounts'][-1]:  # 如果不是最后一个账号
                    self.logger(f"Sleeping for 1 minutes after processing {account}")
                    time.sleep(30)  # 休眠1分钟
                
            except Exception as e:
                traceback.print_exc()
                self.logger(f"Error processing account {account}: {e}")
        
        # 保存检查过的文章记录
        self.save_checked_articles()
        self.logger("Monitoring process completed")

    def start_scheduler(self):
        """启动定时任务"""
        interval_hours = self.config.get('interval_hours', 1)
        self.logger(f"Scheduling monitoring every {interval_hours} hour(s)")
        self.process_registrations()
        # 立即运行一次
        self.run_once()
        
        # 立即处理注册
        
        
        # 设置定时任务
        schedule.every(interval_hours).hours.do(self.run_once)
        
        # 设置注册处理每3小时运行一次
        schedule.every(3).hours.do(self.process_registrations)
        
        while True:
            schedule.run_pending()
            time.sleep(30)  # 每分钟检查一次是否有待执行的任务

    def run(self):
        """主运行循环"""
        self.logger("Starting monitoring service...")
        
        # 初始化计数器，用于跟踪运行的次数，每3次处理一次注册（即每3小时）
        run_count = 0
        
        while True:
            try:
                self.run_once()
                
                # 每3次运行（3小时）处理一次注册
                run_count += 1
                if run_count >= 3:
                    self.logger("Processing registrations after 3 hours")
                    self.process_registrations()
                    run_count = 0
                
                next_run = datetime.now() + timedelta(hours=self.config['interval_hours'])
                self.logger(f"Next run scheduled at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 分钟级别的睡眠，便于更快响应中断
                for _ in range(self.config['interval_hours'] * 30):
                    time.sleep(30)
                    
            except KeyboardInterrupt:
                self.logger("Received keyboard interrupt, shutting down...")
                break
            except Exception as e:
                self.logger(f"Error in main loop: {e}")
                self.logger("Waiting 2 minutes before retry...")
                time.sleep(120)  # 5分钟后重试


def main():
    """主函数"""
    print("WeChatMonitor starting...")
    monitor = WeChatMonitor()
    #monitor.process_registrations()
    monitor.start_scheduler()


if __name__ == "__main__":
    main() 