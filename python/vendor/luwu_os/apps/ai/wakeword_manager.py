#!/usr/bin/env python3
"""
唤醒词检测管理器 - "小陆同学"

按 /opt/luwu-os/deploy-cm5/inference.py 的方式实现：
- onnxruntime CPU 推理
- melspectrogram.onnx + embedding_model.onnx + xiaolu_classmate.onnx
- sounddevice 实时采集，归一化浮点样本转换到模型要求的 PCM16 幅值
- 16000Hz / 2秒推理窗口 / 每0.5秒滑动一次

模型文件: /opt/luwu-os/model/xiaolu_classmate.onnx
"""

import os
import sys
import time
import math
import threading
from collections import deque
from contextlib import nullcontext

import numpy as np

# ── 路径与常量 ────────────────────────────────────────
LUWU_ROOT = os.environ.get("LUWU_ROOT", "/opt/luwu-os")
MODEL_DIR = os.path.join(LUWU_ROOT, "model")
MODEL_PATH = os.path.join(MODEL_DIR, "xiaolu_classmate.onnx")
EN_MODEL_PATH = os.path.join(MODEL_DIR, "hi_luka_qwen.onnx")
MEL_ONNX = os.path.join(MODEL_DIR, "melspectrogram.onnx")
EMBEDDING_ONNX = os.path.join(MODEL_DIR, "embedding_model.onnx")
SAMPLE_RATE = 16000
EMBEDDING_WINDOW = 76
EMBEDDING_STRIDE = 8
MIN_EMBEDDINGS = 16
CLIP_DURATION = 2.0
STRIDE_DURATION = 0.5
CLIP_SAMPLES = int(SAMPLE_RATE * CLIP_DURATION)
STRIDE_SAMPLES = int(SAMPLE_RATE * STRIDE_DURATION)
THRESHOLD = 0.1
COOLDOWN_SEC = 1.5
MAX_SCORING_AGE = .5


class SpeechGate:
    """Did somebody speak in the last two seconds? (DRADUCK, 2026-11-25)

    A wake model can score high on the microphone's own noise: the lab duck woke three times in half an hour
    with nobody speaking, on audio within 4 dB of the room's noise in every band. A spoken wake word stands
    well over that noise for most of a second. So: the power between 300 and 3000 Hz of each 80 ms frame,
    against the noise floor (a low percentile of the last 30 s), and a wake counts only when enough of the
    last two seconds' frames stand `rise_db` over the floor. Levels are relative, so microphone gain and the
    PCM scale don't matter. The floor outlives a restart of the listening thread."""
    FRAME = 1280                # 80 ms at 16 kHz
    WINDOW = 25                 # frames in the model's two seconds
    FLOOR_FRAMES = 375          # 30 s
    FLOOR_PERCENTILE = 20
    LOW_HZ, HIGH_HZ = 300, 3000

    def __init__(self, rise_db, frames):
        if (isinstance(rise_db, bool) or not isinstance(rise_db, (int, float)) or not math.isfinite(rise_db)
                or not 3 <= rise_db <= 30):
            raise ValueError('speech rise_db must be 3–30')
        if type(frames) is not int or not 1 <= frames <= self.WINDOW:
            raise ValueError(f'speech frames must be 1–{self.WINDOW}')
        self.ratio, self.frames = 10 ** (rise_db / 10), frames
        freq = np.fft.rfftfreq(self.FRAME, 1 / SAMPLE_RATE)
        self._band = (freq >= self.LOW_HZ) & (freq < self.HIGH_HZ)
        self._hann = np.hanning(self.FRAME).astype(np.float32)
        self._rest = np.zeros(0, dtype=np.float32)
        self._floor = deque(maxlen=self.FLOOR_FRAMES)
        self._recent = deque(maxlen=self.WINDOW)

    def reset(self):
        """The audio stream broke: the two seconds start again; the noise floor stays."""
        self._rest = np.zeros(0, dtype=np.float32)
        self._recent.clear()

    def feed(self, audio):
        audio = np.concatenate([self._rest, np.asarray(audio, dtype=np.float32).reshape(-1)])
        whole = len(audio) - len(audio) % self.FRAME
        for start in range(0, whole, self.FRAME):
            spectrum = np.fft.rfft(audio[start:start + self.FRAME] * self._hann)
            power = float((np.abs(spectrum[self._band]) ** 2).sum()) + 1e-12
            self._floor.append(power)
            self._recent.append(power)
        self._rest = audio[whole:]

    def loud_frames(self):
        """How many of the last two seconds' frames stand over the noise floor."""
        if len(self._floor) < self.WINDOW:
            return 0
        floor = float(np.percentile(self._floor, self.FLOOR_PERCENTILE))
        return sum(power >= floor * self.ratio for power in self._recent)

    def spoke(self):
        return self.loud_frames() >= self.frames


class WakeWordManager:
    """唤醒词检测管理器"""

    def __init__(self, on_wakeup=None, on_ready=None, model_path=None, threshold=None, device=None,
                 on_audio=None, input_transform=None, input_scale=None, stride_duration=None,
                 cooldown_sec=None, input_channels=1, input_latency=.32, shared_input=False,
                 detection_context=None, *, threshold_for_context=None, confirm_windows=1,
                 speech_rise_db=None, speech_frames=4):
        """
        Args:
            on_wakeup: 检测到唤醒词后的回调
            on_ready: 模型加载并打开音频流后的回调
            model_path: 模型文件路径
            threshold: 触发阈值，默认 0.1
            device: 麦克风设备索引，默认系统默认设备
            on_audio: 可选 PCM 旁路 (16kHz float32 单声道)，回调必须快速返回
            input_transform: 可选采集增益，在推理线程中处理，不修改声卡回调数据
            input_scale: 32768 为原 PCM16 幅值模型；1 为归一化音频训练的模型
            stride_duration: 推理间隔秒数，默认 0.5；新模型可指定 0.08
            cooldown_sec: 触发间隔秒数，默认 1.5
            shared_input: 由聊天采集流通过 feed_pcm 提供单声道 PCM16
            detection_context: 可选。返回当前检测上下文，None 时只更新窗口。
                启用时命中后继续监听，并把检测上下文传给回调。
            threshold_for_context: 可选。根据检测上下文和默认阈值返回本次阈值。
            confirm_windows: 连续多少个推理窗口达到阈值才触发，默认 1（原行为）。
                说出的唤醒词会让相邻窗口连续高分；背景噪声常只让单个窗口冲高。
            speech_rise_db: 可选。启用人声能量门限 (SpeechGate)：最近 2 秒内至少 speech_frames 个
                80ms 帧的 300–3000Hz 能量高出底噪这么多 dB 才允许触发。默认 None（不启用，原行为）。
        """
        self._on_wakeup = on_wakeup
        self._on_ready = on_ready
        self._model_path = model_path or MODEL_PATH
        self._threshold = threshold if threshold is not None else THRESHOLD
        self._device = device
        if type(input_channels) is not int or input_channels not in (1, 2):
            raise ValueError('input_channels must be 1 or 2')
        if (isinstance(input_latency, bool) or not isinstance(input_latency, (int, float))
                or not math.isfinite(input_latency) or not .16 <= input_latency <= .6):
            raise ValueError('wake input_latency must be 0.16–0.6 seconds')
        self._input_channels, self._input_latency = input_channels, input_latency
        self._capture_stats = dict(callbacks=0, input_overflows=0, queue_drops=0,
                                   stale_blocks=0, catchup_blocks=0, discontinuities=0,
                                   input_latency_ms=None)
        self._shared_input = shared_input
        self._detection_context = detection_context
        self._threshold_for_context = threshold_for_context
        if type(confirm_windows) is not int or not 1 <= confirm_windows <= 8:
            raise ValueError('confirm_windows must be 1–8')
        self._confirm_windows = confirm_windows
        self._speech_gate = None if speech_rise_db is None else SpeechGate(speech_rise_db, speech_frames)
        self._feed_queue = None
        self._on_audio = on_audio
        self._input_transform = input_transform or (lambda samples: samples[:, 0] if samples.ndim == 2 else samples)
        self._input_scale = 32768. if input_scale is None else input_scale
        if (isinstance(self._input_scale, bool) or self._input_scale not in (1., 32768.)):
            raise ValueError('input_scale must be 1 or 32768')
        self._stride_duration = STRIDE_DURATION if stride_duration is None else stride_duration
        self._cooldown_sec = COOLDOWN_SEC if cooldown_sec is None else cooldown_sec
        for name, value, low, high in (('stride_duration', self._stride_duration, .04, .5),
                                      ('cooldown_sec', self._cooldown_sec, 1., 5.)):
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(value) or not low <= value <= high):
                raise ValueError(f'{name} must be {low}–{high} seconds')
        self._stride_samples = round(SAMPLE_RATE * self._stride_duration)
        # Adjacent 80 ms windows share most embeddings. Reuse only byte-identical
        # mel windows; changed context/normalization always runs the real graph.
        self._embedding_cache = {} if self._input_scale == 1. else None
        self._embedding_cache_hits = self._embedding_cache_misses = 0

        self._running = False
        self._thread = None
        self._model = None
        self._available = all(os.path.exists(p) for p in (self._model_path, MEL_ONNX, EMBEDDING_ONNX))

        if self._available:
            print(f"[WakeWord] 模型文件就绪: {self._model_path}", flush=True)
            print(f"[WakeWord] 预处理模型就绪: {MEL_ONNX}, {EMBEDDING_ONNX}", flush=True)
        else:
            print(
                f"[WakeWord] 模型文件缺失: classifier={self._model_path} "
                f"mel={MEL_ONNX} embedding={EMBEDDING_ONNX}",
                flush=True,
            )

    def is_available(self) -> bool:
        """检查唤醒词功能是否可用"""
        return self._available

    def start(self) -> bool:
        """开始监听唤醒词"""
        if not self.is_available():
            print("[WakeWord] 模型不可用，无法启动监听", flush=True)
            return False

        if self._running:
            print("[WakeWord] 已在监听中，忽略重复启动", flush=True)
            return True

        self._running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            name="wakeword_listener",
            daemon=True,
        )
        self._thread.start()
        print("[WakeWord] 开始监听唤醒词...", flush=True)
        return True

    def stop(self):
        """停止监听唤醒词"""
        if not self._running:
            return

        print("[WakeWord] 停止监听唤醒词", flush=True)
        self._running = False

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self._thread = None

    def cleanup(self):
        """释放资源"""
        self.stop()
        self._model = None
        print("[WakeWord] 资源已释放", flush=True)

    def _load_model(self):
        """加载 inference.py 所需的三个 ONNX 模型"""
        try:
            import onnxruntime as ort

            opts = ort.SessionOptions()
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            opts.intra_op_num_threads = 1
            opts.inter_op_num_threads = 1

            mel_session = ort.InferenceSession(str(MEL_ONNX), opts, providers=["CPUExecutionProvider"])
            emb_session = ort.InferenceSession(str(EMBEDDING_ONNX), opts, providers=["CPUExecutionProvider"])
            cls_session = ort.InferenceSession(str(self._model_path), opts, providers=["CPUExecutionProvider"])

            self._model = {
                "mel_session": mel_session,
                "mel_input": mel_session.get_inputs()[0].name,
                "emb_session": emb_session,
                "emb_input": emb_session.get_inputs()[0].name,
                "cls_session": cls_session,
                "cls_input": cls_session.get_inputs()[0].name,
            }
            if self._embedding_cache is not None:
                self._embedding_cache.clear()
                self._embedding_cache_hits = self._embedding_cache_misses = 0
            print(f"[WakeWord] ONNX模型加载成功: {self._model_path}", flush=True)
            return True
        except ImportError:
            print("[WakeWord] onnxruntime 未安装，唤醒词功能不可用", flush=True)
        except Exception as e:
            print(f"[WakeWord] 模型加载失败: {e}", flush=True)
        return False

    def _compute_mel(self, audio: np.ndarray) -> np.ndarray:
        """16 kHz float capture → this classifier's training amplitude range → mel."""
        if audio.ndim == 1:
            audio = audio[np.newaxis, :]
        # The matching openWakeWord graph is trained with PCM16 amplitudes,
        # even though its ONNX tensor dtype is float32. Feeding [-1, 1] loses
        # quiet speech detail at the graph's mel/log floor. Classifiers trained
        # by the normalized livekit frontend instead explicitly select scale 1.
        pcm = audio.astype(np.float32)
        if self._input_scale == 32768.:
            pcm = np.clip(pcm * 32768.0, -32768.0, 32767.0)
        out = self._model["mel_session"].run(None, {self._model["mel_input"]: pcm})[0]
        if out.ndim == 4:
            out = out[0, 0, :, :]
        elif out.ndim == 3:
            out = out[0, :, :]
        return out / 10.0 + 2.0

    def _compute_embeddings(self, mel: np.ndarray) -> np.ndarray:
        """Sliding-window embeddings: (time_frames, 32) → (n_windows, 96)"""
        time_frames = mel.shape[0]
        n_windows = max(0, (time_frames - EMBEDDING_WINDOW) // EMBEDDING_STRIDE + 1)
        if n_windows < MIN_EMBEDDINGS:
            return np.zeros((0, 96), dtype=np.float32)
        windows = np.stack(
            [
                mel[i * EMBEDDING_STRIDE : i * EMBEDDING_STRIDE + EMBEDDING_WINDOW, :]
                for i in range(n_windows)
            ],
            axis=0,
        )
        if self._embedding_cache is not None:
            keys = [window.tobytes() for window in windows]
            missing = {key: window for key, window in zip(keys, windows)
                       if key not in self._embedding_cache}
            self._embedding_cache_hits += len(keys) - len(missing)
            self._embedding_cache_misses += len(missing)
            if missing:
                batch = np.stack(list(missing.values()))[..., np.newaxis].astype(np.float32)
                out = self._model['emb_session'].run(None, {self._model['emb_input']: batch})[0]
                for key, embedding in zip(missing, out.squeeze(axis=(1, 2))):
                    self._embedding_cache[key] = embedding.copy()
            embeddings = np.stack([self._embedding_cache[key] for key in keys])
            while len(self._embedding_cache) > 32:
                self._embedding_cache.pop(next(iter(self._embedding_cache)))
            return embeddings
        emb_out = self._model["emb_session"].run(
            None,
            {self._model["emb_input"]: windows[..., np.newaxis].astype(np.float32)},
        )[0]
        return emb_out.squeeze(axis=(1, 2))

    def _predict(self, audio: np.ndarray) -> float:
        """执行完整 inference.py 推理 pipeline，返回置信度"""
        mel = self._compute_mel(audio)
        embeddings = self._compute_embeddings(mel)
        if embeddings.shape[0] < MIN_EMBEDDINGS:
            return 0.0
        emb_sequence = embeddings[-MIN_EMBEDDINGS:, :]
        emb_input_arr = emb_sequence[np.newaxis, :, :].astype(np.float32)
        outputs = self._model["cls_session"].run(None, {self._model["cls_input"]: emb_input_arr})
        return float(outputs[0][0, 0])

    def _listen_loop(self):
        """后台线程用配置的步长检测 2 秒音频窗口。"""
        if not self._shared_input:
            try:
                import sounddevice as sd
            except ImportError:
                print("[WakeWord] sounddevice 未安装，无法监听", flush=True)
                self._running = False
                return

        if not self._load_model() or not self._running:
            self._running = False
            return

        # Hard memory bound plus a worker-side age limit. Dropped blocks reset
        # the two-second window instead of stitching discontinuous speech.
        queue_stride = min(self._stride_duration, .06) if self._shared_input else self._stride_duration
        audio_queue = deque(maxlen=max(4, math.ceil(CLIP_DURATION / queue_stride) + 2))
        stats = self._capture_stats
        sequence = 0
        last_trigger = -math.inf
        over = over_peak = ignored = 0           # consecutive windows at or over the threshold; lone spikes dropped
        gate = self._speech_gate
        quiet_until = -math.inf                  # a high score with nobody speaking is logged once per cooldown
        peak_score = 0.0
        chunk_count = 0
        last_diag = time.time()
        woke = False

        def audio_callback(indata, frames, time_info, status):
            nonlocal sequence
            sequence += 1
            stats['callbacks'] += 1
            if status and getattr(status, 'input_overflow', False):
                stats['input_overflows'] += 1
            if len(audio_queue) == audio_queue.maxlen:
                stats['queue_drops'] += 1
            samples = indata[:, 0] if self._input_channels == 1 else indata
            audio_queue.append((sequence, time.monotonic(), stats['input_overflows'], samples.copy()))

        try:
            print(
                f"[WakeWord] 监听参数: threshold={self._threshold} confirm_windows={self._confirm_windows} "
                f"speech_gate={'off' if self._speech_gate is None else 'on'} "
                f"sample_rate={SAMPLE_RATE} window={CLIP_DURATION:.1f}s "
                f"stride={self._stride_duration:g}s input_scale={self._input_scale:g}",
                flush=True,
            )

            if self._shared_input:
                self._feed_queue = audio_queue
                stream_context = nullcontext()
            else:
                try:
                    default_input = self._device if self._device is not None else sd.default.device[0]
                    dev_info = sd.query_devices(default_input)
                    if dev_info:
                        print(f"[WakeWord] 音频设备: [{default_input}] {dev_info['name']}", flush=True)
                except Exception:
                    pass
                stream_context = sd.InputStream(
                    samplerate=SAMPLE_RATE, channels=self._input_channels, dtype="float32",
                    blocksize=self._stride_samples, latency=self._input_latency,
                    device=self._device, callback=audio_callback)
            with stream_context as stream:
                actual_latency = getattr(stream, 'latency', None)
                if isinstance(actual_latency, (float, int)):
                    stats['input_latency_ms'] = round(actual_latency * 1000, 1)
                print("[WakeWord] 监听已就绪，可以说唤醒词", flush=True)
                if self._on_ready:
                    try:
                        self._on_ready()
                    except Exception as e:
                        print(f"[WakeWord] ready callback error: {e}", flush=True)

                ring = np.zeros(CLIP_SAMPLES, dtype=np.float32)
                filled_samples = 0  # 已写入 ring 的真实音频样本数（warmup 防止零数据误触发）

                for new_audio, reset, fresh in self._capture_chunks(audio_queue):
                    if reset:
                        ring.fill(0)
                        filled_samples = 0
                        if gate is not None:
                            gate.reset()
                    if gate is not None:
                        gate.feed(new_audio)
                    if fresh and self._on_audio is not None:
                        try:
                            self._on_audio(new_audio)
                        except Exception:
                            pass
                    if len(new_audio) >= CLIP_SAMPLES:
                        ring = new_audio[-CLIP_SAMPLES:]
                        filled_samples = CLIP_SAMPLES
                    else:
                        ring = np.concatenate([ring[len(new_audio):], new_audio])
                        filled_samples = min(CLIP_SAMPLES, filled_samples + len(new_audio))

                    now = time.time()
                    chunk_count += 1

                    # 预热保护：ring 未灌满 2 秒真实音频前不评分，避免零数据误触发
                    if filled_samples < CLIP_SAMPLES:
                        if chunk_count == 1:
                            print(
                                f"[WakeWord] 预热中: 已采集 {filled_samples}/{CLIP_SAMPLES} 样本",
                                flush=True,
                            )
                        continue

                    if not fresh:
                        continue
                    context = self._detection_context() if self._detection_context else None
                    if self._detection_context is not None and context is None:
                        over = 0
                        continue
                    threshold = self._threshold
                    if context is not None and self._threshold_for_context is not None:
                        threshold = self._threshold_for_context(context, threshold)
                    inference_start = time.perf_counter()
                    score = self._predict(ring)
                    inference_ms = (time.perf_counter() - inference_start) * 1000
                    if not self._running:
                        break

                    if score > peak_score:
                        peak_score = score

                    if now - last_diag >= 5.0:
                        audio_level = np.abs(new_audio).mean() * 32768.0
                        print(
                            f"[WakeWord] 诊断: windows={chunk_count} "
                            f"score={score:.4f} peak={peak_score:.4f} audio_level={audio_level:.0f} "
                            f"inference_ms={inference_ms:.1f} "
                            f"overflows={stats['input_overflows']} queue_drops={stats['queue_drops']} "
                            f"stale_blocks={stats['stale_blocks']} catchup_blocks={stats['catchup_blocks']} "
                            f"latency_ms={stats['input_latency_ms']}",
                            flush=True,
                        )
                        peak_score = 0.0
                        last_diag = now

                    triggered_at = time.monotonic()
                    if score >= threshold:
                        over, over_peak = over + 1, max(score, over_peak if over else 0.)
                    else:
                        if 0 < over < self._confirm_windows and triggered_at - last_trigger >= self._cooldown_sec:
                            ignored += 1
                            print(
                                f"[WakeWord] 忽略短暂高分: 连续{over}窗 < {self._confirm_windows} "
                                f"peak={over_peak:.4f} threshold={threshold:.2f} 累计={ignored}",
                                flush=True,
                            )
                        over = 0
                    if over >= self._confirm_windows and triggered_at - last_trigger >= self._cooldown_sec:
                        if self._detection_context is not None and self._detection_context() != context:
                            over = 0
                            continue
                        if gate is not None and not gate.spoke():
                            # The model scored high, but nothing in the last two seconds stood over the noise.
                            if triggered_at >= quiet_until:
                                quiet_until = triggered_at + self._cooldown_sec
                                ignored += 1
                                print(
                                    f"[WakeWord] 忽略无人声的高分: 置信度={max(score, over_peak):.4f} "
                                    f"threshold={threshold:.2f} 高于底噪的帧={gate.loud_frames()}/{gate.frames} "
                                    f"累计={ignored}",
                                    flush=True,
                                )
                            continue
                        last_trigger = triggered_at
                        over = 0
                        print(
                            f"[WakeWord] 检测到唤醒词! "
                            f"置信度={max(score, over_peak):.4f} "
                            f"时间={time.strftime('%H:%M:%S')} threshold={threshold:.2f}",
                            flush=True,
                        )
                        if self._detection_context is None:
                            woke = True
                            break
                        self._notify_wakeup(context)

        except Exception as e:
            print(f"[WakeWord] 监听异常: {e}", flush=True)
        finally:
            self._feed_queue = None
            self._running = False
            print("[WakeWord] 监听线程退出", flush=True)
        if woke:
            self._notify_wakeup()

    def _notify_wakeup(self, *args):
        if self._on_wakeup:
            try:
                self._on_wakeup(*args)
            except Exception as e:
                print(f"[WakeWord] 唤醒回调失败: {e}", flush=True)

    def feed_pcm(self, pcm, captured_at, overflows, sequence):
        """Accept an immutable mono frame from the codec worker."""
        audio_queue = self._feed_queue
        if audio_queue is not None and self._running:
            stats = self._capture_stats
            stats['callbacks'] += 1
            stats['input_overflows'] = overflows
            if len(audio_queue) == audio_queue.maxlen:
                stats['queue_drops'] += 1
            audio_queue.append((sequence, captured_at, overflows, pcm))

    def _capture_chunks(self, audio_queue):
        """Keep model stride independent of the shared stream's Opus frame size."""
        stats = self._capture_stats
        previous_sequence = None
        previous_overflows = 0
        stride_bytes = self._stride_samples * 2
        pending = b""
        reset = False
        while self._running:
            if not audio_queue:
                time.sleep(.02)
                continue
            sequence, captured_at, overflows, samples = audio_queue.popleft()
            age = time.monotonic() - captured_at
            fresh = age <= MAX_SCORING_AGE
            if not fresh:
                if not self._shared_input or age > CLIP_DURATION:
                    stats['stale_blocks'] += 1
                    continue
                # The shared codec delivers 60 ms frames after AEC. A slow
                # inference can briefly put sequential frames behind; keep
                # them as context so a transient delay doesn't force warmup.
                stats['catchup_blocks'] += 1
            if ((previous_sequence is not None and sequence != previous_sequence + 1)
                    or overflows != previous_overflows):
                pending = b""
                reset = True
                stats['discontinuities'] += 1
            previous_sequence, previous_overflows = sequence, overflows
            if self._shared_input:
                pending += samples
                while self._running and len(pending) >= stride_bytes:
                    chunk, pending = pending[:stride_bytes], pending[stride_bytes:]
                    yield np.frombuffer(chunk, dtype="<i2").astype(np.float32) / 32768, reset, fresh
                    reset = False
            else:
                yield self._input_transform(samples.astype(np.float32)), reset, fresh
                reset = False
