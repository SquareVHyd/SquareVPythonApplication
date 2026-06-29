import os

file_path = r'f:\python_project\sqv_180062026\SquareVPythonApplication\app\ui\quotations\module_items\module_items_viewer_dialog.py'

style = '''
        btn_style = \"\"\"
            QPushButton {
                background-color: #f1f5f9;
                color: #0f172a;
                border: 1px solid #cbd5e1;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #e0f2fe; }
            QPushButton:pressed { background-color: #e2e8f0; }
            QPushButton:disabled { background-color: transparent; color: #94a3b8; border: none; }
            QComboBox {
                background-color: white;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                padding: 5px 12px;
                font-size: 13px;
                color: #0f172a;
            }
            QComboBox::drop-down {
                border-left: 1px solid #cbd5e1;
                width: 24px;
            }
        \"\"\"
        self.setStyleSheet(self.styleSheet() + btn_style)
'''

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'border: 1px solid #cbd5e1;' not in content:
    new_content = content.replace("    def setup_ui(self):\n        layout = QVBoxLayout(self)", "    def setup_ui(self):\n        layout = QVBoxLayout(self)\n" + style)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print(f"Updated {file_path}")
else:
    print("Already updated.")
