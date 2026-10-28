# 开发路线图（本 fork）

目标：把 XGO Duck 做成像成熟产品一样好用的机器人。用户用 iPhone App 扫鸭子身上的二维码就能配对、配网和控制，以后再给它加上摄像头、声音和 AI。

开发者继续用 Arduino App Lab 开发和部署鸭子上的程序。网页控制页保留，作为开发者调试工具。

## 现有硬件

| 有 | 还没有 |
| --- | --- |
| UNO Q（Wi-Fi、蓝牙 5.1）、扩展板 V1.1、15 个舵机、QMI8658 IMU、2S 18650 电池 | 摄像头、麦克风、喇叭、USB 集线器 |

所以**第 1 到第 3 阶段只用现有硬件**。需要摄像头和声音的功能都放在第 4 阶段。配网等状态的反馈，先由 App 通过蓝牙收到后显示在手机上，不依赖鸭子发出声音。

## 整体架构

```
iPhone App（SwiftUI）
 ├─ 首次：扫鸭子身上的二维码 → 蓝牙配对 → 把 Wi-Fi 发给鸭子
 ├─ 日常：Bonjour 自动发现鸭子 → WebSocket 实时控制
 └─ 没网时：蓝牙直接遥控、看电量
                │
鸭子（UNO Q）
 ├─ duck-connect：App Lab 之外的常驻服务（systemd，开机自启）
 │   蓝牙 GATT、Wi-Fi 配网（NetworkManager）、Bonjour 广播、配对验证
 │   通过 http://127.0.0.1:9527 调用下面这个 App
 └─ XGO Duck App（App Lab 部署，就是本仓库）
     走路控制、安全保护、网页调试页、以后的 AI
```

蓝牙和 Wi-Fi 配置放在 App Lab 外面，是因为 App Lab 的 Python 跑在容器里，可能访问不到蓝牙，也改不了系统网络。

## 第 0 阶段：已完成

- [x] 校准页每个关节的零位参考图（`20c2eef`）
- [x] 网页显示电池电压和低电量提醒（`189a992`），**待上板验证**舵机电压寄存器 0x3E
- [x] README 非官方改版说明，`.gitignore` 忽略 `.env`（`81c4b07`）

## 第 1 阶段：鸭子端基础（现有硬件）

App 和连接服务都要依赖这些功能，网页调试页也能直接受益。

- [ ] **1.1 配置保存**：动作幅度、平滑、IMU 滤波、鸭子名字写进 `data/settings.json`，开机自动恢复。接口为 `GET /api/settings`、`POST /api/settings`（只改传入的字段）和 `POST /api/settings/reset`。代码已写好（分支 `feat/config-persistence`），**待上板验证**。
- [ ] **1.2 设备身份**：首次启动时生成 8 位编号和 128 位配对密钥，保存在 `data/identity.json`（权限 600）。文件损坏时报错，不会悄悄重新生成，以免已打印的贴纸作废。`GET /api/identity` 只返回编号，不返回密钥。代码已写好，**待上板验证**。
- [ ] **1.3 贴纸二维码**：网页新增 Pairing 页，显示二维码并可以按 30mm 宽打印，内容格式为 `xgoduck://pair?id=<编号>&k=<密钥>&v=1`。点"I have saved the sticker"后（认领），鸭子不再通过网络显示密钥。弄丢贴纸时，删除 `data/identity.json` 重新生成。二维码由 Python 库 segno 生成，已加进 `requirements.txt`。代码已写好，**待上板验证**。以后可以考虑改成 https 通用链接，这样没装 App 的人扫码也能看到说明页。
- [ ] **1.4 访问令牌**：挑战-应答配对，`GET /api/pair/challenge` 取一次性随机数，`POST /api/pair` 提交 `HMAC-SHA256(密钥, "xgoduck-pair:<编号>:<随机数>")`，换取令牌。密钥不在网络上传输，鸭子只保存令牌的哈希（`data/access.json`）。FastAPI 中间件统一检查 `Authorization: Bearer`。默认免密；在 Pairing 页打开"Require pairing"后，未配对的客户端只能看状态。打开这个开关要求当前浏览器已配对，防止把自己锁在外面；文件损坏时按锁定处理。网页用自带的 SHA-256 和 HMAC（普通 HTTP 页面没有 `crypto.subtle`）。代码已写好，**待上板验证**。以后可以用 WebUI 自带的 TLS（`use_tls`）给令牌加密。
- [ ] **1.5 实时通道**：用 WebUI brick 自带的 Socket.IO（`/socket.io`）以 10 Hz 推送精简状态，接收 `command`、`mode`（只允许 shadow、off、hold、policy）和 `action`（pick、roulade）。WebUI 连接时拿不到令牌，所以客户端先发 `hello` 带令牌，之后每条消息都重新核对，被移除的设备立即失去控制权。正在遥控的客户端断开时立即停止移动。网页继续用 REST。iOS 端可以用 Socket.IO-Client-Swift。代码已写好，并用真实的 WebUI brick 源码测过，**待上板验证**。

## 第 2 阶段：连接服务 duck-connect（现有硬件）

- [ ] **2.1 蓝牙 GATT 服务**：设备信息、配对验证（基于配对密钥的挑战-应答）、Wi-Fi 列表、Wi-Fi 配置（加密写入）、配网状态通知、电量和模式通知、简单遥控。
- [ ] **2.2 Wi-Fi 管理**：通过 NetworkManager 扫描、连接、保存多个网络并设置优先级，包括家里的 Wi-Fi 和手机热点。
- [ ] **2.3 Bonjour 广播**：用 avahi 广播 `_xgoduck._tcp`，TXT 记录里带编号和端口。
- [ ] **2.4 安装脚本**：`tools/install-connect.sh` 安装 systemd 服务，做法和 `tools/router-2m.sh` 一样。
- [ ] **2.5 测试**：先用 iPhone 上的 nRF Connect 测完所有蓝牙功能，再开始写 App。

## 第 3 阶段：iOS App 最小版本（现有硬件）

新仓库 `xgoduck_ios`，用 SwiftUI 开发，需要真 iPhone 测试，模拟器测不了蓝牙。

- [ ] **3.1 扫码配对**：扫贴纸二维码，用 CoreBluetooth 连接对应的鸭子，再完成配对验证。
- [ ] **3.2 配网**：显示鸭子扫到的 Wi-Fi 列表，输入密码，提供"使用 iPhone 热点"选项，并显示配网进度。
- [ ] **3.3 日常控制**：通过 Bonjour 自动发现鸭子，用 WebSocket 控制。界面包括模式按钮、双摇杆、头和嘴的滑杆、Torque off、电量卡片和低电量提醒。
- [ ] **3.4 设置页**：动作幅度、平滑等参数，通过 1.1 的配置接口保存在鸭子上。
- [ ] **3.5 蓝牙备用控制**：没有 Wi-Fi 时用蓝牙遥控和查看电量。
- [ ] **3.6 TestFlight 分发**：需要加入苹果开发者计划。

## 第 4 阶段：摄像头、声音和 AI（需要新硬件）

硬件清单见下面的"待购硬件"。音视频部分参考上游的 `next-audio-video-tof` 分支，移植到当前代码上。

- [ ] **4.1 摄像头**：装在头部当眼睛，UVC 视频流显示到 App 里，先用 MJPEG，以后换 WebRTC。
- [ ] **4.2 看二维码配网**：给鸭子看手机上的 Wi-Fi 二维码，它自己连网。作为不装 App 时的备用方式。
- [ ] **4.3 语音提示**：鸭子开口说"我连上网了""电量低"等。
- [ ] **4.4 AI 灵魂**：语音识别 → 大模型 → 语音合成，在 App 里设置性格和声音，说话时动嘴、点头。
- [ ] **4.5 头部加重后**：如果走路明显变差，按新的头部质量重新训练走路模型。

## 第 5 阶段：产品化打磨

- [ ] AccessorySetupKit：靠近鸭子时系统弹出配对卡片（iOS 18 起）
- [ ] 远程更新、恢复出厂设置
- [ ] 可选：云端中转和账号，实现不在同一网络时也能控制
- [ ] 可选：Android App（鸭子端协议不用改）
- [ ] 公开销售前：联系 hello@xgorobot.com 取得商用授权，并确认技适、PSE 等认证

## 待上板确认

- [ ] 1910 舵机电压寄存器 0x3E 的读数和万用表实测是否一致
- [ ] App Lab 里的 Python 能写入哪个目录，并且重启和重新部署后不会丢（1.1、1.2 需要）
- [ ] App Lab 会不会按 `requirements.txt` 自动安装新加的 segno（1.3 需要）
- [ ] 板子上 WebUI brick 的版本是否提供 `ui.app`（FastAPI 实例），令牌中间件要挂在它上面（1.4 需要）
- [ ] 板子上是否有 BlueZ（`bluetoothctl`）、NetworkManager（`nmcli`）和 avahi
- [ ] 板子外的服务能否访问 `127.0.0.1:9527`
- [ ] 板子上是否有技适标志

## 待购硬件（Amazon.co.jp，2026-10-28 选定）

| 用途 | 商品 | 备注 |
| --- | --- | --- |
| 摄像头 | [InnoMaker 720P UVC，120°](https://www.amazon.co.jp/dp/B0CLRJZG8D) | 装在头部，镜头从眼眶穿出，眼孔要从 11.4mm 扩到约 14.5mm |
| 集线器 | [ELECOM U3HC-R030EBK](https://www.amazon.co.jp/dp/B0FT2DGWRN) | USB-C 直插，插头可旋转，21g |
| 声卡 | [USB 声卡模组（带麦克风）](https://www.amazon.co.jp/dp/B0CXJ2RTWJ) | 附带的 100mm 喇叭装不下，不用 |
| 喇叭 | [8Ω 2W，28×40mm，PH2.0 插头](https://www.amazon.co.jp/dp/B0D625YLZF) | 贴在机身侧面 |

头部只放摄像头。训练时头部质量只在 ±5% 内随机，大约 ±9g，其余部件都放在机身上。

## 原则

- 每一步都在现有基础上增加功能，不推翻已有的控制和安全逻辑。
- 所有遥控指令都要经过现有的控制器和超时保护。
- 密钥和 API key 只放在 `.env` 或板子上，绝不提交到仓库。
