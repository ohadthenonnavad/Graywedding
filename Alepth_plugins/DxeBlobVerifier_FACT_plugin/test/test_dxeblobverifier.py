from pathlib import Path
import pytest

from objects.file import FileObject
from ..code.dxeblobverifier import AnalysisPlugin

TEST_DATA_DIR = Path(__file__).parent / 'data'

@pytest.mark.AnalysisPluginTestConfig(plugin_class=AnalysisPlugin)
def test_process_object(analysis_plugin):
    test_fo = FileObject(file_path=str(TEST_DATA_DIR / 'firmware_sample.bin'))
    test_fo.processed_analysis['file_type'] = {'full': 'data'}
    processed_file = analysis_plugin.process_object(test_fo)
    assert AnalysisPlugin.NAME in processed_file.processed_analysis
