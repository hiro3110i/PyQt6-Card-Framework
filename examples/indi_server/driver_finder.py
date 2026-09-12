"""INDI driver discovery tool.

Parses INDI XML driver definition files and maps them to installed binaries.
"""

from __future__ import annotations

import os
import shutil
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


@dataclass
class IndiDriverInfo:
    binary: str
    label: str
    group: str
    manufacturer: str = ""
    version: str = ""


class IndiDriverFinder:
    """Finds installed INDI driver binaries and enriches them with metadata from XML files."""

    def __init__(
        self,
        xml_dirs: list[Path | str] | None = None,
        bin_dirs: list[Path | str] | None = None,
    ) -> None:
        self.xml_dirs = [
            Path(p) for p in (xml_dirs or ["/usr/share/indi", "/usr/local/share/indi"])
        ]
        self.bin_dirs = [
            Path(p) for p in (bin_dirs or ["/usr/bin", "/usr/local/bin"])
        ]

    def find_installed_binaries(self) -> set[str]:
        """Find all `indi_*` executable binary names present on the system."""
        binaries: set[str] = set()
        
        # Check explicit directories
        for d in self.bin_dirs:
            if d.is_dir():
                for p in d.glob("indi_*"):
                    if p.is_file() and os.access(p, os.X_OK):
                        binaries.add(p.name)

        # Check PATH as well
        path_env = os.environ.get("PATH", "")
        for path_dir in path_env.split(os.pathsep):
            p_dir = Path(path_dir)
            if p_dir.is_dir():
                for p in p_dir.glob("indi_*"):
                    if p.is_file() and os.access(p, os.X_OK):
                        binaries.add(p.name)

        # Exclude server core / helper binaries that are not individual drivers
        helpers = {
            "indiserver",
            "indi_eval",
            "indi_getxml",
            "indi_setprop",
            "indi_fifo",
        }
        return binaries - helpers

    def parse_xml_files(self) -> tuple[dict[str, IndiDriverInfo], list[IndiDriverInfo]]:
        """Parse all XML files in xml_dirs and return (binary_to_info map, list_of_all_driver_infos)."""
        binary_map: dict[str, IndiDriverInfo] = {}
        driver_list: list[IndiDriverInfo] = []

        xml_files: list[Path] = []
        for xml_dir in self.xml_dirs:
            if xml_dir.is_dir():
                xml_files.extend(xml_dir.glob("*.xml"))

        for xml_file in xml_files:
            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()
                if root.tag != "driversList":
                    continue
                for dev_group in root.findall("devGroup"):
                    group_name = dev_group.attrib.get("group", "Other")
                    for device in dev_group.findall("device"):
                        device_label = device.attrib.get("label", "")
                        manufacturer = device.attrib.get("manufacturer", "")
                        driver_elem = device.find("driver")
                        version_elem = device.find("version")
                        
                        if driver_elem is not None and driver_elem.text:
                            binary_name = driver_elem.text.strip()
                            version = version_elem.text.strip() if version_elem is not None and version_elem.text else ""
                            label = device_label or driver_elem.attrib.get("name", binary_name)
                            
                            info = IndiDriverInfo(
                                binary=binary_name,
                                label=label,
                                group=group_name,
                                manufacturer=manufacturer,
                                version=version,
                            )
                            driver_list.append(info)
                            if binary_name not in binary_map:
                                binary_map[binary_name] = info
            except Exception:
                continue

        return binary_map, driver_list

    def get_categorized_drivers(self) -> dict[str, list[IndiDriverInfo]]:
        """Returns a dict mapping group names to lists of installed IndiDriverInfo objects."""
        installed_binaries = self.find_installed_binaries()
        binary_map, _ = self.parse_xml_files()

        result: dict[str, list[IndiDriverInfo]] = {}

        for binary in sorted(installed_binaries):
            if binary in binary_map:
                info = binary_map[binary]
            else:
                # Binary without XML definition
                clean_name = binary.removeprefix("indi_")
                label = clean_name.replace("_", " ").title()
                info = IndiDriverInfo(
                    binary=binary,
                    label=label,
                    group="Uncategorized",
                )

            if info.group not in result:
                result[info.group] = []
            result[info.group].append(info)

        # Sort drivers within each group by label
        for group in result:
            result[group].sort(key=lambda d: d.label.lower())

        # Sort groups in a preferred order if present
        preferred_order = [
            "Simulators",
            "Telescopes",
            "CCDs",
            "Focusers",
            "Filter Wheels",
            "Domes",
            "Rotators",
            "Auxiliary",
            "Spectrographs",
            "Alignment",
            "Uncategorized",
        ]
        
        sorted_result: dict[str, list[IndiDriverInfo]] = {}
        for group in preferred_order:
            if group in result:
                sorted_result[group] = result.pop(group)
        # Add any remaining groups
        for group in sorted(result.keys()):
            sorted_result[group] = result[group]

        return sorted_result


if __name__ == "__main__":
    finder = IndiDriverFinder()
    categorized = finder.get_categorized_drivers()
    for g, drivers in categorized.items():
        print(f"=== {g} ({len(drivers)}) ===")
        for d in drivers[:3]:
            print(f"  - {d.label} ({d.binary}) [{d.manufacturer}]")
        if len(drivers) > 3:
            print(f"  ... and {len(drivers) - 3} more")
