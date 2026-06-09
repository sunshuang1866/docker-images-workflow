# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: infra-error
- 置信度: 低
- 知识库匹配: 模式22
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
（日志截断前未出现致命错误，以下是日志中出现的非致命信息）

日志截断前最后一段输出：
```
#11 354.0 -- Installing: /usr/local/googletest-4jQjSxQTd-HjwRWNCS8vl2kq9IImdZqr5MUHruTRYJs/include/gmock/gmock-spec-builders.h
...
#11 354.0 -- Installing: /usr/local/googletest-4jQjSxQTd-HjwRWNCS8vl2kq9IImdZqr5MUHruTRYJs/include/gmock/gmock-more-matchers.h
```

日志中出现的非致命警告/信息：
- `fatal: not a git repository (or any of the parent directories): .git` (在 zstd、boost 构建阶段出现)
- 多条 `SEND_ERROR "Target Boost::xxx already has an imported location..."` (Boost 构建系统的已知警告，非致命)
- `note: failed.  See http://www.boost.org/libs/python/doc/building.html` (Boost Python 组件构建提示，非致命)
- `-- Failed to find LLVM FileCheck` (CMAKE 配置阶段可选检查未通过，非致命)
- 多个 `Performing Test ... - Failed` (CMAKE 编译特性探测失败，属于正常探测行为，非致命)

### 根因定位
- 失败位置: 无法定位（日志在 googletest 安装阶段被截断，尚未进入 fbthrift 本身的编译）
- 失败原因: **证据不足，无法确定根因**。日志仅覆盖了 getdeps 依赖构建阶段（ninja → benchmark → zlib → zstd → fmt → boost → fast_float → gflags → glog → googletest），尚未进入 fbthrift 源码编译。实际导致 CI 失败的错误极可能发生在日志截断之后的阶段。

### 与 PR 变更的关联
PR 新增了 fbthrift 2026.06.08.00 版本的 Dockerfile 及配套文件：
1. **Dockerfile**：定义构建流程（dnf 安装依赖 → 复制 libaio 包 → 克隆 fbthrift → 运行 fix_getdeps.py → 执行 getdeps.py 构建）
2. **fix_getdeps.py**：两个关键操作：
   - 将 `"openeuler"` 加入 getdeps 平台识别列表
   - 使用正则替换跳过 libaio 的哈希校验 `_verify_hash` 方法
3. **libaio-libaio-0.3.113.tar.gz**：预下载的 libaio 源码包
4. **README.md / doc/image-info.yml / meta.yml**：元数据更新

PR 变更本身可能触发的潜在问题（因日志截断无法证实）：
- `fix_getdeps.py` 中 `_verify_hash` 替换正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 使用 lookahead 依赖后续的 `def ` 作为边界标记——若 `_verify_hash` 是该类最后一个方法（无后续方法定义），正则将不匹配，hash 校验不会被跳过，可能导致 libaio 构建时因校验失败而中止

## 修复方向

### 方向 1（置信度: 低）
**正则边界修复**：若实际失败由 `fix_getdeps.py` 的 regex 引起，需修改 `_verify_hash` 替换正则，使其能处理「类中最后一个方法」的边界情况（当前 `(?=\n    def )` lookahead 在无后续 `def` 时匹配失败）。可改用匹配到方法体结束（如到下一个 `def ` 或类结束/文件结束）的模式。

### 方向 2（置信度: 低）
**其他未知构建错误**：由于日志截断，无法排除 fbthrift 源码编译阶段的其他错误（如缺少编译依赖、C++ 标准不兼容、链接错误等）。需获取完整日志后才能判断。

## 需要进一步确认的点
1. **获取完整 CI 日志**：当前日志仅覆盖到 googletest 安装阶段（依赖构建），需要获取包含 fbthrift 本体编译阶段（`Building fbthrift...` 之后）的完整日志才能定位真正导致失败的错误
2. 确认 `fix_getdeps.py` 中的正则替换是否实际生效：在目标文件中 `_verify_hash` 是否为该类最后一个方法——若是，则正则无法匹配，需修复
3. 确认 libaio tarball (`libaio-libaio-0.3.113.tar.gz`) 的文件内容是否与上游哈希匹配（若 hash 校验未成功跳过，需要比对）
4. 确认依赖库版本（boost 1.83.0、fmt、glog、gflags 等）与 fbthrift 2026.06.08.00 的兼容性
