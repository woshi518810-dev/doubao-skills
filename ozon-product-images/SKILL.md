---
name: ozon-product-images
description: Ozon俄罗斯电商平台商品图片批量下载。输入Ozon商品页面URL，自动遍历所有颜色/款式变体，下载每个变体左侧主图区域的全套商品图（高清wc1500分辨率），按变体分文件夹保存。触发词：ozon下载、ozon图片、ozon套图、下载ozon商品图、ozon商品图片。当用户提供Ozon商品链接并要求下载图片/套图/主图时使用。
---

# Ozon商品图片批量下载

## 功能

自动下载Ozon商品页所有颜色/款式变体的左侧主图套图，每个变体单独一个文件夹。

## 使用方法

用户提供Ozon商品URL后，执行：

```bash
python "<skill_dir>/scripts/ozon_download.py" "<Ozon商品URL>"
```

指定输出目录（可选，默认 `D:\ozon下图`）：

```bash
python "<skill_dir>/scripts/ozon_download.py" "<Ozon商品URL>" "<输出目录>"
```

实际保存路径：`<输出目录>\ozon_<商品ID>\`

## 工作流程

1. 启动Chrome（selenium，反检测配置）
2. 加载商品URL
3. 若出现滑块验证码，暂停提示用户手动拖动，通过后自动继续
4. 扫描右侧颜色/款式区域，提取所有变体ID
5. 逐个点击变体 → 提取左侧垂直套图缩略图 → 转高清(wc1500) → 过滤非商品图 → 分文件夹保存
6. 输出统计和文件夹列表

## 输出结构

```
D:\ozon下图\
└── ozon_<商品ID>\
    ├── variant_01_ID123456789\
    │   ├── 01.jpg
    │   ├── 02.jpg
    │   └── ...
    └── variant_02_ID987654321\
        └── ...
```

## 重要说明

### 验证码

Ozon会触发滑块拼图验证码。脚本无法自动通过，会暂停提示用户手动操作。每次点击变体都可能触发，脚本反复检测并提示。

### ChromeDriver

自动查找：脚本同目录 → 已知路径 → 系统PATH。Chrome更新后需替换对应版本chromedriver。

### 图片过滤

自动排除：视频封面、二维码、网站logo、CMS静态资源。只保留multimedia商品图片。

### 依赖

```bash
pip install selenium requests
```
