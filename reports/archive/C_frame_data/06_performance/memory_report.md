# 内存与计时限制

memory_peak.csv为原生runner进程峰值，含全序列预解码缓存，不能当作在线算法常驻内存。python_research_memory.csv为研究进程RSS峰值，包含日志/消融/辅助缓存，非原生C核心。未做C++集成，C-native峰值和端到端采集/IO预算均NOT_MEASURED。原始内存与逐帧解码日志保留。
