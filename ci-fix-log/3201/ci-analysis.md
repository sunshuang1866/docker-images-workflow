# CI 失败分析报告

## 基本信息
- PR: #3201 — 增加maca-sdk镜像
- 失败类型: dependency-error
- 置信度: 高
- 知识库匹配: 新模式
- 新模式标题: RPM源元数据GPG签名缺失
- 新模式症状关键词: repo_gpgcheck, GPG signature is not available, copr, repomd.xml.asc, 404

## 根因分析

### 直接错误
```
#10 2.579 Errors during downloading metadata for repository 'copr:eur.****.openatom.cn:ObjectNotFound:maca-sdk':
#10 2.579   - Status code: 404 for https://eur.****.openatom.cn/results/ObjectNotFound/maca-sdk/****-24.03_LTS_SP2-x86_64/repodata/repomd.xml.asc (IP: 121.36.2.159)
#10 2.579 Error: Failed to download metadata for repo 'copr:eur.****.openatom.cn:ObjectNotFound:maca-sdk': GPG verification is enabled, but GPG signature is not available. This may be an error or the repository does not support GPG verification: Status code: 404 for https://eur.****.openatom.cn/results/ObjectNotFound/maca-sdk/****-24.03_LTS_SP2-x86_64/repodata/repomd.xml.asc (IP: 121.36.2.159)
#10 288.7 Ignoring repositories: copr:eur.****.openatom.cn:ObjectNotFound:maca-sdk
#10 289.6 No match for argument: maca-sdk-x86_64
#10 289.7 Error: Unable to find a match: maca-sdk-x86_64
```

### 根因定位
- 失败位置: `AI/maca-sdk/3.7/24.03-lts-sp3/EUR.repo:5`（`repo_gpgcheck=1` 行）
- 失败原因: `EUR.repo` 中设置了 `repo_gpgcheck=1`，要求 dnf 验证仓库元数据（`repomd.xml`）的 GPG 签名。但上游 Copr 仓库未提供元数据签名文件（`repomd.xml.asc` 返回 HTTP 404），导致 dnf 拒绝信任该仓库并将其忽略。仓库被忽略后，`maca-sdk-x86_64` 包无法被检索到，`dnf install` 因无匹配包而失败（exit code: 1）。

**完整失败链路**:
1. `EUR.repo` 中 `repo_gpgcheck=1` 启用仓库元数据 GPG 签名验证
2. `dnf makecache --refresh` 尝试下载 `repomd.xml.asc`，上游返回 404
3. dnf 报 "GPG signature is not available"，将仓库标记为忽略
4. 随后 `dnf install maca-sdk-x86_64` 在所有已启用仓库中找不到该包（"No match for argument"）
5. 构建失败

注：`gpgcheck=1`（第 5 行的包级 GPG 检查）和 GPG key 的下载导入均正常（日志中可见 "Importing GPG key 0x8E1718BB" 成功），问题仅在于 `repo_gpgcheck=1`（第 8 行的仓库元数据级 GPG 检查）。

### 与 PR 变更的关联
**直接关联**：本次 PR 新增了 `AI/maca-sdk/3.7/24.03-lts-sp3/EUR.repo` 文件，其中错误的 `repo_gpgcheck=1` 设置是此次 CI 失败的唯一原因。Dockerfile、meta.yml、README.md 等其余新增文件无问题。`#8` 步骤中出现的 `[MIRROR] Curl error (28): Timeout` 是 openEuler 官方源的瞬态网络波动，已被镜像站 failover 自动恢复，不影响最终构建。

### 次要风险（待修复后验证）
`EUR.repo` 中的 `baseurl` 为 `openeuler-24.03_LTS_SP2-$basearch`，但基础镜像为 `openeuler:24.03-lts-sp3`。虽然 Copr 仓库的包通常不强制绑定特定的 SP 小版本，但如果修复 GPG 问题后 `maca-sdk-x86_64` 能成功安装但运行时出现依赖冲突，需考虑将 baseurl 对应更新为 SP3 路径（前提是上游 Copr 仓库提供了 SP3 构建）。

## 修复方向

### 方向 1（置信度: 高）
将 `AI/maca-sdk/3.7/24.03-lts-sp3/EUR.repo` 第 8 行的 `repo_gpgcheck=1` 改为 `repo_gpgcheck=0`。上游 Copr 仓库未对仓库元数据做 GPG 签名（`repomd.xml.asc` 不存在），禁用仓库级 GPG 检查即可让 dnf 正常读取该仓库的包列表。包级 GPG 检查（`gpgcheck=1`）应保留，因为 `pubkey.gpg` 是可用的。

### 方向 2（置信度: 中）
如果方向 1 修复后构建仍失败（例如因 SP2 与 SP3 包版本不兼容），则需要联系上游 Copr 仓库维护者（ObjectNotFound）确认是否有针对 openEuler 24.03-LTS-SP3 的专用仓库路径，并将 `baseurl` 中的 `openeuler-24.03_LTS_SP2` 更新为 `openeuler-24.03_LTS_SP3`。

## 需要进一步确认的点
1. 上游 Copr 仓库 `eur.openeuler.openatom.cn/results/ObjectNotFound/maca-sdk/` 是否有针对 openEuler 24.03-LTS-SP3 的构建（即 `openeuler-24.03_LTS_SP3-$basearch/` 目录是否存在且包含相同包），若无则当前 SP2 baseurl 已是正确选择。
2. 确认 `maca-sdk` 包在 Copr 仓库中的实际包名是否为 `maca-sdk`（而非如 `maca-sdk-musa` 等变体名），以验证 `dnf install -y maca-sdk-${ARCH}` 的包名拼写无误。

## 修复验证要求
修复后，code-fixer 应确认：
1. dnf 能成功下载 Copr 仓库的元数据（不再出现 "GPG signature is not available" 或 "Ignoring repositories" 日志行）
2. `dnf install -y --allowerasing maca-sdk-${ARCH}` 能成功找到并安装包
3. 容器能正常启动并进入 `/bin/bash`（验证 ENTRYPOINT 生效）
