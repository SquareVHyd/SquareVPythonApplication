import re
import os

def update_quotation_page():
    path = r'f:\python_project\sqv_180062026\SquareVPythonApplication\app\ui\quotations\quotation_page.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update _on_selection_changed
    old_selection = """    def _on_selection_changed(self):
        \"\"\"Enables the Panels button and updates the detail views.\"\"\"
        selected = self.table.selectionModel().selectedRows()
        if hasattr(self.parent_quotation_details_page, 'update_panels_button_state'):
            self.parent_quotation_details_page.update_panels_button_state(len(selected) == 1)
            
        self._clear_layout(self.details_layout)
        if len(selected) == 1:
            row = selected[0].row()
            quote_id = int(self.table.item(row, 0).text())
            customer_id = int(self.table.item(row, 1).text())
            self._add_customer_details(customer_id)
            self._add_quotation_ctc_form(quote_id)
            self._add_common_specs_form(quote_id)"""

    new_selection = """    def _on_selection_changed(self):
        \"\"\"Enables the Panels button and updates the detail views.\"\"\"
        selected = self.table.selectionModel().selectedRows()
        if hasattr(self.parent_quotation_details_page, 'update_panels_button_state'):
            self.parent_quotation_details_page.update_panels_button_state(len(selected) == 1)
            
        self._clear_layout(self.details_layout)
        if len(selected) == 1:
            from PySide6.QtWidgets import QPushButton
            btn_collapse_all = QPushButton("Collapse All Forms")
            btn_collapse_all.setCheckable(True)
            btn_collapse_all.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; font-weight: bold; margin-bottom: 5px;")
            self.details_layout.addWidget(btn_collapse_all)

            row = selected[0].row()
            quote_id = int(self.table.item(row, 0).text())
            customer_id = int(self.table.item(row, 1).text())
            t1, c1 = self._add_customer_details(customer_id)
            t2, c2 = self._add_quotation_ctc_form(quote_id)
            t3, c3 = self._add_common_specs_form(quote_id)

            def toggle_all(checked):
                btn_collapse_all.setText("Expand All Forms" if checked else "Collapse All Forms")
                for t, c in [(t1, c1), (t2, c2), (t3, c3)]:
                    if t and c:
                        t.setChecked(not checked)
                        self._toggle_container(not checked, c, t)

            btn_collapse_all.clicked.connect(toggle_all)"""
    
    content = content.replace(old_selection, new_selection)

    # 2. Add return statements to the 3 form methods
    # For _add_customer_details
    content = content.replace("            self.details_layout.addWidget(group)\n        except Exception as e:\n            container_layout.addWidget(QLabel(f\"Failed to load customer details: {e}\"))\n            self.details_layout.addWidget(group)", "            self.details_layout.addWidget(group)\n            return toggle_btn, container\n        except Exception as e:\n            container_layout.addWidget(QLabel(f\"Failed to load customer details: {e}\"))\n            self.details_layout.addWidget(group)\n            return None, None")

    # For _add_quotation_ctc_form
    content = content.replace("            self.details_layout.addWidget(group)\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load CTC: {e}\"))\n            self.details_layout.addWidget(group)", "            self.details_layout.addWidget(group)\n            return toggle_btn, container\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load CTC: {e}\"))\n            self.details_layout.addWidget(group)\n            return None, None")

    # For _add_common_specs_form
    content = content.replace("            self.details_layout.addWidget(group)\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load Common Specs: {e}\"))\n            self.details_layout.addWidget(group)", "            self.details_layout.addWidget(group)\n            return toggle_btn, container\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load Common Specs: {e}\"))\n            self.details_layout.addWidget(group)\n            return None, None")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def update_quotation_preview():
    path = r'f:\python_project\sqv_180062026\SquareVPythonApplication\app\ui\quotations\quotation_preview.py'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    old_refresh = """    def refresh_view(self):
        self.status_bar.showMessage("Loading quotation data...")
        self._clear_layout(self.content_layout)
        
        self._add_customer_details(self.customer_id)
        self._add_quotation_ctc_form()
        self._add_common_specs_form()"""

    new_refresh = """    def refresh_view(self):
        self.status_bar.showMessage("Loading quotation data...")
        self._clear_layout(self.content_layout)
        
        from PySide6.QtWidgets import QPushButton
        btn_collapse_all = QPushButton("Collapse All Forms")
        btn_collapse_all.setCheckable(True)
        btn_collapse_all.setStyleSheet("background-color: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 4px; font-weight: bold; margin-bottom: 5px;")
        self.content_layout.addWidget(btn_collapse_all)
        
        t1, c1 = self._add_customer_details(self.customer_id)
        t2, c2 = self._add_quotation_ctc_form()
        t3, c3 = self._add_common_specs_form()

        def toggle_all(checked):
            btn_collapse_all.setText("Expand All Forms" if checked else "Collapse All Forms")
            for t, c in [(t1, c1), (t2, c2), (t3, c3)]:
                if t and c:
                    t.setChecked(not checked)
                    self._toggle_container(not checked, c, t)

        btn_collapse_all.clicked.connect(toggle_all)"""
    
    content = content.replace(old_refresh, new_refresh)

    # For _add_customer_details
    content = content.replace("            self.content_layout.addWidget(group)\n        except Exception as e:\n            container_layout.addWidget(QLabel(f\"Failed to load customer details: {e}\"))\n            self.content_layout.addWidget(group)", "            self.content_layout.addWidget(group)\n            return toggle_btn, container\n        except Exception as e:\n            container_layout.addWidget(QLabel(f\"Failed to load customer details: {e}\"))\n            self.content_layout.addWidget(group)\n            return None, None")

    # For _add_quotation_ctc_form
    content = content.replace("            self.content_layout.addWidget(group)\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load CTC: {e}\"))\n            self.content_layout.addWidget(group)", "            self.content_layout.addWidget(group)\n            return toggle_btn, container\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load CTC: {e}\"))\n            self.content_layout.addWidget(group)\n            return None, None")

    # For _add_common_specs_form
    content = content.replace("            self.content_layout.addWidget(group)\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load Common Specs: {e}\"))\n            self.content_layout.addWidget(group)", "            self.content_layout.addWidget(group)\n            return toggle_btn, container\n        except Exception as e:\n            container_layout.addRow(QLabel(f\"Failed to load Common Specs: {e}\"))\n            self.content_layout.addWidget(group)\n            return None, None")

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

update_quotation_page()
update_quotation_preview()
