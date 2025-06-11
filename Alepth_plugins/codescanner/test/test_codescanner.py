from pathlib import Path

import pytest

from objects.file import FileObject

from ..code.codescanner import AnalysisPlugin

TEST_DATA_DIR = Path(__file__).parent / 'data'


@pytest.mark.parametrize(
    ('test_file', 'expected_result', 'type_result', 'tag'),
    [
        ('amd64.elf', 'Intel-64', 'ELF', None),
        ('arm.elf', 'Arm-32-le', 'ELF', None),
        ('hidden_arm.bin', 'Arm-32-le', 'data', 'probably_raw_binary'),
    ]
)
@pytest.mark.AnalysisPluginTestConfig(plugin_class=AnalysisPlugin)
def test_process_object(analysis_plugin, test_file, expected_result, type_result, tag):
    test_fo = FileObject(file_path=str(TEST_DATA_DIR / test_file))
    test_fo.processed_analysis['file_type'] = {'full': type_result}
    processed_file = analysis_plugin.process_object(test_fo)
    assert AnalysisPlugin.NAME in processed_file.processed_analysis
    assert processed_file.processed_analysis[AnalysisPlugin.NAME]['architecture']['Full'] == expected_result
    analysis_tags = processed_file.processed_analysis[AnalysisPlugin.NAME].get('tags')
    if tag is None:
        assert analysis_tags is None
    else:
        assert tag in analysis_tags
