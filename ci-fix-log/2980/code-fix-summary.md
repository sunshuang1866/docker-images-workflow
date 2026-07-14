# 修复摘要

## 修复的问题
无需代码修改。CI 失败为基础设施层网络问题（`infra-error`），非代码缺陷。

## 修改的文件
无

## 修复逻辑
CI 构建失败的直接原因是 openEuler 24.03-LTS-SP4 RPM 仓库（`repo.****.org`）在下载 `gcc-c++`（13 MB 大包）时发生 HTTP/2 流错误（`Curl error (92): Stream error in the HTTP/2 framing layer`），两次重试均失败，导致 `dnf install` 以 exit code 1 终止。

该错误与 PR #2980 的所有改动无关：
- PR 仅新增了 `Others/grads/2.2.3/24.03-lts-sp4/Dockerfile` 和配套元数据文件，变更内容合法正确。
- `dnf install` 中的软件包均在 openEuler 24.03-LTS-SP4 仓库中存在（日志显示 258 个包的依赖解析成功），Dockerfile 语法和包名无误。
- 同一次构建中 `cmake-data` 和 `git-core` 也遭遇同类 Curl error (92)，表明是仓库侧 HTTP/2 协议层的临时网络波动。

**修复方式：重新触发 CI 构建（retest），大概率能够通过。**

## 潜在风险
无