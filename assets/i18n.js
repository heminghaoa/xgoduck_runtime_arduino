// UI text in English, Chinese and Japanese. Pages mark static text with data-i18n (text),
// data-i18n-html (markup from this file) or data-i18n-attr="attr:key,…"; scripts call t(key, vars).
// Load this before the page scripts. The choice is kept in localStorage; ?lang=zh overrides it.
const XGO_LANG_KEY='xgoduck-lang';
const XGO_LANGS={en:'English',zh:'中文',ja:'日本語'};
const XGO_HTML_LANG={en:'en',zh:'zh-CN',ja:'ja'};

// Each entry is [English, Chinese, Japanese]; {name} is filled from t()'s vars.
const I18N={
  'lang.label':['Language','语言','言語'],
  'nav.control':['Control','控制','コントロール'],
  'nav.calibrate':['Calibration','标定','キャリブレーション'],
  'nav.servo':['Servo setup','舵机设置','サーボ設定'],
  'nav.pair':['Pairing','配对','ペアリング'],
  'common.on':['On','开','オン'],
  'common.off':['Off','关','オフ'],
  'common.exit':['Exit','退出','終了'],
  'common.close':['Close','关闭','閉じる'],
  'common.loading':['Loading…','加载中…','読み込み中…'],
  'error.request':['Request failed','请求失败','リクエストに失敗しました'],
  'error.status':['Status read failed','读取状态失败','状態の読み込みに失敗しました'],

  // Control page
  'control.stop':['Torque off','关闭扭矩','トルクオフ'],
  'control.connecting':['Connecting…','正在连接…','接続中…'],
  'control.pairingWarning':[
    '<strong>Pairing required:</strong> this browser can watch but not control the duck. Pair it on the <a href="/pair.html">Pairing</a> page.',
    '<strong>需要配对：</strong>此浏览器只能查看，不能控制鸭子。请到<a href="/pair.html">配对</a>页面配对。',
    '<strong>ペアリングが必要です：</strong>このブラウザは状態を見られますが、ダックを操作できません。<a href="/pair.html">ペアリング</a>ページでペアリングしてください。'],
  'control.feedback':['Feedback','反馈','フィードバック'],
  'control.policy':['Policy','策略','ポリシー'],
  'control.servos':['Servos online','在线舵机','オンラインのサーボ'],
  'control.battery':['Battery','电池','バッテリー'],
  'battery.waiting':['Waiting for a servo','等待舵机读数','サーボの応答待ち'],
  'battery.about':['about {p}%','约 {p}%','約 {p}%'],
  'battery.none':['No servo reading','没有舵机读数','サーボの読み取りなし'],
  'battery.low':[
    '<strong>Battery low:</strong> {v} V. Charge it soon.',
    '<strong>电量低：</strong>{v} V，请尽快充电。',
    '<strong>バッテリー残量が少なくなっています：</strong>{v} V。早めに充電してください。'],
  'battery.critical':[
    '<strong>Battery very low:</strong> {v} V. Turn torque off and charge it now.',
    '<strong>电量严重不足：</strong>{v} V，请关闭扭矩并立即充电。',
    '<strong>バッテリー残量がほとんどありません：</strong>{v} V。トルクをオフにして、すぐに充電してください。'],
  'control.mode':['Mode','模式','モード'],
  'mode.shadow':['Inference only','仅推理','推論のみ'],
  'mode.hold':['Default pose','默认姿态','デフォルト姿勢'],
  'mode.policy':['Walk / get up','行走 / 起身','歩行 / 起き上がり'],
  'control.pick':['Pick','拾取','拾う'],
  'control.roulade':['Roulade','前滚翻','前転'],
  'control.roller':['Roller mode','轮滑模式','ローラーモード'],
  'control.modeHint':[
    'Enable Roller mode to use the roller walking model during Walk / get up. Recovery uses the get-up model. Commands always cover all 15 IDs. A missing ID is shown here and does not block the others. Default pose and walk send position targets. Leaving this page or keeping it in the background zeros motion and preserves the selected control mode. Use Torque off or enter Calibration to unload. Pick runs only while walking upright: it plays xgoduck_pick for one 4 s cycle, then returns to walk. Roulade plays xgoduck_roulade for 1.9 s with twist and head at 0, and leg/neck smoothing at 0.15, then returns to walk and the previous smoothing. Tilt does not select get-up during those 1.9 s.',
    '打开轮滑模式后，“行走 / 起身”会使用轮滑行走模型；摔倒恢复仍使用起身模型。命令始终覆盖全部 15 个 ID，缺失的 ID 会在这里显示，但不影响其他舵机。默认姿态和行走都发送位置目标。离开本页或切到后台会把运动清零，但保留当前控制模式。要卸力，请按“关闭扭矩”或进入标定页。拾取只在直立行走时可用：播放一个 4 秒周期的 xgoduck_pick，然后回到行走。前滚翻播放 1.9 秒的 xgoduck_roulade，期间移动和头部指令为 0，腿和脖子的平滑系数为 0.15，结束后回到行走并恢复原来的平滑系数。这 1.9 秒内倾斜不会触发起身。',
    'ローラーモードをオンにすると、「歩行 / 起き上がり」でローラー歩行モデルを使います。転倒からの復帰には起き上がりモデルを使います。コマンドは常に 15 個すべての ID を対象にします。見つからない ID はここに表示されますが、ほかのサーボは止まりません。デフォルト姿勢と歩行は位置目標を送ります。このページを離れたりバックグラウンドにしたりすると移動はゼロになり、選んだ制御モードはそのまま残ります。脱力するには「トルクオフ」を押すか、キャリブレーションに入ってください。拾う動作は直立して歩行中のみ使えます。xgoduck_pick を 4 秒の 1 周期だけ再生し、歩行に戻ります。前転は xgoduck_roulade を 1.9 秒再生します。その間、移動と頭のコマンドは 0、脚と首の平滑化は 0.15 になり、終わると歩行と元の平滑化に戻ります。この 1.9 秒間は傾きで起き上がりに切り替わりません。'],
  'msg.modeUpdated':['Mode updated','模式已更新','モードを更新しました'],
  'msg.rollerOn':['Roller mode on · {model}','轮滑模式已开 · {model}','ローラーモード オン · {model}'],
  'msg.rollerOff':['Roller mode off · {model}','轮滑模式已关 · {model}','ローラーモード オフ · {model}'],
  'msg.pick':['Pick started · {model}','开始拾取 · {model}','拾う動作を開始 · {model}'],
  'msg.roulade':['Roulade · {model}','前滚翻 · {model}','前転 · {model}'],
  'modeLabel.shadow':['inference only','仅推理','推論のみ'],
  'modeLabel.off':['torque off','扭矩关闭','トルクオフ'],
  'modeLabel.hold':['default pose','默认姿态','デフォルト姿勢'],
  'modeLabel.policy':['walk','行走','歩行'],
  'modeLabel.calibrate':['calibrate','标定','キャリブレーション'],
  'modeLabel.servo_debug':['servo setup','舵机设置','サーボ設定'],
  'status.enabled':[' · enabled',' · 扭矩开',' · トルクオン'],
  'status.torqueOff':[' · torque off',' · 扭矩关',' · トルクオフ'],
  'status.online':['online','在线','オンライン'],
  'status.offline':['offline','离线','オフライン'],
  'status.bridge':['Bridge {mbps} Mbps · state age {age} ms','Bridge {mbps} Mbps · 状态延迟 {age} ms','Bridge {mbps} Mbps · 状態の経過 {age} ms'],
  'recovery.title':['Walk and recovery','行走与恢复','歩行と復帰'],
  'recovery.model':['Active model','当前模型','使用中のモデル'],
  'recovery.tilt':['Tilt from (0, 0, -1)','相对 (0, 0, -1) 的倾斜','(0, 0, -1) からの傾き'],
  'recovery.timer':['Condition timer','条件计时','条件タイマー'],
  'recovery.hint':[
    'Walk: tilt above 55° for 0.15 s selects the get-up model, holds action = 0 for 1 s, then runs the get-up action. Get-up: tilt below 15° for 1 s returns to walk. Twist and head commands are zero during get-up. Inference-only mode previews the switch without enabling torque. During pick the command is a phase encoding; the mouth opens to 30° and closes when φ ≥ 0.4.',
    '行走时：倾斜超过 55° 持续 0.15 秒就切换到起身模型，先保持 action = 0 一秒，再执行起身动作。起身时：倾斜低于 15° 持续 1 秒就回到行走。起身期间移动和头部指令为 0。仅推理模式只预览切换，不会打开扭矩。拾取期间，命令是相位编码；嘴张到 30°，φ ≥ 0.4 时合上。',
    '歩行中：傾きが 55° を超えて 0.15 秒続くと起き上がりモデルに切り替わり、action = 0 を 1 秒保持してから起き上がり動作を実行します。起き上がり中：傾きが 15° 未満で 1 秒続くと歩行に戻ります。起き上がり中は移動と頭のコマンドが 0 になります。推論のみモードでは、トルクを入れずに切り替えだけを確認できます。拾う動作中のコマンドは位相エンコーディングです。くちばしは 30° まで開き、φ ≥ 0.4 で閉じます。'],
  'phase.walk':['walk','行走','歩行'],
  'phase.getup':['get-up','起身','起き上がり'],
  'phase.default_pose':['get-up · action = 0','起身 · action = 0','起き上がり · action = 0'],
  'phase.pick':['pick','拾取','拾う'],
  'phase.roulade':['roulade','前滚翻','前転'],
  'phase.idle':['idle','空闲','待機'],
  'timer.roulade':['roulade {left} / {total} s','前滚翻 {left} / {total} 秒','前転 {left} / {total} 秒'],
  'timer.pick':['pick φ {phi} / 1.00','拾取 φ {phi} / 1.00','拾う φ {phi} / 1.00'],
  'timer.hold':['hold {left} s left','保持，还剩 {left} 秒','保持 残り {left} 秒'],
  'timer.upright':['upright {t} / 1.00 s','直立 {t} / 1.00 秒','直立 {t} / 1.00 秒'],
  'timer.fallen':['fallen {t} / 0.15 s','倾倒 {t} / 0.15 秒','転倒 {t} / 0.15 秒'],
  'motion.title':['Motion','移动','移動'],
  'motion.rollerWarning':[
    '<strong>Warning:</strong> Holding a toe-out stance for long periods heats up the roll motors. Take regular breaks to let them cool down.',
    '<strong>注意：</strong>长时间保持脚尖外撇的站姿会让横滚电机发热。请定时休息，让电机冷却。',
    '<strong>注意：</strong>つま先を外に開いた姿勢を長く続けると、ロール軸のモーターが熱くなります。こまめに休ませて冷ましてください。'],
  'motion.leftWalk':['Forward / strafe','前后 / 横移','前後 / 横移動'],
  'motion.leftRoller':['Forward / backward','前进 / 后退','前進 / 後退'],
  'motion.right':['Yaw','转向','旋回'],
  'motion.zero':['Zero motion','停止移动','移動を停止'],
  'motion.hintPads':[
    'Drag a pad; release returns it to zero. Each axis has a 15% center dead zone and motion smoothing.',
    '拖动摇杆，松手后回到零。每个轴在中心有 15% 的死区，并做了运动平滑。',
    'パッドをドラッグします。離すとゼロに戻ります。各軸には中心 15% のデッドゾーンと動きの平滑化があります。'],
  'motion.limits':['Limits: vx -{back} to +0.4, vy {strafe}, ωz ±{yaw}.','范围：vx -{back} 到 +0.4，vy {strafe}，ωz ±{yaw}。','範囲：vx -{back}〜+0.4、vy {strafe}、ωz ±{yaw}。'],
  'motion.hintKeys':[
    'Ranges follow Roller mode; switching modes clears motion. Keys: W/S forward, A/D strafe, Q/E yaw. Space turns torque off.',
    '范围随轮滑模式变化，切换模式会清除运动。键盘：W/S 前后，A/D 横移，Q/E 转向，空格键关闭扭矩。',
    '範囲はローラーモードに合わせて変わり、モードを切り替えると移動はリセットされます。キー：W/S 前後、A/D 横移動、Q/E 旋回、スペースでトルクオフ。'],
  'head.title':['Head and mouth','头和嘴','頭とくちばし'],
  'head.joint':['head {n}','头 {n}','頭 {n}'],
  'head.mouth':['Mouth 34 (°)','嘴 34 (°)','くちばし 34 (°)'],
  'head.hint':[
    'Head 1–4 are radians (±1). The mouth is motor 34, 0–30°, and is sent with the 50 ms command heartbeat. It is not part of the policy observation.',
    '头 1–4 的单位是弧度（±1）。嘴是 34 号电机，范围 0–30°，随 50 ms 的命令心跳一起发送，不属于策略的观测量。',
    '頭 1〜4 の単位はラジアン（±1）です。くちばしは 34 番のモーターで 0〜30°、50 ms ごとのコマンドと一緒に送られます。ポリシーの観測値には含まれません。'],
  'action.title':['Action settings','动作设置','動作設定'],
  'action.walk':['Walking / other models','行走 / 其他模型','歩行・その他のモデル'],
  'action.roller':['Roller walking','轮滑行走','ローラー歩行'],
  'action.scale':['Action scale','动作幅度','動作スケール'],
  'action.leg':['Leg α','腿部 α','脚 α'],
  'action.head':['Head α','头部 α','頭 α'],
  'action.restore':['Restore defaults','恢复默认','デフォルトに戻す'],
  'action.hint':[
    'Adjust separate settings for roller walking and other models. Roller defaults: scale 0.7, leg α 0.4, head α 0.5. Other defaults: scale 1, leg α 0.45, head α 0.2. Scale changes action offsets from the home pose. Release a slider to apply it; the duck saves it and restores it when the app starts. Restore defaults resets both groups and IMU filtering.',
    '轮滑行走和其他模型各有一套设置。轮滑默认：幅度 0.7，腿部 α 0.4，头部 α 0.5。其他默认：幅度 1，腿部 α 0.45，头部 α 0.2。幅度改变动作相对默认姿态的偏移量。松开滑块即生效，鸭子会保存设置，App 启动时自动恢复。“恢复默认”会重置两组设置和 IMU 滤波。',
    'ローラー歩行とそれ以外のモデルで、設定を別々に調整できます。ローラーのデフォルト：スケール 0.7、脚 α 0.4、頭 α 0.5。それ以外のデフォルト：スケール 1、脚 α 0.45、頭 α 0.2。スケールはホーム姿勢からの動作オフセットを変えます。スライダーを離すと適用され、ダックに保存されてアプリ起動時に復元されます。「デフォルトに戻す」は両方の設定と IMU フィルタをリセットします。'],
  'action.confirmRestore':[
    'Restore the default action settings for both groups and the default IMU filtering?',
    '要把两组动作设置和 IMU 滤波都恢复为默认值吗？',
    '両方の動作設定と IMU フィルタをデフォルトに戻しますか？'],
  'action.restored':['Defaults restored and saved','已恢复默认值并保存','デフォルトに戻して保存しました'],
  'imu.title':['IMU filtering','IMU 滤波','IMU フィルタ'],
  'imu.gyro':['Angular velocity α','角速度 α','角速度 α'],
  'imu.tau':['Gravity projection τ (s)','重力投影 τ (秒)','重力投影 τ (秒)'],
  'imu.hint':[
    'Higher angular velocity α gives more smoothing; higher gravity τ slows accelerometer correction. Changes apply immediately and are saved on the duck.',
    '角速度 α 越大，平滑越强；重力 τ 越大，加速度计的修正越慢。修改立即生效，并保存在鸭子上。',
    '角速度 α を大きくすると平滑化が強くなり、重力 τ を大きくすると加速度計による補正が遅くなります。変更はすぐに適用され、ダックに保存されます。'],
  'telemetry.title':['IMU and servos','IMU 与舵机','IMU とサーボ'],
  'telemetry.target':['Target','目标','目標'],
  'telemetry.waiting':['Waiting for command echo…','等待命令回显…','コマンドのエコー待ち…'],
  'telemetry.health':[
    'sent {sent} · MCU echo {echo} · command age {age} · gaps {gaps} · rejected {rejected}',
    '已发送 {sent} · MCU 回显 {echo} · 命令延迟 {age} · 丢帧 {gaps} · 拒收 {rejected}',
    '送信 {sent} · MCU エコー {echo} · コマンド経過 {age} · 欠落 {gaps} · 拒否 {rejected}'],

  // Calibration page
  'cal.pageTitle':['Servo centering · XGO Duck','舵机归中 · XGO Duck','サーボの中心合わせ · XGO Duck'],
  'cal.title':['Servo centering','舵机归中','サーボの中心合わせ'],
  'cal.entering':['Entering calibration and unloading all servos…','正在进入标定并让所有舵机卸力…','キャリブレーションに入り、すべてのサーボを脱力しています…'],
  'cal.procedure':['Procedure','步骤','手順'],
  'cal.unloadAll':['Unload all','全部卸力','すべて脱力'],
  'cal.hintSteps':[
    'Opening this page stops motion and unloads every servo. Turn one joint by hand until it matches its picture, then press Set center & hold. Only that servo will hold position 2048; the others remain unloaded. Repeat for each joint. Use Unload all to release the centered joints for another adjustment. Exiting releases every servo.',
    '打开本页会停止运动并让所有舵机卸力。用手把一个关节转到和图片一致，然后按“设为中位并保持”。只有这个舵机会保持在 2048 位置，其他舵机仍然卸力。每个关节重复一遍。要重新调整已归中的关节，按“全部卸力”。退出时会释放所有舵机。',
    'このページを開くと動きが止まり、すべてのサーボが脱力します。関節を 1 つずつ手で回して写真と同じ向きにし、「中心に設定して保持」を押します。そのサーボだけが位置 2048 を保持し、ほかは脱力したままです。各関節で繰り返してください。中心合わせ済みの関節を調整し直すには「すべて脱力」を押します。終了するとすべてのサーボが解放されます。'],
  'cal.hintPictures':[
    'Target pose: every joint at 0°, rendered from the training model. Tap a joint\'s picture for a close-up. Teal is the part that servo turns, the ring marks its shaft, and the dashed line leads to the next shaft.',
    '目标姿态：所有关节都在 0°，图片由训练模型渲染。点关节的图片可以放大查看。青色是这个舵机带动的部分，圆环标出它的轴，虚线指向下一个轴。',
    '目標姿勢：すべての関節が 0° の状態で、学習モデルからレンダリングしています。関節の写真をタップすると拡大表示します。青緑色はそのサーボが動かす部分、リングは軸の位置、破線は次の軸を示します。'],
  'cal.altFront':['Zero pose from the front','零位姿态（正面）','ゼロ姿勢（正面）'],
  'cal.altSide':['Zero pose from the left','零位姿态（左侧）','ゼロ姿勢（左側）'],
  'cal.altAngle':['Zero pose from the front left','零位姿态（左前方）','ゼロ姿勢（左前方）'],
  'cal.joints':['Joints','关节','関節'],
  'cal.beakClosed':['Beak closed','嘴闭合','くちばしを閉じる'],
  'cal.refLabel':['Zero pose of ID {id}','ID {id} 的零位姿态','ID {id} のゼロ姿勢'],
  'cal.waiting':['Waiting for feedback','等待反馈','フィードバック待ち'],
  'cal.unloaded':['Unloaded','已卸力','脱力中'],
  'cal.center':['Set center & hold','设为中位并保持','中心に設定して保持'],
  'cal.centering':['Centering…','正在归中…','中心合わせ中…'],
  'cal.holding':['Holding 2048','保持 2048','2048 を保持中'],
  'cal.setting':['Setting the center of ID {id}…','正在设置 ID {id} 的中位…','ID {id} の中心を設定しています…'],
  'cal.sent':['Center command sent to ID {id}. It is holding position 2048.','已向 ID {id} 发送归中命令，它正保持在 2048 位置。','ID {id} に中心合わせのコマンドを送りました。位置 2048 を保持しています。'],
  'cal.ready':['All servos are unloaded. Turn one joint by hand, then set its center.','所有舵机已卸力。用手转好一个关节，再设置它的中位。','すべてのサーボを脱力しました。関節を 1 つ手で回してから、中心を設定してください。'],
  'cal.closedMessage':['Calibration closed. All servos are unloaded.','标定已关闭，所有舵机已卸力。','キャリブレーションを終了しました。すべてのサーボは脱力しています。'],
  'cal.active':['Calibration active','标定中','キャリブレーション中'],
  'cal.closed':['Calibration closed','标定已关闭','キャリブレーション終了'],
  'cal.encoder':['Encoder {v}','编码器 {v}','エンコーダー {v}'],
  'cal.noFeedback':['No servo feedback','没有舵机反馈','サーボの応答なし'],
  'joint.10':['Left hip yaw','左髋偏航','左股関節ヨー'],
  'joint.11':['Left hip roll','左髋横滚','左股関節ロール'],
  'joint.12':['Left hip pitch','左髋俯仰','左股関節ピッチ'],
  'joint.13':['Left knee','左膝','左膝'],
  'joint.14':['Left ankle','左踝','左足首'],
  'joint.20':['Right hip yaw','右髋偏航','右股関節ヨー'],
  'joint.21':['Right hip roll','右髋横滚','右股関節ロール'],
  'joint.22':['Right hip pitch','右髋俯仰','右股関節ピッチ'],
  'joint.23':['Right knee','右膝','右膝'],
  'joint.24':['Right ankle','右踝','右足首'],
  'joint.30':['Neck pitch','颈部俯仰','首ピッチ'],
  'joint.31':['Head pitch','头部俯仰','頭ピッチ'],
  'joint.32':['Head yaw','头部偏航','頭ヨー'],
  'joint.33':['Head roll','头部横滚','頭ロール'],
  'joint.34':['Mouth','嘴','くちばし'],
  'ref.10':[
    'Seen from below. The foot points straight ahead; the hip-roll shaft sits directly in front of this one.',
    '从下方看。脚尖朝正前方；髋横滚轴就在这个轴的正前方。',
    '下から見た図。足先はまっすぐ前を向き、股関節ロールの軸がこの軸の真正面にあります。'],
  'ref.11':[
    'Seen from the front. The leg hangs straight down; the hip-pitch shaft is level with this one.',
    '从正面看。腿竖直向下；髋俯仰轴和这个轴等高。',
    '正面から見た図。脚はまっすぐ下に垂れ、股関節ピッチの軸がこの軸と同じ高さにあります。'],
  'ref.12':[
    'Seen from the left. The knee shaft sits behind and below this one, about 32° under horizontal.',
    '从左侧看。膝关节轴在这个轴的后下方，比水平线低约 32°。',
    '左から見た図。膝の軸はこの軸の後ろ下、水平から約 32° 下にあります。'],
  'ref.13':[
    'Seen from the left. The ankle shaft is directly below this one: the shank is vertical.',
    '从左侧看。踝关节轴在这个轴的正下方：小腿竖直。',
    '左から見た図。足首の軸はこの軸の真下にあり、すねが垂直です。'],
  'ref.14':['Seen from the left. The sole is flat on the ground.','从左侧看。脚底平贴地面。','左から見た図。足裏が地面にぴったり付いています。'],
  'ref.20':[
    'Seen from below. The foot points straight ahead; the hip-roll shaft sits directly in front of this one.',
    '从下方看。脚尖朝正前方；髋横滚轴就在这个轴的正前方。',
    '下から見た図。足先はまっすぐ前を向き、股関節ロールの軸がこの軸の真正面にあります。'],
  'ref.21':[
    'Seen from the front. The leg hangs straight down; the hip-pitch shaft is level with this one.',
    '从正面看。腿竖直向下；髋俯仰轴和这个轴等高。',
    '正面から見た図。脚はまっすぐ下に垂れ、股関節ピッチの軸がこの軸と同じ高さにあります。'],
  'ref.22':[
    'Seen from the right. The knee shaft sits behind and below this one, about 32° under horizontal.',
    '从右侧看。膝关节轴在这个轴的后下方，比水平线低约 32°。',
    '右から見た図。膝の軸はこの軸の後ろ下、水平から約 32° 下にあります。'],
  'ref.23':[
    'Seen from the right. The ankle shaft is directly below this one: the shank is vertical.',
    '从右侧看。踝关节轴在这个轴的正下方：小腿竖直。',
    '右から見た図。足首の軸はこの軸の真下にあり、すねが垂直です。'],
  'ref.24':['Seen from the right. The sole is flat on the ground.','从右侧看。脚底平贴地面。','右から見た図。足裏が地面にぴったり付いています。'],
  'ref.30':[
    'Seen from the left. The neck is vertical: the head-pitch shaft is directly above this one.',
    '从左侧看。脖子竖直：头部俯仰轴在这个轴的正上方。',
    '左から見た図。首は垂直で、頭ピッチの軸がこの軸の真上にあります。'],
  'ref.31':['Seen from the left. The head-yaw shaft is directly above this one.','从左侧看。头部偏航轴在这个轴的正上方。','左から見た図。頭ヨーの軸がこの軸の真上にあります。'],
  'ref.32':['Seen from above. The head faces straight ahead.','从上方看。头朝正前方。','上から見た図。頭はまっすぐ前を向いています。'],
  'ref.33':['Seen from the front. The head is level from side to side.','从正面看。头部左右水平。','正面から見た図。頭は左右に傾いていません。'],
  'ref.34':[
    'Not in the training model. Center it with the beak closed: walking holds 0° and Pick opens it to 30°.',
    '训练模型里没有嘴。请在嘴闭合时归中：行走时保持 0°，拾取时张开到 30°。',
    '学習モデルには含まれていません。くちばしを閉じた状態で中心を合わせてください。歩行中は 0° を保ち、拾う動作で 30° まで開きます。'],

  // Servo setup page
  'servo.pageTitle':['Servo setup · XGO Duck','舵机设置 · XGO Duck','サーボ設定 · XGO Duck'],
  'servo.warn':[
    'When changing an ID, connect only the servo you want to change. Duplicate IDs cannot be distinguished on the same bus.',
    '修改 ID 时，只接上要修改的那一个舵机。同一总线上重复的 ID 无法区分。',
    'ID を変更するときは、変更したいサーボだけを接続してください。同じバス上で重複した ID は区別できません。'],
  'servo.intro':['Scan for servos, then select an ID to read or change its settings.','先扫描舵机，再选择一个 ID 读取或修改它的设置。','サーボをスキャンしてから、ID を選んで設定を読み取るか変更してください。'],
  'servo.scan':['Scan all IDs','扫描全部 ID','すべての ID をスキャン'],
  'servo.stopScan':['Stop scan','停止扫描','スキャン停止'],
  'servo.scanIdle':['Scan IDs 0–253 to find connected servos.','扫描 ID 0–253，查找已连接的舵机。','ID 0〜253 をスキャンして、接続されたサーボを探します。'],
  'servo.progressLabel':['Servo scan progress','舵机扫描进度','サーボのスキャン進捗'],
  'servo.resultsLabel':['Discovered servo IDs','找到的舵机 ID','見つかったサーボの ID'],
  'servo.scanHint':[
    'Select a found ID to read or change that servo\'s settings. Stop scan keeps the results found so far. IDs 254 and 255 are reserved.',
    '选择找到的 ID 来读取或修改该舵机的设置。停止扫描会保留已找到的结果。ID 254 和 255 是保留的。',
    '見つかった ID を選ぶと、そのサーボの設定を読み取ったり変更したりできます。スキャンを止めても、それまでの結果は残ります。ID 254 と 255 は予約済みです。'],
  'servo.resetMid':['Reset Mid','重设中位','中心をリセット'],
  'servo.gainsLabel':['Set KP/KD','设置 KP/KD','KP/KD 設定'],
  'servo.setGains':['Set KpKd','写入 KpKd','KpKd 書込'],
  'servo.newIdLabel':['Change ID to','把 ID 改为','ID の変更先'],
  'servo.newId':['New ID','新 ID','新しい ID'],
  'servo.setId':['Change ID','修改 ID','ID を変更'],
  'servo.read':['Read','读取','読み取り'],
  'servo.protection':['All-servo voltage / overcurrent protection','全部舵机的电压 / 过流保护','全サーボの電圧・過電流保護'],
  'servo.enable':['Enable','启用','有効にする'],
  'servo.disable':['Disable','禁用','無効にする'],
  'servo.notApplied':['Not applied','未应用','未適用'],
  'servo.currentLabel':['Protection current in amperes','保护电流（安培）','保護電流（アンペア）'],
  'servo.setCurrent':['Set protection current','设置保护电流','保護電流を設定'],
  'servo.protectionHint':[
    'Enable / Disable changes only the protection switch. Set protection current changes only the current threshold. Both operations broadcast to every servo; no scan or ID selection is needed. Overheat protection stays enabled, and stored voltage limits are unchanged. Current resolution is 6.5 mA. Broadcast writes have no per-servo acknowledgement.',
    '“启用 / 禁用”只改变保护开关，“设置保护电流”只改变电流阈值。两者都会广播给所有舵机，不需要扫描或选择 ID。过热保护始终开启，已保存的电压限制不变。电流精度为 6.5 mA。广播写入没有逐个舵机的确认。',
    '「有効にする / 無効にする」は保護のオン・オフだけを、「保護電流を設定」は電流のしきい値だけを変えます。どちらも全サーボにブロードキャストするので、スキャンや ID の選択は不要です。過熱保護は常に有効で、保存済みの電圧制限は変わりません。電流の分解能は 6.5 mA です。ブロードキャストの書き込みには、サーボごとの確認応答がありません。'],
  'servo.selected':['Selected ID {id}','已选择 ID {id}','ID {id} を選択しました'],
  'servo.badId':['ID must be between 0 and 253','ID 必须在 0 到 253 之间','ID は 0〜253 の範囲で指定してください'],
  'servo.noFeedback':['No MCU feedback. Servo setup is not ready.','没有 MCU 反馈，舵机设置还没准备好。','MCU からの応答がありません。サーボ設定の準備ができていません。'],
  'servo.stopping':['Stopping scan…','正在停止扫描…','スキャンを停止しています…'],
  'servo.closed':['Servo setup closed','舵机设置已关闭','サーボ設定を終了しました'],
  'servo.changing':['Changing ID {id} to {to}…','正在把 ID {id} 改为 {to}…','ID {id} を {to} に変更しています…'],
  'servo.working':['ID {id} · {action}…','ID {id} · {action}…','ID {id} · {action}…'],
  'servo.readout':['ID {id} · Pos {pos} · KP {kp} · KD {kd}','ID {id} · 位置 {pos} · KP {kp} · KD {kd}','ID {id} · 位置 {pos} · KP {kp} · KD {kd}'],
  'servo.readDone':['ID {id} · parameters read','ID {id} · 参数已读取','ID {id} · パラメーターを読み取りました'],
  'servo.midDone':['ID {id} · Mid reset sent. Servo remains unloaded.','ID {id} · 已发送重设中位，舵机保持卸力。','ID {id} · 中心リセットを送信しました。サーボは脱力したままです。'],
  'servo.idChanged':['ID changed. Scan again to select the updated servo.','ID 已修改。请重新扫描，再选择修改后的舵机。','ID を変更しました。もう一度スキャンして、変更後のサーボを選んでください。'],
  'servo.idDone':['ID {id} → {to} · verified','ID {id} → {to} · 已验证','ID {id} → {to} · 確認済み'],
  'servo.gainsDone':['ID {id} · KP/KD written','ID {id} · KP/KD 已写入','ID {id} · KP/KD を書き込みました'],
  'servo.preparing':['Preparing scan…','正在准备扫描…','スキャンを準備しています…'],
  'servo.deploy':['Deploy the updated project to enable servo setup.','请部署更新后的项目以启用舵机设置。','サーボ設定を使うには、更新したプロジェクトをデプロイしてください。'],
  'servo.badScanReply':['Invalid scan reply','扫描回复无效','スキャンの応答が不正です'],
  'servo.scanningTorqueOff':['Scanning · torque off','扫描中 · 扭矩已关','スキャン中 · トルクオフ'],
  'servo.scanning':['Scanning ID {id} · {checked}/254 checked · {found} found','正在扫描 ID {id} · 已检查 {checked}/254 · 找到 {found} 个','ID {id} をスキャン中 · {checked}/254 確認済み · {found} 個検出'],
  'servo.scanDone':['Scan complete · 254 IDs checked · {found} found','扫描完成 · 已检查 254 个 ID · 找到 {found} 个','スキャン完了 · 254 個の ID を確認 · {found} 個検出'],
  'servo.selectFound':['Select a found ID to read or change its settings.','选择找到的 ID 来读取或修改它的设置。','見つかった ID を選んで、設定を読み取るか変更してください。'],
  'servo.noneFound':['No servos replied. Check servo power, bus connection and baud rate.','没有舵机回应。请检查舵机电源、总线连接和波特率。','応答したサーボがありません。サーボの電源、バスの接続、ボーレートを確認してください。'],
  'servo.scanStopped':['Stopped','已停止','停止'],
  'servo.scanFailed':['Scan failed','扫描失败','スキャン失敗'],
  'servo.partial':['{state} · {checked}/254 checked · {found} found (partial results)','{state} · 已检查 {checked}/254 · 找到 {found} 个（部分结果）','{state} · {checked}/254 確認済み · {found} 個検出（途中までの結果）'],
  'servo.stoppedMessage':['Scan stopped. Select a found ID to continue.','扫描已停止。选择找到的 ID 继续。','スキャンを停止しました。見つかった ID を選んで続けてください。'],
  'servo.noReply':['No MCU reply. Scan stopped.','没有 MCU 回复，扫描已停止。','MCU から応答がないため、スキャンを停止しました。'],
  'servo.badCurrent':['Enter a protection current between 0 and 425.9775 A.','请输入 0 到 425.9775 A 之间的保护电流。','保護電流は 0〜425.9775 A の範囲で入力してください。'],
  'servo.broadcasting':['Broadcasting protection settings to all servos…','正在向所有舵机广播保护设置…','全サーボに保護設定をブロードキャストしています…'],
  'servo.badBroadcastReply':['Invalid broadcast reply','广播回复无效','ブロードキャストの応答が不正です'],
  'servo.currentSent':['Broadcast sent · {a} A','已广播 · {a} A','ブロードキャスト送信済み · {a} A'],
  'servo.protectionOn':['Broadcast sent · voltage / overcurrent on','已广播 · 电压 / 过流保护：开','ブロードキャスト送信済み · 電圧・過電流保護：オン'],
  'servo.protectionOff':['Broadcast sent · voltage / overcurrent off','已广播 · 电压 / 过流保护：关','ブロードキャスト送信済み · 電圧・過電流保護：オフ'],
  'servo.broadcastDone':['Protection broadcast sent. Individual servo writes are not verified.','保护设置已广播。各个舵机的写入没有逐一验证。','保護設定をブロードキャストしました。サーボごとの書き込みは確認していません。'],

  // Pairing page
  'pair.pageTitle':['Pairing · XGO Duck','配对 · XGO Duck','ペアリング · XGO Duck'],
  'pair.duckId':['Duck ID','鸭子 ID','ダック ID'],
  'pair.print':['Print sticker','打印贴纸','ステッカーを印刷'],
  'pair.claim':['I have saved the sticker','我已保存贴纸','ステッカーを保存しました'],
  'pair.stickerHint':[
    'The QR code holds this duck\'s ID and pairing key; the phone app will scan it to pair. Print sticker prints it 30 mm wide. Stick it under the duck or on the battery bracket.',
    '二维码里有这只鸭子的 ID 和配对密钥，手机 App 扫描它来配对。“打印贴纸”会按 30 mm 宽打印。把它贴在鸭子底部或电池支架上。',
    'QR コードにはこのダックの ID とペアリングキーが入っていて、スマホアプリが読み取ってペアリングします。「ステッカーを印刷」で幅 30 mm で印刷されます。ダックの底面かバッテリーブラケットに貼ってください。'],
  'pair.openHint':[
    'Anyone on this network can open this page until you press I have saved the sticker. After that the duck never shows its pairing key over the network again.',
    '在你按下“我已保存贴纸”之前，同一网络里的任何人都能打开本页。按下之后，鸭子不会再通过网络显示配对密钥。',
    '「ステッカーを保存しました」を押すまでは、同じネットワークの誰でもこのページを開けます。押した後は、ダックがネットワーク経由でペアリングキーを表示することはありません。'],
  'pair.claimed':[
    'The sticker is saved. The duck no longer shows its pairing key over the network.',
    '贴纸已保存。鸭子不再通过网络显示配对密钥。',
    'ステッカーは保存済みです。ダックはネットワーク経由でペアリングキーを表示しません。'],
  'pair.lostHint':[
    'Lost the sticker? Delete <code>data/identity.json</code> in the app folder on the board and restart the app. The duck gets a new ID and sticker, and the old sticker stops working.',
    '贴纸丢了？删除板子上 App 文件夹里的 <code>data/identity.json</code>，然后重启 App。鸭子会生成新的 ID 和贴纸，旧贴纸随之失效。',
    'ステッカーをなくしたら、ボード上のアプリフォルダにある <code>data/identity.json</code> を削除してアプリを再起動します。ダックに新しい ID とステッカーが作られ、古いステッカーは使えなくなります。'],
  'pair.access':['Access','访问控制','アクセス'],
  'pair.require':['Require pairing on this network','在此网络上要求配对','このネットワークでペアリングを必須にする'],
  'pair.requireHint':[
    'When this is on, only paired phones and browsers can move the duck or change its settings; everyone else can still see its status. Turning it on needs this browser to be paired first. If you get locked out, delete <code>data/access.json</code> on the board and restart the app.',
    '打开后，只有已配对的手机和浏览器能控制鸭子或修改设置，其他人仍能查看状态。要打开它，这个浏览器需要先配对。如果把自己锁在外面了，删除板子上的 <code>data/access.json</code> 并重启 App。',
    'オンにすると、ペアリング済みのスマホとブラウザだけがダックを動かしたり設定を変えたりできます。ほかの人も状態は見られます。オンにするには、先にこのブラウザをペアリングする必要があります。締め出されてしまったら、ボード上の <code>data/access.json</code> を削除してアプリを再起動してください。'],
  'pair.thisBrowser':['This browser','此浏览器','このブラウザ'],
  'pair.secret':['Pairing link or key','配对链接或密钥','ペアリングリンクまたはキー'],
  'pair.name':['Name','名称','名前'],
  'pair.defaultName':['Browser','浏览器','ブラウザ'],
  'pair.pair':['Pair this browser','配对此浏览器','このブラウザをペアリング'],
  'pair.unpair':['Unpair this browser','取消此浏览器的配对','このブラウザのペアリングを解除'],
  'pair.pairHint':[
    'Before the sticker is saved, Pair this browser works with the field empty. Afterwards, scan the sticker with the phone camera and paste the link it shows. Pairing is per address: opening the page at a new address needs pairing again.',
    '保存贴纸之前，输入框留空也能直接“配对此浏览器”。保存之后，请用手机相机扫描贴纸，把显示的链接粘贴进来。配对按地址区分：换一个地址打开页面需要重新配对。',
    'ステッカーを保存する前は、入力欄が空のままでも「このブラウザをペアリング」できます。保存後は、スマホのカメラでステッカーを読み取り、表示されたリンクを貼り付けてください。ペアリングはアドレスごとです。別のアドレスでページを開くと、もう一度ペアリングが必要です。'],
  'pair.pairedList':['Paired phones and browsers','已配对的手机和浏览器','ペアリング済みのスマホとブラウザ'],
  'pair.saved':['Pairing sticker saved','配对贴纸已保存','ペアリングステッカーは保存済みです'],
  'pair.printPrompt':['Print this sticker, then press I have saved the sticker.','请打印这张贴纸，然后按“我已保存贴纸”。','このステッカーを印刷してから「ステッカーを保存しました」を押してください。'],
  'pair.required':['· pairing required','· 需要配对','· ペアリング必須'],
  'pair.open':['· open on this network','· 对此网络开放','· このネットワークに公開中'],
  'pair.pairedAs':['· paired as {name}','· 已配对为 {name}','· {name} としてペアリング済み'],
  'pair.notPaired':['· not paired','· 未配对','· 未ペアリング'],
  'pair.you':[' · this browser',' · 此浏览器',' · このブラウザ'],
  'pair.remove':['Remove','移除','削除'],
  'pair.confirmRemove':['Remove {name}? It will need to pair again.','要移除 {name} 吗？它需要重新配对。','{name} を削除しますか？もう一度ペアリングが必要になります。'],
  'pair.removed':['{name} removed','已移除 {name}','{name} を削除しました'],
  'pair.none':['None yet','还没有','まだありません'],
  'pair.confirmClaim':[
    'Have you printed or saved the sticker? After this the duck never shows its pairing key over the network again.',
    '你已经打印或保存贴纸了吗？之后鸭子不会再通过网络显示配对密钥。',
    'ステッカーを印刷または保存しましたか？この後、ダックはネットワーク経由でペアリングキーを表示しなくなります。'],
  'pair.scanPrompt':['Scan the sticker with the phone camera and paste the link it shows.','请用手机相机扫描贴纸，把显示的链接粘贴进来。','スマホのカメラでステッカーを読み取り、表示されたリンクを貼り付けてください。'],
  'pair.paired':['This browser is paired','此浏览器已配对','このブラウザをペアリングしました'],
  'pair.confirmUnpair':[
    'Unpair this browser? If pairing is required, it will no longer be able to move the duck.',
    '要取消此浏览器的配对吗？如果开启了“要求配对”，它将无法再控制鸭子。',
    'このブラウザのペアリングを解除しますか？ペアリングが必須の場合、ダックを動かせなくなります。'],
  'pair.unpaired':['This browser is unpaired','已取消此浏览器的配对','このブラウザのペアリングを解除しました'],
  'pair.confirmRequire':[
    'Only paired phones and browsers will be able to move the duck or change its settings. Turn this on?',
    '之后只有已配对的手机和浏览器能控制鸭子或修改设置。确定打开吗？',
    'ペアリング済みのスマホとブラウザだけがダックを動かしたり設定を変えたりできるようになります。オンにしますか？'],
  'pair.nowRequired':['Pairing is now required','现在需要配对了','ペアリングが必須になりました'],
  'pair.nowOpen':['The duck is open on this network again','鸭子重新对此网络开放','ダックはこのネットワークに再び公開されました'],
  'pair.badSecret':['Paste the pairing link from the sticker, or its 22-character key.','请粘贴贴纸上的配对链接，或它的 22 位密钥。','ステッカーのペアリングリンクか、22 文字のキーを貼り付けてください。'],
  'pair.wrongDuck':['This sticker belongs to duck {id}, not {current}.','这张贴纸属于鸭子 {id}，不是 {current}。','このステッカーはダック {id} のもので、{current} のものではありません。'],
  'pair.challengeFailed':['Challenge failed','获取配对挑战失败','チャレンジの取得に失敗しました'],
  'pair.failed':['Pairing failed','配对失败','ペアリングに失敗しました'],

  // 3D view page
  'view.pageTitle':['3D view · XGO Duck','3D 视图 · XGO Duck','3D ビュー · XGO Duck'],
  'view.title':['3D view','3D 视图','3D ビュー'],
  'view.loading':['Loading the model…','正在加载模型…','モデルを読み込んでいます…'],
  'view.live':['Live pose','实时姿态','ライブ姿勢'],
  'view.tilt':['Tilt from IMU','用 IMU 倾斜','IMU で傾ける'],
  'view.parts':['Add-on parts','扩展部件','追加パーツ'],
  'view.reset':['Reset view','重置视角','視点をリセット'],
  'view.hint':[
    'Drag to rotate, scroll or pinch to zoom, right-drag or drag with two fingers to pan. Live pose follows the servo feedback ten times a second; without feedback the duck stands in its default pose. The mouth is not modelled. Add-on parts shows where the planned USB camera, hub, sound card and speaker go, with the head see-through.',
    '拖动旋转，滚轮或双指捏合缩放，右键拖动或双指拖动平移。实时姿态每秒按舵机反馈更新十次；没有反馈时鸭子保持默认姿态。模型里没有嘴。“扩展部件”会显示计划中的 USB 摄像头、集线器、声卡和喇叭装在哪里，并把头部变成半透明。',
    'ドラッグで回転、スクロールかピンチでズーム、右ドラッグか 2 本指ドラッグで移動します。ライブ姿勢はサーボのフィードバックに合わせて毎秒 10 回更新し、フィードバックがないときはデフォルト姿勢で立ちます。くちばしはモデル化していません。「追加パーツ」では、予定している USB カメラ、ハブ、サウンドカード、スピーカーの取り付け位置を、頭を透かして表示します。'],
  'view.missing':['{file} missing','缺少 {file}','{file} がありません'],
  'view.default':['Showing the default pose','正在显示默认姿态','デフォルト姿勢を表示しています'],
  'view.liveStatus':['Live · {hz} Hz feedback · {n}/15 servos','实时 · 反馈 {hz} Hz · 舵机 {n}/15','ライブ · フィードバック {hz} Hz · サーボ {n}/15'],
  'view.noFeedback':['No servo feedback: showing the default pose','没有舵机反馈：显示默认姿态','サーボの応答がないため、デフォルト姿勢を表示しています'],
  'view.notLoaded':['3D model not loaded: {error}','3D 模型未加载：{error}','3D モデルを読み込めませんでした：{error}'],
  // Add-on parts by their id in assets/model/model.json; the model's own English text is the fallback.
  'part.camera':['USB camera','USB 摄像头','USB カメラ'],
  'part.camera.note':['Inside the head; the lens looks out through the eye.','在头里，镜头从眼睛处往外看。','頭の中にあり、レンズが目の部分から外を見ます。'],
  'part.hub':['USB hub','USB 集线器','USB ハブ'],
  'part.hub.note':['On the Uno Q\'s USB-C, folded flat along the board\'s top edge.','插在 Uno Q 的 USB-C 上，沿板子上边缘平折。','Uno Q の USB-C に挿し、ボードの上端に沿って平らに折りたたみます。'],
  'part.sound':['Sound card','声卡','サウンドカード'],
  'part.sound.note':['Right side of the body, above the thigh.','身体右侧，大腿上方。','胴体の右側、太ももの上。'],
  'part.speaker':['Speaker','喇叭','スピーカー'],
  'part.speaker.note':['Left side of the body, above the thigh.','身体左侧，大腿上方。','胴体の左側、太ももの上。'],
};

function xgoLang(){
  const pick=code=>Object.keys(XGO_LANGS).find(l=>String(code||'').toLowerCase().startsWith(l));
  let saved=null;
  try{saved=localStorage.getItem(XGO_LANG_KEY);}catch(e){}
  return pick(new URLSearchParams(location.search).get('lang'))||pick(saved)
    ||(navigator.languages||[navigator.language]).map(pick).find(Boolean)||'en';
}
const XGO_LANG=xgoLang();
const XGO_LANG_INDEX=Object.keys(XGO_LANGS).indexOf(XGO_LANG);

function t(key,vars,fallback){
  const entry=I18N[key];
  const text=entry?entry[XGO_LANG_INDEX]??entry[0]:fallback??key;
  return vars?text.replace(/\{(\w+)\}/g,(m,name)=>name in vars?vars[name]:m):text;
}
function xgoApplyI18n(root=document){
  root.querySelectorAll('[data-i18n]').forEach(el=>{el.textContent=t(el.dataset.i18n);});
  root.querySelectorAll('[data-i18n-html]').forEach(el=>{el.innerHTML=t(el.dataset.i18nHtml);});
  root.querySelectorAll('[data-i18n-attr]').forEach(el=>el.dataset.i18nAttr.split(',').forEach(pair=>{
    const [attr,key]=pair.split(':');el.setAttribute(attr,t(key));
  }));
}

document.documentElement.lang=XGO_HTML_LANG[XGO_LANG];
xgoApplyI18n();
{
  // Switching reloads the page so text built by the page scripts is redone as well.
  const picker=document.createElement('select');
  picker.className='lang';picker.setAttribute('aria-label',t('lang.label'));
  for(const [code,name] of Object.entries(XGO_LANGS))picker.add(new Option(name,code,false,code===XGO_LANG));
  picker.onchange=()=>{
    const url=new URL(location.href);
    try{localStorage.setItem(XGO_LANG_KEY,picker.value);url.searchParams.delete('lang');}
    catch(e){url.searchParams.set('lang',picker.value);}
    location.replace(url);
  };
  // Top-right corner of the page, on its own row above the header.
  const bar=document.createElement('div');
  bar.className='lang-bar';bar.append(picker);
  document.querySelector('main')?.prepend(bar);
}
