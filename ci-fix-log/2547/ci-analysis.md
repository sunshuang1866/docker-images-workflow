# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 模式22（部分匹配）+ 新模式
- 新模式标题: 上游下载源失效
- 新模式症状关键词: `Content-Type: text/html`, `pagure.io`, `libaio`, `Download with`, `tar.gz`

## 根因分析

### 直接错误

Docker 构建在第 5 步（RUN getdeps）失败，exit code: 1。日志末尾显示 getdeps 在处理 libaio 依赖时，从 pagure.io 下载返回了 HTML 页面而非有效的 tar.gz 归档文件：

```
#11 354.0 Assessing libaio...
#11 354.0 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 354.0 .. 2238 of (Unknown)  [Complete in 1.187799 seconds]
#11 354.0 Date: Tue, 09 Jun 2026 01:09:04 GMT
#11 354.0 Server: Apache/2.4.37 (Red Hat Enterprise Linux) OpenSSL/1.1.1k mod_wsgi/4.6.4 Python/3.6
#11 354.0 Content-Type: text/html; charset=utf-8
```

关键证据：
- 下载仅获取了 **2238 字节**，远小于正常 tar.gz 的大小
- 响应 `Content-Type: text/html; charset=utf-8` — 表明返回的是 HTML 页面而非二进制归档
- 正常场景期望的 Content-Type 应为 `application/gzip` 或 `application/octet-stream`

### 根因定位

- 失败位置: Dockerfile 第 18–23 行（RUN getdeps 命令链），具体在 getdeps 的 libaio 下载/提取阶段
- 失败原因: pagure.io 上 libaio 的归档下载 URL 返回了 HTML 页面（可能为 404 错误页、重定向页或登录页面），getdeps 将其当作 tar.gz 归档处理导致提取或后续校验失败。同时 PR 中预置的本地 libaio 压缩包未被 getdeps 有效利用——getdeps 仍然优先通过网络下载，下载到的 HTML 内容覆盖或无法替代预置的合法压缩包，最终导致构建中止。

### 与 PR 变更的关联

**直接相关。** PR 为 fbthrift v2026.06.08.00 新增了完整的 Dockerfile 及其辅助文件：

1. `Dockerfile` 第 18–23 行定义了 fbthrift 的构建流程，依赖 getdeps 自动解析并下载 libaio
2. `libaio-libaio-0.3.113.tar.gz` 被纳入仓库作为预下载的本地副本（54 KB 二进制文件），Dockerfile 中将其复制到 getdeps 的 downloads 目录
3. `fix_getdeps.py` 被编写用于绕过两个问题：(a) openEuler 发行版不被 getdeps 识别；(b) libaio 的哈希校验

但这两个辅助措施未完全阻止 getdeps 从 pagure.io 发起网络下载。日志清楚显示 getdeps 执行了在线下载，且下载结果被 HTML 内容污染，导致构建失败。失败的直接触发条件是 PR 引入的新 Dockerfile 所执行的 `getdeps.py build fbthrift` 命令。

## 修复方向

### 方向 1（置信度: 高）
**阻止 getdeps 通过网络重新下载 libaio，强制使用本地预置的 tar.gz 文件。**

getdeps 在检出本地 downloads 目录已存在目标文件时可能仍会发起网络请求（或覆盖已有文件）。需要确保 getdeps 完全使用预置的本地文件，不触发网络下载。可行的思路包括：
- 修改 `fix_getdeps.py` 或直接在 Dockerfile 中 patch getdeps 的 fetcher 逻辑，在下载前判断本地文件是否已存在且大小合理，若存在则跳过在线下载步骤
- 或者将 libaio 的获取方式从 "URL 下载" 改为 "本地文件" 源，直接引用 `/tmp/libaio.tar.gz` 路径

### 方向 2（置信度: 中）
**检查并修复 pagure.io 下载 URL。**

当前 URL `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 可能因 pagure.io 平台变更、认证要求或资源路径调整而失效。如果方向 1 不可行，可尝试查找 libaio 的替代下载源（如 GitHub 镜像），或修正 URL 路径使其返回正确的二进制归档。

### 方向 3（置信度: 低）
**修复 fix_getdeps.py 中 `_verify_hash` 正则表达式的边界匹配缺陷（模式22）。**

模式22 指出当前正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 在 `_verify_hash` 是类中最后一个方法时无法匹配，导致哈希校验未被跳过。即使方向 1 解决了下载问题，如果目标 tarball 的哈希与 getdeps 记录的期望值不一致，也可能在后续校验阶段失败。修复此正则确保 `_verify_hash` 在所有情况下均被替换为 `pass` 是一个防御性补充。

## 需要进一步确认的点

1. **pagure.io 当前状态**：需要确认 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 目前是否可正常访问并返回有效的 tar.gz 归档，还是已永久失效。如果是临时性故障（如限流），则方向 1 仍然是最可靠的长期方案。
2. **getdeps 的下载跳过逻辑**：需要在 fbcode_builder 仓库中确认 getdeps 的 fetcher 在 downloads 目录已存在目标文件时是否会跳过网络下载，以及跳过的判断条件（仅检查文件存在 vs. 检查文件大小/哈希）。这决定了方向 1 的具体实施方式。
3. **模式22 的当前状态**：需要检查当前 PR 中 `fix_getdeps.py` 的正则表达式是否已修复了 `_verify_hash` 位于类末尾的边界情况。若尚未修复，方向 3 也需要同步执行。
4. **日志完整性**：日志在 libaio 下载返回 HTML 后立即截断，未显示 getdeps 随后输出的具体错误信息（如 tar 提取错误、哈希校验错误等）。如果能获取完整的 getdeps stderr/stdout 输出，可以帮助更精确地确定失败点。
