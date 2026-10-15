# OpenClash AI Rules

独立维护 ChatGPT、Claude、Gemini / NotebookLM、Copilot、Grok、Perplexity、OpenRouter、Poe、Cursor、Windsurf、DeepSeek、通义千问、Kimi、豆包、智谱 GLM 和 MiniMax 的域名分流。

## 更新

- GitHub Actions 每天北京时间 02:17 同步，支持 Actions → Update AI rules → Run workflow 手动运行。GitHub 定时任务可能延迟，长期无活动时也可能停用，请以 Actions 结果为准。
- OpenClash 的每个 rule-provider 每 86400 秒拉取对应规则，与机场节点订阅分开更新。
- 有独立源的服务同步 MetaCubeX/meta-rules-dat；无独立源的服务使用本仓库种子规则和 custom/<服务>.list。具体状态、来源、数量和校验值见 manifest.json。
- 下载失败、空文件或格式异常会使任务失败，原已发布规则保持不变。检查源成功不代表 AI 节点通过服务可用性检测。

## OpenClash

`templates/AI_Services.conf` 是不含任何凭据的通用覆写模块。仅导入一个 AI 优化模块，勿同时启用旧的 Bypass_Optimize.conf，否则产生重名策略组。模块保留原订阅节点和原规则，增加 16 个 AI 服务的独立自动故障切换组，每组另有“手动优先”选择入口。

- 先在“规则下载”选可访问 GitHub Raw 的节点；默认 DIRECT 为避免对新机场引用不存在的节点。
- “普通代理”和“AI默认出口”首次使用或切换机场后应选取适用节点。每个海外 AI 组可独立选择节点，初始使用 AI默认出口。
- 国内 AI 组初始 DIRECT；不代表该服务所有海外站点均适用直连，可单独切换。
- 在模块信息里选择“添加到所有配置文件”，新增机场即可继承策略。缺少节点时通用组会保留普通代理回退，不硬编码机场名或节点名。
- 媒体组测速只反映网络可达性，不保证 Netflix、Disney+ 等地区解锁。
- 此模块不改变 LAN 网关、防火墙访问权限、DNS 劫持方式和 OpenClash 的 TUN 工作模式。

## 自定义和来源

`custom/<服务>.list` 每行一个完整域名或 `+.example.com` 后缀域名；禁止 IP、整段规则指令、脚本和凭据。同步脚本会验证格式并去重。

规则来源：[MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)，上游规则及其许可证归对应维护者；参见上游许可证与来源说明。本仓库的自动同步不声称拥有上游内容。

这里绝不存储机场订阅、节点 UUID/密码、控制面板密钥。AI 服务的域名规则与节点是否能登录/生成内容是两个独立问题。

## 自动检测的范围

每个 AI 自动组对该服务的网站发送 HTTP 连通性检测，期望状态码 200–299；使用中的组每 10 分钟检查，失败时按配置顺序选择可响应节点，并优先保留健康的手动出口。闲置组采用惰性检测。媒体自动测速每 5 分钟检测。普通代理、规则下载、AI默认出口及“手动优先”是人工选择入口。

这不验证账号登录、地区解锁或模型生成。反爬验证可能让可用节点被误判；全部失败时内核也不能保证选中可用节点。切换订阅后若原节点不存在，需要重新设置手动优先出口。路由器会自动拉取域名规则；本地覆写模块结构不会自动同步仓库模板。
