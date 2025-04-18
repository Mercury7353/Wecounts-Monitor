#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import sys
import time
from wechat_monitor import WeChatMonitor

def main():
    """测试注册功能"""
    print("Starting registration test...")
    
    # 初始化监控器
    monitor = WeChatMonitor()
    
    # 处理注册
    monitor.process_registrations()
    
    print("Registration test completed")

if __name__ == "__main__":
    main() 