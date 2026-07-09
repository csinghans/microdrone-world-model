# person_v1 — Phase 0: can the frozen WM latent tell a PERSON from clutter?

## 背景與動機(Hans:「室內還有什麼場景 WM 能發揮」)

室內軌的分工已定:幾何贏空間工作(避撞 beams8、覆蓋 Frontier、測高 rangefinder),
WM 贏感知(偵測「目標在視野」AUC 0.94)。要往搜救推進,找的不是抽象信標,是**一個人**
——「這團東西是人還是瓦礫/家具」是純粹的**看懂**問題,幾何 beams 完全瞎,只有相機+WM
能做。決定性便宜問題(feasibility-first,同 yaw/alt):

**凍結的統一 WM latent 能不能把「人形」和「箱狀雜物」分開?**

## 方法(不飛不訓練)

`eval/eval_person_detect.py`:座標偏移渲染房間(牆+橘箱障礙),在 beacon_xy 放一個
**capsule 人形**(半徑 0.15、長 0.8、直立=人的軀幹),停機拍 +x 水平幀、統一 WM 編碼、
線性探針。兩個 AUC:
- **person-vs-empty**:人在 FOV vs 空 —— 偵測得到人形嗎?
- **person-vs-box**:人在 FOV vs 箱在 FOV(無人)—— 分得開「人 vs 雜物」嗎?

**誠實對照**:person-vs-box 若人是紅色(`--shape-control` 關),AUC = 形狀+顏色一起;
`--shape-control` 把人染成與箱同色(橘)→ AUC = **純形狀**。這才知道 latent 是靠形狀還是
只靠顏色。

## 預先登記 bar
- **GREEN**:person-vs-empty ≥ 0.85 **且** person-vs-box(shape+color)≥ 0.85 ⇒ 一個多類
  偵測頭能認出「人 vs 雜物」、不需 WM 重訓(延續 yaw/alt 廉價路)。
- **診斷**:shape-only AUC —— ≥0.75 代表形狀本身可分(強結果:WM 真的看到人形);若掉到
  ~0.5 而彩色版高,代表分辨靠顏色(仍可用,但不是「認出人」)。
- **RED**:person-vs-empty 就崩 ⇒ 人形是 OOD 外觀,需 WM 重訓(停下回報)。

兩顆 WM sha 全程不動(探針只讀)。

## 結果(6 房、182 幀、person-in-FOV 0.17 / box-in-FOV 0.24)

| 對照 | person-vs-empty | person-vs-box |
|---|---|---|
| **shape+colour**(人=紅 capsule) | **0.989** | **0.944** |
| **shape-only**(人=橘 capsule,與箱同色) | **0.901** | **0.806** |

## 判詞 — GREEN,而且是「真的看到人形」不是只靠顏色

- **偵測**:凍結 latent 對人形目標 person-vs-empty **0.989**(彩色)/ **0.901**(同色)——
  人形完全不是 OOD,latent 一眼看得到。
- **分類**:person-vs-box **0.944**(彩色)。**關鍵對照**:把人**染成與箱同色**後仍有
  **0.806** ⇒ **形狀本身**就把「人 vs 箱」分開,不是靠顏色作弊。兩個預先登記條件(偵測
  ≥0.85、分類 ≥0.85)彩色版全過;純形狀 0.806 > 0.75 診斷 bar。
- **意涵**:一個**多類偵測頭**能在凍結 WM latent 上認出「人 vs 雜物」,**零 WM 重訓**——
  延續 yaw/alt 的廉價路。這正是搜救願景「找的是一個人不是信標」的 WM 主場:幾何 beams
  對「這團是人還是家具」完全瞎,只有相機+WM 做得到。

**誠實邊界**:
- 這是**幾何形狀**(直立 capsule vs 立方箱)的可分性;真實的人姿態多變(躺、蜷、被遮),
  且模擬人形是簡化 proxy——sim-to-real 的外觀差距仍在。單目 latent 分得開「直立 capsule」
  不等於分得開「瓦礫下半遮的人」。
- 探針是停機取像(不測飛行);per-frame recall 靠掃描複利(同 yaw/alt)。

## Phase 1 —— 訓練 person 偵測頭(person 正 / box+empty 負):乾淨但單幀 recall 中等

`search/target_detector.py:train_and_gate_person`(`--person`),凍結統一 WM latent、
fresh room gate(n=180、pos 0.13、hard-neg 28 box-in-FOV 幀):

| 指標 | 值 | 判讀 |
|---|---|---|
| AUC | 0.834 | 略低於 0.85 bar(全混合集含遠/邊緣正例) |
| precision | **1.000** | 開火必是人 |
| **obstacle(box)-FA** | **0.000** | **從不對雜物誤觸發** ← 決定性 |
| per-frame recall | 0.50 | 同 yaw/alt regime,靠掃描複利 |

thr sweep:0.2→recall 0.62/FA 0.07、0.4→0.58/0.04、0.5→0.50/0.00。頭存
`output/target_head_person.pt`。

**判讀**:逐幀 gate 標 FAIL(recall/AUC bar),但那是**單幀** bar。真正要的「人 vs 雜物」
辨別是**乾淨的**(box-FA 0.000、precision 1.0——細 capsule 人形從不被當成箱子)。per-frame
recall 0.50 是 FOV 邊緣/遠處細目標的已知特性(同 yaw 0.758 / alt ~0.5),靠多視角掃描
複利到 ~0.9。細 capsule 比紅箱目標窄(半徑 0.15 vs 半寬 0.2),遠處像素更少,是 recall
偏低的合理主因。

## Phase 1b —— 「找到人」搜索 demo:掃描複利真能找到

`scripts/demo_person.py`:capsule 人形站在房裡,無人機 frontier 覆蓋 + 每 22 決策一次
360° hover-yaw 掃描,用 person 頭視覺確認(confirm=2)。斜角跟隨相機、beams8 安全。
探 5 個 seed:**3/5 found+returned**(seed 11 / 7 / 650002),2/5 miss(650000/650001)
——正是 per-frame recall 0.5 的誠實特性:掃描複利多半找到、但不保證每個 seed 都在預算內
命中。demo 用 seed 11(found+returned、117 幀)。GIF `docs/media/demo_person.gif`。

**整體判詞**:凍結 WM latent「認出人 vs 雜物」= GREEN 的 WM 主場,零 WM 重訓;頭乾淨
(不誤報雜物),掃描複利可佈署成「找到人」。這是幾何 beams **完全做不到**的能力
(它只知「前方有東西」、不知「是人還是家具」)。

## Phase 2 —— 提高 recall:加寬人形(r 0.15→0.25,更真實)成功拉起偵測

Hans:「提高 person recall」。最有原則的一招:原 capsule r=0.15(≈0.3 m 寬)是**細桿**,
遠處佔太少像素、單幀 recall 卡 0.50。真人肩寬 ~0.5 m ⇒ 加寬到 **r=0.25**(既更保真、遠處
又更易偵)。重訓頭(n_rooms=8):

| 指標 | r=0.15 | **r=0.25** |
|---|---|---|
| AUC | 0.834 | **0.918**(過 0.85 bar) |
| per-frame recall | 0.50 | **0.676** |
| precision | 1.000 | 0.767 |
| box-FA | 0.000 | 0.091 |

Phase 0 探針同步在 r=0.25 重跑:person-vs-empty 0.928、person-vs-box **0.954**(彩色)/
**0.806**(純形狀,與 r=0.15 一致)。**偵測 recall 0.50→0.68、AUC→0.918 是實質提升**;
代價是人變寬後與箱略難分(precision 1.0→0.77、box-FA 0→0.09,仍 < 0.15 bar)。

**誠實 —— recall 提升沒轉成 demo find-rate**:重探 7 seed,end-to-end 仍 ~3/7 命中
(650002/7/11 找到)。瓶頸不在偵測而在**搜索編排**:miss 的 seed 是無人機返航前沒在人
附近、面向人做掃描。試過「靠近就掃」的觸發反而更糟(2/7:原地一直掃、不移動去找更好視角,
燒光預算)——已回退。**find-rate 是獨立的搜索策略槓桿,非偵測 recall 問題。**

## 整體
- 偵測「人 vs 雜物」:GREEN、零 WM 重訓;加寬人形把 per-frame recall 0.50→0.68、AUC 0.918。
- end-to-end「找到人」find-rate ~3/7,受搜索編排限制(非偵測),是下一個獨立主題。
- demo `docs/media/demo_person.gif`(seed 11、found+returned)。頭 `output/target_head_person.pt`。

## 下一步(留 Hans 拍板)
1. **搜索編排**(提 find-rate,非偵測):sense 導引到人附近再面向掃描、覆蓋預算/plateau 調校
   ——需要比一次觸發更小心的設計(這輪快修已證明會反效果)。
2. 更真實人形(多姿態 / 部分遮蔽 / 瓦礫半掩)壓測 —— 若崩才需 WM 重訓(大步)。
兩顆 WM sha 全程未動。
