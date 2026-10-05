# NanoJev 环境与进度备忘（给后续 AI/协作会话）

## 网络（重要：只用代理，不用任何镜像）

- 代理：mihomo，HTTP `http://127.0.0.1:7890`（socks 7891），跑在 tmux 会话 `proxy` 的 0 号窗口。
- git 已全局配置：`http.version=HTTP/1.1`，且仅 github.com 走 `127.0.0.1:7890`。直接 `git clone https://github.com/...` 即可。
- HuggingFace 下载走官方 `huggingface.co` + 代理（见 `download_model.py`），必须设 `HF_HUB_DISABLE_XET=1`。
- **坑**：走代理访问 github/google 时 curl/git 必须用 HTTP/1.1（链路会掐 ALPN 含 h2 的 TLS）；pip 装大包会卡死，**装包一律用 uv**（`venv/bin/uv pip install ...`，官方 PyPI + 代理即可）。
- 曾经用过的镜像（gh-proxy / hf-mirror / tuna / aliyun）已全部弃用并清理，勿再引入。

## 路径

- 工作区：`/media/disk/shensd/learn_jev/`（根分区小，大文件一律放 /media/disk）
- venv：`venv/`（Python 3.10；torch 2.14.0+cu130 / transformers 5.17.0 / numpy 2.2.6 / uv）
- 代码：`NanoJev/`（origin = github.com/TianyuCodings/NanoJev，unified-games-v1 发布；
  **fork remote = git@github.com:SeddonShen/NanoJev.git，分支 `shensd-repro`**。
  约定：凡改仓库代码或工作区工具，改完就 commit+push 到 fork 的 `shensd-repro`；
  工作区级工具（launcher/dashboard/ENV_NOTES）在 fork 的 `workspace/` 目录留副本。
  推送依赖 `~/.ssh/shensd_key`（已在 ~/.ssh/config 绑定 github.com；公钥需登记到 GitHub 账号后才能推））
- 模型：`checkpoints/NanoJev-unified/`（best.safetensors 与 training_initialization/ 的 SHA256 均已对官方校验一致）
- 数据：`data/NanoJev-unified/`（213 文件全过官方 SHA256 清单；unified/{hard,soft} 五行分均在；
  games_v4/data/scaled_games_v4b/events 是 RLCD events 实验数据，games_v4/runs 附官方三臂原始产物）
- 启动器：`launch_reproduction.py`（4-arm 并行训练；--dry-run/--status/--stop/--arms）
- 可视化：`dashboard/live_dashboard.py`（纯 stdlib；默认 8799 端口；读 runs/unified_repro/registry.json）
- 复现产物：`runs/unified_repro/{hard_lr1e5,hard_lr2e5,soft_lr1e5,soft_lr2e5}/`，stdout 在 `runs/unified_repro/logs/`
- 冒烟训练产物：`runs/smoke_hard_lr1e5/`

## 对外访问约定（2026-10-06 起）

- 给用户的链接一律用 **http://175.102.130.90:端口/**（服务都绑 0.0.0.0），不要给 127.0.0.1。
- 端口分配：**8799** 训练实时面板 · **8800** 数据集浏览器（自建）· **8080** 官方 web 演示（仓库 web/，
  已加中英切换：共享 `web/i18n-zh.js` + 各页一行 `<script>`，默认中文，右上角按钮切换，
  MutationObserver 覆盖 JS 动态渲染；PRE/CODE/JSON 面板不翻译）。
- 启动命令：
  `nohup venv/bin/python dashboard/live_dashboard.py --port 8799 > runs/unified_repro/logs/dashboard.log 2>&1 &`
  `nohup venv/bin/python dashboard/dataset_viewer.py --port 8800 > runs/unified_repro/logs/dataset_viewer.log 2>&1 &`
  `nohup venv/bin/python -m http.server 8080 --bind 0.0.0.0 --directory NanoJev/web > runs/unified_repro/logs/web_demos.log 2>&1 &`

## GPU 占用（2026-10-06 核实）

- **0/3/5/7 空闲归我们**；**1/2/4/6 是同事 chenyan+ 的 vLLM 服务**（TP=4，已跑 12 天，各占 22.9GB，
  util 常年 0%，不是僵尸进程）。显存上可共存（我们训练峰值 ~16.6GB），共用前先知会对方。
- 单卡实测：官方 flag 下 ~8 s/步（0.6B、batch 24 题、microbatch 8、梯度检查点、bf16）。
  600 步 ≈ 1.5h + 6 次 dev 评测（每次 ~1 分钟 + 2.4GB 存盘）。

## 已完成进度（2026-10-06）

1. 8×A800-80G 确认；环境装好；/tmp 清理过（根分区 92%）。
2. 模型+数据下载完成并校验；17/17 契约单测通过；validate-only 数据校验与官方文档一致
   （18,760 行 / 隔离 11 / 训练池 10,893 = Maze 651 + Snake 400 + Basic 3054 + PP 6788）。
3. 24 步冒烟训练（GPU3，hard_lr1e5 同款超参）：dev 加权 CE 0.9546 → 0.7177，loss 正常下降。
4. serving 验证通过：POST /api/evaluate 三模式（choice/boolean/score）返回完整概率分布，
   单请求稳态 31–36ms（bf16, cuda）。服务当前未运行，需要时：
   `cd NanoJev && CUDA_VISIBLE_DEVICES=0 venv/bin/python scripts/serve_decisions.py \
    --checkpoint-dir ../checkpoints/NanoJev-unified --web-root web --port 8765 --disable-native-triton`
5. 完整 600 步训练命令见 `checkpoints/NanoJev-unified/TRAINING_RECIPE.md`（backbone lr 1e-5 / head 1e-4，
   池权重用数据集自带 `configs/sonic_policy_pool_weights.json`）。
6. **4-arm 全实验并行复现已启动**（GPU 0/3/5/7，各 ~1.5-2h，官方 flag 原样 + --log-every 1）：
   hard/soft × {1e-5/1e-4, 2e-5/2e-4}。完成后每个 arm 有 best.safetensors + summary.json，
   可与官方 `evaluation/experiment/` 的 dev 轨迹对账。
7. **实时训练面板**：`venv/bin/python dashboard/live_dashboard.py --port 8799` →
   http://127.0.0.1:8799 （四臂 dev CE 对比图、每臂 loss 曲线/进度/ETA/GPU 状态，3s 刷新）。
8. **多卡方案结论**：本实验的最优并行 = 4 独立 arm × 4 卡（零训练代码改动、零复现偏差）；
   DDP 无收益（单 arm 已 1.5h 且无空余卡）；flag 级调优（去 checkpointing/开 triton）预计再省
   20-30% 但偏离官方配方，复现阶段不用。8 卡扩展方案见下。

## 与官方配方的偏差记录

- `NanoJev/scripts/train_unified_games.py` 打了 logging-only 补丁：新增 `--log-every N`
  （默认 12 = 官方节奏；我们传 1 以便 dashboard 逐步实时）。不影响训练数学；
  config.json 里的 implementation_sha256 会因此不同于官方，属预期。
- 硬件/依赖：A800-80G vs 官方 A100-80G；Python 3.10 vs 官方 3.14（torch/transformers 同 2.14/5.17）。

## 8 卡方案（原则：1/2/4/6 共用前知会 chenyan+）

- 0/3/5/7（独占）：seed17 官方 4-arm 复现（进行中）。
- 1/2/4/6（与 vLLM 共存，各余 ~57GB）：按需跑 **seed 18/19 复跑**（官方仅单 seed，仓库文档明确
  说规模化决策需多 seed）——最有价值的用途，且零训练代码改动（只需给我们的 launcher 加
  --seed/--gpu 参数）。不建议同卡叠两个训练，不建议 DDP。
- 备选：RLCD events 三臂 + 初始评测恰好 4 个任务，但缺官方初始 checkpoint
  （v3_teacher_coords_multi_seed17，HF 未见；用 unified checkpoint 替代需记录偏差）。

## 下一阶段（进行中）

- 自造决策数据：先走 RLCD 冷启动小闭环，不依赖外部 API/Jev。
- 本地已经打通 Maze+Snake 20 局随机冻结策略 rollout，并生成 outcome 数据：
  `data/rlcd_pilot/`（`random_episodes_v0.jsonl` + `outcomes_random_v0/`）。
- ViZDoom 包已按官方 PyPI + mihomo 代理装好（uv 缓存在 `.uv-cache/`），
  但本容器内 ViZDoom 实机 `game.init()` 段错误；Maze/Snake 正常。
  之前完整任务需回到可用的 GPU/宿主环境跑。
- 注意：`outcomes_random_v0` 仅含 Maze/Snake outcome，训练器的 task-balanced critic
  采样池要求 train 中每个任务都有 outcome，所以当前只通过 schema/来源审计，
  不能直接开始 critic 训练。下一步要么加入 ViZDoom rollout，要么先做一个
  Maze+Snake-only 的临时训练/采样变体。

## 下一阶段（排队中）

- 等 4-arm 跑完：与官方 dev 轨迹对账（selection CE 曲线、best step 方向）
- 自造决策数据的 schema 参考：本地数据包 manifest + verify_dataset.py +
  research/query_distribution_zh.md（原计划的"Intern-Decision DATA.md"查无公开仓库，疑为私有项目）
- RLCD 后训练（events 三臂对照，或上面 pilot 的 Maze/Snake outcome 路线）
