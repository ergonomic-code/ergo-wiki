import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.fixture
def site(tmp_path):
    (tmp_path / 'content/docs/terminology').mkdir(parents=True)
    (tmp_path / 'layouts/_default').mkdir(parents=True)
    (tmp_path / 'layouts/shortcodes').mkdir(parents=True)
    shutil.copy(Path(__file__).parents[1] / 'layouts/shortcodes/term.html', tmp_path / 'layouts/shortcodes')
    (tmp_path / 'hugo.toml').write_text(
        'baseURL = "https://example.org/wiki/"\n[security.exec]\nallow = ["^asciidoctor$"]\n', encoding='utf-8',
    )
    (tmp_path / 'layouts/_default/single.html').write_text('{{ .Content }}', encoding='utf-8')
    (tmp_path / 'content/docs/try.adoc').write_text(
        '---\ntitle: Тест\n---\n\nПростое {{< term "action" "действие" >}}.\n', encoding='utf-8',
    )
    return tmp_path


def build(site):
    return subprocess.run(['hugo', '--source', str(site)], text=True, capture_output=True, check=False)


def test_term_shortcode_renders_asciidoc_and_hugo_page_url(site):
    (site / 'content/docs/terminology/action.adoc').write_text(
        '---\ntitle: Действие\nurl: /special/action/\n---\n\n'
        '// tag::definition[]\n_Операция_ с *эффектом*.\n// end::definition[]\n', encoding='utf-8',
    )
    result = build(site)
    assert result.returncode == 0, result.stderr
    page = (site / 'public/docs/try/index.html').read_text(encoding='utf-8')
    assert '<em>Операция</em> с <strong>эффектом</strong>.' in page
    assert 'href="/wiki/special/action/">Подробнее</a>' in page
    assert '>действие</span>' in page


@pytest.mark.parametrize('source', [None, 'Нет определения.'])
def test_term_shortcode_rejects_missing_page_or_definition(site, source):
    if source is not None:
        (site / 'content/docs/terminology/action.adoc').write_text(
            '---\ntitle: Действие\n---\n\n' + source, encoding='utf-8',
        )
    result = build(site)
    assert result.returncode != 0
