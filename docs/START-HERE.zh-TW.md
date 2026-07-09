# 從這裡開始（繁體中文導覽）

歡迎。這個 repo 是一個「量測紀律優先」的微型無人機世界模型研究專案——
每個主張都能追溯到一條可重跑的指令，連失敗都有判決書。本頁是繁中讀者
的導覽地圖；深入內容以英文為主（維護成本考量），但入口在這裡。

## 你是誰？從哪裡進來？

**從課程 repo（nanodrone-ai）過來的**：課程教「完整可學」，這裡做
「尖銳可測」。課程第 29 課的世界模型就是這裡 v0.1 的前身——你已經懂
八成的詞彙了，直接跳「第一個小時」。

**全新的人類研究員**：走
[docs/ONBOARDING.md](ONBOARDING.md)（英文）的「第一個小時」路徑：
三行指令裝環境 → 跑自檢 → 讀一份戰役日誌 → 跑一個乾跑閘門 → 抓冠軍
工件 → 產出你的第一個真實量測。全程約一小時。

**AI agent**：先讀
[.claude/commands/research-operator.md](../.claude/commands/research-operator.md)
（操作員憲章——規定性流程、固定回報格式、明文禁區），能力夠強再升級到
[.claude/commands/research.md](../.claude/commands/research.md)
（研究員憲章——閘門之間的判斷是你的工作）。

## 五分鐘理解這裡的玩法

1. **技能（skill）**＝插件：宣告場景、凍結的及格線（bars）、實驗排程
   （knobs）。範例：穿圍欄縫、追滑動缺口、關閉中的門。另有一條**室內主動
   搜索軌**（`experiments/search_*`）——覆蓋未知房間、找信標、返航——並在
   v0.8 打破 yaw=0 相機鎖、長出垂直搜索（飛到目標高度平視，找高櫃與床底），
   詳見 [docs/ROADMAP.md](ROADMAP.md) 的 Indoor Active Search Track。
2. **戰役（campaign）**＝一個技能的完整研究弧：自動 runner 逐閘門
   （gate）執行——訓練、飛行、對線、記日誌、commit——直到達標或預算盡。
3. **家規**：一次只轉一個旋鈕；及格線在數字出現前凍結；護欄（guards）
   神聖不可侵犯；誠實負結果照記不重試；用撞毀率驗收、不用 loss。
   全文在 [CLAUDE.md](../CLAUDE.md)。
4. **詞彙表**：[docs/GLOSSARY.md](GLOSSARY.md)——knob/gate/bar/guard/
   draw/champion 這些行話的定義＋活例連結。
5. **想做什麼**：[docs/RESEARCH-IDEAS.md](RESEARCH-IDEAS.md)——難度
   分級的公開題庫（★ 是刻意留給新手的第一場戰役）。

## 三行指令起步

```bash
conda env create -f environment.yml && conda activate microdrone-wm
pip install --no-deps git+https://github.com/utiasDSL/gym-pybullet-drones.git
pip install -e . && python -m scripts.fetch_champions
```

然後讀一份戰役日誌感受一下這裡的敘事方式（強烈推薦，15 分鐘）：
[experiments/gap_flight/journal.md](../experiments/gap_flight/journal.md)
——113 行走完「誠實的零樣本失敗 → 目標過但護欄破 → 具名偏離 → 通過」
的完整劇情。

## 常見疑問

- **我的數字跟日誌對不上？** 正常。機制會重現、小數點不會（訓練有
  隨機性、Mac 的 MPS 尤其）。這裡發表的是範圍不是單次好運，詳見
  詞彙表的「two-tier claims」。
- **想加新技能？** `python -m scripts.new_skill 我的技能` 會生出
  骨架，所有慣例已填好、要你決定的地方都標了 `TODO(researcher)`。
- **跑之前不確定會不會爆？** `python -m scripts.research doctor
  skills/我的技能`——預飛檢查會把帳單先算給你看。
