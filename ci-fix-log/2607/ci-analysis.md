# CI 失败分析报告

## 基本信息
- PR: #2607 — 【自动升级】fbthrift容器镜像升级至2026.06.15.00版本.
- 失败类型: build-error
- 置信度: 中
- 知识库匹配: 新模式
- 新模式标题: pagure.io下载返回HTML
- 新模式症状关键词: pagure.io, text/html, Content-Type, libaio, getdeps, _verify_hash, fix_getdeps.py

## 根因分析

### 直接错误
```
#11 340.2 Download with https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz -> /tmp/fbcode_builder_getdeps-ZbuildZbuildZfbcode_builder-root/downloads/libaio-libaio-libaio-0.3.113.tar.gz ...
#11 340.2 .. 2238 of (Unknown)  [Complete in 1.196933 seconds]
#11 340.2 Content-Type: text/html; charset=utf-8
#11 340.2 Set-Cookie: techaro.lol-anubis-auth=; Path=/; Expires=Tue, 16 Jun 2026 02:32:44 GMT; Max-Age=0; Secure; SameSite=None

#11 ERROR: process "/bin/sh -c git clone -b ${VERSION} --depth 1 https://github.com/facebook/fbthrift.git /build &&     cd /build &&     mkdir -p ... &&     cp /tmp/libaio.tar.gz ... &&     python3 /tmp/fix_getdeps.py &&     ./build/fbcode_builder/getdeps.py --allow-system-packages --install-prefix /usr/local build fbthrift" did not complete successfully: exit code: 1
```

### 根因定位
- 失败位置: Dockerfile:18-23 (RUN 指令), getdeps 构建依赖 libaio 阶段
- 失败原因: pagure.io 对 libaio 归档文件的下载请求返回 HTML 错误页面（Content-Type: text/html，仅 2238 字节），而非有效的 tar.gz 文件；同时 PR 中预拷贝的本地 libaio tar.gz 未能阻止 getdeps 尝试重新下载

### 与 PR 变更的关联
PR #2607 新增了 fbthrift 2026.06.15.00 的 Dockerfile，其中包含两项关键工作：
1. **预拷贝 libaio 包**：通过 `COPY libaio-libaio-0.3.113.tar.gz /tmp/libaio.tar.gz` 将本地 tarball 放入容器，再 `cp` 到 getdeps 下载目录
2. **跳过哈希校验**：`fix_getdeps.py` 使用正则替换 `fetcher.py` 中的 `_verify_hash` 方法为空操作

但这两项工作未能阻止 getdeps 尝试从 pagure.io 下载。可能原因：
- `fix_getdeps.py` 中的正则 `r'def _verify_hash\(self\):.*?(?=\n    def )'` 依赖下一个 `def ` 作为匹配终点；若 `_verify_hash` 是所在类的最后一个方法，则正则无法匹配，哈希校验未被实际跳过，导致 getdeps 检测到本地文件哈希不匹配后重新从上游下载
- pagure.io 归档链接 `https://pagure.io/libaio/archive/libaio-0.3.113/libaio-libaio-0.3.113.tar.gz` 当前不可用（返回 HTML 错误页）

## 修复方向

### 方向 1（置信度: 中）
修复 `fix_getdeps.py` 中的正则表达式，使其能正确匹配 `_verify_hash` 方法——即使该方法是类中最后一个方法。将正则从依赖后续 `def ` 边界改为匹配到类结尾或方法体结束，确保哈希校验被实际跳过，使 getdeps 直接使用预拷贝的本地 libaio tar.gz。

### 方向 2（置信度: 低）
更换 libaio 的下载源。若 pagure.io 长期不可用，可考虑从其他镜像源（如 GitHub releases、kernel.org 等）获取 libaio 源码包，或在 Dockerfile 中从系统包管理器（dnf）安装 `libaio-devel` 替代源码编译。

## 需要进一步确认的点
1. `build/fbcode_builder/getdeps/fetcher.py` 中 `_verify_hash` 方法是否确实是其所在类的最后一个方法——这直接决定正则是否能匹配成功
2. 本地提供的 `libaio-libaio-0.3.113.tar.gz` 文件哈希是否与 getdeps 期望的哈希值一致——若不一致，即使跳过验证也可能有其他完整性检查触发重新下载
3. pagure.io 的 `libaio-0.3.113` 归档链接是永久失效还是临时故障——可从外部浏览器验证该 URL 是否可访问
4. 之前版本（2026.05.18.00）的 fbthrift Dockerfile 是否使用相同的 getdeps 构建流程、有无类似问题
