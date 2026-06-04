"""
UI State Manager - Handles saving and restoring application UI state
Persists window geometry, page state, table column widths, and search states
"""

import json
import os
from pathlib import Path
from PySide6.QtCore import QByteArray


class UIStateManager:
    """Manages persistent UI state across application sessions."""
    
    STATE_DIR = Path.home() / ".enterprise_erp"
    STATE_FILE = STATE_DIR / "ui_state.json"
    
    DEFAULT_STATE = {
        "window": {
            "x": 100,
            "y": 100,
            "width": 1400,
            "height": 850,
        },
        "current_page": 0,  # 0: dashboard, 1: customers, 2: states
        "customer_page": {
            "column_widths": {},
            "header_state": None,
            "v_header_state": None,
            "scroll_position": 0,
            "search_text": "",
        },
        "pricelist_page": {},
        "modules_page": {},
        "busbar_page": {},
        "dialog_states": {},
    }

    @classmethod
    def _serialize(cls, obj):
        """Convert non-serializable objects (like QByteArray) to JSON-friendly formats."""
        if isinstance(obj, dict):
            return {k: cls._serialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [cls._serialize(v) for v in obj]
        if isinstance(obj, QByteArray):
            return f"hex:{obj.toHex().data().decode()}"
        return obj

    @classmethod
    def _deserialize(cls, obj):
        """Convert serialized hex strings back to QByteArray."""
        if isinstance(obj, dict):
            return {k: cls._deserialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [cls._deserialize(v) for v in obj]
        if isinstance(obj, str) and obj.startswith("hex:"):
            return QByteArray.fromHex(obj[4:].encode())
        return obj
    
    @classmethod
    def _ensure_state_dir(cls):
        """Ensure state directory exists."""
        cls.STATE_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load_state(cls):
        """Load UI state from disk."""
        cls._ensure_state_dir()
        
        try:
            if cls.STATE_FILE.exists():
                with open(cls.STATE_FILE, "r") as f:
                    raw_state = json.load(f)
                    return cls._deserialize(raw_state)
        except Exception:
            pass
        
        return cls.DEFAULT_STATE.copy()

    @classmethod
    def get_dialog_state(cls, dialog_name):
        state = cls.load_state()
        dialogs = state.get("dialog_states") or {}
        return dialogs.get(dialog_name, {})

    @classmethod
    def save_dialog_state(
        cls,
        dialog_name,
        column_widths=None,
        search_text=None,
    ):
        state = cls.load_state()
        dialogs = state.get("dialog_states") or {}

        dialog_state = dialogs.get(dialog_name, {})
        if column_widths is not None:
            dialog_state["column_widths"] = column_widths
        if search_text is not None:
            dialog_state["search_text"] = search_text

        dialogs[dialog_name] = dialog_state
        state["dialog_states"] = dialogs
        cls.save_state(state)
    
    @classmethod
    def save_state(cls, state):
        """Save UI state to disk."""
        cls._ensure_state_dir()
        
        try:
            serializable_state = cls._serialize(state)
            with open(cls.STATE_FILE, "w") as f:
                json.dump(serializable_state, f, indent=2)
        except Exception:
            pass  # Silently fail if we can't save state
    
    @classmethod
    def get_window_geometry(cls):
        """Get saved window geometry."""
        state = cls.load_state()
        return state.get("window", cls.DEFAULT_STATE["window"])
    
    @classmethod
    def save_window_geometry(cls, x, y, width, height):
        """Save window geometry."""
        state = cls.load_state()
        state["window"] = {"x": x, "y": y, "width": width, "height": height}
        cls.save_state(state)
    
    @classmethod
    def get_current_page(cls):
        """Get last viewed page index."""
        state = cls.load_state()
        return state.get("current_page", 0)
    
    @classmethod
    def save_current_page(cls, page_index):
        """Save current page index."""
        state = cls.load_state()
        state["current_page"] = page_index
        cls.save_state(state)
    
    @classmethod
    def get_customer_page_state(cls):
        """Get customer page state."""
        state = cls.load_state()
        return state.get("customer_page", cls.DEFAULT_STATE["customer_page"])

    @classmethod
    def save_customer_page_state(cls, state_dict):
        state = cls.load_state()
        state["customer_page"] = state_dict
        cls.save_state(state)

    @classmethod
    def get_pricelist_page_state(cls):
        state = cls.load_state()
        return state.get("pricelist_page") or {}

    @classmethod
    def save_pricelist_page_state(cls, state_dict):
        state = cls.load_state()
        state["pricelist_page"] = state_dict
        cls.save_state(state)

    @classmethod
    def get_modules_page_state(cls):
        state = cls.load_state()
        return state.get("modules_page") or {}

    @classmethod
    def save_modules_page_state(cls, state_dict):
        state = cls.load_state()
        state["modules_page"] = state_dict
        cls.save_state(state)

    @classmethod
    def get_busbar_page_state(cls):
        state = cls.load_state()
        return state.get("busbar_page") or {}

    @classmethod
    def save_busbar_page_state(cls, state_dict):
        state = cls.load_state()
        state["busbar_page"] = state_dict
        cls.save_state(state)
