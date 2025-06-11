#!/usr/bin/env python3
# pylint: disable=ungrouped-imports
import logging
from pathlib import Path

try:
    from helperFunctions.install import check_distribution
    from plugins.installer import AbstractPluginInstaller
except ImportError:
    import sys
    SRC_PATH = Path(__file__).absolute().parent.parent.parent.parent
    sys.path.append(str(SRC_PATH))

    from helperFunctions.install import check_distribution
    from plugins.installer import AbstractPluginInstaller


class CodescannerInstaller(AbstractPluginInstaller):
    base_path = Path(__file__).resolve().parent


# Alias for generic use
Installer = CodescannerInstaller

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    Installer(check_distribution()).install()
