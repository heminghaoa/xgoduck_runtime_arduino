// Language layer for Luwu's pages. The pages stay in English; this file only changes what is shown.
// Loaded first on each page: an observer translates text as the page parses and updates it.
// Text it doesn't know stays in English, so a new string in an update can't break anything.
// Each entry is [English, Chinese, Japanese]; {name} stands for a value inside the sentence.
(()=>{
const LANGS={en:'English',zh:'中文',ja:'日本語'},HTML_LANG={en:'en',zh:'zh-CN',ja:'ja'},KEY='xgoduck-lang';
const D=[
[' · enabled',' · 扭矩开',' · トルクオン'],
[' · torque off',' · 扭矩关',' · トルクオフ'],
['{m} · enabled','{m} · 扭矩开','{m} · トルクオン'],
['{m} · torque off','{m} · 扭矩关','{m} · トルクオフ'],
['{name} · returning to walk after 0.4 s','{name} · 0.4 秒后回到行走','{name} · 0.4 秒後に歩行へ戻ります'],
['{name} {left} s left','{name}，还剩 {left} 秒','{name} 残り {left} 秒'],
['{state} · {checked}/254 checked · {found} found (partial results)','{state} · 已检查 {checked}/254 · 找到 {found} 个（部分结果）','{state} · {checked}/254 確認済み · {found} 個検出（途中までの結果）'],
['Action scale','动作幅度','動作スケール'],
['Action settings','动作设置','動作設定'],
['Action settings ·','动作设置 ·','動作設定 ·'],
['Adjust movement size and smoothing. Each walking mode keeps its own settings.','调整动作幅度和平滑度。每种行走模式各自保存设置。','動きの大きさとスムージングを調整します。歩行モードごとに設定を保存します。'],
['After a fall, the robot gets up and returns to walking.','摔倒后，鸭子会自己起身并回到行走。','転倒すると、ダックは自分で起き上がって歩行に戻ります。'],
['All servos are unloaded. Scan for servos, then select an ID.','所有舵机已卸力。先扫描舵机，再选择一个 ID。','すべてのサーボを脱力しました。サーボをスキャンして ID を選んでください。'],
['All servos are unloaded. Turn one joint by hand, then set its center.','所有舵机已卸力。用手转好一个关节，再设置它的中位。','すべてのサーボを脱力しました。関節を 1 つ手で回してから、中心を設定してください。'],
['All-servo voltage / overcurrent protection','全部舵机的电压 / 过流保护','全サーボの電圧・過電流保護'],
['Bridge {mbps} Mbps · state age {age} ms','Bridge {mbps} Mbps · 状态延迟 {age} ms','Bridge {mbps} Mbps · 状態の経過 {age} ms'],
['Broadcast sent · {a} A','已广播 · {a} A','ブロードキャスト送信済み · {a} A'],
['Broadcast sent · voltage / overcurrent off','已广播 · 电压 / 过流保护：关','ブロードキャスト送信済み · 電圧・過電流保護：オフ'],
['Broadcast sent · voltage / overcurrent on','已广播 · 电压 / 过流保护：开','ブロードキャスト送信済み · 電圧・過電流保護：オン'],
['Broadcasting protection settings to all servos…','正在向所有舵机广播保护设置…','全サーボに保護設定をブロードキャストしています…'],
['calibrate','标定','キャリブレーション'],
['Calibrate IMU','标定 IMU','IMU をキャリブレーション'],
['Calibrating… {p}%','正在标定… {p}%','キャリブレーション中… {p}%'],
['Calibration','标定','キャリブレーション'],
['Calibration · XGO Duck','标定 · XGO Duck','キャリブレーション · XGO Duck'],
['Calibration active','标定中','キャリブレーション中'],
['Calibration closed','标定已关闭','キャリブレーション終了'],
['Calibration closed. All servos are unloaded.','标定已关闭，所有舵机已卸力。','キャリブレーションを終了しました。すべてのサーボは脱力しています。'],
['Calibration could not be loaded. Calibrate again or reset it.','无法载入标定。请重新标定或重置。','キャリブレーションを読み込めません。やり直すかリセットしてください。'],
['Centering…','正在归中…','中心合わせ中…'],
['Change ID','修改 ID','ID を変更'],
['Change ID to','把 ID 改为','ID の変更先'],
['Changing ID {id} to {to}…','正在把 ID {id} 改为 {to}…','ID {id} を {to} に変更しています…'],
['Connecting…','正在连接…','接続中…'],
['Control','控制','コントロール'],
['Controls ready.','控制已就绪。','操作できます。'],
['Current action','当前动作','現在の動作'],
['default pose','默认姿态','デフォルト姿勢'],
['Default pose','默认姿态','デフォルト姿勢'],
['Default pose holds a standing pose. Walk / get up walks and recovers after a fall. Choose Pick, Roulade, Sit/Stand or a kick to perform that action. Enable Skating mode for skating. Inference only previews motion; Torque off releases the motors.','默认姿态保持站立。行走 / 起身可以行走，摔倒后会自己起来。选择拾取、前滚翻、坐下 / 站起或踢球来做对应动作。滑行时请打开滑行模式。仅推理只预览动作；扭矩关闭会放松电机。','デフォルト姿勢は立った姿勢を保ちます。歩行 / 起き上がりは歩行し、転倒すると起き上がります。拾う、前転、座る / 立つ、キックを選ぶとその動作をします。スケートにはスケートモードをオンにします。推論のみは動きのプレビューで、トルクオフはモーターを脱力します。'],
['Deploy the updated project to enable servo setup.','请部署更新后的项目以启用舵机设置。','サーボ設定を使うには、更新したプロジェクトをデプロイしてください。'],
['Disable','禁用','無効にする'],
['Discovered servo IDs','找到的舵机 ID','見つかったサーボの ID'],
['Drag a pad to move; release to stop. W/S moves forward/back, A/D moves sideways and Q/E turns. Space releases the motors.','拖动摇杆移动，松手停止。W/S 前后，A/D 横移，Q/E 转向。空格键放松电机。','パッドをドラッグすると移動し、離すと止まります。W/S で前後、A/D で横移動、Q/E で旋回します。スペースキーでモーターを脱力します。'],
['Enable','启用','有効にする'],
['Enable / Disable changes only the protection switch. Set protection current changes only the current threshold. Both operations broadcast to every servo; no scan or ID selection is needed. Overheat protection stays enabled, and stored voltage limits are unchanged. Current resolution is 6.5 mA. Broadcast writes have no per-servo acknowledgement.','“启用 / 禁用”只改变保护开关，“设置保护电流”只改变电流阈值。两者都会广播给所有舵机，不需要扫描或选择 ID。过热保护始终开启，已保存的电压限制不变。电流精度为 6.5 mA。广播写入没有逐个舵机的确认。','「有効にする / 無効にする」は保護のオン・オフだけを、「保護電流を設定」は電流のしきい値だけを変えます。どちらも全サーボにブロードキャストするので、スキャンや ID の選択は不要です。過熱保護は常に有効で、保存済みの電圧制限は変わりません。電流の分解能は 6.5 mA です。ブロードキャストの書き込みには、サーボごとの確認応答がありません。'],
['Encoder {v}','编码器 {v}','エンコーダー {v}'],
['Enter a protection current between 0 and 425.9775 A.','请输入 0 到 425.9775 A 之间的保护电流。','保護電流は 0〜425.9775 A の範囲で入力してください。'],
['Entering calibration and unloading all servos…','正在进入标定并让所有舵机卸力…','キャリブレーションに入り、すべてのサーボを脱力しています…'],
['Entering servo setup and unloading all servos…','正在进入舵机设置，并让所有舵机卸力…','サーボ設定に入り、すべてのサーボを脱力しています…'],
['Error: Slight movement. Please recalibrate.','出错：有轻微晃动，请重新标定。','エラー：わずかな動きがありました。もう一度キャリブレーションしてください。'],
['Exit','退出','終了'],
['fallen {t} / 0.15 s','倾倒 {t} / 0.15 秒','転倒 {t} / 0.15 秒'],
['Feedback','反馈','フィードバック'],
['Forward / backward','前进 / 后退','前進 / 後退'],
['Forward / strafe','前后 / 横移','前後 / 横移動'],
['Getting up','正在起身','起き上がり中'],
['Gravity smoothing','重力平滑','重力のスムージング'],
['Gyro smoothing','陀螺仪平滑','ジャイロのスムージング'],
['Head {n}','头 {n}','頭 {n}'],
['Head and mouth','头和嘴','頭とくちばし'],
['Head smoothing','头部平滑','頭のスムージング'],
['Heading hold','航向保持','方位保持'],
['hold {left} s left','保持，还剩 {left} 秒','保持 残り {left} 秒'],
['Holding center','保持中位','中心を保持中'],
['ID {id} · {action}…','ID {id} · {action}…','ID {id} · {action}…'],
['ID {id} · KP/KD written','ID {id} · KP/KD 已写入','ID {id} · KP/KD を書き込みました'],
['ID {id} · Mid reset sent. Servo remains unloaded.','ID {id} · 已发送重设中位，舵机保持卸力。','ID {id} · 中心リセットを送信しました。サーボは脱力したままです。'],
['ID {id} · parameters read','ID {id} · 参数已读取','ID {id} · パラメーターを読み取りました'],
['ID {id} · Pos {pos} · KP {kp} · KD {kd}','ID {id} · 位置 {pos} · KP {kp} · KD {kd}','ID {id} · 位置 {pos} · KP {kp} · KD {kd}'],
['ID {id} → {to} · verified','ID {id} → {to} · 已验证','ID {id} → {to} · 確認済み'],
['ID {id} is holding its center.','ID {id} 正在保持中位。','ID {id} は中心を保持しています。'],
['ID changed. Scan again to select the updated servo.','ID 已修改。请重新扫描，再选择修改后的舵机。','ID を変更しました。もう一度スキャンして、変更後のサーボを選んでください。'],
['ID must be between 0 and 253','ID 必须在 0 到 253 之间','ID は 0〜253 の範囲で指定してください'],
['idle','空闲','待機'],
['IMU and servos','IMU 与舵机','IMU とサーボ'],
['IMU calibrated and saved.','IMU 已标定并保存。','IMU をキャリブレーションして保存しました。'],
['IMU calibration','IMU 标定','IMU キャリブレーション'],
['IMU calibration posture: Arduino upright with its bottom edge resting on the tabletop.','IMU 标定姿势：Arduino 竖直，底边放在桌面上。','IMU キャリブレーションの姿勢：Arduino を立て、下端を机に付けます。'],
['IMU calibration reset. Previous calibration backed up.','IMU 标定已重置，之前的标定已备份。','IMU キャリブレーションをリセットしました。以前の値はバックアップしました。'],
['IMU filtering','IMU 滤波','IMU フィルタ'],
['Increase smoothing for steadier readings.','加大平滑可以让读数更稳。','スムージングを強くすると読み取り値が安定します。'],
['inference only','仅推理','推論のみ'],
['Inference only','仅推理','推論のみ'],
['Invalid broadcast reply','广播回复无效','ブロードキャストの応答が不正です'],
['Invalid scan reply','扫描回复无效','スキャンの応答が不正です'],
['Joints','关节','関節'],
['Keep Arduino upright, with its bottom edge firmly against the tabletop. Hold still for 1.5 seconds.','让 Arduino 竖直，底边紧贴桌面，保持不动 1.5 秒。','Arduino を立てて下端を机にしっかり付け、1.5 秒間動かさないでください。'],
['Keep the board still. Calibrating for {s} seconds…','保持板子不动，正在标定 {s} 秒…','基板を動かさないでください。{s} 秒間キャリブレーションしています…'],
['Keep the board still. Calibrating for 1.5 seconds…','请保持板子不动，正在标定 1.5 秒…','ボードを動かさないでください。1.5 秒間キャリブレーションしています…'],
['Language','语言','言語'],
['left kick','左踢','左キック'],
['Left kick','左踢','左キック'],
['Leg smoothing','腿部平滑','脚のスムージング'],
['Let the roll motors cool down between longer skating sessions.','长时间滑行之间，请让横滚电机冷却一下。','長くスケートしたあとは、ロール軸のモーターを冷ましてください。'],
['Limits: vx -{back} to +{forward}, vy {strafe}, ωz ±{yaw}.','范围：vx -{back} 到 +{forward}，vy {strafe}，ωz ±{yaw}。','範囲：vx -{back}〜+{forward}、vy {strafe}、ωz ±{yaw}。'],
['Limits: vx {a}, vy {b}, ωz {c}.','限制：vx {a}，vy {b}，ωz {c}。','制限：vx {a}、vy {b}、ωz {c}。'],
['Loading…','加载中…','読み込み中…'],
['Mode','模式','モード'],
['Mode updated','模式已更新','モードを更新しました'],
['Motion','移动','移動'],
['Mouth','嘴','くちばし'],
['Move the sliders to adjust the head and open or close the mouth.','拖动滑杆可以调整头部，并张开或合上嘴。','スライダーで頭の向きを変え、くちばしを開閉できます。'],
['New ID','新 ID','新しい ID'],
['No MCU feedback. Servo setup is not ready.','没有 MCU 反馈，舵机设置还没准备好。','MCU からの応答がありません。サーボ設定の準備ができていません。'],
['No MCU reply. Scan stopped.','没有 MCU 回复，扫描已停止。','MCU から応答がないため、スキャンを停止しました。'],
['No servo feedback','没有舵机反馈','サーボの応答なし'],
['No servos replied. Check servo power, bus connection and baud rate.','没有舵机回应。请检查舵机电源、总线连接和波特率。','応答したサーボがありません。サーボの電源、バスの接続、ボーレートを確認してください。'],
['Not applied','未应用','未適用'],
['Not calibrated. Hold the board upright and still.','尚未标定。请让板子竖直并保持不动。','未キャリブレーションです。ボードを立てて動かさないでください。'],
['Off','关','オフ'],
['offline','离线','オフライン'],
['On','开','オン'],
['online','在线','オンライン'],
['Opening this page unloads all motors. Align each joint by hand, then choose Set center & hold. Use Unload all to readjust. Exit releases the motors.','打开此页面后，所有电机都会卸力。用手对准每个关节，然后选择“设为中位并保持”。要重新调整就用“全部卸力”。退出时会释放电机。','このページを開くと、すべてのモーターが脱力します。各関節を手で合わせてから「中心に設定して保持」を選びます。やり直すときは「すべて脱力」を使います。終了するとモーターを解放します。'],
['pick','拾取','拾う'],
['Pick','拾取','拾う'],
['Pick started · {model}','开始拾取 · {model}','拾う動作を開始 · {model}'],
['pick φ {phi} / 1.00','拾取 φ {phi} / 1.00','拾う φ {phi} / 1.00'],
['Policy','策略','ポリシー'],
['Preparing','准备中','準備中'],
['Preparing {name}','正在准备 {name}','{name} を準備中'],
['Preparing scan…','正在准备扫描…','スキャンを準備しています…'],
['Preparing to get up','准备起身','起き上がりの準備中'],
['Procedure','步骤','手順'],
['Protection broadcast sent. Individual servo writes are not verified.','保护设置已广播。各个舵机的写入没有逐一验证。','保護設定をブロードキャストしました。サーボごとの書き込みは確認していません。'],
['Protection current in amperes','保护电流（安培）','保護電流（アンペア）'],
['Read','读取','読み取り'],
['Reading calibration status…','正在读取标定状态…','キャリブレーションの状態を読み込んでいます…'],
['Ready','就绪','準備完了'],
['request failed','请求失败','リクエストに失敗しました'],
['Request failed','请求失败','リクエストに失敗しました'],
['Reset IMU calibration','重置 IMU 标定','IMU キャリブレーションをリセット'],
['Reset Mid','重设中位','中心をリセット'],
['right kick','右踢','右キック'],
['Right kick','右踢','右キック'],
['Robot ready','机器人已就绪','ロボットの準備ができました'],
['roulade','前滚翻','前転'],
['Roulade','前滚翻','前転'],
['Roulade · {model}','前滚翻 · {model}','前転 · {model}'],
['roulade {left} / {total} s','前滚翻 {left} / {total} 秒','前転 {left} / {total} 秒'],
['Saved IMU calibration loaded.','已载入保存的 IMU 标定。','保存した IMU キャリブレーションを読み込みました。'],
['Scan all IDs','扫描全部 ID','すべての ID をスキャン'],
['Scan complete · 254 IDs checked · {found} found','扫描完成 · 已检查 254 个 ID · 找到 {found} 个','スキャン完了 · 254 個の ID を確認 · {found} 個検出'],
['Scan failed','扫描失败','スキャン失敗'],
['Scan for servos, then select an ID to read or change its settings.','先扫描舵机，再选择一个 ID 读取或修改它的设置。','サーボをスキャンしてから、ID を選んで設定を読み取るか変更してください。'],
['Scan IDs 0–253 to find connected servos.','扫描 ID 0–253，查找已连接的舵机。','ID 0〜253 をスキャンして、接続されたサーボを探します。'],
['Scan stopped. Select a found ID to continue.','扫描已停止。选择找到的 ID 继续。','スキャンを停止しました。見つかった ID を選んで続けてください。'],
['Scanning · torque off','扫描中 · 扭矩已关','スキャン中 · トルクオフ'],
['Scanning ID {id} · {checked}/254 checked · {found} found','正在扫描 ID {id} · 已检查 {checked}/254 · 找到 {found} 个','ID {id} をスキャン中 · {checked}/254 確認済み · {found} 個検出'],
['Select a found ID to read or change its settings.','选择找到的 ID 来读取或修改它的设置。','見つかった ID を選んで、設定を読み取るか変更してください。'],
['Select a found ID to read or change that servo\'s settings. Stop scan keeps the results found so far. IDs 254 and 255 are reserved.','选择找到的 ID 来读取或修改该舵机的设置。停止扫描会保留已找到的结果。ID 254 和 255 是保留的。','見つかった ID を選ぶと、そのサーボの設定を読み取ったり変更したりできます。スキャンを止めても、それまでの結果は残ります。ID 254 と 255 は予約済みです。'],
['Selected ID {id}','已选择 ID {id}','ID {id} を選択しました'],
['Servo scan progress','舵机扫描进度','サーボのスキャン進捗'],
['servo setup','舵机设置','サーボ設定'],
['Servo setup','舵机设置','サーボ設定'],
['Servo setup · XGO Duck','舵机设置 · XGO Duck','サーボ設定 · XGO Duck'],
['Servo setup closed','舵机设置已关闭','サーボ設定を終了しました'],
['Servos online','在线舵机','オンラインのサーボ'],
['Set center & hold','设为中位并保持','中心に設定して保持'],
['Set KP/KD','设置 KP/KD','KP/KD 設定'],
['Set KpKd','写入 KpKd','KpKd 書込'],
['Set protection current','设置保护电流','保護電流を設定'],
['Setting the center of ID {id}…','正在设置 ID {id} 的中位…','ID {id} の中心を設定しています…'],
['Sit','坐下','座る'],
['sit · holding','坐下 · 保持中','座る · 保持中'],
['Sit · holding','坐下 · 保持中','座る · 保持中'],
['Sitting','坐着','座っています'],
['Skating','滑行','スケート'],
['Skating mode','滑行模式','スケートモード'],
['Skating mode off','滑行模式已关闭','スケートモードをオフにしました'],
['Skating mode on','滑行模式已开启','スケートモードをオンにしました'],
['Stand','站起','立つ'],
['Stand · returning to walk after {s} s','站起 · {s} 秒后回到行走','立つ · {s} 秒後に歩行へ戻ります'],
['stand {left} s left','站起，还剩 {left} 秒','立つ 残り {left} 秒'],
['Standing up','正在站起','立ち上がり中'],
['Status','状态','状態'],
['status read failed','读取状态失败','ステータスの読み取りに失敗しました'],
['Status read failed','读取状态失败','状態の読み込みに失敗しました'],
['Stop scan','停止扫描','スキャン停止'],
['Stopped','已停止','停止'],
['Stopping scan…','正在停止扫描…','スキャンを停止しています…'],
['Target','目标','目標'],
['Tilt','倾斜','傾き'],
['torque off','扭矩关闭','トルクオフ'],
['Torque off','关闭扭矩','トルクオフ'],
['Unload all','全部卸力','すべて脱力'],
['Unloaded','已卸力','脱力中'],
['upright {t} / 1.00 s','直立 {t} / 1.00 秒','直立 {t} / 1.00 秒'],
['Voltage','电压','電圧'],
['Waiting for feedback','等待反馈','フィードバック待ち'],
['Waiting for feedback.','正在等待反馈。','フィードバックを待っています。'],
['Waiting for feedback…','等待反馈…','フィードバック待ち…'],
['Waiting for robot…','正在等待机器人…','ロボットを待っています…'],
['walk','行走','歩行'],
['Walk / get up','行走 / 起身','歩行 / 起き上がり'],
['Walk and recovery','行走与恢复','歩行と復帰'],
['Walking','行走中','歩行中'],
['Walking / other models','行走 / 其他模型','歩行・その他のモデル'],
['When changing an ID, connect only the servo you want to change. Duplicate IDs cannot be distinguished on the same bus.','修改 ID 时，只接上要修改的那一个舵机。同一总线上重复的 ID 无法区分。','ID を変更するときは、変更したいサーボだけを接続してください。同じバス上で重複した ID は区別できません。'],
['Yaw','转向','旋回'],
['Zero motion','停止移动','移動を停止'],
['Roller walking','滑行','スケート'],
['Roller mode','滑行模式','スケートモード'],
['Servo centering','舵机中位校准','サーボ中心合わせ'],
['Servo centering · XGO Duck','舵机中位校准 · XGO Duck','サーボ中心合わせ · XGO Duck'],
['Opening this page stops motion and unloads every servo. Turn one joint by hand to its mechanical center, then press Set center & hold. Only that servo will hold position 2048; the others remain unloaded. Repeat for each joint. Use Unload all to release the centered joints for another adjustment. Exiting releases every servo.','打开此页面会停止运动并让所有舵机卸力。用手把一个关节转到机械中点，然后按“设为中位并保持”。只有这个舵机会保持在位置 2048，其余舵机继续卸力。每个关节重复一次。需要重新调整时，按“全部卸力”放开已对中的关节。退出时所有舵机都会卸力。','このページを開くと動作が止まり、すべてのサーボが脱力します。関節を1つ手で機械的中心まで回し、「中心に設定して保持」を押してください。そのサーボだけが位置 2048 を保持し、ほかは脱力したままです。関節ごとに繰り返します。調整し直すときは「すべて脱力」で中心合わせ済みの関節を解放します。終了するとすべてのサーボが脱力します。'],
['Center command sent to ID {id}. It is holding position 2048.','已向 ID {id} 发送中位命令，正在保持位置 2048。','ID {id} に中心コマンドを送信しました。位置 2048 を保持しています。'],
['Encoder','编码器','エンコーダー'],
['Holding 2048','保持 2048','2048 を保持中'],
['Active model','当前模型','使用中のモデル'],
['Adjust separate settings for roller walking and other models. Roller defaults: scale 0.7, leg α 0.4, head α 0.5. Other defaults: scale 1, leg α 0.35, head α 0.45. Kick uses fixed scale 0.8 and leg/head α 0, independently of these sliders. Sit/Stand uses fixed scale 1.1; its leg/head α follow the ordinary-model sliders. Scale changes action offsets from the home pose. Release a slider to apply; restarting the app restores each group\'s defaults.','滑行和其他模型分开设置。滑行默认：幅度 0.7，腿部 α 0.4，头部 α 0.5。其他默认：幅度 1，腿部 α 0.35，头部 α 0.45。踢球固定使用幅度 0.8、腿部和头部 α 0，不受这些滑块影响。坐下/站起固定使用幅度 1.1，腿部和头部 α 跟随普通模型的滑块。幅度决定动作相对初始姿态的偏移量。松开滑块后生效，重启程序会恢复各组默认值。','スケートとほかのモデルを別々に設定します。スケートの既定値：スケール 0.7、脚 α 0.4、頭 α 0.5。そのほかの既定値：スケール 1、脚 α 0.35、頭 α 0.45。キックはスライダーに関係なくスケール 0.8、脚・頭 α 0 に固定です。座る/立つはスケール 1.1 に固定で、脚・頭 α は通常モデルのスライダーに従います。スケールはホーム姿勢からの動作オフセットを変えます。スライダーを離すと適用され、アプリを再起動すると各グループの既定値に戻ります。'],
['Angular velocity α','角速度 α','角速度 α'],
['Condition timer','条件计时','条件タイマー'],
['Drag a pad; release returns it to zero. Each axis has a 15% center dead zone and motion smoothing.','拖动摇杆，松手归零。每个轴有 15% 的中心死区和运动平滑。','パッドをドラッグします。離すとゼロに戻ります。各軸に 15% の中央デッドゾーンと動きのスムージングがあります。'],
['Enable Roller mode to use the roller walking model during Walk / get up. Recovery uses the get-up model. Commands always cover all 15 IDs. A missing ID is shown here and does not block the others. Default pose and walk send position targets. Leaving this page or keeping it in the background zeros motion and preserves the selected control mode. Use Torque off or enter Calibration to unload. Pick runs only while walking upright: it plays xgoduck_pick for one 4 s cycle, then returns to walk. Roulade plays xgoduck_roulade for 1.9 s with twist and head at 0, and leg/neck smoothing at 0.15, then returns to walk and the previous smoothing. Sit uses fixed action scale 1.1 and enables seated holding; the button changes to Stand. Stand runs for 1 s, then returns to walking. Walk, Pick and Roulade are unavailable during sit/stand. A fall cancels sit/stand and uses normal get-up recovery. Tilt does not select get-up during Roulade\'s 1.9 s. left_kick and right_kick each play for 0.4 s with velocity and pose commands at zero, then return to walk. Kick settings are fixed at scale 0.8 and leg/head α 0. A fall cancels the kick and uses normal get-up recovery.','开启滑行模式后，“行走 / 起身”会使用滑行模型，恢复时使用起身模型。命令始终覆盖全部 15 个 ID，缺少的 ID 会显示在这里，不影响其他舵机。默认姿态和行走发送位置目标。离开此页面或让它留在后台会把运动清零，并保留所选的控制模式。要卸力，请选择“关闭扭矩”或进入标定。拾取只在直立行走时运行：播放一次 4 秒的 xgoduck_pick，然后回到行走。前滚翻播放 1.9 秒的 xgoduck_roulade，此时移动和头部命令为 0，腿部和颈部平滑为 0.15，之后回到行走并恢复原来的平滑度。坐下固定使用动作幅度 1.1 并启用坐姿保持，按钮变为“站起”。站起运行 1 秒后回到行走。坐下/站起期间不能使用行走、拾取和前滚翻。摔倒会取消坐下/站起并走正常的起身恢复。前滚翻的 1.9 秒内，倾斜不会触发起身。left_kick 和 right_kick 各播放 0.4 秒，速度和姿态命令为 0，然后回到行走。踢球设置固定为幅度 0.8、腿部和头部 α 0。摔倒会取消踢球并走正常的起身恢复。','スケートモードをオンにすると、「歩行 / 起き上がり」でスケートモデルを使います。復帰には起き上がりモデルを使います。コマンドは常に 15 個すべての ID を対象にします。見つからない ID はここに表示され、ほかのサーボには影響しません。デフォルト姿勢と歩行は位置目標を送ります。このページを離れるかバックグラウンドにすると動きはゼロになり、選択中の制御モードは保たれます。脱力するにはトルクオフを選ぶか、キャリブレーションに入ってください。拾う動作は直立歩行中のみ実行でき、xgoduck_pick を 4 秒 1 サイクル再生して歩行に戻ります。前転は xgoduck_roulade を 1.9 秒再生し、その間の移動と頭のコマンドは 0、脚と首のスムージングは 0.15 です。その後、歩行と元のスムージングに戻ります。座るはスケール 1.1 に固定で座位保持を有効にし、ボタンは「立つ」に変わります。立つは 1 秒実行して歩行に戻ります。座る/立つの間は歩行、拾う、前転を使えません。転倒すると座る/立つは取り消され、通常の起き上がり復帰を行います。前転の 1.9 秒間は傾いても起き上がりを選びません。left_kick と right_kick はそれぞれ 0.4 秒再生し、その間の速度と姿勢のコマンドは 0 で、その後歩行に戻ります。キックの設定はスケール 0.8、脚・頭 α 0 に固定です。転倒するとキックは取り消され、通常の起き上がり復帰を行います。'],
['Gravity projection τ (s)','重力投影 τ（秒）','重力投影 τ（秒）'],
['Head 1–4 are radians (±1). The mouth is motor 34, 0–30°, and is sent with the 50 ms command heartbeat. It is not part of the policy observation.','头 1–4 单位为弧度（±1）。嘴是 34 号电机，范围 0–30°，随 50 毫秒的命令心跳发送，不属于策略的观测输入。','頭 1〜4 の単位はラジアン（±1）です。くちばしはモーター 34 で範囲は 0〜30°、50 ms のコマンドハートビートと一緒に送られます。ポリシーの観測には含まれません。'],
['Head α','头部 α','頭 α'],
['Higher angular velocity α gives more smoothing; higher gravity τ slows accelerometer correction. Changes apply immediately. Restarting the app restores defaults.','角速度 α 越大越平滑；重力 τ 越大，加速度计修正越慢。修改立即生效，重启程序会恢复默认值。','角速度 α を大きくするとスムージングが強くなり、重力 τ を大きくすると加速度計による補正が遅くなります。変更はすぐに反映され、アプリを再起動すると既定値に戻ります。'],
['Holding a toe-out stance for long periods heats up the roll motors. Take regular breaks to let them cool down.','长时间保持外八站姿会让横滚电机发热，请定时休息让电机降温。','つま先を外に向けた姿勢を長く続けるとロールモーターが熱くなります。定期的に休ませて冷ましてください。'],
['Leg α','腿部 α','脚 α'],
['Ranges follow Roller mode; switching modes clears motion. Keys: W/S forward, A/D strafe, Q/E yaw. Space turns torque off.','范围随滑行模式变化，切换模式会清除运动。按键：W/S 前后，A/D 横移，Q/E 转向，空格键关闭扭矩。','範囲はスケートモードに従い、モードを切り替えると動きはクリアされます。キー：W/S 前後、A/D 横移動、Q/E 旋回、スペースでトルクオフ。'],
['Tilt from (0, 0, -1)','相对 (0, 0, -1) 的倾斜','(0, 0, -1) からの傾き'],
['Waiting for command echo…','等待命令回显…','コマンドのエコーを待っています…'],
['Walk: tilt above 55° for 0.15 s selects the get-up model, holds action = 0 for 1 s, then runs the get-up action. Get-up: tilt below 15° for 1 s returns to walk. Twist and head commands are zero during get-up. Inference-only mode previews the switch without enabling torque. During pick the command is a phase encoding; the mouth opens to 30° and closes when φ ≥ 0.4.','行走：倾斜超过 55° 持续 0.15 秒时切换到起身模型，保持 action = 0 一秒，然后执行起身动作。起身：倾斜低于 15° 持续 1 秒后回到行走。起身期间移动和头部命令为零。仅推理模式可以预览切换，不会开启扭矩。拾取时命令是相位编码；嘴张开到 30°，φ ≥ 0.4 时闭合。','歩行：傾きが 55° を超えた状態が 0.15 秒続くと起き上がりモデルを選び、action = 0 を 1 秒保持してから起き上がり動作を実行します。起き上がり：傾きが 15° 未満の状態が 1 秒続くと歩行に戻ります。起き上がり中の移動と頭のコマンドはゼロです。推論のみのモードではトルクをかけずに切り替えを確認できます。拾う動作中のコマンドは位相エンコードで、くちばしは 30° まで開き、φ ≥ 0.4 で閉じます。'],
['Warning:','警告：','警告：'],
['Selected ID','已选 ID','選択中の ID'],
['servo reply timeout','舵机应答超时','サーボの応答がタイムアウトしました'],
['{side}_kick {s} s left','{side}_kick 还剩 {s} 秒','{side}_kick 残り {s} 秒'],
['head {n}','头 {n}','頭 {n}'],
['Mouth 34 (°)','嘴 34（°）','くちばし 34（°）'],
];
const pick=code=>Object.keys(LANGS).find(l=>String(code||'').toLowerCase().startsWith(l));
let saved=null;
try{saved=localStorage.getItem(KEY);}catch(e){}
const lang=pick(new URLSearchParams(location.search).get('lang'))||pick(saved)
  ||(navigator.languages||[navigator.language]).map(pick).find(Boolean)||'en';
const column=Object.keys(LANGS).indexOf(lang);

const exact=new Map(),patterns=[],cache=new Map();
for(const row of D){
  const en=row[0],to=row[column];
  if(!en.includes('{')){exact.set(en,to);continue;}
  const names=[];
  const source=en.split(/(\{\w+\})/).map(part=>{
    const m=/^\{(\w+)\}$/.exec(part);
    if(m){names.push(m[1]);return '(.+?)';}
    return part.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
  }).join('');
  patterns.push({re:new RegExp('^'+source+'$','s'),names,to,size:en.length});
}
patterns.sort((a,b)=>b.size-a.size);
function translate(text){
  const core=text.trim();
  if(!core||!/[A-Za-z]/.test(core))return text;
  let out=cache.get(core);
  if(out===undefined){
    out=exact.get(core);
    if(out===undefined)for(const p of patterns){
      const m=p.re.exec(core);
      if(!m)continue;
      const values={};
      p.names.forEach((name,i)=>{values[name]=translate(m[i+1]);});
      out=p.to.replace(/\{(\w+)\}/g,(all,name)=>name in values?values[name]:all);
      break;
    }
    if(out===undefined)out=core;
    if(cache.size>2000)cache.clear();
    cache.set(core,out);
  }
  return out===core?text:text.replace(core,()=>out);
}

const ATTRS=['title','placeholder','aria-label','alt'],SKIP=new Set(['SCRIPT','STYLE']);
function visitAttr(el,name){
  const value=el.getAttribute(name);
  if(!value)return;
  const shown=translate(value);
  if(shown!==value)el.setAttribute(name,shown);
}
function visit(node){
  if(node.nodeType===3){
    if(SKIP.has(node.parentNode&&node.parentNode.nodeName))return;
    const shown=translate(node.data);
    if(shown!==node.data)node.data=shown;
  }else if(node.nodeType===1&&!SKIP.has(node.nodeName)){
    for(const name of ATTRS)visitAttr(node,name);
    node.childNodes.forEach(visit);
  }
}
document.documentElement.lang=HTML_LANG[lang];
if(lang!=='en')new MutationObserver(list=>{
  for(const m of list){
    if(m.type==='characterData')visit(m.target);
    else if(m.type==='attributes')visitAttr(m.target,m.attributeName);
    else m.addedNodes.forEach(visit);
  }
}).observe(document,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:ATTRS});

document.addEventListener('DOMContentLoaded',()=>{
  const style=document.createElement('style');
  style.textContent='.lang-bar{display:flex;justify-content:flex-end;margin:-16px 0 4px}'
    +'.lang{font:inherit;font-size:14px;color:#9cafc3;padding:5px 8px;border:1px solid #26384b;border-radius:8px;background:#0e1924;cursor:pointer}'
    +'@media(max-width:620px){.lang-bar{margin-top:-8px}}';
  document.head.append(style);
  const picker=document.createElement('select');
  picker.className='lang';
  picker.setAttribute('aria-label','Language');
  for(const [code,name] of Object.entries(LANGS))picker.add(new Option(name,code,false,code===lang));
  // Reloading redoes the text the page scripts built, so nothing needs translating back.
  picker.onchange=()=>{
    const url=new URL(location.href);
    try{localStorage.setItem(KEY,picker.value);url.searchParams.delete('lang');}
    catch(e){url.searchParams.set('lang',picker.value);}
    location.replace(url);
  };
  const bar=document.createElement('div');
  bar.className='lang-bar';
  bar.append(picker);
  document.querySelector('main')?.prepend(bar);
});
})();
