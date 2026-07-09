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

## 後續(未排程,Hans 拍板)

- 若要謹慎/停-觀-走能力:訓練一個 stop-aware slalom 策略(station-tick 先例),
  再測它在統一 WM 上是否也更穩健(把「打斷鏈」做進策略、而非事後包 wrapper)。
- 工具留任:`eval/eval_slalom_stopobserve.py --hover N`、`StopObserveSlalom`。
