"""INDI Server Control Card Widget."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if sys.platform.startswith("linux"):
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from PyQt6 import QtCore, QtGui, QtWidgets

from card_widget import BaseCardWidget, run_card

try:
    from .driver_finder import IndiDriverFinder, IndiDriverInfo
    from .server_manager import IndiServerManager
except ImportError:
    from examples.indi_server.driver_finder import IndiDriverFinder, IndiDriverInfo
    from examples.indi_server.server_manager import IndiServerManager


class IndiServerCard(BaseCardWidget):
    """Card widget for configuring and running an INDI server."""

    def __init__(self) -> None:
        super().__init__("INDI Server", width=260, height=260)
        self._manager = IndiServerManager(self)
        self._finder = IndiDriverFinder()
        self._categorized_drivers = self._finder.get_categorized_drivers()
        
        self._presets: dict[str, list[str]] = {
            "Simulators": ["indi_simulator_ccd", "indi_simulator_telescope", "indi_simulator_focuser"],
            "ZWO Setup": ["indi_asi_ccd", "indi_asi_focuser", "indi_asi_wheel", "indi_asi_rotator"],
        }
        self._updating_tree = False
        
        self._build_ui()
        self._connect_signals()
        self._populate_tree()
        self._populate_presets()

    def _build_ui(self) -> None:
        self.content_layout.setSpacing(4)

        # 1. Top Control Bar (Start/Status Button + Port)
        top_box = QtWidgets.QHBoxLayout()
        top_box.setSpacing(6)

        self.start_button = QtWidgets.QPushButton("▶ Start Server")
        self.start_button.setFixedHeight(28)
        self.start_button.setStyleSheet(self._get_button_style("Stopped"))
        top_box.addWidget(self.start_button, 1)

        port_label = QtWidgets.QLabel("Port:")
        port_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        top_box.addWidget(port_label)

        self.port_spin = QtWidgets.QSpinBox()
        self.port_spin.setRange(1024, 65535)
        self.port_spin.setValue(7624)
        self.port_spin.setFixedWidth(56)
        self.port_spin.setFixedHeight(28)
        self.port_spin.setStyleSheet(
            "QSpinBox { background: #1e293b; color: #f8fafc; border: 1px solid #475569; border-radius: 4px; font-size: 11px; padding: 1px 2px; }"
        )
        top_box.addWidget(self.port_spin)
        self.content_layout.addLayout(top_box)

        # 2. Preset Section
        preset_layout = QtWidgets.QHBoxLayout()
        preset_layout.setSpacing(4)
        
        preset_label = QtWidgets.QLabel("Preset:")
        preset_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        preset_layout.addWidget(preset_label)

        self.preset_combo = QtWidgets.QComboBox()
        self.preset_combo.setFixedHeight(24)
        self.preset_combo.setStyleSheet(
            "QComboBox { background: #1e293b; color: #f8fafc; border: 1px solid #475569; border-radius: 4px; padding: 2px 4px; font-size: 11px; }"
            "QComboBox::drop-down { border: none; }"
            "QComboBox QAbstractItemView { background: #0f172a; color: #f8fafc; selection-background-color: #334155; }"
        )
        preset_layout.addWidget(self.preset_combo, 1)

        self.add_preset_btn = QtWidgets.QPushButton("+")
        self.add_preset_btn.setFixedSize(20, 24)
        self.add_preset_btn.setToolTip("Save current drivers as a preset")
        self.add_preset_btn.setStyleSheet("QPushButton { background: #334155; color: #f8fafc; border-radius: 3px; font-weight: bold; font-size: 11px; } QPushButton:hover { background: #475569; }")
        preset_layout.addWidget(self.add_preset_btn)

        self.del_preset_btn = QtWidgets.QPushButton("-")
        self.del_preset_btn.setFixedSize(20, 24)
        self.del_preset_btn.setToolTip("Delete current preset")
        self.del_preset_btn.setStyleSheet("QPushButton { background: #334155; color: #f8fafc; border-radius: 3px; font-weight: bold; font-size: 11px; } QPushButton:hover { background: #ef4444; }")
        preset_layout.addWidget(self.del_preset_btn)

        self.content_layout.addLayout(preset_layout)

        # 3. Filter Box
        self.filter_edit = QtWidgets.QLineEdit()
        self.filter_edit.setFixedHeight(24)
        self.filter_edit.setPlaceholderText("Filter drivers...")
        self.filter_edit.setClearButtonEnabled(True)
        self.filter_edit.setStyleSheet(
            "QLineEdit { background: #1e293b; color: #f8fafc; border: 1px solid #334155; border-radius: 4px; padding: 2px 6px; font-size: 11px; }"
        )
        self.content_layout.addWidget(self.filter_edit)

        # 4. Drivers Tree Widget
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet(
            "QTreeWidget { background: #0f172a; color: #e2e8f0; border: 1px solid #334155; border-radius: 4px; font-size: 11px; padding: 1px; }"
            "QTreeWidget::item { padding: 2px; margin: 0px; border-radius: 2px; }"
            "QTreeWidget::item:hover { background: #1e293b; }"
            "QTreeWidget::item:selected { background: #334155; color: #ffffff; }"
        )
        self.content_layout.addWidget(self.tree, 1)

        # 5. Selected Summary Label
        self.summary_label = QtWidgets.QLabel("Selected: 0 drivers")
        self.summary_label.setStyleSheet("color: #64748b; font-size: 10px;")
        self.summary_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        self.content_layout.addWidget(self.summary_label)

    def _get_button_style(self, status: str) -> str:
        base_style = "QPushButton { font-weight: bold; border-radius: 4px; font-size: 11px; padding: 0px; text-align: center; } "
        if status == "Running":
            return base_style + (
                "QPushButton { background: #c17a7a; color: #1f1414; }"
                "QPushButton:hover { background: #b06a6a; }"
                "QPushButton:pressed { background: #9f5959; }"
            )
        elif status in ("Starting...", "Stopping..."):
            return base_style + (
                "QPushButton { background: #b59f63; color: #1f1a10; }"
                "QPushButton:disabled { background: #4b5563; color: #94a3b8; }"
            )
        elif "Error" in status:
            return base_style + (
                "QPushButton { background: #b85c5c; color: #1f1010; }"
                "QPushButton:hover { background: #a74b4b; }"
            )
        else:  # Stopped
            return base_style + (
                "QPushButton { background: #7ba883; color: #14201a; }"
                "QPushButton:hover { background: #6b9873; }"
                "QPushButton:pressed { background: #5c8764; }"
            )

    def _connect_signals(self) -> None:
        self.start_button.clicked.connect(self._toggle_server)
        self._manager.status_changed.connect(self._on_status_changed)
        self.closing.connect(self._on_closing)

        self.filter_edit.textChanged.connect(self._filter_tree)
        self.tree.itemChanged.connect(self._on_tree_item_changed)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        self.add_preset_btn.clicked.connect(self._add_preset)
        self.del_preset_btn.clicked.connect(self._delete_preset)

    def _populate_tree(self) -> None:
        self.tree.blockSignals(True)
        self.tree.clear()

        for group, drivers in self._categorized_drivers.items():
            parent_item = QtWidgets.QTreeWidgetItem(self.tree)
            parent_item.setText(0, f"{group} ({len(drivers)})")
            parent_item.setFlags(
                parent_item.flags()
                | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                | QtCore.Qt.ItemFlag.ItemIsAutoTristate
            )
            parent_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
            parent_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, "group")

            # Group drivers by manufacturer within each category
            mfg_map: dict[str, list[IndiDriverInfo]] = {}
            for driver in drivers:
                mfg = driver.manufacturer.strip() if driver.manufacturer.strip() else "Generic"
                if mfg not in mfg_map:
                    mfg_map[mfg] = []
                mfg_map[mfg].append(driver)

            for mfg_name in sorted(mfg_map.keys()):
                mfg_drivers = mfg_map[mfg_name]
                mfg_item = QtWidgets.QTreeWidgetItem(parent_item)
                mfg_item.setText(0, f"{mfg_name} ({len(mfg_drivers)})")
                mfg_item.setFlags(
                    mfg_item.flags()
                    | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                    | QtCore.Qt.ItemFlag.ItemIsAutoTristate
                )
                mfg_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                mfg_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, "mfg")

                for driver in mfg_drivers:
                    child_item = QtWidgets.QTreeWidgetItem(mfg_item)
                    child_item.setText(0, f"{driver.label} ({driver.binary})")
                    child_item.setFlags(
                        child_item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                    )
                    child_item.setCheckState(0, QtCore.Qt.CheckState.Unchecked)
                    child_item.setData(0, QtCore.Qt.ItemDataRole.UserRole, driver.binary)

        self.tree.blockSignals(False)
        self._update_summary()

    def _populate_presets(self) -> None:
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("Custom", None)
        for name in sorted(self._presets.keys()):
            self.preset_combo.addItem(name, name)
        
        # Select first preset by default if available
        if self.preset_combo.count() > 1:
            self.preset_combo.setCurrentIndex(1)
            self._apply_preset(self.preset_combo.currentText())
        self.preset_combo.blockSignals(False)

    def _get_selected_drivers(self) -> list[str]:
        selected: list[str] = []

        def collect(item: QtWidgets.QTreeWidgetItem) -> None:
            data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if data and data not in ("group", "mfg"):
                if item.checkState(0) == QtCore.Qt.CheckState.Checked:
                    selected.append(data)
            else:
                for i in range(item.childCount()):
                    collect(item.child(i))

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            collect(root.child(i))
        return selected

    def _apply_preset(self, preset_name: str) -> None:
        if preset_name not in self._presets:
            return

        target_drivers = set(self._presets[preset_name])
        self._updating_tree = True
        self.tree.blockSignals(True)

        def apply(item: QtWidgets.QTreeWidgetItem) -> None:
            data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            if data and data not in ("group", "mfg"):
                state = (
                    QtCore.Qt.CheckState.Checked
                    if data in target_drivers
                    else QtCore.Qt.CheckState.Unchecked
                )
                item.setCheckState(0, state)
            else:
                for i in range(item.childCount()):
                    apply(item.child(i))

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            apply(root.child(i))

        self.tree.blockSignals(False)
        self._updating_tree = False
        self._update_summary()

    def _on_tree_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if self._updating_tree:
            return

        if not self._updating_tree:
            # Set preset combo to "Custom" when manually toggling items
            self.preset_combo.blockSignals(True)
            self.preset_combo.setCurrentIndex(0)
            self.preset_combo.blockSignals(False)

        self._update_summary()

    def _update_summary(self) -> None:
        selected = self._get_selected_drivers()
        count = len(selected)
        self.summary_label.setText(f"Selected: {count} driver{'s' if count != 1 else ''}")

    def _filter_tree(self, text: str) -> None:
        search = text.lower().strip()

        def filter_node(item: QtWidgets.QTreeWidgetItem) -> bool:
            data = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            is_leaf = data not in ("group", "mfg")

            item_text_matches = search in item.text(0).lower()

            if is_leaf:
                matches = item_text_matches if search else True
                item.setHidden(not matches)
                return matches

            has_matching_child = False
            for i in range(item.childCount()):
                if filter_node(item.child(i)):
                    has_matching_child = True

            node_matches = item_text_matches or has_matching_child if search else True
            item.setHidden(not node_matches)
            if search and node_matches:
                item.setExpanded(True)
            elif not search:
                item.setExpanded(False)

            return node_matches

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            filter_node(root.child(i))

    def _on_preset_selected(self, index: int) -> None:
        preset_name = self.preset_combo.itemText(index)
        if preset_name != "Custom":
            self._apply_preset(preset_name)

    def _add_preset(self) -> None:
        selected = self._get_selected_drivers()
        if not selected:
            QtWidgets.QMessageBox.information(self, "Preset", "Please select at least one driver first.")
            return

        name, ok = QtWidgets.QInputDialog.getText(self, "Save Preset", "Enter preset name:")
        if ok and name.strip():
            preset_name = name.strip()
            self._presets[preset_name] = selected
            self._populate_presets()
            index = self.preset_combo.findText(preset_name)
            if index >= 0:
                self.preset_combo.setCurrentIndex(index)

    def _delete_preset(self) -> None:
        preset_name = self.preset_combo.currentText()
        if preset_name == "Custom":
            return
        if preset_name in self._presets:
            del self._presets[preset_name]
            self._populate_presets()

    def _toggle_server(self) -> None:
        if self._manager.is_running():
            self._manager.stop_server()
        else:
            selected = self._get_selected_drivers()
            port = self.port_spin.value()
            self._manager.start_server(selected, port=port)

    def _on_status_changed(self, status: str) -> None:
        if status == "Running":
            self.start_button.setText("■ Stop Server")
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet(self._get_button_style("Running"))
            self.port_spin.setEnabled(False)
        elif status in ("Starting...", "Stopping..."):
            self.start_button.setText(f"⏳ {status}")
            self.start_button.setEnabled(False)
            self.start_button.setStyleSheet(self._get_button_style(status))
        elif "Error" in status:
            self.start_button.setText("⚠️ Error - Retry")
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet(self._get_button_style("Error"))
            self.port_spin.setEnabled(True)
        else:  # Stopped
            self.start_button.setText("▶ Start Server")
            self.start_button.setEnabled(True)
            self.start_button.setStyleSheet(self._get_button_style("Stopped"))
            self.port_spin.setEnabled(True)

    def _on_closing(self) -> None:
        """Handle card close event cleanly."""
        if self._manager.is_running():
            self._manager.stop_server()


if __name__ == "__main__":
    raise SystemExit(run_card(IndiServerCard, sys.argv))
