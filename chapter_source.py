"""Read one plain-text chapter per numbered .md file; no third-party packages."""
from datetime import date
from pathlib import Path
import re


def load_chapters(directory):
    directory = Path(directory)
    numbered = []
    for path in directory.glob('*.md'):
        if path.name.lower() == 'readme.md':
            continue
        if not re.fullmatch(r'[0-9]+', path.stem):
            raise ValueError(f'{path.name}: 章节文件请使用数字编号，例如 04.md')
        numbered.append((int(path.stem), path))
    if not numbered:
        raise ValueError('章节目录为空，请添加 01.md，并写入标题和正文。')
    chapters, seen = [], set()
    for number, path in sorted(numbered, key=lambda item: item[0]):
        if number in seen:
            raise ValueError(f'{path.name}: 章节编号重复，请检查 01.md 与 001.md 等同号文件。')
        seen.add(number)
        lines = path.read_text(encoding='utf-8-sig').strip().splitlines()
        if not lines:
            raise ValueError(f'{path.name}: 请在第一行写标题，下面粘贴正文。')
        title = re.sub(r'^#{1,6}\s+', '', lines[0].strip()).strip()
        if not title:
            raise ValueError(f'{path.name}: 章节标题不能为空。')
        body = [line.strip() for line in lines[1:] if line.strip()]
        published = ''
        if body and re.match(r'^(?:日期\s*[:：]|date\s*:)', body[0], re.I):
            published = re.split(r'[:：]', body.pop(0), maxsplit=1)[1].strip()
            try:
                if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', published):
                    raise ValueError('date format')
                date.fromisoformat(published)
            except ValueError:
                raise ValueError(f'{path.name}: 日期请写成 YYYY-MM-DD，例如 2026-10-31') from None
        notice = body.pop(0) if body and body[0].startswith('【演示文本】') else ''
        if not body:
            raise ValueError(f'{path.name}: 标题下方还没有正文；粘贴正文后再提交。')
        chapters.append({
            'slug': f'{number:02d}',
            'title': title,
            'date': published,
            'paragraphs': body,
            'notice': notice,
            'demo': bool(notice),
            'source_file': str(path.name),
        })
    return chapters


def load_single_story(path):
    """A title-only file is an unpublished work; body text publishes one full story."""
    path = Path(path)
    lines = path.read_text(encoding='utf-8-sig').strip().splitlines()
    if not lines:
        return []
    title = re.sub(r'^#{1,6}\s+', '', lines[0].strip()).strip()
    if not title:
        raise ValueError(f'{path.name}: 第一行请保留作品标题。')
    body = [line.strip() for line in lines[1:] if line.strip()]
    published = ''
    if body and re.match(r'^(?:日期\s*[:：]|date\s*:)', body[0], re.I):
        published = re.split(r'[:：]', body.pop(0), maxsplit=1)[1].strip()
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', published):
                raise ValueError('date format')
            date.fromisoformat(published)
        except ValueError:
            raise ValueError(f'{path.name}: 日期请写成 YYYY-MM-DD。') from None
    if not body:
        return []
    return [{'slug':'01','title':title,'date':published,'paragraphs':body,'notice':'','demo':False,'source_file':path.name}]
