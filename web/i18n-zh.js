/* NanoJev web demos — client-side zh/EN toggle (default: 中文).
 * Shared across pages; injected as <script src="...i18n-zh.js" defer>.
 * Translates text nodes and common attributes; a MutationObserver covers
 * JS-rendered content. Original strings are kept in dataset.i18nOrig so the
 * page can switch back to English exactly. PRE/CODE/SCRIPT/STYLE and
 * JSON/raw panels are never touched. */
(function () {
  "use strict";
  var ZH = {
    "STATE → QUESTION → PROBABILITY → ACTION": "状态 → 问题 → 概率 → 动作",
    "A nano replica of Jev": "Jev 的纳米级复刻",
    "Explore how the model chooses, acts, and sometimes fails. Replay real experiment records or connect to the optional live endpoint.": "看模型如何选择、行动，以及偶尔失败。可回放真实实验记录，或连接可选的实时推理服务。",
    "Dynamic candidates": "动态候选", "Typed probabilities": "原生概率输出",
    "No answer-text decoding": "不生成答案文本", "Model / baseline": "模型 / 基线",
    "CHECKPOINT": "检查点", "Not loaded": "未加载", "Reload records": "重新加载记录",
    "The evaluation cohort and controller appear here after loading.": "加载后这里显示评测队列与控制器。",
    "Full model summary and evaluation scope": "完整模型摘要与评测范围",
    "Game replay": "游戏回放", "Parallel probabilities": "并行概率",
    "Live endpoint API": "实时推理 API", "Live endpoint": "实时端点",
    "RECORDED EPISODE": "已录制对局", "Every step, on record": "每一步都有记录",
    "Select an episode": "选择一局", "No episodes yet": "暂无对局",
    "Waiting for game records": "等待游戏记录", "Replay": "回放", "Play replay": "播放回放",
    "Waiting for experiment results": "等待实验结果", "Waiting for experiment data": "等待实验数据",
    "Load demo_results.json to see the actual recorded trajectories.": "加载 demo_results.json 查看真实录制轨迹。",
    "Replay progress": "回放进度", "Action distribution": "动作分布",
    "Recorded values": "录制值", "Select a recorded episode.": "选择一局录制。",
    "Action probabilities are not final win probabilities.": "动作概率不等于最终获胜概率。",
    "Execution record": "执行记录", "Record": "记录", "Waiting for data": "等待数据",
    "Episode outcome": "对局结果", "Full trajectory": "完整轨迹",
    "Failures and forced actions remain visible. Solver and random baselines are listed separately.": "失败与强制动作仍会显示。求解器与随机基线单列。",
    "Game": "游戏", "Status": "状态", "Steps": "步数", "Goal": "目标", "Food": "食物",
    "Wall": "墙", "Collisions": "碰撞", "Grid size": "棋盘大小", "Position": "位置",
    "Speed": "速度", "Trail": "轨迹", "Show trail": "显示轨迹", "Controller": "控制器",
    "Maze": "迷宫", "Snake": "贪吃蛇", "Basic": "Basic 瞄准", "Predict Position": "Predict Position 预判",
    "AMMO": "弹药", "ELAPSED TICKS": "已流逝 tick", "CASE": "案例", "DECISION": "决策",
    "LAST DECISION": "最近决策", "Last decision": "最近决策", "INITIAL STATE": "初始状态",
    "Initial state": "初始状态", "RECORDED ACTION": "录制的动作", "RECORDED": "已录制",
    "Request JSON": "请求 JSON", "Response JSON": "响应 JSON", "Actual response": "实际响应",
    "Batch: raw JSON": "批次：原始 JSON", "Current step: raw JSON": "当前步：原始 JSON",
    "Next environment step": "下一环境步", "Previous environment step": "上一环境步",
    "Next physical tick": "下一物理 tick", "Previous physical tick": "上一物理 tick",
    "Next step": "下一步", "Previous step": "上一步", "Next tick (→)": "下一 tick (→)",
    "Previous tick (←)": "上一 tick (←)", "Play / pause (Space)": "播放/暂停（空格）",
    "Restart (R)": "重启 (R)", "Pause": "暂停", "Play": "播放", "Restart": "重启",
    "Ready": "就绪", "Running": "运行中", "Loading": "加载中", "Space": "空格", "step": "步",
    "Play all recordings": "播放全部录制", "Play all three recordings": "播放三路录制",
    "Play recorded run": "播放录制的对局", "Restart all recordings": "重启全部录制",
    "One shared physical clock. Each run holds its final recorded frame.": "共享同一物理时钟。每路保留其最终录制帧。",
    "Same map. Three real trajectories.": "同一张地图。三条真实轨迹。", "Three models.": "三个模型。",
    "The target keeps moving. The rocket takes time. Watch three models choose their moment.": "目标在移动，火箭有飞行时间。看三个模型如何选择开火时机。",
    "Jev and untuned Qwen fire early and miss this moving target.": "Jev 和未微调 Qwen 过早开火，打不中移动目标。",
    "NanoJev waits, fires, and hits.": "NanoJev 等待时机，开火命中。",
    "NanoJev hits. Both baselines miss.": "NanoJev 命中。两个基线都未命中。",
    "Land the single rocket": "用仅有的一发火箭命中", "Track the moving target": "跟踪移动目标",
    "Choose when to fire": "选择开火时机", "One rocket.": "一发火箭。", "Make it count": "一击必中",
    "Rocket ready": "火箭就绪", "1 rocket · not fired": "1 发火箭 · 未发射",
    "Actual rocket launch moments": "实际火箭发射时刻",
    "Actual target eliminations · same controller and seeds": "实际消灭目标数 · 相同控制器与种子",
    "Same target, same starting state, same controller.": "同一目标、同一初始状态、同一控制器。",
    "Same target. Same starting state.": "同一目标。同一初始状态。",
    "All 128 test episodes.": "全部 128 个测试局。", "Selected success cases": "选定的成功案例",
    "Final results": "最终结果", "How Predict Position works": "Predict Position 是怎么玩的",
    "Three-model Predict Position replay": "三模型 Predict Position 回放",
    "Three-model shooting replay": "三模型射击回放", "Three-system replay": "三系统对比回放",
    "Side-by-side game comparison": "并排游戏对比",
    "Synchronized by environment step": "按环境步同步", "Shared environment step": "共享环境步",
    "Shared physical tick": "共享物理 tick", "SHARED TICK TIMELINE": "共享 tick 时间轴",
    "Synchronized playback controls": "同步播放控制", "Shared playback controls": "共享播放控制",
    "Playback controls": "播放控制", "Playback speed": "播放速度", "PLAYBACK": "播放",
    "Slow": "慢速", "Normal": "常速", "Fast": "快速",
    "Recorded Doom frame": "录制的 Doom 画面", "Recorded game board": "录制的游戏棋盘",
    "Recorded game state": "录制的游戏状态", "Recorded gameplay": "录制的实机画面",
    "Recorded model decision": "录制的模型决策", "Recorded step": "录制的步",
    "Recorded attempts": "录制尝试次数", "Recorded example": "录制示例",
    "Recorded experiment summary": "实验摘要（录制）",
    "Recorded decisions + code planning": "录制决策 + 代码规划",
    "Recorded decisions + shared code planning": "录制决策 + 共享代码规划",
    "Recorded decisions + shared game controller": "录制决策 + 共享游戏控制器",
    "Recorded showcase loaded · synchronized by environment step": "录制展示已加载 · 按环境步同步",
    "Recordings are not available yet": "录制尚未就绪", "The recordings are not available yet": "录制尚未就绪",
    "The recording could not be loaded": "录制加载失败",
    "Run statistics": "运行统计", "Try your own state": "试试你自己的状态",
    "Run inference": "运行推理", "Waiting for local model inference…": "等待本地模型推理…",
    "Start a local model service with /api/evaluate support first.": "请先启动带 /api/evaluate 的本地模型服务。",
    "Start an HTTP model service before using the live endpoint.": "使用实时端点前，请先启动 HTTP 模型服务。",
    "The request must be a valid JSON object. Nothing was sent.": "请求必须是合法 JSON 对象。未发送任何内容。",
    "The actual response will appear here.": "实际响应将显示在这里。",
    "No response to this request yet": "该请求尚无响应", "Request incomplete": "请求不完整",
    "Batched states, independent questions": "多状态同批，问题相互独立",
    "Multi-state batching is shown only when supported by the saved execution record.": "仅当保存的执行记录支持时才显示多状态批处理。",
    "Select a batch": "选择一个批次", "No batches yet": "暂无批次", "No batch record": "无批次记录",
    "Select a step to inspect its recorded decision.": "选择一步查看其录制的决策。",
    "The executed action is highlighted.": "被执行的动作已高亮。",
    "Environment steps · recorded probabilities · real outcomes": "环境步 · 录制概率 · 真实结果",
    "Explore the recorded run, one step at a time.": "逐步浏览录制的对局。",
    "Original frames & model decisions": "原始画面与模型决策",
    "Slow motion · 0.5× playback. All panels share the same game clock.": "慢放 · 0.5× 速度。所有面板共享同一游戏时钟。",
    "Views": "视图", "Lab": "实验室", "Development": "开发", "Development arcade": "开发街机",
    "Game demos": "游戏演示", "NanoJev home": "NanoJev 主页", "NanoJev development home": "NanoJev 开发主页",
    "NanoJev repository": "NanoJev 仓库", "Full experiment viewer ↗": "完整实验查看器 ↗",
    "Maze + Snake: open the decision arcade ↗": "迷宫 + 贪吃蛇：打开决策街机 ↗",
    "DECISION SYSTEM": "决策系统", "THE DECISION ARCADE": "决策街机",
    "THE DECISION ARCADE / PREDICT POSITION": "决策街机 / PREDICT POSITION",
    "THE DECISION ARCADE / VIZDOOM": "决策街机 / VIZDOOM",
    "NAVIGATION LAB": "导航实验室", "MAZE": "迷宫", "RECORDED RUNS": "录制对局",
    "REAL GAME REPLAYS": "真实游戏回放", "FULL RECORDED RUNS": "完整录制对局",
    "SELECTED TEST REPLAY": "选定测试回放", "BEYOND THE SELECTED REPLAYS": "不止这些回放",
    "BEYOND THIS ONE REPLAY": "不止这一回放", "FEATURED WIN": "精选胜局",
    "JUMP TO A SHOT": "跳到开火时刻", "TYPED PROBABILITIES": "原生概率",
    "OPTIONAL LIVE ENDPOINT": "可选实时端点", "ORIGINS & SCOPE": "来源与范围",
    "CURRENT ARENA": "当前竞技场", "SPEED": "速度", "Model": "模型",
    "UNIFIED MODEL · STEP 400": "统一模型 · 第 400 步", "Unified model · step 400": "统一模型 · 第 400 步",
    "Small model. Visible decisions.": "小模型，看得见的决策。",
    "SMALL MODEL. VISIBLE DECISIONS.": "小模型，看得见的决策。",
    "SMALL MODELS. BIG DECISIONS.": "小模型，大决策。",
    "A little model. A complete view.": "小模型，完整视角。", "One arena": "同一竞技场",
    "Inspired by Jev. Measured in action.": "受 Jev 启发，用行动检验。", "Decisions in motion": "动态决策",
    "The updated unified model takes aim. Compare its real gameplay with Jev and untuned Qwen.": "更新后的统一模型瞄准目标。对比它与 Jev、未微调 Qwen 的真实对局。",
    "One unified NanoJev model across Maze, Snake and ViZDoom. Real runs, side by side.": "同一个 NanoJev 统一模型玩迷宫、贪吃蛇和 ViZDoom。真实对局并排呈现。",
    "Three systems. The same game. Every move, side by side.": "三个系统，同一游戏，每一步并排呈现。",
    "Preparing the shared arena and its decision timeline.": "正在准备共享竞技场与决策时间轴。",
    "Opening the arcade": "正在打开街机", "Loading the real runs": "加载真实对局",
    "Loading the recordings": "加载录制", "Loading recorded decisions and game states.": "加载录制的决策与游戏状态。",
    "Loading arena frames…": "加载竞技场画面…", "Loading experiment records": "加载实验记录",
    "Experiment records not loaded": "实验记录未加载", "Experiment selection": "实验选择",
    "Selected map": "选定地图", "Goal / food": "目标 / 食物", "Agent / head": "智能体 / 蛇头",
    "Waiting for recorded trajectories": "等待录制轨迹",
    "Waiting for recorded trajectories. Run the media assembly script to load the showcase.": "等待录制轨迹。运行媒体装配脚本加载展示。",
    "Waiting for the local results file": "等待本地结果文件",
    "Model action probabilities": "模型动作概率", "Action probabilities": "动作概率",
    "▶ Play the NanoJev win": "▶ 播放 NanoJev 胜局", "play / pause": "播放 / 暂停",
    "NanoJev recorded game demonstrations": "NanoJev 录制的游戏演示"
  };
  var TITLES = {
    "NanoJev · Decision Lab": "NanoJev · 决策实验室",
    "NanoJev — Decisions in motion": "NanoJev — 动态决策",
    "NanoJev — The decision arcade": "NanoJev — 决策街机",
    "NanoJev · A nano replica of Jev": "NanoJev · Jev 的纳米复刻",
    "NanoJev Development — Shooting": "NanoJev 开发 — 射击",
    "NanoJev — Predict Position": "NanoJev — Predict Position 预判"
  };
  var PATTERNS = [
    [/^(\d+) steps\/s$/, "$1 步/秒"],
    [/^(\d+)\s*\/\s*(\d+) steps$/, "$1 / $2 步"],
    [/^Step (\d+)$/, "第 $1 步"],
    [/^Step (\d+) \/ (\d+)$/, "第 $1 / $2 步"],
    [/^Episode (\d+)$/, "第 $1 局"],
    [/^tick (\d+)$/i, "tick $1"]
  ];
  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, PRE: 1, CODE: 1, TEXTAREA: 1 };
  function skipNode(node) {
    var p = node;
    while (p && p !== document.body) {
      if (SKIP_TAGS[p.nodeName]) return true;
      var cls = p.classList ? p.className : "";
      if (typeof cls === "string" && /json|raw|code/i.test(cls)) return true;
      p = p.parentNode;
    }
    return false;
  }
  function translate(text) {
    var t = text.trim();
    if (!t || !/[a-zA-Z]{2}/.test(t)) return null;
    if (ZH[t]) return ZH[t];
    for (var i = 0; i < PATTERNS.length; i++) {
      if (PATTERNS[i][0].test(t)) return t.replace(PATTERNS[i][0], PATTERNS[i][1]);
    }
    return null;
  }
  function apply(node, zh) {
    if (!node.i18nOrig) node.i18nOrig = node.nodeValue;
    node.nodeValue = zh;
  }
  function walk(root, toZh) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    var node;
    while ((node = walker.nextNode())) {
      if (node.nodeType === 3) {
        if (skipNode(node) || node.parentElement === btn) continue;
        if (toZh) {
          var zh = translate(node.nodeValue);
          if (zh !== null && zh !== node.nodeValue.trim()) {
            var lead = node.nodeValue.match(/^\s*/)[0], tail = node.nodeValue.match(/\s*$/)[0];
            apply(node, lead + zh + tail);
          }
        } else if (node.i18nOrig) {
          node.nodeValue = node.i18nOrig;
        }
      } else if (node.nodeType === 1 && node !== btn) {
        ["placeholder", "title", "aria-label"].forEach(function (a) {
          var v = node.getAttribute && node.getAttribute(a);
          if (!v) return;
          if (toZh) {
            var z = translate(v);
            if (z !== null) {
              if (!node.getAttribute("data-i18n-" + a)) node.setAttribute("data-i18n-" + a, v);
              node.setAttribute(a, z);
            }
          } else {
            var o = node.getAttribute("data-i18n-" + a);
            if (o) node.setAttribute(a, o);
          }
        });
      }
    }
  }
  var btn;
  function setLang(lang) {
    try { localStorage.setItem("nanojev-lang", lang); } catch (e) {}
    walk(document.body, lang === "zh");
    var t = TITLES[document.title];
    if (lang === "zh" && t) {
      if (!document.documentElement.dataset.i18nTitle) document.documentElement.dataset.i18nTitle = document.title;
      document.title = t;
    } else if (document.documentElement.dataset.i18nTitle) {
      document.title = document.documentElement.dataset.i18nTitle;
    }
    if (btn) btn.textContent = lang === "zh" ? "EN" : "中文";
  }
  function init() {
    btn = document.createElement("button");
    btn.type = "button";
    btn.style.cssText = "position:fixed;top:10px;right:12px;z-index:99999;padding:4px 12px;" +
      "border-radius:14px;border:1px solid rgba(255,255,255,.35);background:rgba(20,26,38,.85);" +
      "color:#e8edf5;font:600 12px/1.6 system-ui,sans-serif;cursor:pointer;backdrop-filter:blur(4px)";
    btn.onclick = function () { setLang((localStorage.getItem("nanojev-lang") || "zh") === "zh" ? "en" : "zh"); };
    document.body.appendChild(btn);
    var lang = "zh";
    try { lang = localStorage.getItem("nanojev-lang") || "zh"; } catch (e) {}
    setLang(lang);
    var pending = null;
    new MutationObserver(function () {
      clearTimeout(pending);
      pending = setTimeout(function () {
        walk(document.body, (localStorage.getItem("nanojev-lang") || "zh") === "zh");
      }, 120);
    }).observe(document.body, { childList: true, subtree: true, characterData: false });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
