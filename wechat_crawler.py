#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import json
import os
import random
import re
import time
from datetime import datetime
import traceback

import pandas as pd
import requests


class WeChatCrawler:
    def __init__(self, cookie_path="cookies.json", fakeid_path="account_fakeids.json"):
        """初始化微信爬虫"""
        self.base_url = "https://mp.weixin.qq.com/cgi-bin/appmsg"
        self.user_agent_list = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
            'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0',
            'Mozilla/5.0 (Windows NT 6.1; rv:2.0.1) Gecko/20100101 Firefox/4.0.1',
            "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.75 Mobile Safari/537.36",
        ]
        self.cookies = self.load_cookies(cookie_path)
        self.token = self.cookies.get('token', '1910835749')  # 默认值，实际中需要从cookie中获取
        
        # 加载公众号fakeid映射
        self.account_fakeids = self.load_account_fakeids(fakeid_path)
        
        # 数据目录
        self.data_dir = "data"
        
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def load_cookies(self, cookie_path):
        """加载Cookie文件"""
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cookies: {e}")
                return self.get_default_cookies()
        else:
            print(f"Cookie file {cookie_path} not found, using default cookies.")
            return self.get_default_cookies()
    
    def load_account_fakeids(self, fakeid_path):
        """加载公众号fakeid映射文件"""
        if os.path.exists(fakeid_path):
            try:
                with open(fakeid_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("accounts", {})
            except Exception as e:
                print(f"Error loading account fakeids: {e}")
                return {}
        else:
            print(f"Account fakeid file {fakeid_path} not found, using empty mapping.")
            return {}
    
    def get_default_cookies(self):
        """获取默认Cookie（仅作示例，实际使用需要真实的登录态Cookie）"""
        return {
            "cookie_string": "",  # 实际使用时需要填入有效的Cookie字符串
            "token": "1910835749"  # 实际使用时需要填入有效的token
        }
    
    def get_cookie_string(self):
        """获取Cookie字符串"""
        return self.cookies.get('cookie_string', '')
    
    def get_account_fakeid(self, account_name):
        """从映射文件获取公众号的fakeid"""
        # 直接从映射文件中查找
        fakeid = self.account_fakeids.get(account_name)
        
        if fakeid:
            print(f"Found fakeid for {account_name}: {fakeid}")
            return fakeid
        else:
            print(f"Warning: No fakeid found for {account_name} in account_fakeids.json")
            print(f"Please add {account_name}'s fakeid to account_fakeids.json")
            return None
    
    def get_headers(self):
        """获取请求头"""
        return {
            "Cookie": self.get_cookie_string(),
            "User-Agent": random.choice(self.user_agent_list)
        }
    
    def get_articles(self, account_name, count=1):
        """获取公众号最新文章
        
        Args:
            account_name: 公众号名称
            count: 获取的文章数量，默认为1（最新一篇）
            
        Returns:
            list: 文章列表，每篇文章包含title, link, create_time
        """
        print(f"Getting latest {count} article(s) for {account_name}...")
        
        # 获取公众号的fakeid
        fakeid = self.get_account_fakeid(account_name)
        if not fakeid:
            print(f"Failed to get fakeid for {account_name}")
            return []
        
        # 确保count是整数
        try:
            count = int(count)
        except (TypeError, ValueError):
            print(f"Invalid count value: {count}, using default value 1")
            count = 1
        
        # 构造请求参数
        params = {
            "token": self.token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": "1",
            "action": "list_ex",
            "begin": "0",
            "count": str(count),  # 转换为字符串
            "query": "",
            "fakeid": fakeid,
            "type": "9",
        }
        
        # 打印请求参数（不包含敏感信息）
        print(f"Request parameters: {params}")
        
        try:
            # 发送请求
            response = requests.get(
                self.base_url, 
                headers=self.get_headers(), 
                params=params,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                print(f"Failed to get articles, status code: {response.status_code}")
                print(f"Response content: {response.text}")
                return []
            
            # 解析响应数据
            content_json = response.json()
            print(f"API Response status: {content_json.get('base_resp', {}).get('err_msg', 'unknown')}")
            
            # 检查错误码
            if content_json.get('base_resp', {}).get('ret') == 200002:
                print("Token may be expired or invalid. Please update your cookies.")
                return []
            
            if 'app_msg_list' not in content_json:
                print(f"No articles found for {account_name}, response: {content_json}")
                return []
            
            # 提取文章信息
            articles = []
            for item in content_json["app_msg_list"]:
                # 格式化发布时间
                t = time.localtime(item["create_time"])
                create_time = time.strftime("%Y-%m-%d %H:%M:%S", t)
                
                articles.append({
                    "title": item["title"],
                    "link": item["link"],
                    "create_time": create_time
                })
                
                # 打印检查点
                print(f"Found article: {item['title']} - {create_time}")
                print(f"URL: {item['link']}")
            
            return articles
            
        except Exception as e:
            print(f"Error getting articles for {account_name}: {e}")
            print(f"Full error details: {traceback.format_exc()}")
            return []
    
    def save_articles_to_csv(self, account_name, articles):
        """保存文章到CSV文件"""
        if not articles:
            return
        
        file_path = os.path.join(self.data_dir, f"{account_name}_articles.csv")
        
        # 准备DataFrame
        df = pd.DataFrame(articles)
        
        # 保存到CSV
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"Saved {len(articles)} articles to {file_path}")
    
    def get_article_content(self, url):
        """获取文章内容"""
        try:
            headers = {"User-Agent": random.choice(self.user_agent_list)}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                print(f"Failed to get article content, status code: {response.status_code}")
                return None
            
            # 打印检查点
            print(f"Successfully fetched article content, content length: {len(response.content)} bytes")
            
            # 返回HTML内容
            return response.content.decode('utf-8', errors='ignore')
        except Exception as e:
            print(f"Error getting article content: {e}")
            return None


# 使用示例
if __name__ == "__main__":
    crawler = WeChatCrawler()
    
    # 测试获取公众号文章
    account_name = "人民日报"
    articles = crawler.get_articles(account_name, count=1)
    
    if articles:
        print(f"Got {len(articles)} article(s) from {account_name}:")
        for i, article in enumerate(articles, 1):
            print(f"  {i}. {article['title']} - {article['create_time']}")
            print(f"     {article['link']}")
            
            # 获取并显示文章内容摘要
            content = crawler.get_article_content(article['link'])
            if content:
                # 提取文本内容并显示前200个字符
                text = re.sub(r'<.*?>', '', content)
                text = re.sub(r'\s+', ' ', text)
                print(f"  Content preview: {text[:200]}...")
        
        # 保存文章
        crawler.save_articles_to_csv(account_name, articles)
    else:
        print(f"No articles found for {account_name}") 