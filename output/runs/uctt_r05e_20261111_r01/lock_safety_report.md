# 首锁安全

B3 BLOCKED，0新归属运行。原始R03 contracts.cpp/state.hpp/seed未经修改，tests/r03_provenance.json记录来源hash。16原测试15 PASS，coherent_wrong_first_lock FAIL：错误候选与其路径自洽即可首次锁定并写入历史。没有替换fixture，也没有用只返回unknown的旁路声称锁定修复。真实无裂纹负例缺失，真实FP NOT_VERIFIED。
