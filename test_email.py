#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import os
from datetime import datetime

from wechat_monitor import WeChatMonitor

def test_email_sending():
    """测试邮件发送功能"""
    print("开始测试邮件发送功能...")
    
    # 初始化微信监控器
    monitor = WeChatMonitor()
    
    # 创建一个模拟的文章数据，包含关键词
    mock_article = {
        "title": "关于2025年形式政策的通知",
        "author": "测试公众号",
        "content": "这是一个测试文章，包含关键词'形势政策'和'加分'。本文仅用于测试邮件发送功能。",
        "url": "https://example.com/test-article"
    }
    
    # 检查文章中的关键词
    title_keywords = monitor.check_keywords(mock_article["title"])
    content_keywords = monitor.check_keywords(mock_article["content"])
    all_keywords = list(set(title_keywords + content_keywords))
    
    print(f"在测试文章中发现关键词: {', '.join(all_keywords)}")
    
    # 发送邮件提醒
    if all_keywords:
        result = monitor.send_email_alert(mock_article, all_keywords)
        if result:
            print("邮件发送成功！请检查您的邮箱。")
        else:
            print("邮件发送失败，请检查邮件配置。")
    else:
        print("未找到关键词，不发送邮件。")

if __name__ == "__main__":
    test_email_sending() 