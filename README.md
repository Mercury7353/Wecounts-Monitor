# 微信公众号监控系统

这是一个可以定时爬取指定微信公众号文章并根据关键词发送邮件提醒的应用程序。

## 功能特点

- 定时爬取指定的微信公众号文章
- 检查文章中是否包含预设的关键词
- 发现关键词时通过邮件发送提醒
- 支持多个公众号监控
- 支持多个关键词检测
- 邮件提醒中包含文章链接，方便直接查看

## 使用前准备

### 1. 安装依赖

首先，确保您已安装Python。然后在项目目录下运行以下命令来安装所需的依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置微信Cookie

由于微信对爬虫有严格限制，您需要提供有效的微信公众平台登录Cookie才能正常使用此应用程序。

- 登录 [微信公众平台](https://mp.weixin.qq.com/)
- 登录成功后，使用浏览器开发者工具获取Cookie
- 将获取到的Cookie填入 `cookies.json` 文件中
- 参考教程：[如何获取微信Cookie](https://blog.csdn.net/jingyoushui/article/details/131613819)

### 3. 配置公众号fakeid映射

编辑 `account_fakeids.json` 文件，设置要监控的公众号及其对应的fakeid：

```json
{
    "accounts": {
        "公众号1": "对应的fakeid",
        "公众号2": "对应的fakeid",
        "人民日报": "MjM5MDIzNzQxMA=="
    }
}
```

获取fakeid的方法：
- 登录微信公众平台
- 在公众号搜索页面搜索目标公众号
- 使用浏览器开发者工具查看网络请求，从请求参数中找到fakeid

### 4. 配置监控参数

编辑 `config.json` 文件，设置要监控的公众号、关键词和邮件信息：

```json
{
    "accounts": [
        "公众号1",
        "公众号2"
    ],
    "keywords": [
        "关键词1",
        "关键词2"
    ],
    "email": {
        "smtp_server": "smtp服务器地址",
        "smtp_port": 端口号,
        "username": "邮箱账号",
        "password": "邮箱密码或授权码",
        "recipient": "接收提醒的邮箱"
    },
    "interval_hours": 监控间隔小时数
}
```

#### SMTP 邮件设置

- **smtp_server**: 您的邮件服务提供商的SMTP服务器地址。例如，Gmail的SMTP服务器地址是 `smtp.gmail.com`。
- **smtp_port**: SMTP服务器的端口号。通常，SSL端口为465，TLS端口为587。
- **username**: 您的邮箱账号。
- **password**: 您的邮箱密码或授权码。注意：某些邮箱服务需要使用应用专用密码或授权码。
- **recipient**: 接收提醒的邮箱地址。

确保您的邮箱开启了SMTP服务和授权码登录。具体设置方法可以参考您的邮箱服务提供商的帮助文档。

## 运行程序

在项目目录下运行以下命令启动程序：

```bash
python wechat_monitor.py
```

程序启动后，会立即执行一次监控任务，然后按照配置的时间间隔定期执行。每次只会爬取各公众号的最新一篇文章，每处理完一个公众号后会休眠2分钟以避免被封禁。

## 文件说明

- `wechat_monitor.py` - 主程序
- `wechat_crawler.py` - 微信爬虫模块
- `config.json` - 配置文件，设置监控的公众号和关键词
- `account_fakeids.json` - 公众号与fakeid的映射关系
- `cookies.json` - 微信Cookie配置
- `requirements.txt` - 依赖列表
- `data/` - 数据存储目录
- `logs/` - 日志存储目录

## 注意事项

1. 本程序仅用于学习和研究，请勿用于任何商业用途。
2. 过于频繁的请求可能导致IP被微信封禁，系统已设置每爬取一个公众号后休眠2分钟。
3. 由于微信的限制，Cookie和fakeid可能会定期失效，需要定期更新。