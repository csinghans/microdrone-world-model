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

## 下一步(留 Hans 拍板)
1. **走廉價路**:訓一個多類頭(人 / 箱 / 空),量 fresh-room 分類準確率 + 飛行中確認
   (同 yaw-scan 複利),做成「找到人」的搜索 demo。
2. 更真實人形(多姿態 / 部分遮蔽)壓測 —— 若崩,才需 WM 重訓(大步)。
兩顆 WM sha 全程未動(探針只讀)。
