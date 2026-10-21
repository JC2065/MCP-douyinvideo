# 热点同步部署与维护

## 选择与范围

采用 [imsyy/DailyHotApi](https://github.com/imsyy/DailyHotApi) 2.0.8（MIT）作为内部采集接口。相比包含完整阅读界面的 NewsNow，本项目只需要接口，因此复用 DailyHotApi 更直接。不依赖作者的公共演示服务。

上游源码存于服务器 `/opt/youai/hotspots/DailyHotApi-master`，保留 LICENSE；下载归档 SHA-256：`a73a619ec0a277e9c0e26b8fbddcd90a48db43a3112ce7c129e3375d03079d3a`。归档取自 master，并非不可变版本标签；后续升级须记录新归档哈希并重新验收。当前镜像留存便于回滚。

本轮接入抖音、微博、今日头条、快手。公众号、小红书缺少本次验证可用的对应接口，暂不显示入口。源站返回顺序作为榜内序号，综合按序号交错展示，不比较各平台热度。来源可能含推荐位，序号不保证等同官方客户端显示的名次。

## 通路与更新机制

小程序（包括开发者工具）→ `https://api.onesvips.top/youai/hotspots` → 现有纽约 HTTPS 通路 → 广州视频服务读取快照 → 内网 DailyHotApi → 各平台。

- 广州 Docker 容器 `youai-hotspots-dailyhot-1`，限制256MB/0.5CPU，不映射公网端口。
- `scripts/hotspot-feed.py` 随视频服务启动独立后台线程；每600秒启动一轮，四源顺序抓取，每个请求20秒超时，不重叠。
- 主动请求 `?cache=false`，服务内缓存TTL600；手机请求只读快照，不能触发额外抓取。DailyHotApi 默认TTL3600不可直接沿用。
- `scripts/patch-dailyhot.py` 加入可选REDIS_DISABLED开关，使用内存缓存，避免上游每次强刷删除Redis键时等待未部署的Redis。MIT原文件和许可保留。
- `/data/hotspots/snapshot.json`（主机video-data/hotspots）原子持久化；重启先载入上次快照。
- 每源单独记录抓取时间、上游更新时间、尝试时间。失败保留最后成功数据并标注缓存；超过24小时不再返回该源条目。全源失败不生成假榜。
- 更新表示每10分钟尝试同步，不承诺源站可用或源站本身每10分钟有新内容。手机前台每10分钟重读，切回页面立即重读，离开后停止计时器。
- 搜热点仅在当前同步标题中匹配关键词，不声称进行AI联网搜索。存入灵感保留来源URL、平台、榜内序号和抓取时间。

## 复现与回滚

1. 使用上述哈希对应归档；解压后运行 `python scripts/patch-dailyhot.py <源码目录>` 一次。
2. 将 `deploy/Dockerfile.dailyhot` 作为构建文件，在源码目录构建 `youai-dailyhot:2.0.8`；保留生成的依赖锁与镜像用于恢复，升级依赖另行验证。
3. `docker compose -f compose.hotspots.yml up -d`，加入已有youai-cloud_default网络。
4. 视频镜像需包含hotspot-feed.py和新版video-server.py；compose.video-cloud.yml配置YOUAI_HOTSPOT_API，持久数据继续使用video-data目录。
5. 当前增量镜像基于config-67构建为hotspots-71。服务端回滚使用 `/opt/youai/internal-api/releases/hotspots-71/compose.before.yml` 和 `env.before` 恢复原配置并重建视频容器；现有数据库、视频文件无需删除。前端回滚对应Git提交。

本次需要更新一次小程序包才会使用新接口；之后排行榜数据更新由服务器完成，无须每次提审。未更改独立web/project-1视觉原型。

## 验证记录

以下仅为服务端与开发者工具证据，不视为微信真机验收。

- 2026-10-14：定向JS81/81、Python热点5/5、视频25/25通过。开发者工具连接真实公网服务，197条快照加载、搜索、详情、平台筛选及首页加载通过，无脚本异常；截图位于仓库外codexYOUAI-services/hotspots-ui.png与hotspots-main.png。
- 两次自动轮询启动epoch为1791912132.4451492、1791912732.4452422，间隔600秒。重启后保留榜单，续查连续运行14小时；最新检查200条，抖音/微博/头条fresh，快手stale。快手首次失败后曾恢复，后续仍间歇失败，不承诺四源同时最新。
- 小程序preview编译成功；预览码有时效，旧码不能当正式发布。未提交审核，真机复测仍待完成。

2026-10-14升温优化：改为保留最近6次同源成功采集历史，最新两次间隔≤30分钟时计算榜内升降与新入采集榜；缓存内容不进入升温。页面默认升温，完整榜保持来源数据可查。细则和本轮验收见hotspot-trends-plan.md。视频镜像更新为trends-72，回滚材料位于releases/trends-72。
