"""Check pending-to-published single works without changing actual novel files."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from chapter_source import load_single_story


class SingleWorkTests(unittest.TestCase):
    def test_title_only_and_date_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'story.md'
            path.write_text('杀手杰克 / Killer Jack\n', encoding='utf-8')
            self.assertEqual(load_single_story(path), [])
            path.write_text('# 杀手杰克\n日期：2026-11-01\n\n第一段。\n\n第二段。\n', encoding='utf-8')
            story, = load_single_story(path)
            self.assertEqual(story['title'], '杀手杰克')
            self.assertEqual(story['date'], '2026-11-01')
            self.assertEqual(story['paragraphs'], ['第一段。', '第二段。'])
            path.write_text('杀手杰克\n日期：2026-02-30\n正文。', encoding='utf-8')
            with self.assertRaises(ValueError):
                load_single_story(path)

    def test_publish_full_story_and_preserve_serial_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('build.py', 'chapter_source.py', 'validate.py'):
                shutil.copy(ROOT / name, root / name)
            for name in ('fonts', 'style.css', 'app.js', 'favicon.svg'):
                (root / name).symlink_to(ROOT / name)
            (root / 'content').mkdir()
            (root / 'content/site.json').write_text((ROOT / 'content/site.json').read_text(), encoding='utf-8')
            (root / 'chapters').mkdir()
            (root / 'chapters/01.md').write_text('第一章\n连载测试正文。\n', encoding='utf-8')
            (root / 'stories').mkdir()
            story = root / 'stories/killer-jack.md'
            story.write_text('杀手杰克 / Killer Jack\n', encoding='utf-8')
            output = root / 'dist'
            env = dict(os.environ, SITE_URL='https://example.com/daswohltemperierte', OUTPUT_DIR=str(output))

            def build():
                for name in ('build.py', 'validate.py'):
                    subprocess.run([sys.executable, str(root / name)], cwd=root, env=env, check=True, capture_output=True, text=True)

            build()
            self.assertTrue((output / 'read/OP81 LN4/01/index.html').exists())
            self.assertFalse((output / 'read/killer-jack/01/index.html').exists())
            pending = (output / 'works/killer-jack/index.html').read_text()
            self.assertIn('正文待发布', pending)
            self.assertIn('content="noindex"', pending)
            self.assertNotIn('killer-jack', (output / 'sitemap.xml').read_text())
            management = (output / 'manage/index.html').read_text()
            self.assertIn('/edit/main/stories/killer-jack.md', management)
            self.assertIn('粘贴全文', management)

            story.write_text('# 杀手杰克 / Killer Jack\n日期：2026-11-01\n\n第一段 <script>alert(1)</script>\n\n第二段。\n', encoding='utf-8')
            build()
            reader = (output / 'read/killer-jack/01/index.html').read_text()
            self.assertIn('data-work="killer-jack"', reader)
            self.assertIn('data-base="/daswohltemperierte"', reader)
            self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', reader)
            self.assertIn('— 全文完 —', reader)
            self.assertNotIn('下一章', reader)
            self.assertIn('ShortStory', reader)
            self.assertIn('/read/killer-jack/01/', (output / 'sitemap.xml').read_text())
            archive = (output / 'works/index.html').read_text()
            self.assertIn('href="/daswohltemperierte/read/killer-jack/01/"', archive)
            self.assertIn('阅读全文', archive)
            self.assertNotIn('正文待发布', archive)
            self.assertIn('修改全文', (output / 'manage/index.html').read_text())


if __name__ == '__main__':
    unittest.main()
