<h1 align="center">Glink</h1>

<p align="center"><strong>局域网内 Android 设备远程控制 Windows 电脑</strong></p>

<p align="center">
  Languages:
  <a href="./README.md">简体中文</a> |
  <a href="./docs/README_en.md">English</a>
</p>



## 快速开始

### 环境要求

+ Python 3.11+
+ Windows 系统
+ 电脑与 Android 手机处于同一局域网/Wi-Fi



### 运行步骤

```sh
# 1. 创建虚拟环境
python -m venv .venv
# 2. 激活虚拟环境
.venv\Scripts\activate
# 3. 升级pip（可选）
python -m pip install --upgrade pip
# 4. 安装构建工具
pip install build
# 5. 构建
python -m build
# 6. 安装
pip install -e .
# 7. 运行
glink-server
```



### 连接手机

1. 确保 Android 手机与 Windows 电脑连接同一 Wi-Fi
2. 在手机上安装并运行 [Glink 客户端](https://gitee.com/clfundev/glink-android)
3. 客户端会自动发现局域网内的服务端并展示在首页，点击连接即可查看和操控电脑



### 安全提示

> [!CAUTION]
>
> 目前客户端与服务端之间是明文通信，请勿在不可信、不安全的网络下使用！！！
