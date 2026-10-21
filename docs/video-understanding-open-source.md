# 视频理解开源选型 · 2026-10-17

| 项目与官方来源 | 适用能力 | 接入决策与许可 |
| --- | --- | --- |
| [video-to-prompt](https://github.com/lewisluc87-hub/video-to-prompt)、[实现说明](https://github.com/lewisluc87-hub/video-to-prompt/blob/main/SPEC.md) | 镜头检测→逐镜头主体/动作/构图/相机运动→结构记录→复刻提示词；转写为上下文而非直接画面描述 | 最贴近创作复刻的应用路线，适合借鉴结构/适配已有模型网关。仓库MIT；不能将其可选YOLO等依赖一概当MIT。本次只读README/SPEC/pyproject，未执行代码或安装全量依赖；成熟度和准确率尚未实测 |
| [Qwen3-VL](https://github.com/QwenLM/Qwen3-VL)、[视频理解示例](https://github.com/QwenLM/Qwen3-VL/blob/main/cookbooks/video_understanding.ipynb) | 时间戳对应画面、事件时间段、连续动作 | 主线优先参考；沿用云API网关。本次强化主体/动作/机位描述并展示时间分段；未复制上游代码。仓库Apache-2.0，云API另遵服务条款 |
| [PySceneDetect](https://github.com/Breakthrough/PySceneDetect) | 镜头边界、转场、镜头内抽帧 | 下一步候选，替代简单帧差切镜启发式；不能独立理解动作。本次未安装。BSD-3-Clause，引入时保留许可和第三方声明 |
| [SenseVoice](https://github.com/QwenAudio/SenseVoice) | 音频事件、多语种转写 | 音轨分支候选，需评估音乐/歌声/口播混淆。本次未安装或下载权重。源码MIT，模型权重另遵模型卡及FunASR模型许可，不能混同 |
| [InternVideo](https://github.com/OpenGVLab/InternVideo) | 时序动作、长视频理解 | 后续独立GPU服务比较项，当前不迁移基础设施。仓库Apache-2.0，具体权重独立核对 |

本次在线核查上述官方仓库；优先借鉴Qwen时间证据方法，不将整仓fork或安装依赖当成功能完成。不宣称已接通PySceneDetect/SenseVoice。

另对比[Zulelee/Video2Prompt](https://github.com/Zulelee/Video2Prompt)和[NarratoAI](https://github.com/linyqh/NarratoAI)：前者为其他同名候选，不能混用仓库身份与许可；后者更偏解说剪辑，与无口播舞蹈复刻的当前重点不同。上述两者未完成代码/许可专项审计，不引入其代码。本机git clone video-to-prompt遇到schannel TLS握手错误，未关闭证书验证，改用官方GitHub页面和raw文件只读审阅。

## 根因与本次落地

生产日志reference.understanding.failed code=model；当前连接GET /models不包含qwen-vl-plus，包含qwen3-vl-plus；阿里云[视觉理解文档](https://www.alibabacloud.com/help/en/model-studio/vision-model/)列出该视觉模型。仅查询目录，没有真实模型探测。默认改为qwen3-vl-plus，缺失场景自动补齐，保留显式自定义模型，qwen3-vl系列关闭思考模式适配同步结构化结果。

素材获取成功和视觉理解成功分开；错误码/安全说明可见；画面失败不把元数据和歌词当“可复用内容结构”。成功时展示逐段主体、动作、景别/机位；无口播不需要虚构文案或营销结构。转写可能是歌词/背景音/误识别，只作待核对材料。content-evidence-3使旧分析缓存失效。

静帧不能确认的音乐节奏和帧间动作必须标为不确定。真实效果待用户用纯音乐舞蹈、歌曲背景、口播、无声演示、多镜头剧情样片验收；模型目录存在不等于真实推理质量验收。当前mock覆盖视觉模型不可用、无口播舞蹈和歌词不冒充画面依据，以及失败重试、错误脱敏。
