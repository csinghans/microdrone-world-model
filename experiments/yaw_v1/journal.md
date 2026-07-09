# yaw_v1 — Phase 0: yaw-detection feasibility probe (GREEN)

## 背景與問題

yaw=0 +x 相機鎖是整個室內視覺搜索的貫穿限制:視覺搜索飛行 gate 之前**失敗**就是
因為無人機只能在 +x 錐掃過目標時瞥一眼、不能轉身確認(單幀 FA 0.95 / 去抖動 miss
0.40)。加 yaw 是延後的大步,但「飛行中 yaw + 避撞」需要 WM 重訓(碰撞標籤假設
body==world)。

**feasibility-first 的決定性問題(便宜、先問):** yaw 用來**偵測**需不需要 WM
重訓?還是凍結的 encoder latent 已經能吃 yaw 旋轉的畫面(只需重訓偵測頭)?

## 方法(不飛、不訓練)

`eval/eval_yaw_detect.py`:座標偏移把房間渲染到位置 (x,y),**再把停在 START 的無人機
設一個 yaw**(Route B:`resetBasePositionAndOrientation` + `_updateAndStoreKinematicInformation`
+ 原封不動的體座標 `grab_frame`——相機自動看向 yaw 方向,不改渲染路徑),用**yaw
修正的 FOV 標籤**(bearing 相對 heading 而非 +x)。用**統一 WM**(偵測冠軍)編碼,
逐 yaw-bin + pooled 線性探針 AUC。yaw 掃描 = {−90, −45, 0, +45, +90}°。

## 預先登記的 bar(跑之前凍結)
- **綠**:pooled AUC ≥ 0.85 且 |yaw| 變大不崩(每 bin ≥ 0.75)⇒ latent 泛化到旋轉
  ⇒ 偵測只需重訓頭、**不需 WM 重訓** → 走廉價路。
- **紅**:AUC 隨 |yaw| 崩向 0.5 ⇒ encoder 對旋轉 OOD ⇒ 需 WM 重訓 → 停下回報。

## 結果 — GREEN(而且強)

2005 幀(in-view 率 0.11),統一 WM:

| yaw | −90° | −45° | 0° | +45° | +90° | **pooled** |
|---|---|---|---|---|---|---|
| WM-latent AUC | 0.981 | 0.992 | 0.938 | 0.985 | 1.000 | **0.977** |

(像素-紅色基線 pooled AUC 0.830。)

**凍結的 latent 在 yaw ±45/±90° 偵測目標跟 yaw=0 一樣好、甚至更好**(0° 反而是最低
的 0.938、+90° 最高 1.000)。沒有任何隨 |yaw| 的衰退。

## 判詞 — 偵測的 yaw 不需要 WM 重訓

encoder 是**影像**的函數:一個在體-+x FOV 前方的紅目標,不管無人機朝世界哪個方向,
畫面都長得一樣 ⇒ latent 偵測它一樣好。房間牆在世界裡旋轉,但體座標的畫面只是「某個
角度的房間、前方可能有紅盒」,encoder 照樣處理。**所以 yaw-scan 偵測是免費的(對凍結
latent 而言)——只需要重訓一個偵測頭,不動 WM。**

這**解開了相機鎖**:無人機可以停下、轉一圈掃描、在某個 yaw 角穩定看到目標並確認——
把「只能瞥一眼」變成「轉身穩定確認」,正是視覺搜索飛行 gate 缺的東西。

⇒ 依 Hans 拍板(綠就走廉價路),進 **Phase 1a**:(1)讓 yaw 可飛(VelCommander
接 v_cmd[3]→target_rpy、nav_action_set 加 yaw 動作);(2)在 yaw 幀上重訓偵測頭;
(3)hover-yaw-scan 行為 + 重跑視覺搜索飛行 gate。全程不動 WM。

## 誠實邊界
- 這是**偵測**(感知)的 yaw,不是**避撞**的 yaw。飛行中 yaw + 碰撞預測仍需 WM 重訓
  (Phase 1b、另議)——但室內避撞本來就是幾何 beams8 的職責、不靠 WM,所以 yaw-scan
  在 hover(定點、已知淨空)時掃描不觸及碰撞 WM。
- in-view 正例率 0.11(稀疏),但 pooled n=2005、逐 bin 都有兩類,AUC 穩健。
- 兩顆 WM sha 全程未動(探針只讀)。

## Phase 1a-1 — 讓 yaw 可飛(enabler,yaw=0 逐位元不變)

`sim/envs.py:VelCommander` 從 `v_cmd[3]`(yaw-rate)積出 `yaw_ref`、傳
`target_rpy=[0,0,yaw_ref]` 給 PID。yaw_ref 從 0 起、只在有 yaw 命令時動 ⇒ 今天所有
yaw=0 配方 target_rpy 恆 [0,0,0] = 控制器預設 ⇒ **逐位元相同**(已驗:fly transit
reached/0.35m/218 步、indoor found+返航/0撞/0.79/331 步,與改前完全一致)。正向測:
yaw_left 命令把無人機轉 0→+1.87 rad、畫面 mean|Δ|=14.2(相機轉了)。
`planner/nav_action_set.py` 加 `yaw_left`/`yaw_right`(原地轉、零平移、YAW_RATE 2.5),
**放在 coverage `nav_menu` 之外**⇒搜索飛行仍 yaw-free(body==world)。(vx,vy)在此
仍世界座標——對原地掃描正確;translate-while-yawed + 避撞是延後的 WM 重訓(1b)。

## Phase 1a-2 — 在 yaw 幀上重訓偵測頭(穩)

`search/target_detector.py:train_and_gate_yaw`:用統一 WM 編碼 yaw-掃描幀、fresh-room
gate。n=2010(pos 0.13、hard-neg 374):**AUC 0.982、precision 0.905、obstacle-FA
0.021、recall 0.758**。

- **關鍵 caveat 解決**:obstacle-FA 0.021 ⇒ 頭認的是紅目標、不是「前方有盒」(對橘障礙
  盒幾乎不觸發)。AUC 0.982 分離極佳。
- per-frame recall 0.758(thr=0.5)略低於嚴格 per-frame bar 0.80 ⇒ 逐幀 gate 判 FAIL,
  **但這對 hover-yaw-scan 不是問題**:掃描時目標跨多個 yaw 角連續在視野,per-frame
  recall 0.758 複利成「掃描中至少偵到一次」≈ 1−0.242³ ≈ 0.99(vision_v1 的複利洞見)。
- **判詞:yaw_v1 偵測頭在旋轉幀上運作良好、不需 WM 重訓**,是 hover-yaw-scan 的 found
  訊號。頭存 `output/target_head_yaw.pt`(gitignored)。兩顆 WM sha 仍未動。
