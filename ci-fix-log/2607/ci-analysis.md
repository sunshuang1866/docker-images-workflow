# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: libaio哈希校验绕过失败
- 新模式症状关键词: Assessing libaio, exit code: 1, _verify_hash, getdeps, fix_getdeps.py

## 根因分析

### 直接错误
```
#11 332.5 Building googletest...
#11 332.5 Assessing libaio...
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
------
Dockerfile:18
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.15.00/24.03-lts-sp3/Dockerfile:18` (RUN 指令)
- 失败原因: getdeps 构建系统在 "Assessing libaio..." 阶段异常退出（exit code: 1），所有前置依赖（ninja、benchmark、zlib、zstd、fmt、boost、fast_float、gflags、glog、googletest）均构建成功，唯独 libaio 评估阶段失败，且日志中无具体错误信息（被截断）。

### 与 PR 变更的关联
**直接关联**。PR 新增了 4 个文件，其中 Dockerfile 和 fix_getdeps.py 是实现 fbthrift 容器化构建的核心文件。`fix_getdeps.py` 承担两项关键职责：

1. 使 getdeps 识别 openEuler 发行版（已验证生效：glog/gflags/googletest 等依赖均构建成功）
2. **绕过 libaio 的哈希校验**（疑似未生效）

`fix_getdeps.py:15-21` 中的 `_verify_hash` 绕过逻辑使用正则：
```
r'def _verify_hash\(self\):.*?(?=\n    def )'
```
该正则的 lookahead `(?=\n    def )` 依赖固定 4 空格缩进来定位下一个方法定义。若上游 fbcode_builder 的 `fetcher.py` 中 `_verify_hash` 的缩进风格不同（如 2 空格、tab），或 `_verify_hash` 是类中最后一个方法（无后续 `def` 可锚定），则 `re.sub` 将静默返回原内容（不替换），哈希校验未被真正禁用。libaio 的 tgz 文件为手动提供（非从上游仓库下载），哈希值必然与 manifest 中记录的不一致，导致 getdeps 校验失败并退出。

## 修复方向

### 方向 1（置信度: 中）
修复 `fix_getdeps.py` 中绕过哈希校验的正则表达式，使其不依赖固定缩进格式和后续方法锚点。改用更稳健的匹配方式（如匹配 `def _verify_hash(self):` 到方法体结束的 `return` 或整个方法块），或直接在函数体开头插入 `return` 语句提前返回。

### 方向 2（置信度: 低）
libaio 的 tar.gz 文件本身可能损坏或格式不兼容。若方向 1 修复后仍失败，需验证 `libaio-libaio-0.3.113.tar.gz` 是否完整且可被 `tar` 正确解压。

## 需要进一步确认的点
1. 获取 libaio 评估失败时的完整 stderr 输出——当前日志在 "Assessing libaio..." 后即被截断，缺少 getdeps.py 实际输出的错误信息，无法 100% 确定是哈希校验失败还是其他原因。
2. 确认上游 fbcode_builder `fetcher.py` 中 `_verify_hash` 方法的实际缩进格式（4 空格 / 2 空格 / tab），以验证正则是否匹配。
3. 验证 `libaio-libaio-0.3.113.tar.gz` 文件完整性（SHA256 checksum）。
