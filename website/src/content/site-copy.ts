export type Locale = "zh-TW" | "en";

export type EvidenceKey = "transit" | "indoor" | "embedded" | "latency";

type NavItem = {
  label: string;
  href: string;
};

type MediaCopy = {
  title: string;
  description: string;
  ariaLabel: string;
};

export type SiteCopy = {
  accessibility: {
    skip: string;
    play: string;
    pause: string;
  };
  brand: {
    name: string;
    descriptor: string;
    homeLabel: string;
    githubLabel: string;
    languageLabel: string;
  };
  nav: NavItem[];
  hero: {
    eyebrow: string;
    title: string;
    lede: string;
    primaryCta: string;
    secondaryCta: string;
    recordLabel: string;
    recordStatus: string;
    media: MediaCopy;
    metricLabels: {
      transit: string;
      indoor: string;
      embedded: string;
    };
  };
  constraints: {
    items: Array<{ value: string; label: string }>;
  };
  pipeline: {
    eyebrow: string;
    title: string;
    intro: string;
    steps: Array<{ title: string; description: string }>;
    horizonsLabel: string;
    horizons: string[];
  };
  modes: {
    eyebrow: string;
    title: string;
    intro: string;
    items: Array<{
      id: "transit" | "indoor";
      tag: string;
      title: string;
      description: string;
      media: MediaCopy;
      roles: Array<{ label: string; value: string }>;
    }>;
  };
  evidence: {
    eyebrow: string;
    title: string;
    intro: string;
    recordLabel: string;
    passLabel: string;
    qualifier: string;
    sourceLabel: string;
    cards: Array<{
      key: EvidenceKey;
      label: string;
      description: string;
    }>;
    storyEyebrow: string;
    storyTitle: string;
    storyBody: string;
    storyAlt: string;
  };
  findings: {
    eyebrow: string;
    title: string;
    intro: string;
    items: Array<{ title: string; description: string }>;
  };
  research: {
    eyebrow: string;
    title: string;
    intro: string;
    steps: Array<{ title: string; description: string }>;
    principles: string[];
  };
  limits: {
    eyebrow: string;
    title: string;
    intro: string;
    items: Array<{ title: string; description: string }>;
    safetyLabel: string;
    safety: string;
  };
  quickstart: {
    eyebrow: string;
    title: string;
    intro: string;
    commands: string[];
    guideLabel: string;
    ideasLabel: string;
  };
  footer: {
    note: string;
    license: string;
  };
};

export const siteCopy: Record<Locale, SiteCopy> = {
  "zh-TW": {
    accessibility: {
      skip: "跳至主要內容",
      play: "播放飛行紀錄",
      pause: "暫停飛行紀錄",
    },
    brand: {
      name: "microdrone-world-model",
      descriptor: "flight recorder / research stack",
      homeLabel: "回到首頁",
      githubLabel: "GitHub 原始碼",
      languageLabel: "English",
    },
    nav: [
      { label: "預測流程", href: "#architecture" },
      { label: "證據", href: "#evidence" },
      { label: "研究方法", href: "#method" },
      { label: "限制", href: "#limits" },
    ],
    hero: {
      eyebrow: "Embedded world model / simulation records",
      title: "512 KB 裡，可以買到多少預判？",
      lede:
        "一個為 27 g 微型無人機打造的 tiny latent world-model stack：不生成像素，只預測每個動作會把未來帶到哪裡，並用可重跑的模擬閘門驗證每一個主張。",
      primaryCta: "查看可重跑證據",
      secondaryCta: "開啟 GitHub",
      recordLabel: "single-course flight record",
      recordStatus: "simulated / verified",
      media: {
        title: "提早轉向，而不是等到撞擊前反應",
        description: "單課程模擬的 top-down 記錄；控制迴路沒有 privileged look-ahead。",
        ariaLabel: "微型無人機在模擬柱體課程中提早轉向避障的飛行紀錄",
      },
      metricLabels: {
        transit: "Transit 模擬 gate",
        indoor: "Indoor 模擬 gate",
        embedded: "v0.1 完整 stack",
      },
    },
    constraints: {
      items: [
        { value: "512 KB", label: "權重、activation 與 workspace 共用的記憶體上限" },
        { value: "12 Hz", label: "每 83 ms 做一次有用的飛行決策" },
        { value: "60°", label: "固定在機身上的前視相機，沒有雲台" },
        { value: "≈ 8 ms", label: "依 0.5 GMAC/s 假設推算；不是 GAP8 實機量測" },
      ],
    },
    pipeline: {
      eyebrow: "How it looks ahead",
      title: "一次看見，評估多個未來。",
      intro:
        "昂貴的影像編碼只做一次；之後用小型 MLP 反覆評估候選動作。規劃器需要的不是漂亮影像，而是哪個選項會靠近障礙物。",
      steps: [
        { title: "Camera frame", description: "單一、固定、前視 60° 影像。" },
        { title: "64-d latent", description: "bearing-aware encoder 保留方向資訊。" },
        { title: "Candidate actions", description: "同一份 latent 配上不同飛行命令。" },
        { title: "Predicted futures", description: "residual predictor 向前看四個時間尺度。" },
        { title: "Planner", description: "warn／critical collision heads 交給 MPC 或 PPO。" },
      ],
      horizonsLabel: "prediction horizons",
      horizons: ["83 ms", "167 ms", "333 ms", "667 ms"],
    },
    modes: {
      eyebrow: "One pair / two missions",
      title: "世界模型只做它真正擅長的工作。",
      intro:
        "Transit 與室內搜索不是同一套故事。兩個模式在起飛前綁定各自的模型、控制器與安全工具，避免把感知能力誤寫成空間能力。",
      items: [
        {
          id: "transit",
          tag: "mode 01 / transit",
          title: "提早避開高速障礙",
          description:
            "Pinned world model 讀取相機中的危險，skill policy 將預測串成長決策鏈；安全濾網保留最後一道 veto。",
          media: {
            title: "Transit：dense pillars，1.4 m/s",
            description: "正式模式示意；相機固定在機身上。",
            ariaLabel: "微型無人機高速穿越密集柱體的 transit 模擬紀錄",
          },
          roles: [
            { label: "Perception", value: "Pinned world model" },
            { label: "Decision", value: "PPO skill policy" },
            { label: "Safety", value: "Safety filter" },
          ],
        },
        {
          id: "indoor",
          tag: "mode 02 / indoor search",
          title: "找得到，也回得來",
          description:
            "Unified world model 負責辨認視野中的目標；Frontier／grid 管覆蓋，beams8 rangefinder ring 管避撞。Indoor safety 並不是 vision-only。",
          media: {
            title: "Indoor：三房、雜物、找到並返航",
            description: "室內主動搜索的 top-down 模擬記錄。",
            ariaLabel: "微型無人機在三房室內模擬中搜索目標並返航的紀錄",
          },
          roles: [
            { label: "Perception", value: "Unified WM + target head" },
            { label: "Coverage", value: "Frontier / grid geometry" },
            { label: "Safety", value: "beams8 rangefinder ring" },
          ],
        },
      ],
    },
    evidence: {
      eyebrow: "Gate-of-record / 2026-07",
      title: "數字旁邊，永遠放著它的邊界。",
      intro:
        "這些是模擬部署前置閘門，不是真機成功率。每張卡都連回 committed record，並附有可重新飛行或自測的入口。",
      recordLabel: "record",
      passLabel: "green",
      qualifier:
        "Simulation only。137.3 KB 是 v0.1 完整 stack 的 int8 帳單；約 8 ms 是解析 MAC 數加上假設吞吐量的 estimated latency。",
      sourceLabel: "查看來源與重跑方式",
      cards: [
        {
          key: "transit",
          label: "Transit integration gate",
          description: "100 條隨機三段式模擬課程；正式門檻為 0.70。",
        },
        {
          key: "indoor",
          label: "Indoor mission gate",
          description: "found AND returned AND zero collisions；四類模擬任務。",
        },
        {
          key: "embedded",
          label: "Measured memory bill",
          description: "v0.1 權重、peak activations 與 DMA workspace 的合計。",
        },
        {
          key: "latency",
          label: "Estimated decision cost",
          description: "3.9 M MACs，以 0.5 GMAC/s effective int8 throughput 推算。",
        },
      ],
      storyEyebrow: "Failure histogram → next lineup",
      storyTitle: "五次 lineup，才跨過 0.70。",
      storyBody:
        "每一階都由上一個 failure histogram 決定：clone、anchored fine-tune、hybrid，再加入具名 specialist。這張圖保留失敗，因為爬坡本身就是結果。",
      storyAlt: "Transit integration success 從 0.33 經五次 lineup 上升到 0.72 並跨過 0.70 門檻的長條圖",
    },
    findings: {
      eyebrow: "What the experiments taught us",
      title: "更好的模型分數，不保證更好的飛行。",
      intro:
        "這個專案最重要的輸出不是單一 champion，而是哪些機制重現、哪些洞只是換了位置。",
      items: [
        {
          title: "世界模型擅長感知",
          description: "它能讀出視野中的碰撞風險與目標身份；這是便宜 rangefinder 無法回答的問題。",
        },
        {
          title: "幾何擅長空間工作",
          description: "室內 coverage、測高與環形避撞交給 Frontier、grid 與 beams8，成本更低也更穩。",
        },
        {
          title: "負結果也要進帳",
          description: "在 clutter coverage 上，加入世界模型反而輸給 grid-only 與 Frontier；專案保留這個 verdict，不重試到它變綠。",
        },
      ],
    },
    research: {
      eyebrow: "Flight skills / autonomous research loop",
      title: "把研究紀律寫進 runner。",
      intro:
        "每個 flight skill 都是插件：先凍結目標與護欄，再讓 runner 逐一訓練、飛行、評分與記錄。閘門之間的判斷仍由研究者負責。",
      steps: [
        { title: "Skill", description: "宣告場景、bars、guards。" },
        { title: "Knob", description: "一次只改一個變因。" },
        { title: "Fly", description: "使用固定 seeds 與 trajectory predicate。" },
        { title: "Gate", description: "對凍結門檻判決；borderline 才重測。" },
        { title: "Journal", description: "成功與失敗都寫入 committed record。" },
      ],
      principles: [
        "每個主張都能重跑",
        "及格線在數字出現前凍結",
        "護欄不可用主目標交換",
        "誠實負結果不重抽到通過",
      ],
    },
    limits: {
      eyebrow: "Honest limits",
      title: "可以做什麼，也寫清楚還不能做什麼。",
      intro:
        "目前所有 deployment gates 都是模擬中的硬體解凍前置條件。限制不是附註，而是每個數字的一部分。",
      items: [
        { title: "仍是 simulation", description: "真機硬體仍 parked；79/100 與 91/100 不能寫成實機可靠度。" },
        { title: "Latency 是推算", description: "約 8 ms 來自 MAC count 與吞吐量假設，不是 GAP8 實測。" },
        { title: "Indoor safety 不是 vision-only", description: "空間避撞由 beams8 rangefinder ring 負責。" },
        { title: "量化尚未完全閉環", description: "Indoor stack 可量化飛行；transit trigger 目前仍保留 float。" },
        { title: "Person 是模擬 proxy", description: "現有找人任務使用直立 capsule proxy，不等於真實人體辨識。" },
        { title: "飛行中偵測仍有債", description: "靜態分數不代表移動中穩定；temporal evidence 是下一條前沿。" },
      ],
      safetyLabel: "Safety boundary",
      safety:
        "本專案只用於安全導向的自主導航、避撞、教育與研究；不支援武器化、濫用監控或規避安全與法律限制。",
    },
    quickstart: {
      eyebrow: "Start with a measurement",
      title: "三行起飛，先跑證據。",
      intro: "抓取鎖定的 champion 後，先讀一份 journal，再用 scorecard 驗證整套治理層。",
      commands: [
        "conda env create -f environment.yml && conda activate microdrone-wm",
        "pip install --no-deps git+https://github.com/utiasDSL/gym-pybullet-drones.git",
        "pip install -e . && python -m scripts.fetch_champions",
      ],
      guideLabel: "繁中入門導覽",
      ideasLabel: "公開研究題庫",
    },
    footer: {
      note: "從 nanodrone-ai Lesson 29 長出的獨立研究 stack。所有首頁數字都連回可重跑的 record。",
      license: "Apache-2.0 license",
    },
  },
  en: {
    accessibility: {
      skip: "Skip to main content",
      play: "Play flight record",
      pause: "Pause flight record",
    },
    brand: {
      name: "microdrone-world-model",
      descriptor: "flight recorder / research stack",
      homeLabel: "Back to home",
      githubLabel: "GitHub source",
      languageLabel: "繁體中文",
    },
    nav: [
      { label: "Prediction", href: "#architecture" },
      { label: "Evidence", href: "#evidence" },
      { label: "Method", href: "#method" },
      { label: "Limits", href: "#limits" },
    ],
    hero: {
      eyebrow: "Embedded world model / simulation records",
      title: "How much anticipation can 512 KB buy?",
      lede:
        "A tiny latent world-model stack for a 27 g micro-drone. It never generates pixels; it predicts where each action takes the future, then grades every claim with a rerunnable simulation gate.",
      primaryCta: "Inspect the evidence",
      secondaryCta: "Open GitHub",
      recordLabel: "single-course flight record",
      recordStatus: "simulated / verified",
      media: {
        title: "Veer early instead of reacting at impact",
        description: "Top-down record from one simulated course; no privileged look-ahead in the control loop.",
        ariaLabel: "Simulation record of a micro-drone veering early around pillars",
      },
      metricLabels: {
        transit: "Transit simulation gate",
        indoor: "Indoor simulation gate",
        embedded: "Complete v0.1 stack",
      },
    },
    constraints: {
      items: [
        { value: "512 KB", label: "One memory ceiling for weights, activations, and workspace" },
        { value: "12 Hz", label: "One useful flight decision every 83 ms" },
        { value: "60°", label: "One forward camera, fixed rigidly to the body" },
        { value: "≈ 8 ms", label: "Estimated at an assumed 0.5 GMAC/s; not a GAP8 hardware benchmark" },
      ],
    },
    pipeline: {
      eyebrow: "How it looks ahead",
      title: "Encode once. Price several futures.",
      intro:
        "The expensive image encoding runs once. Tiny MLPs then reuse it across candidate commands. A planner does not need a beautiful future image; it needs to know which option approaches danger.",
      steps: [
        { title: "Camera frame", description: "One fixed, forward-facing 60° view." },
        { title: "64-d latent", description: "A bearing-aware encoder preserves direction." },
        { title: "Candidate actions", description: "Pair one latent with several flight commands." },
        { title: "Predicted futures", description: "A residual predictor looks across four timescales." },
        { title: "Planner", description: "Warn and critical heads feed hand MPC or PPO." },
      ],
      horizonsLabel: "prediction horizons",
      horizons: ["83 ms", "167 ms", "333 ms", "667 ms"],
    },
    modes: {
      eyebrow: "One pair / two missions",
      title: "The world model only owns the jobs it wins.",
      intro:
        "Transit and indoor search are not the same story. Before takeoff, each mode binds its own model, controller, and safety instruments so perception is never mistaken for spatial competence.",
      items: [
        {
          id: "transit",
          tag: "mode 01 / transit",
          title: "Anticipate obstacles at speed",
          description:
            "The pinned world model reads danger from the camera, a skill policy turns those predictions into a long decision chain, and a safety filter keeps the final veto.",
          media: {
            title: "Transit: dense pillars at 1.4 m/s",
            description: "A formal-mode illustration with the camera rigid to the body.",
            ariaLabel: "Simulation record of a micro-drone transiting dense pillars at speed",
          },
          roles: [
            { label: "Perception", value: "Pinned world model" },
            { label: "Decision", value: "PPO skill policy" },
            { label: "Safety", value: "Safety filter" },
          ],
        },
        {
          id: "indoor",
          tag: "mode 02 / indoor search",
          title: "Find the target, then come home",
          description:
            "The unified world model identifies what is in view. Frontier and grid geometry own coverage; a beams8 rangefinder ring owns collision safety. Indoor safety is not vision-only.",
          media: {
            title: "Indoor: three rooms, clutter, find and return",
            description: "Top-down record of the indoor active-search simulation.",
            ariaLabel: "Simulation record of a micro-drone searching three indoor rooms and returning",
          },
          roles: [
            { label: "Perception", value: "Unified WM + target head" },
            { label: "Coverage", value: "Frontier / grid geometry" },
            { label: "Safety", value: "beams8 rangefinder ring" },
          ],
        },
      ],
    },
    evidence: {
      eyebrow: "Gate-of-record / 2026-07",
      title: "Every number travels with its boundary.",
      intro:
        "These are simulated pre-deployment gates, not real-hardware success rates. Every card points back to a committed record and a command that can rerun or verify it.",
      recordLabel: "record",
      passLabel: "green",
      qualifier:
        "Simulation only. 137.3 KB is the complete int8 bill for the v0.1 stack; about 8 ms is an estimated latency from analytical MACs and assumed throughput.",
      sourceLabel: "Inspect source and rerun path",
      cards: [
        {
          key: "transit",
          label: "Transit integration gate",
          description: "100 randomized three-stage simulation courses against a frozen 0.70 bar.",
        },
        {
          key: "indoor",
          label: "Indoor mission gate",
          description: "Found AND returned AND zero collisions across four simulated mission families.",
        },
        {
          key: "embedded",
          label: "Measured memory bill",
          description: "v0.1 weights, peak activations, and DMA workspace combined.",
        },
        {
          key: "latency",
          label: "Estimated decision cost",
          description: "3.9 M MACs at an assumed 0.5 GMAC/s effective int8 throughput.",
        },
      ],
      storyEyebrow: "Failure histogram → next lineup",
      storyTitle: "It took five lineups to cross 0.70.",
      storyBody:
        "Each rung came from the previous failure histogram: clone, anchored fine-tune, hybrid, then named specialists. The chart keeps every failure visible because the climb is itself a result.",
      storyAlt: "Bar chart showing transit integration success rising from 0.33 to 0.72 across five lineups and crossing the 0.70 gate",
    },
    findings: {
      eyebrow: "What the experiments taught us",
      title: "A better model score is not automatically a better flight.",
      intro:
        "The durable output is not one champion. It is knowing which mechanisms reproduce, and which interventions merely move the hole.",
      items: [
        {
          title: "World models win at perception",
          description: "They read collision risk and target identity in the camera view—questions a cheap rangefinder cannot answer.",
        },
        {
          title: "Geometry wins at spatial jobs",
          description: "Indoor coverage, height, and ring safety go to Frontier, grids, and beams8 because they are cheaper and more reliable there.",
        },
        {
          title: "Negative results stay on record",
          description: "Under clutter, world-model coverage lost to grid-only and Frontier. The verdict remains published instead of being rerun until green.",
        },
      ],
    },
    research: {
      eyebrow: "Flight skills / autonomous research loop",
      title: "The method is encoded in the runner.",
      intro:
        "Every flight skill is a plugin: freeze targets and guards first, then let the runner train, fly, grade, and record each knob. Judgment between gates still belongs to the researcher.",
      steps: [
        { title: "Skill", description: "Declare scenarios, bars, and guards." },
        { title: "Knob", description: "Change one variable per training run." },
        { title: "Fly", description: "Use fixed seeds and trajectory predicates." },
        { title: "Gate", description: "Grade frozen bars; recheck only borderline cells." },
        { title: "Journal", description: "Commit wins and honest negatives alike." },
      ],
      principles: [
        "Every claim can be rerun",
        "Bars freeze before numbers appear",
        "Guards cannot be traded for the target",
        "Honest negatives are not rerolled",
      ],
    },
    limits: {
      eyebrow: "Honest limits",
      title: "State what it can do—and what it cannot do yet.",
      intro:
        "Every deployment gate today is a simulated precondition for unfreezing hardware. Limits are part of the number, not a footnote underneath it.",
      items: [
        { title: "Still simulation", description: "Hardware remains parked; 79/100 and 91/100 are not real-flight reliability." },
        { title: "Latency is estimated", description: "About 8 ms comes from MAC count and assumed throughput, not a GAP8 measurement." },
        { title: "Indoor safety is not vision-only", description: "A beams8 rangefinder ring owns spatial collision avoidance." },
        { title: "Quantization is not closed end to end", description: "The indoor stack flies quantized; the transit trigger still remains float." },
        { title: "The person is a simulated proxy", description: "The current person mission uses an upright capsule proxy, not real human recognition." },
        { title: "In-flight detection still carries debt", description: "Strong static scores do not imply motion robustness; temporal evidence is the next frontier." },
      ],
      safetyLabel: "Safety boundary",
      safety:
        "This project is for safety-focused navigation, collision avoidance, education, and research. It does not support weaponization, surveillance abuse, or evasion of safety and legal constraints.",
    },
    quickstart: {
      eyebrow: "Start with a measurement",
      title: "Three lines to take off. Evidence first.",
      intro: "Fetch the locked champions, read one campaign journal, then verify the governance layer with the scorecard.",
      commands: [
        "conda env create -f environment.yml && conda activate microdrone-wm",
        "pip install --no-deps git+https://github.com/utiasDSL/gym-pybullet-drones.git",
        "pip install -e . && python -m scripts.fetch_champions",
      ],
      guideLabel: "Traditional Chinese guide",
      ideasLabel: "Open research ideas",
    },
    footer: {
      note: "An independent research stack grown from nanodrone-ai Lesson 29. Every homepage number links back to a rerunnable record.",
      license: "Apache-2.0 license",
    },
  },
};
