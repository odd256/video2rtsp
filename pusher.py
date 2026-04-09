import subprocess
import os
import tempfile
import logging
import threading


class StreamPusher:
    def __init__(self, name, url, files, loop=True):
        self.name = name
        self.url = url
        self.files = files
        self.loop = loop
        self.process = None
        self.playlist_path = None

    def start(self):
        # 将传入的文件路径转换为绝对路径并验证文件是否存在
        valid_files = []
        for v in self.files:
            abs_path = os.path.abspath(v)
            if not os.path.exists(abs_path):
                logging.warning(f"[{self.name}] 文件不存在 (忽略): {abs_path}")
            else:
                valid_files.append(abs_path)

        if not valid_files:
            logging.error(f"[{self.name}] 没有有效的视频文件，推流停止。")
            return

        # 创建一个临时文件来存储视频播放列表
        fd, self.playlist_path = tempfile.mkstemp(
            prefix=f"playlist_{self.name}_", suffix=".txt", text=True
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            for abs_path in valid_files:
                # 针对 FFmpeg concat 需要的安全转义 (处理单引号等)
                escaped_path = abs_path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        # 构建 FFmpeg 命令
        # -re: 按正常帧率播放，防止直接高速倾倒数据给服务端
        # -f concat: 使用 FFmpeg 内置的分离器顺序拉取多个文件
        # -loglevel error: 只打印错误，减少不必要的日志信息
        # -fflags +genpts: 自动生成时间戳，解决 concat 模式下可能的时间戳不连续问题
        cmd = ["ffmpeg", "-loglevel", "error", "-re", "-fflags", "+genpts", "-f", "concat", "-safe", "0"]

        if self.loop:
            cmd.extend(["-stream_loop", "-1"])

        cmd.extend(
            [
                "-i",
                self.playlist_path,
                "-c:v",
                "copy",
                "-f",
                "rtsp",
                "-rtsp_transport",
                "tcp",  # 推流通常推荐使用 TCP 防止丢包，如需适应 UDP 可以去掉
                "-rw_timeout",
                "15000000", # 设置超时为 15 秒（单位：微秒），防止网络断开时无限挂起
                self.url,
            ]
        )

        logging.info(f"[{self.name}] 正在启动 FFmpeg 推流...")
        logging.debug(f"[{self.name}] 完整命令: {' '.join(cmd)}")
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,  # FFmpeg 的日志默认输出在 stderr 中
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # 启动后台线程读取 FFmpeg 的错误输出
        self.error_thread = threading.Thread(target=self._read_stderr, daemon=True)
        self.error_thread.start()

    def _read_stderr(self):
        """实时读取 FFmpeg stderr 并记录到日志中"""
        if self.process and self.process.stderr:
            try:
                for line in iter(self.process.stderr.readline, ""):
                    if line:
                        line = line.strip()
                        # 将 stderr 修改为 debug 级别，默认 INFO 级别不会输出
                        logging.debug(f"[{self.name} FFmpeg] {line}")
            except Exception as e:
                logging.debug(f"[{self.name}] 读取错误日志线程异常: {e}")

    def stop(self):
        if self.process and self.process.poll() is None:
            logging.info(f"[{self.name}] 正在停止 FFmpeg 进程...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()

        # 清理临时创建的列表文件
        if self.playlist_path and os.path.exists(self.playlist_path):
            try:
                os.remove(self.playlist_path)
            except Exception as e:
                logging.error(
                    f"[{self.name}] 无法删除临时列表文件 {self.playlist_path}: {e}"
                )
