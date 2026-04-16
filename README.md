# Video2RTSP Pusher 🎥

这是一个轻量级、高性能的 Python 工具，专门用于将本地视频文件顺序推送到 RTSP 服务器。它支持配置多个并发流，并能够处理视频文件的循环播放。

## ✨ 功能特性

- 🚀 **高性能**: 默认采用 `-c copy` 模式，直接透传音视频流，极低 CPU 占用。
- 📉 **子码流模拟**: 支持通过转码自动生成低分辨率、低码率的子流，满足模拟监控环境需求。
- 📑 **列表播放**: 利用 FFmpeg 的 `concat` 分离器，支持将多个视频文件按顺序无缝拼接推流。
- 🔄 **循环模式**: 支持单个流的无限循环推流。
- 🔇 **音频控制**: 支持为主流或子流配置音频开关，默认关闭音频以节省带宽。
- 🧵 **并发处理**: 能够在一个进程中同时管理多个独立的 RTSP 推流任务。
- 🛡️ **优雅管理**: 自动管理 FFmpeg 进程，支持 Ctrl+C 优雅退出，自动清理临时文件。
- ⚙️ **灵活配置**: 使用 TOML 格式配置文件，结构清晰，易于维护。

## 🛠️ 环境要求

- **Python**: 3.11+
- **FFmpeg**: 系统需安装 FFmpeg 并将其添加到系统环境变量 `PATH` 中。
- **RTSP Server**: 需要一个接收端服务器（强烈建议使用 [MediaMTX](#-配套流媒体服务器建议-mediamtx)）。

## 🚀 快速开始

### 1. 克隆或下载项目
下载本项目到本地。

### 2. 安装依赖
由于本项目采用了现代化的 Python 包管理方式，推荐使用 `uv` 进行快速安装：

```bash
uv sync
```

或者使用传统的 `pip`:

```bash
pip install .
```

### 3. 配置推流任务
参考 `config_example.toml` 创建你的配置文件（例如 `config.toml`）：

```toml
[[streams]]
name = "Live_Stream_1"
url = "rtsp://localhost:8554/stream1"
files = [
  "videos/clip1.mp4",
  "videos/clip2.mp4"
]
loop = true
audio = false  # 主流默认关闭音频

# 子码流配置（可选）
[[streams.sub_streams]]
name_suffix = "_sub"
url_suffix = "_sub"
width = 640
height = 360
video_bitrate = "500k"
audio = false
```

### 4. 启动推流
运行以下命令启动推流任务：

```bash
python main.py -c config.toml
```

## 🌐 配套流媒体服务器建议 (MediaMTX)

本项目作为**推流端 (Pusher)**，需要一个**服务端 (Server)** 来接收并分发视频流。如果你本地没有现成的 RTSP 环境，推荐使用 **MediaMTX**。

### 角色关系
> **[Video2RTSP] (发货)** ➔ **[MediaMTX] (中转站)** ➔ **[VLC/网页] (收货)**

### 使用步骤：
1. **下载**: 从 [MediaMTX GitHub Releases](https://github.com/bluenviron/mediamtx/releases) 下载适合你系统的版本。
2. **启动**: 解压并运行 `mediamtx.exe` (Windows) 或 `./mediamtx` (Linux/macOS)。它会默认开启 `8554` 端口。
3. **推流**: 运行本项目的 `main.py`。
4. **播放**: 打开播放器（如 VLC），输入网志中配置的地址（例如 `rtsp://localhost:8554/stream1`）即可观看。

## ⚙️ 配置文件说明

| 参数 | 说明 |
| :--- | :--- |
| `name` | 流名称，用于日志识别 |
| `url` | 目标 RTSP 推流地址 |
| `files` | 包含视频文件路径的数组。路径可以是相对或绝对路径 |
| `loop` | `true` 为循环播放视频列表，`false` 为播放结束后停止 |
| `audio` | `true` 为开启音频，`false` 为关闭音频（默认值） |
| `sub_streams` | 子码流配置列表，每个子流都会基于视频源进行转码推流 |
| `sub.width` | 子码流的目标宽度 |
| `sub.height` | 子码流的目标高度 |
| `sub.video_bitrate`| 子码流的视频码率（例如 "500k", "1M"） |
| `sub.name_suffix` | 子流名称后缀，默认为 `_sub` |
| `sub.url_suffix` | 子流 URL 后缀，默认为 `_sub` |

## 📝 注意事项

- **FFmpeg 路径**: 请确保在终端输入 `ffmpeg -version` 能正常显示版本信息。
- **视频格式**: 为了保证拼接推流的稳定性，建议列表中的视频文件具有相同的编码格式、分辨率和帧率。
- **传输协议**: 默认使用 TCP 传输方式 (`-rtsp_transport tcp`)。

## 📜 许可证

MIT License
