#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import subprocess
import time
import sys
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('daemon.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def run_monitor():
    """运行监控程序，并在崩溃时自动重启"""
    while True:
        try:
            logging.info("Starting WeChatMonitor...")
            
            # 启动监控程序
            process = subprocess.Popen([sys.executable, 'wechat_monitor.py'],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
            
            # 等待程序结束
            stdout, stderr = process.communicate()
            
            # 如果程序异常退出
            if process.returncode != 0:
                logging.error(f"WeChatMonitor crashed with error code {process.returncode}")
                logging.error(f"Error output: {stderr.decode('utf-8')}")
                logging.info("Restarting in 30 seconds...")
                time.sleep(30)  # 等待30秒后重启
            else:
                logging.info("WeChatMonitor exited normally")
                
        except Exception as e:
            logging.error(f"Daemon error: {e}")
            logging.info("Restarting in 30 seconds...")
            time.sleep(30)

if __name__ == "__main__":
    run_monitor() 