import argparse
import sys
import time
import logging
import signal
import os
import tomllib
from pusher import StreamPusher

# 配置日志记录格式
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

pushers = []

def signal_handler(sig, frame):
    """
    捕捉 Ctrl+C 或终止信号，确保所有正在跑的子进程都能优雅退出
    """
    logging.info("接收到终止信号，正在关闭所有推流...")
    for p in pushers:
        p.stop()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Multi-stream RTSP Pusher")
    parser.add_argument("-c", "--config", help="配置文件路径", default="config.toml")
    args = parser.parse_args()

    # 读取配置文件
    if not os.path.exists(args.config):
        logging.error(f"找不到配置文件: {args.config}")
        return

    try:
        with open(args.config, 'rb') as f:
            config = tomllib.load(f)
    except Exception as e:
        logging.error(f"解析 TOML 配置文件失败 {args.config}: {e}")
        return


    # 注册终止信号
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    streams_conf = config.get("streams", [])
    if not streams_conf:
        logging.warning("配置文件中没有找到 'streams' 推流任务。")
        return

    # 全局码流开启设置 (both, main, sub)
    stream_mode = config.get("stream_mode", "both")

    # 全局视频编码器设置
    # libx264   = CPU 软件编码（默认，兼容性最好）
    # h264_nvenc = NVIDIA GPU 编码（RTX/GTX 系列，CPU 占用极低）
    # h264_qsv  = Intel 核显编码
    # h264_amf  = AMD GPU 编码
    global_video_encoder = config.get("video_encoder", "libx264")

    # 每路推流的启动间隔（秒），避免多路 GPU 编码 session 同时初始化
    # 使用 GPU 编码时建议设置为 0.5~1.0，CPU 编码可设置为 0
    startup_delay = config.get("startup_delay", 0.0)

    # 并发初始化和启动推流任务
    for sc in streams_conf:
        name = sc.get("name", "Unknown_Stream")
        url = sc.get("url")
        files = sc.get("files", [])
        loop = sc.get("loop", True)
        audio = sc.get("audio", False)
        if not url or not files:
            logging.warning(f"[{name}] 缺少 'url' 或 'files' 参数，跳过启动。")
            continue
            
        # 流级别的编码器设置
        stream_video_encoder = sc.get("video_encoder")

        if stream_mode in ["both", "main"]:
            # 主流配置：如果显式配置了编码器则使用，否则保持 StreamPusher 默认的 "copy"
            pusher_args = {
                "name": name,
                "url": url,
                "files": files,
                "loop": loop,
                "audio": audio
            }
            if stream_video_encoder:
                pusher_args["video_encoder"] = stream_video_encoder
            
            pusher = StreamPusher(**pusher_args)
            # 将启动后的对象保存，在收到终止信号时清理
            pushers.append(pusher)
            pusher.start()
            # 按配置的间隔错开启动，防止多路 GPU session 同时初始化
            if startup_delay > 0:
                time.sleep(startup_delay)
        else:
            logging.info(f"[{name}] 根据配置，跳过启动主码流。")

        # 处理子码流配置
        sub_streams = sc.get("sub_streams", [])
        if stream_mode in ["both", "sub"]:
            for sub in sub_streams:
                s_name = name + sub.get("name_suffix", "_sub")
                s_url = url + sub.get("url_suffix", "_sub")
                s_width = sub.get("width")
                s_height = sub.get("height")
                s_bitrate = sub.get("video_bitrate")
                s_audio = sub.get("audio", False) # 子流默认关闭音频
                # 子流继承逻辑：子流配置 -> 流配置 -> 全局配置
                s_video_encoder = sub.get("video_encoder") or stream_video_encoder or global_video_encoder

                sub_pusher = StreamPusher(
                    s_name, s_url, files, loop,
                    width=s_width, height=s_height,
                    video_bitrate=s_bitrate, audio=s_audio,
                    video_encoder=s_video_encoder,
                )
                pushers.append(sub_pusher)
                sub_pusher.start()
                # 按配置的间隔错开启动，防止多路 GPU session 同时初始化
                if startup_delay > 0:
                    time.sleep(startup_delay)
        elif sub_streams:
            logging.info(f"[{name}] 根据配置，跳过启动 {len(sub_streams)} 个子码流。")

    logging.info(f"共启动了 {len(pushers)} 个并发推流任务。按下 Ctrl+C 停止运行。")

    try:
        # 主线程挂起监控子进程的状态
        while True:
            for p in pushers:
                if p.process and p.process.poll() is not None:
                    # 如果 poll() 不是 None，说明进程退出了（异常断开、奔溃等）
                    ret_code = p.process.poll()
                    logging.error(f"[{p.name}] FFmpeg 进程已退出，返回码: {ret_code}。正在尝试自动重启...")
                    # 调用 p.start() 重新启动推流任务
                    p.start()
            time.sleep(5)
    except KeyboardInterrupt:
        # 回退处理机制
        pass

if __name__ == "__main__":
    main()
