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
  articles: {
    eyebrow: string;
    title: string;
    intro: string;
    linkLabel: string;
    items: Array<{ title: string; simple: string; slug: string }>;
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
      { label: "文章", href: "#articles" },
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
    articles: {
      eyebrow: "The article series / 費曼規則",
      title: "十一篇文章，每篇先講白話版。",
      intro:
        "完整雙語系列在 repo 的 writing/ 目錄；每篇開頭都有一段零行話的白話版——這裡就是那十段。",
      linkLabel: "閱讀全文 →",
      items: [
        {
          title: "為什麼微型無人機需要「小小的」世界模型",
          simple:
            "一台手掌大的無人機，腦容量比一張照片還小——512 KB——而且速度一快，反射就失靈：等到東西「看起來很近」，閃避已經來不及。騎腳踏車的人不是盯著前輪底下反應，而是隨時在心裡預演下一秒。這個系列就是把那份預演做小到裝得進無人機：不是更利的眼睛，而是半秒鐘的預知。本篇量到：純反射在兩倍速下摔 57–63%。解藥是預判。",
          slug: "01-why-tiny-world-models",
        },
        {
          title: "為什麼預測像素是錯的目標",
          simple:
            "過馬路時，你不會在腦中畫出每台車的照片——你只追蹤「那台會不會開到我面前」。讓一顆小模型去預測未來的「畫面」，等於把全部預算花在壁紙上；無人機真正需要預測的只有一件事：往左飛，會不會受傷？所以我們預測場景的精簡摘要、而不是場景本身——摔機數字站在摘要這一邊。",
          slug: "02-why-predicting-pixels-is-wrong",
        },
        {
          title: "反應式 vs 預判式：實測那道速度懸崖",
          simple:
            "打者不會等球到本壘才揮棒——他朝球「將要到的位置」揮。給兩個飛行員同一雙眼睛：一個對看到的東西做反應、一個照半秒後的預測行動。同一台機、同一顆相機、同樣的賽道、速度加倍——反應式的直接摔下懸崖，預測式的沒有。一條曲線講完整個論點。",
          slug: "03-the-speed-cliff-measured",
        },
        {
          title: "打造動作條件化的 latent 世界模型（81 KB 權重）",
          simple:
            "老司機不會記得路上的每一幀畫面——他帶著一份精簡的「路感」，加上每個動作會通往哪裡的直覺。我們把這件事做進 81 KB 的權重裡：把相機壓成 64 個數字、學會每個指令會怎麼改變這些數字、再問一個小小的裁判「這樣飛下去會不會撞」。下面每一個設計決定都有同一個理由：另一個選項實測飛得更差。",
          slug: "04-building-the-world-model",
        },
        {
          title: "用撞毀率評估，不用 loss",
          simple:
            "模擬考分數更高的學生，路考照樣可能被當。我們升級過在每一項紙面指標上都更漂亮的模型——飛起來反而更糟。這個專案唯一信任的分數，是唯一算數的那個：真任務上有沒有少摔？這條規則有四次量測在案，四次都攔下了「包裝成升級的降級」。",
          slug: "05-evaluate-by-crash-rate",
        },
        {
          title: "單元測試全綠，整合測試全紅：爬向佈署門檻",
          simple:
            "四個短跑冠軍湊在一起，不會自動變成接力金牌隊——掉棒都掉在交接區。五個飛行技能各自考試全綠，第一次串成完整任務只考出 33/100。這篇講的就是從 33 爬到 72/100 部署門的過程：每一分都用同一個方法買回來——找出棒掉在哪裡、為什麼掉。",
          slug: "06-the-integration-climb",
        },
        {
          title: "KL 錨守不住的東西",
          simple:
            "跟新員工說「做法不要偏離老師傅太多」，然後讓他整個月只操練一項新任務——一千步「每步都沒偏太多」之後，他做起事來已經是另一個人。這就是帶 KL 錨的微調：鏈子綁的是每一步、不是你最後走到哪。本篇是「升級一個技能而不磨掉其他技能」的量測版安全法——外加誠實的一句：有些東西，任何錨都守不住。",
          slug: "07-what-anchors-cannot-defend",
        },
        {
          title: "從模擬走向 Crazyflie：嵌入式預算",
          simple:
            "行李限重 7 公斤不只限制你怎麼打包——它決定你能擁有什麼。晶片的 512 KB 就是這樣決定了模型的整個長相。而「帳面上裝得下」不等於「飛得起來」：當我們終於用晶片的方式（壓成 int8）跑整套系統，模型都活了下來，但決定「現在閃！」的那條引線斷了。過磅，不等於登機。",
          slug: "08-the-embedded-budget",
        },
        {
          title: "縫的代價：老師總是把車開回家",
          simple:
            "看教練開車，永遠學不會「自己壓線之後怎麼救回來」——因為教練不會壓線。我們的飛行員老是死在關卡交接的瞬間，而再多的示範都治不好：稱職的老師幾秒內就把車開回熟悉的路，學生自己犯錯之後的世界從不出現在教材裡。解法——讓學生開、教練對他實際遇到的每個處境逐一點評——把考試從 72 分帶到 79 分。",
          slug: "09-the-seam-tax",
        },
        {
          title: "單幀 recall 是謊言：把偵測當成序列證據",
          simple:
            "保全不需要每一瞥都看對——他會再看一眼。我們的偵測器單幀會漏掉三分之一的目標，任務卻有 93% 找得到，因為搜索本身被設計成「多看幾眼、每眼刻意不同」。但反過來的招數會失敗：「把懷疑無限累積下去」的規則，最後會把每個路人都當成小偷——微小的誤差無上限地疊加。能用的配方是：多看幾次、記得短一點。",
          slug: "10-per-frame-recall-is-a-lie",
        },
        {
          title: "那一秒的退縮：解剖一個瞬間",
          simple:
            "匯入高速公路時，緊張的駕駛會在最該踩油門的瞬間踩了剎車。我們的無人機在移動缺口前做一樣的事——這是當場抓到退縮、證明縫本來穿得過、然後發現「不退縮」為什麼教不會的故事：教練靠學生的後照鏡解析不了的東西判斷時機。殘餘有名字：感知稅。",
          slug: "11-the-flinch",
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
        { title: "仍是 simulation", description: "真機硬體仍 parked；85/100 與 91/100 不能寫成實機可靠度。" },
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
      { label: "Articles", href: "#articles" },
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
    articles: {
      eyebrow: "The article series / the Feynman rule",
      title: "Eleven articles, each opening in plain language.",
      intro:
        "The full bilingual series lives in the repo's writing/ directory; every article opens with a jargon-free simple version — these are those ten.",
      linkLabel: "Read the article \u2192",
      items: [
        {
          title: "Why micro-drones need tiny world models",
          simple:
            "A palm-sized drone carries a brain smaller than one photo — 512 KB — and at speed, reflexes stop working: by the time something LOOKS close, it is already too late to dodge. A cyclist doesn't ride by reacting to what's under the front wheel; they carry a running guess of what happens next. This series builds that guess small enough to fit the drone: not sharper eyes — half a second of foresight. Measured here: pure reflexes crash 57–63 % of the time at double speed. Foresight is the cure.",
          slug: "01-why-tiny-world-models",
        },
        {
          title: "Why predicting pixels is the wrong target",
          simple:
            "To cross a road you don't paint a mental photograph of every car — you only track \"will that one reach me\". Training a tiny model to predict future PICTURES spends its whole budget on wallpaper; the one thing the drone needs predicted is: if I go left, do I get hurt? So we predict a small summary of the scene instead of the scene itself — and the crash numbers side with the summary.",
          slug: "02-why-predicting-pixels-is-wrong",
        },
        {
          title: "Reactive vs proactive: the speed cliff, measured",
          simple:
            "A batter doesn't swing when the ball reaches the plate — they swing at where it WILL be. Give two pilots the same eyes: one reacts to what it sees, the other acts on a half-second forecast. Same drone, same camera, same courses, double the speed — the reactive pilot falls off a cliff and the forecasting one doesn't. One curve carries the whole argument.",
          slug: "03-the-speed-cliff-measured",
        },
        {
          title: "Building an action-conditioned latent world model",
          simple:
            "An experienced driver doesn't remember every frame of the road — they carry a compact \"feel\" for the situation, plus an instinct for where each move leads. We build exactly that in 81 KB of weights: squeeze the camera into 64 numbers, learn how each command changes those numbers, and ask a tiny judge \"does this end in a crash?\". Every design choice below is here because the alternative measurably flew worse.",
          slug: "04-building-the-world-model",
        },
        {
          title: "Evaluate by crash rate, not loss",
          simple:
            "A student with better mock-exam scores can still fail the road test. We upgraded models that beat the old ones on every paper metric — and they flew worse. The only score this project trusts is the one that matters: does it crash less on the real mission? That rule has stopped us four measured times from shipping a downgrade dressed as an upgrade.",
          slug: "05-evaluate-by-crash-rate",
        },
        {
          title: "Unit-green is not integration-green",
          simple:
            "Four sprint champions don't automatically make a relay team — batons drop at the hand-offs. Five flying skills, each green on its own test, scored 33/100 the first time they were chained into full missions. This article is the climb from 33 to a 72/100 deployment gate, where every point was bought the same way: find where the baton dropped, and why.",
          slug: "06-the-integration-climb",
        },
        {
          title: "What a KL anchor cannot defend",
          simple:
            "Tell a new employee \"don't stray too far from how the old hands do it\", then have them drill one new task for a month — a thousand small, individually-allowed steps later, they work like someone else. That is fine-tuning with a KL anchor: the leash bounds each step, not where you end up. This article is the measured safety law for improving one skill without erasing the rest — and an honest line about what no anchor can defend.",
          slug: "07-what-anchors-cannot-defend",
        },
        {
          title: "From sim toward Crazyflie: the embedded budget",
          simple:
            "A 7 kg carry-on limit doesn't just constrain your packing — it decides what you own. Our chip's 512 KB decided the model's entire shape the same way. And \"it fits on paper\" is not \"it flies\": when we finally ran the stack the way the chip would — squeezed to int8 — the models survived, but the tripwire that decides \"dodge NOW\" did not. Weighing your luggage is not the same as boarding the plane.",
          slug: "08-the-embedded-budget",
        },
        {
          title: "The seam tax: the teacher always drives home",
          simple:
            "Watching your driving instructor never teaches you how to recover after YOU drift out of lane — because the instructor never drifts. Our pilot kept dying at stage hand-offs, and better demonstrations couldn't fix it: a competent teacher steers back onto familiar roads within seconds, so the student's own mistakes never appear in the data. The cure — let the student drive while the teacher comments on every situation the student actually gets into — took the gate from 72 to 79.",
          slug: "09-the-seam-tax",
        },
        {
          title: "Per-frame recall is a lie",
          simple:
            "A security guard doesn't need every glance to be right — they look again. Our detector misses the target in a third of single frames, yet the mission finds it 93 % of the time, because the search is built to take many deliberately different looks. But the opposite trick fails: a rule that accumulates suspicion FOREVER ends up flagging every passerby, because tiny errors pile up without limit. The working recipe: look many times, remember briefly.",
          slug: "10-per-frame-recall-is-a-lie",
        },
        {
          title: "The flinch: anatomy of one second",
          simple:
            "Merging onto a highway, a nervous driver sometimes brakes at exactly the moment they should commit. Our drone does the same at moving gaps — this is the story of catching the flinch in the act, proving the gap was takeable, and discovering why not-flinching is so hard to teach: the instructor knows the moment by seeing things the student\u2019s mirrors cannot resolve. The residue has a name: the perception tax.",
          slug: "11-the-flinch",
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
        { title: "Still simulation", description: "Hardware remains parked; 85/100 and 91/100 are not real-flight reliability." },
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
