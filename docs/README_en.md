<h1 align="center">Glink</h1>

<p align="center"><strong>Remotely control a Windows PC using Android devices on the same LAN</strong></p>

<p align="center">
  Languages:
  <a href="../README.md">简体中文</a> |
  <a href="./docs/README_en.md">English</a>
</p>



## Quick Start

### Requirements

+ Python 3.11+
+ Windows
+ The PC and the Android phone must be on the same LAN / Wi-Fi



### Steps

```sh
# 1. Create a virtual environment
python -m venv .venv

# 2. Activate the virtual environment
.venv\Scripts\activate

# 3. Upgrade pip (optional)
python -m pip install --upgrade pip

# 4. Install the build tool
pip install build

# 5. Build
python -m build

# 6. Install
pip install -e .

# 7. Run
glink-server
```



### Connect Your Phone

1. Make sure the Android phone and the Windows PC are connected to the same Wi-Fi.
2. Install and run the [Glink client](https://gitee.com/clfundev/glink-android) on your phone.
3. The client will automatically discover servers on the LAN and list it on the home page. Tap to connect and view/control the PC.



### Security Notice

> [!CAUTION]
>
> Currently, communication between the client and the server is unencrypted (plaintext). DO NOT use it on untrusted networks!