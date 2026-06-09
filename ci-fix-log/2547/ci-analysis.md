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
#11 354.0 Assessing libaio...
#11 354.0 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 354.0 .. 2238 of (Unknown)  [Complete in 1.187799 seconds]
#11 354.0 Date: Tue, 09 Jun 2026 01:09:04 GMT
#11 354.0 Content-Type: text/html; charset=utf-8
#11 354.0 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 09 Jun 2026 01:08:04 GMT; Max-Age=0; Secure; SameSite=None
#11 354.0 Connection: close
#11 354.0 Transfer-Encoding: chunked
#11 354.0 
#11 354.0 
#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads &&     cp /tmp/libaio.tar.gz /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: `Others/fbthrift/2026.06.08.00/24.03-lts-sp3/fix_getdeps.py:18-20`（`_verify_hash` 替换正则存在边界缺陷）
- 失败原因: `fix_getdeps.py` 中用于跳过 libaio 哈希校验的正则表达式 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 使用前瞻断言 `(?=\n    def )` 查找下一个方法定义，当 `_verify_hash` 是类中最后一个方法时，前瞻无法匹配任何内容，正则整体不匹配，导致 `_verify_hash` 方法未被替换为 `pass`，哈希校验静默保留。getdeps 随后校验预先拷贝的 libaio tarball 时发现哈希不匹配，回退到从 pagure.io 下载，但 pagure.io 返回的是 HTML 页面（2228字节，Content-Type: text/html）而非有效 tar.gz 文件，导致解压/构建阶段失败。

### 发生链路详析
1. Dockerfile:18 RUN 执行 `fix_getdeps.py`，尝试用正则替换 `_verify_hash` 方法体
2. 正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 依赖后续方法定义作为边界标记
3. `_verify_hash` 是 `Fetcher` 类的最后一个方法，正则匹配失败，原方法保持不变
4. getdeps 在处理 libaio 依赖时，校验预先拷贝的 tarball 哈希 → 不匹配
5. getdeps 回退下载，但 pagure.io 的 URL 返回 HTML 错误页面而非 tarball
6. getdeps 尝试以 tar.gz 格式解压 HTML 内容，失败，exit code 1

### 与 PR 变更的关联
是。该失败由 PR 新增的 `fix_getdeps.py` 脚本中的正则表达式边界缺陷直接触发。脚本本身是为绕开 getdeps 对预拷贝 libaio tarball 的哈希校验而设计，但由于正则缺陷，绕开逻辑未生效。

## 修复方向

### 方向 1（置信度: 高）
修复 `fix_getdeps.py` 中 `_verify_hash` 替换正则的边界缺陷。当前正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 使用前瞻断言要求存在后续方法，当目标方法是类中最后一个方法时匹配失败。应将正则改为能匹配到方法体末尾（即遇到下一个方法定义 **或** 类定义结束/下一个非方法行）的形式，确保无论方法在类中的位置如何都能正确替换为 `pass`。

### 方向 2（置信度: 中）
若修复正则后仍然失败，需确认 pagure.io 上的 libaio 下载 URL 是否已变更。备选方案为将 libaio 的获取逻辑改为完全使用本地预拷贝的 tarball，在 getdeps manifest 或构建参数层面彻底跳过 libaio 的网络下载步骤。

## 需要进一步确认的点
1. 需要查看 fbthrift 源码中 `build/fbcode_builder/getdeps/fetcher.py` 的 `Fetcher` 类结构，确认 `_verify_hash` 是否确实为类中最后一个方法，以验证正则边界缺陷假设。
2. 需要确认 `libaio-libaio-0.3.113.tar.gz` 从 pagure.io 下载的 URL 当前是否仍有效（返回 HTML 可能是 404 或重定向到登录页）。
3. 如果 getdeps 的版本在不同构建间可能变化，需确认 `_verify_hash` 方法在 fetcher.py 中的位置是否稳定。
