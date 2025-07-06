from analysis.PluginBase import AnalysisBasePlugin
from objects.file import FileObject
import uefitool  # your native binding module

class AnalysisPlugin(AnalysisBasePlugin):
    NAME = 'nvramparser'
    DESCRIPTION = 'Extract NVRAM variables using custom UEFITool parser'
    VERSION = '1.0.0'
    DEPENDENCIES = ('file_type',)
    MIME_BLACKLIST = ()
    FILE = __file__

    def process_object(self, file_object: FileObject) -> FileObject:
        result = {}

        firmware_path = file_object.file_path
        parser = uefitool.FitParser()

        try:
            if not parser.load_file(firmware_path):
                self.logger.warning(f"Failed to load firmware file: {firmware_path}")
                result['error'] = 'Failed to load firmware file'
            else:
                nvram_vars = parser.parse_nvram_variables()
                if not isinstance(nvram_vars, dict):
                    result['error'] = 'Unexpected result type from parse_nvram_variables'
                else:
                    result = nvram_vars
        except Exception as e:
            self.logger.warning(f"Exception during NVRAM parsing: {e}")
            result['error'] = str(e)

        file_object.processed_analysis[self.NAME] = result
        return file_object

