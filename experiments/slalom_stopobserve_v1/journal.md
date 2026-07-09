# slalom_stopobserve_v1 — 每過一道門停下觀察(誠實負)

## 背景與假說

slalom 是最長、最緊、最序列的 skill(3 道交錯門、~40 決策鏈)。連續飛行時,
每步的微小動作誤差會**沿鏈複利**(`0.99⁴⁰≈0.67`)——這正是為什麼把 encoder
從冠軍換成統一 WM(unified-WM 全 zoo pass)時,連續 slalom 冠軍從 **80%→0%**
崩掉,而較短的 skill(gap/door)只掉 5–30%。

**假說(Hans:兩者都要):** 若無人機**穿過每一道門後先停下(hover)、從一張
乾淨的 frame 重新規劃、再前進**,就把鏈的誤差累積**重置**——每道門變成獨立的
短視野決策。這應該(a)是個穩健的謹慎飛行行為,並且(b)讓 slalom 撐過 WM 換掉。

## 方法

Wrapper `skills/corridor_slalom_v2/stop_observe.py:StopObserveSlalom`(不重訓、
不改場景):包既有的 slalom 冠軍 `LearnedPolicy`
(`experiments/slalom_v2_promotion/artifacts/ppo_anchor_sched_edge.zip`)。
用與考試判準完全一致的 `planner/learned_policy.py:gate_bonus_hits` 偵測「剛穿過
第 k 道門」→ 回傳 `hover`(id 5,已在冠軍訓練動作集內,VelCommander 把零命令變成
定點)`H` 個決策 → 再交棒回冠軍。「觀察=停穩後重新規劃」(Hans 選的最小版):
hover 本身就是觀察,不加額外感知。`eval/eval_slalom_stopobserve.py` 做 2×2:
{continuous, stop-observe} × {champion WM, unified WM},`slalom_success` 判準,
`tmax = TMAX + H·3·DECIDE_EVERY`(hover 不推進 x),n=20,seed0=22000,speed 0.8 m/s。

## 預先登記的 bar(跑之前凍結)

- continuous×champion ≈ 80%(已知基線);continuous×unified ≈ 0%(全 zoo 找到的崩)。
- **謹慎 PASS**:stop-observe×champion ≥ continuous×champion(在原生 WM 上停頓不傷)。
- **穩健 PASS**:stop-observe×unified 明顯勝過 continuous×unified(打斷鏈救回換 WM)。

## 結果 — 雙重負

| WM | continuous | stop-observe (H=10) | stop-observe (H=3) |
|---|---|---|---|
| champion | **80%** | 10% | 0% |
| unified | **0%** | 0% | 0% |

- 基線重現:continuous×champion 80%、continuous×unified 0%(與全 zoo pass 一致)。
- **謹慎 FAIL**:stop-observe **弄壞了冠軍**(80%→10%(H=10)/ 0%(H=3))。
- **穩健 FAIL**:stop-observe 完全沒救回 unified(0%→0%)。
- 兩個 hover 長度都崩 ⇒ **不是 hover 長度的調參問題**。

## 判詞 — 假說被否證(對「wrapper 包連續冠軍」這條路)

**停頓本身就是 OOD。** 冠軍是對**連續**織線飛行訓練的,從沒見過「中途停死、
零速、下一道門在 0.7m 外、觀測歷史全是靜止幀」的狀態;強迫它停再重啟,製造了一個
**比它要修的漂移更嚴重的 OOD 條件**——它抓不回織線。H=3 比 H=10 更糟,很可能因為
短 hover 讓無人機沒完全停穩就重啟,瞬態更亂;長 hover 至少偶爾(10%)停穩後救得回。

所以「打斷鏈」的直覺沒錯,但**用 wrapper 包一個連續訓練的冠軍實現不了**:修法
(hover)引入的 OOD 大於它針對的漂移。要真正實現停下觀察,需要**訓練一個預期
停-觀-走節奏的策略**(repo 已有先例:dodgeball 的 "station" 模式訓練無人機定點
懸停並每步計 tick——`planner/learned_policy.py` 的 `station_tick`);那是重訓路線,
明確不在本次「不重訓」範圍內、由 Hans 拍板。

## 誠實邊界 / 未試

- **未試的變體**:hover 期間**凍結**冠軍的觀測歷史(不餵靜止幀),讓它重啟時
  以為時間沒流逝。物理上無人機仍停了(位置變化與歷史不符),仍是 OOD,不預期能
  救,但沒實測——列為未試。
- 基礎設施可重用且沒問題:`StopObserveSlalom` wrapper、`gate_bonus_hits` 觸發、
  2×2 harness 都乾淨(continuous×champion 80% 證明 harness 正確)。負結果是關於
  「wrapper-on-連續冠軍」這條路,不是「謹慎模式」這個概念本身(那需要 stop-aware
  重訓)。
- 對 unified 的結論不變:連續 slalom 在統一 WM 上仍是 0%(晉升仍需重訓 zoo,或
  走並存)——停下觀察沒有提供一條繞過重訓的捷徑。

## 後續已做:把停頓訓練進策略(部分正面,Hans「1/2 都做」核准)

wrapper 失敗的根因是「連續冠軍無法從死停重啟」。修法=**把停頓做進策略**:
`WMPolicyEnv` 加 `stop_hover`(過門後開一個獎勵窗、付 policy 選 HOVER +0.5、
移動 −0.05、壓掉 progress),warm-start 微調 slalom 冠軍 500k
(`scripts/train_stopaware_slalom.py` → `output/ppo_slalom_stopaware.zip`)。
部署時它**自己會停**(learned),所以讀 `--policy` 的 continuous(raw)欄:

| WM | 連續冠軍(基線) | stop-aware 策略(raw 自停) |
|---|---|---|
| champion | 80% | **75%** |
| unified | **0%** | **25%** |

(n=20;stop-observe 欄=wrapper 疊在已自停策略上=過度停頓 0%,忽略。)

**判詞:部分正面,方向確認。**
1. **在 wrapper 失敗處成功**:stop-aware 策略在冠軍上 75%(wrapper 包連續冠軍
   只 0–10%)⇒ 它學會了停穩再重啟,「把停頓訓練進去」才是實現停-觀-走的正解,
   且幾乎沒犧牲 slalom 技巧(75%≈80% 雜訊內)。
2. **部分救回換 WM 穩健性**:unified 上 **0%→25%**⇒ 打斷鏈做進策略確實買到
   真實但不完整的 encoder-swap 穩健性(5/20 vs 0/20,方向明確、n=20 有 ±~10%)。

**為何只部分(25% 非 75%):** 停頓重置的是**位置漂移**;但每道門的**局部感知**
(讀 gap)仍吃統一 latent 的位移,停頓修不了那部分。加上 500k warm-start 可能
欠訓(冠軍本體要 900k–1.35M)、stop_hover=8 未必完全沉降。**全恢復的候選**(未做、
Hans 拍板):更長訓練、更長 hover、或直接**在兩顆 WM 的 latent 上一起訓練**
(data-aug 對 encoder-swap 的正解)。

**對晉升的意涵:** 打斷鏈不是免費繞過重訓的捷徑,但證明**用 stop-aware 重訓能把
被 encoder-swap 打壞的長鏈 skill 部分救回**——若要走「重蒸餾 zoo 後晉升」,
stop-aware 是讓 slalom(最敏感的一環)更耐 swap 的一個具體手段。

## 後續²:兩顆 WM 一起訓練(data-aug over the encoder)— 機制確認,但是重新平衡

換 encoder 的正解=對 encoder 做 data augmentation。`WMPolicyEnv` 加 `aug_wm_path`:
每一集隨機用**冠軍或統一** encoder 編碼 obs(50/50),讓策略學一個與「哪顆 WM 餵它」
無關的控制。warm-start 微調冠軍 500k、`stop_hover=0`(隔離 data-aug)、aug=統一
→ `output/ppo_slalom_twowm.zip`。raw 部署 2×2,n=20,與前兩者並列:

| 方法 | champion | unified | 合計 |
|---|---|---|---|
| 連續冠軍(基線) | 80% | 0% | 80 |
| stop-aware(過門停頓) | 75% | 25% | 100 |
| **two-WM data-aug** | **35%** | **75%** | **110** |

**判詞:data-aug 是換 WM 穩健性最強的手段(unified 0%→75%,逼近冠軍原生 80%)
——「換 encoder 用 data-aug」的正解確認。** 但它**不是「兩邊都高」,而是重新平衡**:
unified 大漲、champion 卻從 80%→35%。50/50 的 aug 竟偏向 unified,代表這個
500k 預算下 policy 往統一 latent 的幾何靠攏、部分遺忘冠軍(warm-start 的冠軍
技巧被沖淡)。合計分(110)是三者最高、且是唯一讓 unified 真正能飛的。

**達成「兩邊都高」的候選(未做,Hans 拍板):** 冠軍-加權的 aug 比例
(如 0.66/0.34 偏冠軍)、更長訓練(冠軍本體要 900k–1.35M)、或 stop_hover + aug
兩機制疊加。目前 500k、50/50 落在「偏 unified」的平衡點。

**對兩條部署路線的意涵(關鍵):**
- **Option A(並存、已選):** 穿越 skill 跑**冠軍**——直接用原始冠軍 policy(80%),
  two-WM policy 不需要、也不該用(它把冠軍拉到 35%)。two-WM 結果不改變 Option A。
- **Option B(重蒸餾後晉升):** 若覆蓋成統一 WM,skill 要在統一 latent 上重訓——
  **two-WM data-aug 正是讓最敏感的 slalom 撐過 swap 的手段(unified 75%)**;
  覆蓋後 champion 分數無關(已被覆蓋)。故 two-WM 是 Option B 的可行性證據。

工具留任:`scripts/train_stopaware_slalom.py --stop-hover/--aug-wm`、
`eval/eval_slalom_stopobserve.py --policy`、`WMPolicyEnv(stop_hover=, aug_wm_path=)`、
`StopObserveSlalom`。
