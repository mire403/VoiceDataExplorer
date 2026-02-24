# 🎙️ VoiceDataExplorer — 语音数据智能挖掘

<p align="center">
  <strong>🔊 不是转写工具 · 是语音原生的决策级数据系统</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Voice-First-00b4d8?style=for-the-badge" alt="Voice-First" />
  <img src="https://img.shields.io/badge/Structured-Queryable-0077b6?style=for-the-badge" alt="Structured" />
  <img src="https://img.shields.io/badge/Traceable-Timestamps-023e8a?style=for-the-badge" alt="Traceable" />
</p>

---

## 📌 一句话定位

> **VoiceDataExplorer is not a transcription tool.**  
> It is a **voice-native analytical system** that transforms spoken content into **structured, queryable data**.

把 **「大量非结构化语音」** 变成 **可查询、可聚合、可追溯到秒级的决策级数据资产**。

- ❌ 不是「语音转文字」Demo  
- ❌ 不是「一整段 transcript」  
- ❌ 不是「帮我总结一下会议」  
- ❌ 不是「一次性 prompt 出结果」  
- ✅ 是 **事件抽取 → 实体关系 → 时间线 → 语音级查询** 的完整流水线  

---

## 🏗️ 系统架构总览

```
📁 Audio Files (wav/mp3)
        │
        ▼
🛠️ Speech-to-Text (Whisper / WhisperX)  ← 标准化 JSON：utterance_id, speaker, start, end, text
        │
        ▼
✂️ Utterance Segmentation  ← 按说话人 + 时间切分/合并
        │
        ▼
🧠 Semantic Event Extraction  ← Decision / KPI_Mention / Action_Item / Risk / Concern
        │
        ▼
🔗 Entity & Relation Modeling  ← KPI / Person / Project / Client + mentions / decides_on / assigned_to
        │
        ▼
⏱️ Temporal Event Graph  ← 事件图 + 时间线（秒级可追溯）
        │
        ▼
🔍 Queryable Timeline / Report  ← 三种查询 + Markdown / HTML 输出
```

---

## 📖 项目简介（详细版）

### 我们要解决什么问题？

会议、访谈、客服录音里藏着大量 **决策、KPI、责任人、风险、行动项**，但通常只以「一整段文字」或「会议纪要」的形式存在，无法按「上周客户会议里所有和 KPI 相关的决策」「某个指标被讨论了多少次」「还没形成决策的风险点」这类问题做**精准检索与聚合**。

VoiceDataExplorer 的目标是：**以语音为第一输入模态**，把每段话变成**结构化事件**，再建**实体与关系**，最后支持**语音级查询**（问的是「决策」「KPI」「风险」，而不是搜关键词）。

### 核心能力拆解

| 能力 | 说明 |
|------|------|
| **1️⃣ 语音 → 结构化事件** | 每段语音中抽取：决策点、KPI/指标、责任人、时间约束、行动项、风险/担忧 |
| **2️⃣ 事件关系建模** | 显式建模：哪个事件触发了哪个决策、哪些 KPI 被多次提及、同一指标在不同会议中的变化（接口已留） |
| **3️⃣ Voice-first 查询** | 用户问的是「上周客户会议中关于 KPI 的所有决策」「某个 KPI 被讨论的次数和趋势」「未形成决策的风险点」 |

### MVP 范围

- **输入**：1–2 小时会议，约 50–200 条 utterances  
- **输出**：每一步都是结构化 JSON；每个事件都能 **trace 回原始语音时间戳**  
- **LLM 角色**：只做**分类与抽取**，不做「记忆」或开放式生成  

---

## 🧩 功能描述（按模块）

### 🔊 语音识别层（Speech Layer）

- **技术**：Whisper / WhisperX  
- **输出**：每条包含 `text`、`speaker`（若可用）、`start_time` / `end_time`，并统一为 `utterance_id`。  
- **用途**：为后续事件、实体、时间线提供「可定位到秒」的原文。

### ✂️ 话语切分（Segmentation）

- 对 STT 结果做**按说话人 + 时间**的合并（同说话人、间隔小于阈值的相邻段可合并）。  
- 支持按最小/最大时长过滤，为抽取提供合适粒度的片段。

### 🧠 语义事件抽取（核心）

- **事件类型**：`Decision`、`KPI_Mention`、`Action_Item`、`Risk`、`Concern`。  
- **输出**：每条事件带 `content`、`entities`、`owner`、`time_ref`、`source_utterance`（必填，用于追溯）。  
- **实现**：LLM 做**分类 + 抽取**，不写长文总结。

### 🔗 实体与关系

- **实体**：KPI、Person、Project、Client，带 `source_events`。  
- **关系**：`mentions`、`decides_on`、`assigned_to`、`depends_on`，显式存 `from` / `to` / `relation`。  
- 用于后续「KPI 决策」「某 KPI 被提及趋势」「风险是否被决策覆盖」等查询。

### ⏱️ 时间线

- 基于**事件 + 源 utterance 的时间戳**生成 **Event Timeline**（不是平铺文本列表）。  
- 每条：时间点、事件摘要、类型、**原始语音定位（秒）**。  
- 可输出 Markdown / HTML，便于阅读和分享。

### 🔍 查询引擎（三种）

1. **上周会议中所有 KPI 决策**：按事件类型 + 实体/关系过滤。  
2. **某个 KPI 被讨论的次数和趋势**：按实体 + 关系聚合，带时间线。  
3. **未形成决策的风险点**：找出 Risk/Concern 且未被 Decision 覆盖的事件。  

实现上以 **事件 + 实体过滤** 为主，规则 + 可选 LLM 判断，不做复杂 NL2SQL。

---

## 💻 代码段与深度解析

### 1️⃣ 数据模型：`schemas.py` — 全链路类型统一

所有环节的输入输出都基于 Pydantic 模型，保证**结构化 JSON** 和**可追溯**。

```python
# voice_data_explorer/schemas.py

class Utterance(BaseModel):
    """STT 输出的标准化一条话：必须带时间与说话人"""
    utterance_id: str
    speaker: str
    start: float   # 秒
    end: float
    text: str

EventType = Literal["Decision", "KPI_Mention", "Action_Item", "Risk", "Concern"]

class ExtractedEvent(BaseModel):
    """从某条 utterance 里抽出的一个语义事件"""
    event_id: str
    type: EventType
    content: str
    entities: list[str] = Field(default_factory=list)
    owner: Optional[str] = None
    time_ref: Optional[str] = None
    source_utterance: str   # 🔑 关键：必须能反查到原始 utterance → 时间戳

class Relation(BaseModel):
    """显式关系：谁指向谁、什么关系"""
    from_id: str
    to_id: str
    relation: Literal["mentions", "decides_on", "assigned_to", "depends_on"]
```

**深度解析**：  
- `Utterance` 的 `start`/`end` 是后续「时间线」和「按时间过滤」的唯一时间来源。  
- `ExtractedEvent.source_utterance` 把每个事件钉在一条 utterance 上，从而钉在时间轴上，实现「决策级数据 + 秒级追溯」。  
- `Relation` 的显式存储使得「哪个决策针对哪个 KPI」「谁被指派」都可以做图查询与过滤，而不是依赖全文检索。

---

### 2️⃣ 语音层：`transcribe.py` — 标准化 STT 输出

无论用 Whisper 还是 WhisperX，对外都统一成同一套 JSON 结构。

```python
# voice_data_explorer/audio/transcribe.py

def transcribe_audio(
    audio_path: str | Path,
    model_size: str = "base",
    device: str = "cpu",
    use_whisperx: bool = False,
) -> TranscriptionResult:
    path = Path(audio_path)
    if use_whisperx:
        return transcribe_audio_whisperx(str(path), device=device)
    return transcribe_audio_whisper(str(path), model_size=model_size, device=device)

def transcribe_audio_whisper(...) -> TranscriptionResult:
    model = whisper.load_model(model_size, device=device)
    result = model.transcribe(audio_path, word_timestamps=False)
    segments = result.get("segments") or []
    utterances = []
    for seg in segments:
        utterances.append(Utterance(
            utterance_id=_utterance_id(),
            speaker="Unknown",   # 纯 Whisper 无说话人
            start=float(seg["start"]),
            end=float(seg["end"]),
            text=(seg.get("text") or "").strip(),
        ))
    return TranscriptionResult(source_file=audio_path, utterances=utterances)
```

**深度解析**：  
- 上层只依赖 `TranscriptionResult` 和 `Utterance`，不关心底层是 Whisper 还是 WhisperX。  
- 每条 utterance 都有唯一 `utterance_id`，后续事件、实体、关系、时间线都通过它做引用。  
- WhisperX 分支可提供 `speaker` 和更准的边界，但接口一致，便于切换与扩展。

---

### 3️⃣ 事件抽取：`event_extractor.py` — LLM 只做「分类 + 抽取」

这里体现「不是让 LLM 写总结，而是做结构化抽取」。

```python
# voice_data_explorer/extraction/event_extractor.py

SYSTEM_PROMPT = """You are an extractor. For each utterance (labeled with [utterance_id]), output a JSON array of events.
Event types: Decision, KPI_Mention, Action_Item, Risk, Concern.
For each event output exactly:
- source_utterance: the utterance_id from the input
- type: one of the types above
- content: short phrase (what was said)
- entities: list of named things (KPIs, people, projects) mentioned
- owner: person responsible if mentioned, else null
- time_ref: time constraint if mentioned (e.g. "next quarter"), else null
Output only a JSON array. Every event must have source_utterance set to one of the given utterance IDs."""

def extract_events_from_batch(utterances: list[Utterance], model: str = "gpt-4o-mini") -> list[ExtractedEvent]:
    valid_ids = {u.utterance_id for u in utterances}
    lines = [f"[{u.utterance_id}] {u.speaker}: {u.text}" for u in utterances]
    raw = llm_extract(SYSTEM_PROMPT, "\n".join(lines), model=model)
    events = []
    for e in raw:
        if e.get("type") not in EVENT_TYPES:
            continue
        src = e.get("source_utterance")
        if src not in valid_ids:
            src = utterances[0].utterance_id if utterances else ""
        events.append(ExtractedEvent(
            event_id=_event_id(),
            type=e["type"],
            content=e.get("content") or "",
            entities=e.get("entities") or [],
            owner=e.get("owner"),
            time_ref=e.get("time_ref"),
            source_utterance=src,   # 保证每条事件都能 trace 回 utterance
        ))
    return events
```

**深度解析**：  
- Prompt 明确要求「每个事件必须带 `source_utterance`」，保证与原始话语一一对应。  
- 校验 `source_utterance in valid_ids`，异常时回退到首条 utterance，避免断链。  
- 按 batch 调用可控制 token 与延迟，适合 50–200 条 utterance 的会议规模。

---

### 4️⃣ 时间线构建：`timeline_builder.py` — 从事件到「可读时间轴」

时间线不是「按段罗列」，而是**按时间排序的事件列表**，每条都带秒级定位。

```python
# voice_data_explorer/graph/timeline_builder.py

def build_timeline(
    graph: EventGraphData,
    utterances: list[Utterance] | None = None,
) -> list[TimelineEntry]:
    utterances = utterances or graph.utterances
    utt_map = {u.utterance_id: u for u in utterances}
    entries = []
    for ev in graph.events:
        u = utt_map.get(ev.source_utterance)
        start_sec = u.start if u else 0.0   # 时间来自「源 utterance」
        entries.append(TimelineEntry(
            time_seconds=start_sec,
            event_summary=ev.content,
            event_type=ev.type,
            event_id=ev.event_id,
            source_utterance=ev.source_utterance,
            entities=list(ev.entities),
        ))
    entries.sort(key=lambda x: (x.time_seconds, x.event_id))
    return entries
```

**深度解析**：  
- `time_seconds` 直接取自 `utterance.start`，因此时间线与录音时间轴一致，可做「跳到 05:12 听原声」类功能。  
- 按 `(time_seconds, event_id)` 排序保证同一秒内顺序稳定。  
- `TimelineEntry` 保留 `event_id` 和 `source_utterance`，便于和事件图、原文做联动。

---

### 5️⃣ 查询引擎：`query_engine.py` — 三种 Voice-first 查询

用「事件 + 实体 + 关系」实现语义查询，而不是全文检索。

```python
# voice_data_explorer/query/query_engine.py

def query_kpi_decisions(
    graph: EventGraphData,
    event_type: str = "Decision",
    kpi_filter: bool = True,
    since_seconds: float | None = None,
) -> QueryResult:
    decisions = [e for e in graph.events if e.type == event_type]
    if kpi_filter:
        kpi_entity_ids = {e.entity_id for e in graph.entities if e.type == "KPI"}
        # 通过 relation 的 decides_on / mentions 找到与 KPI 绑定的决策
        for r in graph.relations:
            if r.relation in ("mentions", "decides_on") and ...
                event_ids_with_kpi.add(...)
        decisions = [e for e in decisions if e.event_id in event_ids_with_kpi or ...]
    if since_seconds is not None and graph.utterances:
        max_t = max(u.end for u in graph.utterances)
        utt_ids_after = {u.utterance_id for u in graph.utterances if u.start >= max_t - since_seconds}
        decisions = [e for e in decisions if e.source_utterance in utt_ids_after]
    timeline = _events_to_timeline_entries(graph, decisions)
    return QueryResult(events=decisions, timeline_entries=timeline, meta={"query": "kpi_decisions"})
```

**深度解析**：  
- **KPI 决策**：先筛 `type == "Decision"`，再用实体类型 KPI 和关系 `decides_on`/`mentions` 过滤，得到「和 KPI 相关的决策」。  
- **时间窗口**：用 `since_seconds` 和 `utterance.start/end` 做「最近 N 秒」的会议内过滤，为「上周会议」类需求预留扩展（可按会议元数据再筛）。  
- 返回 `QueryResult`（events + timeline_entries + meta），既方便程序处理，也方便直接渲染成 Markdown/HTML。

---

### 6️⃣ 主流程：`app.py` — 八步流水线

从音频到时间线 + 可选查询，一气呵成，且每步都可落盘 JSON。

```python
# app.py 核心流程（节选）

# 1) 语音识别
transcription = transcribe_audio(audio_path, device=args.device, use_whisperx=args.use_whisperx)
save_transcription(transcription, out_dir / "transcription.json")

# 2) 切分
segmented = segment_utterances(transcription)
utterances = segmented.utterances

# 3–5) 抽取（若未 --skip-llm）
events = extract_events(utterances)
entities = extract_entities(events)
relations = extract_relations(events, entities)

# 6) 图
graph = build_event_graph(events, entities, relations, utterances)
# 写入 event_graph.json

# 7) 时间线
timeline = build_timeline(graph)
# 写入 timeline.md / timeline.html

# 8) 可选查询
if args.query:
    result = run_query(graph, args.query)
    # 写入 query_result.md
```

**深度解析**：  
- `--skip-llm` 时只跑 1–2 步，适合只要转写 + 切分的场景，且不需要 `OPENAI_API_KEY`。  
- 每步输出都可持久化（transcription、utterances、event_graph、timeline、query_result），便于调试和二次分析。  
- 查询引擎通过 `run_query(graph, query_text)` 接入，自然语言问句由内部规则映射到三种查询之一，扩展时可加 LLM 做意图识别。

---

## 📂 项目结构

```
VoiceDataExplorer/
├── README.md
├── requirements.txt
├── app.py                      # 入口：八步流水线 + CLI
└── voice_data_explorer/
    ├── __init__.py
    ├── schemas.py               # 全链路 Pydantic 模型
    ├── audio/
    │   ├── __init__.py
    │   └── transcribe.py        # Whisper / WhisperX → 标准化 Utterance
    ├── segmentation/
    │   ├── __init__.py
    │   └── utterance_segmenter.py
    ├── extraction/
    │   ├── __init__.py
    │   ├── llm_client.py        # 统一 LLM 调用（仅分类/抽取）
    │   ├── event_extractor.py
    │   ├── entity_extractor.py
    │   └── relation_extractor.py
    ├── graph/
    │   ├── __init__.py
    │   ├── event_graph.py
    │   └── timeline_builder.py
    ├── query/
    │   ├── __init__.py
    │   └── query_engine.py      # 三种查询 + run_query
    └── output/
        ├── __init__.py
        ├── markdown_renderer.py
        └── html_renderer.py
```

---

## 🚀 快速开始

### 环境

```bash
pip install -r requirements.txt
```

如需跑「事件/实体/关系」抽取，请设置 `OPENAI_API_KEY`（仅用 LLM 做分类与抽取）。

### 只转写（不调用 LLM）

```bash
python app.py --audio path/to/meeting.wav --output-dir ./output --skip-llm
```

### 全流程 + 可选查询

```bash
python app.py --audio path/to/meeting.wav --output-dir ./output
python app.py --audio path/to/meeting.wav -q "KPI decisions"
python app.py --audio path/to/meeting.wav -q "risks without decision"
```

### 使用 WhisperX（说话人 + 更准时间戳）

```bash
python app.py --audio path/to/meeting.wav --use-whisperx --device cuda
```

---

## 📤 输出示例（时间线 Markdown）

```markdown
### 2024-01-12 | Client Meeting

- ⏱️ 05:12  **Decision**: Increase retention KPI by 5%
- ⏱️ 18:40  **Concern**: Risk of churn in SMB segment
```

每条都可对应回原始语音时间戳，实现**可查询、可聚合、可追溯**的决策级数据。

---

## 🔮 后续扩展（接口已预留）

- 多会议 KPI 演化趋势  
- 决策 → 执行 → 结果闭环  
- 语音 + 文档联合事件图  
- Slack / Zoom / 飞书会议接入  

---

<p align="center">
  <strong>🎯 VoiceDataExplorer — 把语音变成可追问的决策资产</strong>
</p>
