# FULL 全帧预算触发分解

只读已经封存的无GT推理展示数据与血缘，不改算法、预算或正式结果。1633帧逐帧验证exhausted等于各真实触发项的逻辑或；多个触发项可同时为真，不能相加成帧数。

```json
[
  {
    "group": "group_a",
    "frames": 551,
    "exhausted": 551,
    "raw_cap": 0,
    "edge_proposal_cap": 0,
    "root_cap": 546,
    "route_state_cap": 0,
    "candidate_cap": 545,
    "roi_cap": 0,
    "recheck_cap": 0,
    "track_cap": 7
  },
  {
    "group": "three_point_bend",
    "frames": 520,
    "exhausted": 93,
    "raw_cap": 0,
    "edge_proposal_cap": 0,
    "root_cap": 0,
    "route_state_cap": 0,
    "candidate_cap": 0,
    "roi_cap": 0,
    "recheck_cap": 0,
    "track_cap": 93
  },
  {
    "group": "group_c",
    "frames": 562,
    "exhausted": 0,
    "raw_cap": 0,
    "edge_proposal_cap": 0,
    "root_cap": 0,
    "route_state_cap": 0,
    "candidate_cap": 0,
    "roi_cap": 0,
    "recheck_cap": 0,
    "track_cap": 0
  }
]
```

原生budget.graph是路径搜索整体预算标记，不能误读为RAW图边提案超过上限。root_cap来自roots_total大于roots_explored，route_state_cap来自未访问前沿，candidate_cap来自确实被预算删除的候选血缘。详细行在diagnostics/full_budget_trigger_decomposition.csv。该分解定位程序触发点，不证明全部漏检的唯一物理原因，也不授权直接增加预算或丢弃分支。
