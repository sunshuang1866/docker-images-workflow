# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 低
- 知识库匹配: 新模式
- 新模式标题: libaio构建阶段失败
- 新模式症状关键词: Assessing libaio, getdeps.py, exit code: 1, fix_getdeps.py

## 根因分析

### 直接错误
```
#11 335.0 Building googletest...
#11 335.0 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
 > [5/5] RUN git clone -b v2026.06.15.00 --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift:
335.0 Assessing libaio...
------
Dockerfile:18
```

### 根因定位
- 失败位置: Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile:18
- 失败原因: `getdeps.py` 在执行 libaio 依赖的 "Assessing" 阶段时以 exit code 1 失败，日志在 "Assessing libaio..." 后截断，**缺少实际错误信息**。

### 与 PR 变更的关联
本次 PR 新增了完整的 fbthrift Dockerfile 和配套的 `fix_getdeps.py`（用于修复 openEuler 发行版识别和跳过 libaio 哈希校验）。`getdeps.py` 的前序依赖（gflags、glog、googletest）均已成功构建，说明 `fix_getdeps.py` 中的发行版识别修复（添加 "openeuler" 到 RHEL 类列表）生效正常。但构建流程在到达 libaio 依赖时中断，可能原因包括：

1. `fix_getdeps.py` 中的 `_verify_hash` 正则替换在 fbthrift v2026.06.15.00 版本的 `fetcher.py` 中匹配失败，导致哈希校验未被成功跳过；
2. 预置的 libaio tarball（`libaio-libaio-0.3.113.tar.gz`）与 getdeps 期望的文件命名/结构不匹配；
3. libaio 源码构建本身在当前环境下的编译/配置问题。

由于日志截断，无法确定具体是哪一种原因。

## 修复方向

### 方向 1（置信度: 低）
检查 `fix_getdeps.py` 中的正则替换是否在 v2026.06.15.00 的 `fetcher.py` 中生效。fbthrift 上游代码可能在版本迭代中改变了 `_verify_hash` 方法的代码结构或缩进风格，导致正则 `def _verify_hash\(self\):.*?(?=\n    def )` 无法匹配。可验证 `fetcher.py` 中 `_verify_hash` 的实际代码结构，必要时调整正则或改用其他方式跳过哈希校验（如直接删除/注释该方法）。

### 方向 2（置信度: 低）
确认预置 libaio tarball 的命名与 getdeps 系统期望的文件名一致。当前 Dockerfile 中 cp 的目标文件名为 `libaio-libaio-libaio-0.3.113.tar.gz`（三个 libaio），需确认 getdeps 的 fetcher/loader 模块对此依赖期望的文件名格式是否匹配。

## 需要进一步确认的点
1. **获取完整的 libaio 构建日志**：当前日志在 "Assessing libaio..." 后截断，缺失错误详情。需要在相同环境重新运行构建或获取完整日志，以看到 getdeps.py 抛出的具体错误信息。
2. **验证 `fix_getdeps.py` 正则匹配结果**：在构建环境中提取 fbthrift v2026.06.15.00 的 `build/fbcode_builder/getdeps/fetcher.py`，检查 `_verify_hash` 方法的实际代码是否被正则成功替换。
3. **确认 libaio 版本兼容性**：`libaio-libaio-0.3.113` 是否与 fbthrift v2026.06.15.00 要求的 libaio 版本一致，以及 tarball 内容是否完整。
