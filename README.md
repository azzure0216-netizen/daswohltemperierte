# daswohltemperierte · Mismatch

橙白极简的个人长篇小说网站。作品为 Mismatch，副标题为“不要小瞧事实婚姻”，署名为 Azzure3。

## 直接粘贴章节

在网站页脚点击 **章节管理**。每章的“粘贴／修改正文”会打开 GitHub 编辑器：

1. 登录拥有仓库写入权限的 GitHub 账号。
2. 选择要更新的章节，全选编辑器中的文件内容。
3. 粘贴完整章节：第一行是标题，下面是正文。
4. 点击 **Commit changes**，提交到 `main`，确认保存。
5. 在 **Actions → Publish novel website** 等待绿色勾号，再刷新网站。

没有提交的编辑不会发布；提交到 main 的正文将公开出现在网站上。

```text
第一章 你的章节标题

这是第一段正文。

这是第二段正文。
```

正文按换行分段，空行可有可无。标题也可以写成 `# 第一章 你的章节标题`。正文按普通文字显示，不将正文中的 HTML 当作网页代码运行。

日期可选，在标题下方写 `日期：2026-10-31`；不填也能发布。

## 新增章节

“章节管理”顶部点击 **新增第 N 章**，入口会预填下一个编号的文件名。保留数字加 `.md` 的文件名，例如 `04.md`，再粘贴标题和正文并提交。

章节位于 `chapters/`，按数字编号自动排序。目录、字数、翻页和站点地图会自动更新，日常更新正文不需要修改 JSON。

已发布文件的编号尽量保持不变。`01.md` 与 `001.md` 是相同编号，不要同时存在。标题或正文为空、日期格式不正确等情况会阻止新版本发布；网站继续使用上一个成功版本。

首批三个章节为网站演示内容。全选替换为你的完整章节时，移除原有 `【演示文本】` 提示，演示标记会自动消失。尚未替换的演示章节会继续保留标记。

## 修改封面与作品资料

编辑 `content/site.json`：

| 字段 | 内容 |
| --- | --- |
| `name` | 网站名称 |
| `author` | 作者署名 |
| `works[0].title` | 小说名称与封面标题 |
| `works[0].subtitle` | 封面副标题 |
| `works[0].description` | 作品简介 |
| `works[0].status` | 连载状态 |
| `works[0].tags` | 作品标签 |

首页大标题等展示文案目前仍在 `build.py`，正文已经改为读取 `chapters/` 中的独立文件。

## 启用 Pages 与独立域名

在 **Settings → Pages → Source** 选择 **GitHub Actions**，再到 **Actions → Publish novel website → Run workflow** 运行一次，分支选 main。成功后在 **Settings → Pages → Visit site** 查看网站。

以后提交到 main 自动发布。工作流读取 Pages 的实际网址，支持仓库子路径与独立域名。

独立域名在 **Settings → Pages → Custom domain** 中配置，按 GitHub 要求填写 DNS，证书生效后启用 **Enforce HTTPS** 并重新运行工作流。当前尚未指定或绑定独立域名。

## 技术与本地检查

Python 3.12 或更新版本，无第三方 Python 依赖：

```bash
python3 build.py
python3 validate.py
python3 -m http.server 8000 --directory dist
```

输出为静态 HTML/CSS/JavaScript。阅读进度、收藏和排版偏好只保存在读者当前浏览器。章节管理页提供 GitHub 编辑入口，不保存密码或令牌；只有拥有仓库写入权限的账号才能提交本站更新。

源码：[azzure0216-netizen/daswohltemperierte](https://github.com/azzure0216-netizen/daswohltemperierte)。
