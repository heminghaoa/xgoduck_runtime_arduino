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
