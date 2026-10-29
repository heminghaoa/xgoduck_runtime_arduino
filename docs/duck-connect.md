# duck-connect：蓝牙配对、配网和 Bonjour

路线图第 2 阶段。duck-connect 是跑在 UNO Q Linux 上的常驻服务（systemd），在 App Lab 的容器外面，负责：

- 蓝牙低功耗（BLE）广播，手机用贴纸上的配对密钥和鸭子互相验证；
- 通过 NetworkManager 扫描、连接、保存 Wi-Fi，设置优先级；
- 用 avahi 广播 `_xgoduck._tcp`，手机在局域网里自动找到鸭子；
- 把手机的状态查询和控制转发给 XGO Duck App（`http://127.0.0.1:9527`）。

代码在 `connect/`，单元测试在 `connect/tests/`。**还没有在鸭子上运行过**，第一次上板时按下面的"上板测试"做。

## 安装

在板子上的 App 文件夹里运行：

```bash
sudo bash tools/install-connect.sh
```

脚本会：

- 在 `/opt/duck-connect` 建 Python 虚拟环境，装 `dbus-fast` 和 `cryptography`（需要联网）；
- 安装并启动 `duck-connect` 服务，开机自动运行；
- 把 XGO Duck App 设成开机自启（`arduino-app-cli properties set default`）。不想要的话加 `--no-autostart`。

再运行一次就是更新代码并重启服务。看日志：`journalctl -u duck-connect -f`。

服务以 root 运行：注册蓝牙 GATT 服务、改网络、写 `/etc/avahi/services/` 都需要 root。它只读取 App 的 `data/identity.json`，不会改它。

## 上板测试（2.5）

原计划用 iPhone 上的 nRF Connect 测试，但 nRF Connect 算不出配对需要的 HMAC，过不了配对这一步。所以改用桌面测试客户端 `connect/ble_client.py`，它在 Mac 上扮演手机：

```bash
pip install bleak cryptography
python connect/ble_client.py scan
python connect/ble_client.py --ssh arduino@<鸭子 IP> status
python connect/ble_client.py --ssh arduino@<鸭子 IP> wifi-scan
python connect/ble_client.py --ssh arduino@<鸭子 IP> wifi-connect "Wi-Fi 名字"
```

`--ssh` 通过 SSH 从板子上读配对密钥，也可以用 `--key` 直接给出密钥或贴纸上的整条 `xgoduck://` 链接。nRF Connect 仍然可以用来看广播和服务是否出现。

单元测试在 Mac 上就能跑：`cd connect && python -m pytest tests`（需要 pytest、cryptography、dbus-fast）。

## GATT

一个主服务，三个特征：

| 名称 | UUID | 属性 | 内容 |
| --- | --- | --- | --- |
| 服务 | `b5f1a6e0-6c1d-4f5e-9a37-2d0c8e4b7a10` | | 广播里带这个 UUID，名字是 "XGO Duck" |
| info | `b5f1a6e1-6c1d-4f5e-9a37-2d0c8e4b7a10` | read | JSON：`{"proto":1,"duck_id":"71577AA6","name":"XGO Duck"}`，不需要配对 |
| rx | `b5f1a6e2-6c1d-4f5e-9a37-2d0c8e4b7a10` | write、write without response | 手机发给鸭子的消息 |
| tx | `b5f1a6e3-6c1d-4f5e-9a37-2d0c8e4b7a10` | notify | 鸭子发给手机的消息 |

手机扫描时按服务 UUID 过滤。附近有几只鸭子时，连上后读 info，用编号找到贴纸上那只。

## 消息格式

每条消息是一个 JSON 对象，前面加 2 字节大端长度（最大 8192 字节）。这串字节按一次写入或通知能装下的大小（MTU − 3）切开发送，接收方拼回去。BLE 保证同一连接里按顺序送达。

- 手机发送时，每块不超过 `maximumWriteValueLength`。
- 鸭子发送时，按 BlueZ 报告的这条连接的 MTU 切块；没有 MTU 时用 hello 里的 `chunk`，再没有就用 20 字节。

请求带 `op`，最好带数字 `id`；回复带同一个 `id` 和 `ok`。不带 `id` 的请求成功时不回复，失败时回复里带 `op`，适合高频的 `command`。

```json
→ {"op":"wifi_scan","id":4}
← {"id":4,"ok":true,"networks":[...]}
← {"id":5,"ok":false,"error":"pair first"}
```

鸭子还会主动发事件（没有 `id`，带 `ev`）：

- `{"ev":"status", ...}`：hello 之后每 3 秒一次，内容同 `status` 的回复。
- `{"ev":"net", ...}`：一次 Wi-Fi 连接结束时，内容同 `net_status`，失败时 `state` 是 `failed`，带 `error`。

## 操作

| op | 需要配对 | 参数 | 回复 |
| --- | --- | --- | --- |
| `hello` | 否 | `chunk`：手机能收的最大块（可选） | `proto`、`duck_id`、`paired` |
| `challenge` | 否 | | `nonce`、`duck_id` |
| `pair` | 否 | `nonce`、`app_nonce`、`proof` | `duck_proof` |
| `status` | 否 | | `mode`、`enabled`、`servos`、`imu_ok`、`battery{voltage,percent,level}`、`phase`、`error` |
| `net_status` | 是 | | `state`、`ssid`、`ip`、`device` |
| `wifi_scan` | 是 | | `networks[]`：`ssid`、`signal`、`security`、`secure`、`active`、`saved` |
| `wifi_saved` | 是 | | `networks[]`：`ssid`、`name`、`priority` |
| `wifi_connect` | 是 | `ssid`、`password`（加密，开放网络不带）、`hidden` | 立即回复 `state: connecting`，结果用 `net` 事件发 |
| `wifi_forget` | 是 | `ssid` | `removed` |
| `wifi_priority` | 是 | `ssid`、`priority`（−999 到 999，大的优先） | `updated` |
| `mode` | 是 | `mode`：shadow、off、hold、policy | App 的回复 |
| `command` | 是 | `twist`、`head`、`mouth`，同 App 的 `/api/command` | |
| `action` | 是 | `name`：pick、roulade | App 的回复 |

遥控时手机要至少每 0.5 秒发一次 `command`：App 1 秒收不到命令就停止移动。连接断开时，duck-connect 立即发送零速度。

## 配对

用的就是贴纸上那个 22 位密钥 `k`，按 UTF-8 字节作为 HMAC-SHA256 的密钥，和网页配对（1.4）一样。双方各出一个随机数，互相证明自己知道密钥：

1. 手机发 `challenge`，鸭子回一次性的 `nonce`。
2. 手机生成 `app_nonce`，发送 `pair`：
   `proof = hex(HMAC(k, "xgoduck-ble-app:<duck_id>:<nonce>:<app_nonce>"))`
3. 鸭子验证通过后回复：
   `duck_proof = hex(HMAC(k, "xgoduck-ble-duck:<duck_id>:<nonce>:<app_nonce>"))`
   **手机必须检查 duck_proof**。对不上就说明对方不知道密钥（假鸭子），不要把 Wi-Fi 密码发给它。
4. 双方算出会话密钥：
   `session = HMAC(k, "xgoduck-ble-session:<duck_id>:<nonce>:<app_nonce>")`（32 字节）

配对只对这一条蓝牙连接有效，断开后要重新配对。每条连接最多错 5 次，之后要重新连接。

## Wi-Fi 密码加密

`wifi_connect` 的 `password` 是 `base64(12 字节随机 IV + AES-256-GCM 密文和 16 字节标签)`：

- 密钥是上面的 `session`；
- 附加数据（AAD）是 `"xgoduck-wifi:" + ssid` 的 UTF-8 字节，所以给一个网络加密的密码不能拿去连别的网络。

iOS 上用 CryptoKit 的 `AES.GCM.seal`，把 `nonce + ciphertext + tag` 拼起来再 base64。

## 已知限制

- 设计上一次只连一部手机。BlueZ 的通知会发给所有已订阅的手机。
- nmcli 连接时，Wi-Fi 密码会出现在 nmcli 的命令行参数里，几十毫秒后消失。板子上只有我们自己的程序，暂时接受。
- 广播里没有鸭子编号，要连上读 info 才知道。以后可以放进广播的厂商数据里。
- 连续重启 App 后单片机可能不发数据（见路线图"已知问题"），duck-connect 还不会自动处理。
