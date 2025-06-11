from codescanner_analysis import CodescannerAnalysisData, ComparisonAnalysis

from analysis.PluginBase import AnalysisBasePlugin
from helperFunctions.tag import TagColor
from objects.file import FileObject
from plugins.mime_blacklists import MIME_BLACKLIST_COMPRESSED, MIME_BLACKLIST_NON_EXECUTABLE


class AnalysisPlugin(AnalysisBasePlugin):

    NAME = 'codescanner'
    DESCRIPTION = 'scan unknown binaries for executable code'
    VERSION = '1.0.1'
    DEPENDENCIES = ('file_type',)
    MIME_BLACKLIST = MIME_BLACKLIST_NON_EXECUTABLE + MIME_BLACKLIST_COMPRESSED
    FILE = __file__

    def process_object(self, file_object: FileObject) -> FileObject:
        binary = CodescannerAnalysisData(file_object.file_path)
        comparison = ComparisonAnalysis(file_object.file_path)
        result = {}

        for key in ['Full', 'ISA', 'Bitness', 'Endianess']:
            result.setdefault('architecture', {}).update({key: binary.architecture.get(key)})

        result['file_size'] = binary.sizes.get('FileSize')

        for key in ['Code', 'Ascii', 'Data', 'HighEntropy']:
            result.setdefault('sections', {}).update({
                key: {
                    'size': binary.sizes.get(key),
                    'regions': binary.regions.get(key),
                }
            })

        result['comparison'] = {
            'codescanner': comparison.cs_regions,
            'header': comparison.x_regions,
        }

        arch = result['architecture']['Full']
        if arch is not None:
            result['summary'] = [result['architecture']['Full']]
        file_object.processed_analysis[self.NAME] = result

        if arch and file_object.processed_analysis.get('file_type', {}).get('full') == 'data':
            self._add_raw_binary_tag(file_object)

        return file_object

    def _add_raw_binary_tag(self, file_object):
        self.add_analysis_tag(
            file_object=file_object,
            tag_name='probably_raw_binary',
            value='Raw Binary',
            color=TagColor.LIGHT_BLUE,
            propagate=False
        )
