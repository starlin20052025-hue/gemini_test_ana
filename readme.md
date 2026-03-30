> [!WARNING]
> 這個 repository 目前包含的是一份 **由 Gemini 產生的加密貨幣策略研究 prototype**。
>
> 雖然我們已完成了 P0 級別的架構強化，包括：
> - 定義了研究協議 (`RESEARCH_PROTOCOL.md`)
> - 重建了可審計的回測引擎 (`src/backtest_engine.py`)
> - 正式建立了反未來函數 (Anti-Leak) 機制 (`ANTI_LEAK_CHECKLIST.md` 及程式碼修正)
> - 重構了 Walk-Forward 驗證流程 (`src/research_script.py`)
> - 重新驗證了績效指標定義 (`METRICS_DEFINITION.md` 及 `src/backtest_engine.py` 修正)
>
> 但此專案**尚未**通過 research-grade 等級的完整驗證，特別是在成本模型細節、缺值 / 缺 bar 處理、Trade-level 分析及 Pair Trade 嚴謹性方面，仍需進一步強化。
>
> 目前 repository 內任何績效結果都應視為 **探索用途**，不能當作最終交易證據。

# Gemini 測試分析

這是一份由 Gemini 產生的加密貨幣策略研究 prototype，保留在此作為後續審查、重構，以及逐步強化成 research-grade 框架的起點。

---

## Repository 狀態

這個 repository 目前保存的是一份 **Gemini 產生的初版加密貨幣策略研究框架 prototype**。

它目前的角色是：

- 保存 Gemini 產出的研究方向與程式骨架
- 作為可被審查的研究材料
- 作為後續強化與重構的起點
- 協助區分哪些部分有價值、哪些部分目前仍不可靠

它目前**不是**：

- 正式可上線的交易系統
- 已驗證完成的研究框架
- 可直接信任的最終回測結論來源
- 完整可用的 pair-trading 平台

---

## 目前範圍

這個 repository 目前包含幾個早期 prototype 模組，例如：

- 歷史市場資料載入
- 單資產 baseline 回測
- 初步的 walk-forward 研究結構
- 實驗性 pair-trade 研究草稿
- 績效指標與報告骨架

這些元件在探索階段有用，但在通過更嚴格的驗證之前，都應視為 **prototype 階段模組**。

---

## 目前成熟度評估

### 有價值的部分

這個 repo 目前已經有幾個明確價值：

- 保留了原始研究需求與方向
- 提供了初步架構雛形
- 有助於後續 review 與 refactor
- 給未來的 agent 或開發者一個具體起點

### 目前不能直接信任的部分

以下幾個面向在完成進一步強化前，都**不應直接信任**：

- 成本模型真實性 (已有所改進，但仍需進一步細化)
- 缺值 / 缺 bar 處理 (已改進為報告，但處理策略仍需定義)
- pair-trade 邏輯與評估方式 (仍為概念性實現)
- 對績效結果的解讀方式

---

## 建議閱讀順序

如果你是第一次 review 這個 repository，建議依照以下順序閱讀：

1. `REVIEW_NOTES.md`
2. `TODO_FIXES.md`
3. `RESEARCH_PROTOCOL.md`
4. `ANTI_LEAK_CHECKLIST.md`
5. `METRICS_DEFINITION.md`
6. `README.md`
7. `src/` 底下的原始碼

這樣的順序可以避免在還沒理解風險前，就先把這個 repo 誤認為是一套已經驗證完成的框架。

---

## 目前最優先的開發方向

在繼續擴充策略庫之前，應優先處理：

1. 修正缺值 / 缺 bar 處理 (已改為報告，但需定義處理策略)
2. 以更嚴格規則重跑 baseline
3. 之後才重新評估是否繼續做 pair trade

---

## 專案目標

這個 repository 的長期目標，是逐步演進成一套更嚴謹的加密貨幣策略研究框架，用於：

- 單資產加密貨幣策略研究
- walk-forward 驗證
- 更完整且可追溯的績效報告
- 未來的 pair-trade / stat-arb 擴充
- 更進一步的多策略 / 多 agent 研究工作流

在目前這個階段，這個 repository 應被視為：

- 一份 prototype
- 一份 AI 產生但值得保留的草稿
- 一個後續重構目標
- 一個持續審查中的研究骨架

---

## Repository 結構

目前預期結構如下：

```text
.
├─ src/
│  ├─ data_loader.py
│  ├─ backtest_engine.py
│  ├─ research_script.py
│  └─ pair_trade_research.py
├─ REVIEW_NOTES.md
├─ TODO_FIXES.md
├─ RESEARCH_PROTOCOL.md
├─ ANTI_LEAK_CHECKLIST.md
├─ METRICS_DEFINITION.md
└─ README.md

目前對各模組成熟度的建議判斷：

data_loader.py -> 已強化，缺值處理待完善
backtest_engine.py -> 已重建，待更精細成本模型
research_script.py -> 已強化，探索用 baseline
pair_trade_research.py -> 概念性 placeholder，仍待重建
原始研究需求

以下保留最初提供給 Gemini 的研究任務說明，讓未來 review 這個 repository 的人可以理解這個專案原本希望達成的研究範圍、標準與設計目標。

任務：請你獨立研究這個加密貨幣交易策略專案，並提出完整框架

你現在扮演的是一位獨立研究員，不是單純的 code assistant。

我要你從以下幾個角度來審查這個專案：

策略研究
回測設計
參數選擇
資料切分
future leak 預防
工程落地

請不要給空泛建議。
我要的是 具體、可執行、可直接落地的分析與方案。

1. 專案目標

我正在建立一套 加密貨幣策略研究框架，主要用於 Binance 永續合約或現貨歷史資料。

目前階段，我希望先把研究框架定清楚，再一步一步實作。

這次任務不是主要要你立刻寫程式，
而是希望你站在研究架構設計者角度，回答下面幾件事：

回測應該怎麼設計才合理
歷史資料應該怎麼抓
訓練集 / 測試集要怎麼切
週期應該怎麼選（例如 1h、4h、1d）
如何避免 future leak / data snooping
指標與參數搜尋該怎麼做才不會自欺欺人
結果應該輸出哪些績效指標
這套框架未來如何擴充成多模型 / 多策略研究平台
2. 核心要求
2.1 全歷史資料

不要只用近幾年。
不要只測局部區間。

假設原則如下：

能抓多少就抓多少
從最早可取得資料一路抓到最新資料

請評估：

為什麼全歷史回測重要
全歷史 vs 局部歷史，會如何影響 CAGR / MDD / Sharpe / Calmar
在不同 market regime（牛市 / 熊市 / 盤整）下，全歷史回測有什麼好處與限制
2.2 必須分訓練集與測試集

這是硬需求。
我不接受「全資料一起回測後挑最好參數」這種方式。

請設計合理方案，例如：

train / validation / test
anchored walk-forward
rolling window
expanding window
nested validation（如果你認為有必要）

請清楚分析每種方案的：

優點
缺點
適合哪類策略
實作複雜度
對加密貨幣這種非平穩市場的適配性

最後請明確選出 你最推薦的一種方案，不要只列選項。

2.3 嚴格避免 future leak

這是核心重點。
請從以下角度檢查：

指標計算是否偷看到未來
標準化 / normalization 是否偷看到未來
參數搜尋是否用了測試集結果
walk-forward 是否真的只用過去資料
bar close 後訊號、下單時點、持倉 shift 是否正確
若使用 K 線與技術指標，哪些寫法最容易不小心 leak

請列出：

常見錯誤清單
正確做法
建議加入哪些防呆機制
2.4 週期選擇：1h、4h、1d

目前在考慮週期問題。
我不希望只是因為「習慣上大家用 1h」就直接選 1h。

請分析：

1h 的優點與缺點
4h 的優點與缺點
1d 的優點與缺點

以及不同週期對以下面向的影響：

雜訊程度
訊號頻率
手續費敏感度
滑點敏感度
regime 切換偵測
訓練樣本數
過擬合風險
live trading 可執行性

最後請直接回答：

如果是第一版 baseline research framework，建議先用哪個週期，為什麼
第二階段擴充時，應該怎麼引入多週期比較
2.5 需要的績效指標

請明確列出至少應該輸出的績效數據。
至少包含：

年化報酬率（CAGR / Annual Return）
最大回撤（MDD）
夏普值（Sharpe Ratio）
卡碼比率（Calmar Ratio）

另外也請補充你認為應該一起看的指標，例如：

Sortino
Win rate
Profit factor
Exposure
Trade count
Avg holding period
Recovery factor
Ulcer index
Turnover

請說明每個指標的意義，以及哪些指標容易誤導。

3. 研究角度需要回答的問題
問題 1：如果要做 baseline，應該怎麼定義？

請幫我定義一個合理的 baseline research setup，例如：

交易標的
資料範圍
bar 週期
特徵類型（先只用 OHLCV / 技術指標）
train/test 切法
交易成本設定
指標輸出
最終報告格式
問題 2：如果做技術指標型策略，怎麼避免 data snooping？

例如可能會測很多種：

SMA
EMA
breakout
ATR filter
volatility filter
z-score / mean reversion
trend filter

請分析：

哪些地方最容易過度最佳化
參數搜尋應該怎麼限制
是否應該先固定小範圍 baseline，再逐步擴大
如何設計一個「不容易騙到自己」的研究流程
問題 3：如果之後要走向 pair trade / stat arb，現在框架要先預留什麼？

雖然目前不一定馬上做，但未來可能會走向：

pair trade
spread z-score
cointegration
hedge ratio
多資產 ranking
cross-sectional signal

請從工程與研究流程角度，說明現在框架應先保留哪些擴充點。

4. 輸出格式要求

請依照以下格式回答：

A. 先給結論摘要

用條列方式直接說：

最推薦的回測切法
最推薦的 baseline 週期
最重要的 3 個風險點
最容易做錯的 3 個地方
B. 再給完整分析

分章節詳細展開：

資料範圍
train/test 設計
future leak 防範
週期比較
績效指標
baseline proposal
pair trade 擴充預留
C. 最後給可直接執行的研究規格

請整理成類似 spec 的格式，例如：

Data:
Backtest Engine:
Split Method:
Signal Timing:
Metrics:
Cost Model:
Output Files:
Validation Rules:
Anti-leak Checklist:
5. 重要限制
不要只講概念，盡量具體
不要只給「視情況而定」，請表明主張
如果提出多個方案，最後一定要選一個最推薦的
不要假設只會做單一策略，未來會擴充成研究平台
請同時兼顧研究嚴謹性與工程可落地性
6. 額外補充

我的偏好：

我很重視 no future leak
我不喜歡只挑漂亮回測圖
我希望使用完整歷史資料
我接受先做 baseline，但 baseline 不能太隨便
我希望未來能接到多模型 / 多 agent 協作研究流程
我希望後續能延伸到 pair trade，而不是只做單一方向策略

請把自己當成一位嚴格的研究主管，幫我審查這個專案。

下一步建議

建議後續新增以下文件，讓 repository 更容易進入可審查、可演進的狀態：

REVIEW_NOTES.md
TODO_FIXES.md
RESEARCH_PROTOCOL.md
ANTI_LEAK_CHECKLIST.md
METRICS_DEFINITION.md

在這些文件完成前，本 repo 應持續被視為 prototype under review，而不是正式研究結論。
