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

    # 全局硬件加速设置
    global_hwaccel = config.get("hwaccel", "none")

    # 并发初始化和启动推流任务
    for sc in streams_conf:
        name = sc.get("name", "Unknown_Stream")
        url = sc.get("url")
        files = sc.get("files", [])
        loop = sc.get("loop", True)
        audio = sc.get("audio", False)
        hwaccel = sc.get("hwaccel", global_hwaccel)

        if not url or not files:
            logging.warning(f"[{name}] 缺少 'url' 或 'files' 参数，跳过启动。")
            continue
            
        pusher = StreamPusher(name, url, files, loop, audio=audio, hwaccel=hwaccel)
        # 将启动后的对象保存，在收到终止信号时清理
        pushers.append(pusher)
        pusher.start()

        # 处理子码流配置
        sub_streams = sc.get("sub_streams", [])
        for sub in sub_streams:
            s_name = name + sub.get("name_suffix", "_sub")
            s_url = url + sub.get("url_suffix", "_sub")
            s_width = sub.get("width")
            s_height = sub.get("height")
            s_bitrate = sub.get("video_bitrate")
            s_audio = sub.get("audio", False) # 子流默认关闭音频
            s_hwaccel = sub.get("hwaccel", hwaccel) # 子流默认继承主流的硬件加速配置

            sub_pusher = StreamPusher(
                s_name, s_url, files, loop,
                width=s_width, height=s_height,
                video_bitrate=s_bitrate, audio=s_audio,
                hwaccel=s_hwaccel
            )
            pushers.append(sub_pusher)
            sub_pusher.start()

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
