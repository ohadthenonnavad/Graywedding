from base64 import b64encode
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional, Tuple

from codescanner_analysis import CodescannerAnalysisData, ComparisonAnalysis
from flask import render_template_string

from storage.fsorganizer import FSOrganizer
from web_interface.components.component_base import ComponentBase
from web_interface.security.decorator import roles_accepted
from web_interface.security.privileges import PRIVILEGES


class PluginRoutes(ComponentBase):
    PLOT_DPI = 120

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fso = FSOrganizer()

    def _init_component(self):
        self._app.add_url_rule('/plugins/codescanner/byte_plot/<uid>', 'plugins/codescanner/byte_plot/<uid>', self._get_byte_plot)
        self._app.add_url_rule('/plugins/codescanner/color_map/<uid>', 'plugins/codescanner/color_map/<uid>', self._get_color_map)
        self._app.add_url_rule('/plugins/codescanner/coma_plot/<uid>', 'plugins/codescanner/coma_plot/<uid>', self._get_coma_plot)

    @roles_accepted(*PRIVILEGES['view_analysis'])
    def _get_byte_plot(self, uid):
        binary = CodescannerAnalysisData(self.fso.generate_path_from_uid(uid))
        image, error = self._get_plot(binary, binary.BYTE_PLOT)
        return self._render_plot(image, error or 'byte plot')

    @roles_accepted(*PRIVILEGES['view_analysis'])
    def _get_color_map(self, uid):
        binary = CodescannerAnalysisData(self.fso.generate_path_from_uid(uid))
        image, error = self._get_plot(binary, binary.COLOR_MAP)
        return self._render_plot(image, error or 'color map')

    def _get_plot(self, binary: CodescannerAnalysisData, plot_type: int) -> Tuple[Optional[bytes], Optional[str]]:
        try:
            return binary.plot_to_buffer(dpi=self.PLOT_DPI, plot_type=plot_type), None
        except IOError as error:
            return None, str(error)

    @roles_accepted(*PRIVILEGES['view_analysis'])
    def _get_coma_plot(self, uid):
        comparison = ComparisonAnalysis(self.fso.generate_path_from_uid(uid))
        with TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / 'out.png'
            try:
                comparison.plot_to_file(str(output_file), dpi=self.PLOT_DPI)
                return self._render_plot(output_file.read_bytes(), 'comparison plot')
            except RuntimeError as error:
                return self._render_plot(None, str(error))

    @staticmethod
    def _render_plot(image: Optional[bytes], alt_text: str) -> str:
        try:
            image_src = f'data:image/png;base64,{b64encode(image).decode()}'
        except IOError as err:
            image_src = ''
            alt_text = f'Error: {str(err)}'
        template_str = f'<img style="max-width:100%;" src="{image_src}" alt="{alt_text}" />'
        return render_template_string(template_str)
