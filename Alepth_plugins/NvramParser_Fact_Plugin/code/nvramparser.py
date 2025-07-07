import os
import json
import re
from analysis.PluginBase import AnalysisBasePlugin
from objects.file import FileObject
import uefitool  # your native binding module

class AnalysisPlugin(AnalysisBasePlugin):
    NAME = 'nvramparser'
    DESCRIPTION = 'Extract NVRAM variables using custom UEFITool parser'
    VERSION = '1.3.0'
    DEPENDENCIES = ('file_type',)
    MIME_BLACKLIST = ()
    FILE = __file__

    SPEC_JSON_PATH = os.path.join(os.path.dirname(__file__), 'spec_variables.json')

    def load_spec_variables(self):
        try:
            with open(self.SPEC_JSON_PATH, 'r', encoding='utf-8') as f:
                spec_vars = json.load(f)
            return {var['VariableName']: var for var in spec_vars}
        except Exception as e:
            self.logger.warning(f"Failed to load spec_variables.json: {e}")
            return {}

    def build_spec_patterns(self, spec_variables):
        patterns = []
        for var_name in spec_variables:
            regex = re.escape(var_name)
            regex = regex.replace(r'\#\#\#\#', r'[0-9A-Fa-f]{4}')
            regex = regex.replace(r'\#\#\#', r'[0-9A-Fa-f]{3}')
            regex = regex.replace(r'\#\#', r'[0-9A-Fa-f]{2}')
            regex = regex.replace(r'\#', r'[0-9A-Fa-f]{1}')
            regex = '^' + regex + '$'
            patterns.append((re.compile(regex), var_name))
        return patterns

    def normalize_var_name(self, var_name, spec_patterns):
        for regex, pattern_name in spec_patterns:
            if regex.match(var_name):
                return pattern_name
        return var_name

    def parse_nvram_attributes(self, attr_string):
        # Extract attributes from parentheses, e.g. "83h (Runtime, AsciiName, Valid)"
        match = re.search(r'\((.*?)\)', attr_string)
        if match:
            attrs = [a.strip() for a in match.group(1).split(',')]
            return attrs
        return []

    def process_object(self, file_object: FileObject) -> FileObject:
        result = {}

        firmware_path = file_object.file_path
        parser = uefitool.FitParser()
        spec_variables = self.load_spec_variables()
        spec_patterns = self.build_spec_patterns(spec_variables)

        try:
            if not parser.load_file(firmware_path):
                self.logger.warning(f"Failed to load firmware file: {firmware_path}")
                result['error'] = 'Failed to load firmware file'
            else:
                nvram_vars = parser.parse_nvram_variables()
                if not isinstance(nvram_vars, dict):
                    result['error'] = 'Unexpected result type from parse_nvram_variables'
                else:
                    enhanced_vars = {}
                    for var_name, var_data in nvram_vars.items():
                        attr_string = var_data.get('Attributes', '')
                        attributes = self.parse_nvram_attributes(attr_string)
                        norm_var_name = self.normalize_var_name(var_name, spec_patterns)
                        spec = spec_variables.get(norm_var_name)
                        entry = {
                            'attributes': attributes,
                            'original_attributes': attr_string,
                        }
                        if spec:
                            entry['known'] = True
                            spec_attrs = set(spec.get('Attributes', []))
                            var_attrs = set(attributes)
                            entry['spec_attributes'] = list(spec_attrs)
                            entry['attribute_match'] = (spec_attrs == var_attrs)
                        else:
                            entry['known'] = False
                            entry['spec_attributes'] = []
                            entry['attribute_match'] = False
                        enhanced_vars[var_name] = entry
                    result = enhanced_vars
        except Exception as e:
            self.logger.warning(f"Exception during NVRAM parsing: {e}")
            result['error'] = str(e)

        file_object.processed_analysis[self.NAME] = result
        return file_object
