# daswohltemperierte · GitHub Pages 版

个人长篇小说网站第一版：橙白极简首页、作品目录、独立章节页、手机排版、阅读设置、本机阅读进度、收藏、RSS 和搜索收录基础配置。

站名已确定为 `daswohltemperierte`。白色为页面底色，橙色用于标题、链接、封面与按钮。封面和《长夜来信》仍为演示内容，正式笔名与小说尚待替换。独立域名尚未绑定。

## 在你的仓库启用网站

目标仓库：[azzure0216-netizen/daswohltemperierte](https://github.com/azzure0216-netizen/daswohltemperierte)。

1. 打开上述仓库，确认根目录能看到 `README.md`、`build.py`、`style.css`、`content` 等文件。
2. 点击仓库顶部 **Settings**，在左侧找到 **Pages**。
3. 在 **Build and deployment** 下，将 **Source** 设为 **GitHub Actions**。
4. 回到仓库顶部 **Actions**，选择左侧 **Publish novel website**，点击右侧 **Run workflow**，分支选择 `main`，再点击绿色 **Run workflow** 按钮。如果第一次提交在 Pages 开启前运行失败，开启后重新运行即可。
5. 等工作流中 `build` 和 `deploy` 都显示绿色勾号。打开 **Settings → Pages**，点击 GitHub 提供的 **Visit site**。该链接才是已部署网站的正式验证入口。
6. 以后提交到 `main` 会自动检查并重新发布，不必每次手动运行。

如果是手动上传本包：解压后，进入外层文件夹，把内部文件和目录上传到仓库根目录，而不是直接上传 ZIP 文件，也不要多套一层 `daswohltemperierte-github-pages` 文件夹。必须包含 `.github/workflows/pages.yml`。macOS Finder 可用 **Command + Shift + .** 显示点开头目录，然后使用 **Add file → Upload files → Commit changes**。

## 如何修改文字、更新章节

1. 在仓库点击 `content`，再点击 `site.json`。
2. 点击右上角铅笔 **Edit this file**。
3. 在 `works[0].chapters` 里修改章节标题和正文。`paragraphs` 中每个引号包起来的字符串就是一段，使用英文双引号与英文逗号；正文里如果有英文双引号，需要写成 `\"`，中文引号“”可以直接使用。
4. 新增章节时，在最后一个章节对象后加英文逗号，然后添加下列对象；最后一个对象后面不加逗号：

```json
{
  "slug": "04",
  "title": "第四章的标题",
  "date": "2026-10-31",
  "paragraphs": [
    "这是第一段正文。",
    "这是第二段正文。"
  ]
}
```

5. 点击 **Commit changes**，选择提交到 `main`，再次确认提交。之后到 **Actions** 等待绿色勾号。
6. 打开网站检查新章节。未更新时先确认工作流成功，再刷新页面。

章节 `slug` 是分享网址的一部分，已发布后尽量不改；新章使用新的编号。`date` 使用你实际发布的日期。章节数、目录、翻页、字数、RSS 和站点地图会自动更新。

演示章节的 `notice` 字段用于演示提示；正式章节可以不写这个字段。正文第一段已经按正常正文处理，不会被误作提示。

首次换上你的整部小说时，请统一替换演示简介、封面文字和演示标识；目前部分首版展示文案仍在 `build.py`。可以先把小说发给助手完成首次替换，之后按上述步骤追加章节。

## 独立域名

1. 先持有要使用的域名。
2. 在 **Settings → Pages → Custom domain** 填入域名并保存，再按 GitHub 官方文档配置 DNS。DNS 目标要按你的账号、域名类型核对，不使用本站临时地址。
3. 等待 DNS 检查和证书完成后，启用 **Enforce HTTPS**，重新运行工作流。
4. 工作流读取 Pages 的实际网址，自动更新页面链接、canonical、站点地图和 RSS；既支持个人主页，也支持 `/仓库名/` 子路径与独立域名。

本项目通过 GitHub Actions 发布。自定义域名必须在 Pages 设置中配置，单独添加 `CNAME` 文件不能代替该设置。

## 以后怎样更新

- 编辑 `content/site.json`，提交到 `main`；Actions 自动生成并发布。
- `name` 是站名，`author` 是公开笔名；作品信息在 `works[0]`，章节在 `chapters`。
- 当前只有一部长篇，暂不支持仅通过追加 JSON 自动生成第二部作品。
- 每章的 `slug` 是稳定网址的一部分，发布后尽量不改。
- 部分首版封面、文案和演示标识写在 `build.py` 中，改正式作品时应一并替换，不能只改 JSON。
- `origin` 默认留空；GitHub Actions 从 Pages 设置中取得实际网址，无需填写你的用户名。
- 本版没有可登录的作者后台。你可以在 GitHub 网页编辑内容，或让助手继续帮你整理、提交章节。

阅读进度和收藏只存在读者的当前浏览器，不能跨设备同步。

## 本地预览（可选）

需要 Python 3.12 或更新版本；无需安装第三方包。

```bash
python3 build.py
python3 validate.py
python3 -m http.server 8000 --directory dist
```

在浏览器打开 `http://localhost:8000/`。不要直接双击 HTML 文件。

可以通过 `SITE_URL` 环境变量指定生成网址；支持 `https://用户名.github.io/仓库名` 或正式独立域名。`OUTPUT_DIR` 可以指定另一输出目录。

## 文件

| 文件 | 用途 |
| --- | --- |
| `.github/workflows/pages.yml` | 构建、检查与自动发布 |
| `content/site.json` | 站名和演示章节数据 |
| `build.py` | 生成独立 HTML 页面 |
| `validate.py` | 检查链接、路径、搜索元数据与订阅文件 |
| `style.css` | 橙白风格与手机排版 |
| `app.js` | 搜索、阅读设置、进度与收藏 |
| `favicon.svg` | 网站图标 |

`dist/` 为构建输出，不需要上传到源码仓库；Actions 会自动生成。

## 官方说明

- [GitHub Pages 自定义工作流](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)
- [设置发布来源](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [管理独立域名](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)

允许抓取并不保证搜索收录、排名或收录时间。正式正文上线后可向搜索引擎站长平台提交站点地图。
