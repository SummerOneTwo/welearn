# WE Learn Auth Assistant

基于 Python 3 的 WE Learn (微盘) 辅助脚本合集，支持账号密码与 Cookie 两种登录方式。项目使用 `uv` 来管理依赖，结构清晰并支持二次开发。

## 功能介绍
- **一键刷课** (`src/welearn_curriculum.py`): 交互式选择已选课的单元，自动以“满分+完成”的状态结算小试卷！支持自定义正确率。
- **自动挂机时长** (`src/welearn_time.py`): 后台通过多线程机制，周期性给服务器同步并累计学习时长，支持给每一个小节设定具体的驻留秒数。

## 开发与运行环境
- Python >= 3.9
- `uv` (推荐) 
- 依赖项：`requests`

## 快速运行
请确保你在项目的根目录：

### 安装依赖
```bash
uv sync 
# 或者如果没有使用 uv
pip install requests
```

### 1. 运行一键刷课
```bash
uv run src/welearn_curriculum.py
```

### 2. 运行挂机刷时长
```bash
uv run src/welearn_time.py
```

## 免责声明
本工具仅供学习网络协议分析交流使用，切勿用作非法或破坏性目的。
