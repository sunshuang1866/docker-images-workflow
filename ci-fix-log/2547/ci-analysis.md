# CI 失败分析报告

## 基本信息
- PR: #2547 — 【自动升级】fbthrift容器镜像升级至2026.06.08.00版本.
- 失败类型: build-error
- 置信度: 高
- 知识库匹配: 模式22
- 新模式标题: (不适用)
- 新模式症状关键词: (不适用)

## 根因分析

### 直接错误
```
#11 354.0 Content-Type: text/html; charset=utf-8
#11 354.0 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 01:08:04 GMT; Max-Age=0; Secure; SameSite=None
#11 354.0 Connection: close
#11 354.0 Transfer-Encoding: chunked
#11 354.0 
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build && ... && ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py:17-21`（`_verify_hash` 替换正则）
- 失败原因: `fix_getdeps.py` 中用于跳过 libaio 哈希校验的正则表达式 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 存在边界缺陷——当 `_verify_hash` 是类中最后一个方法时，lookahead `(?=\n    def )` 无法匹配到下一个方法定义，导致替换失败，哈希校验未被跳过。getdeps 校验预置 tarball 哈希不匹配后将其删除，转而从 `pagure.io` 下载 libaio，而 pagure.io 返回 `Content-Type: text/html`（错误页面/404），getdeps 无法处理 HTML 内容，构建失败。

### 与 PR 变更的关联
PR 新增的 `fix_getdeps.py` 正是本次失败的根因。该脚本的修改逻辑有两个作用：
1. 向 getdeps 发行版识别列表添加 `openeuler`（生效正常）
2. 跳过 libaio 的哈希校验（正则边界缺陷，未生效）

由于第一处修改生效，getdeps 能正确识别 openEuler 并开始构建；但由于第二处修改未生效，getdeps 在遇到预置 libaio tarball 时仍执行哈希校验，校验失败后尝试从原始 URL 下载，而该 URL 已不可用。

## 修复方向

### 方向 1（置信度: 高）
修复 `fix_getdeps.py` 中跳过 `_verify_hash` 方法的正则表达式，覆盖"类中最后一个方法"的边界情况。当前正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 的 lookahead 要求在 `_verify_hash` 之后还有一个 `def` 定义，若 `_verify_hash` 是类末尾方法则匹配失败。应将正则改为匹配到类定义结束或文件末尾，例如使用 `r'def _verify_hash\(self\):.*?(?=\n    def |\nclass |\Z)'` 或等价方案。

### 方向 2（置信度: 低）
若 pagure.io 的 libaio 下载 URL 本身已永久失效（而非仅因正则未生效导致的回退下载），可考虑将 libaio 的下载源切换至其他可用镜像站，或直接改用系统包管理器安装 `libaio-devel`。但由于本日志中 pagure.io 返回 HTML 的根本原因是正则未生效导致的不必要下载，方向 1 应优先处理。

## 需要进一步确认的点
- 确认 `fetcher.py` 中 `_verify_hash` 方法在目标版本 fbthrift 源码中的实际位置（是否为类中最后一个方法），以验证正则边界分析的准确性
- 确认预置的 `libaio-libaio-0.3.113.tar.gz` 文件与 getdeps 期望的 SHA256 哈希值是否一致（若不一致，即使正则修复后也需替换正确的 tarball）
