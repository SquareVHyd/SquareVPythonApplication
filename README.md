# Square V Engineering ERP User Manual

Welcome to the Square V Engineering ERP User Manual. This comprehensive guide covers all functionalities, features, keyboard shortcuts, UI elements, and interactions available within the application.

## Table of Contents
1. [General Application Features](#general-application-features)
2. [Global Keyboard Shortcuts](#global-keyboard-shortcuts)
3. [Main Application Modules](#main-application-modules)
   - [Dashboard](#1-dashboard)
   - [Customers](#2-customers)
   - [Quotation Details](#3-quotation-details)
   - [Price List](#4-price-list)
   - [Generic Description](#5-generic-description)
   - [Modules Overview](#6-modules-overview)
   - [Busbar Materials](#7-busbar-materials)
   - [Master Data](#8-master-data)
4. [Utilities Window](#utilities-window)
5. [Tools Window](#tools-window)

---

## General Application Features
- **Searchable Tables**: Most tables in the application support filtering, column resizing, reordering, and alternating row colors.
- **In-place Editing**: You can double-click or press `Enter` on specific editable columns (like "List Price" or "Discount %") to modify them directly in the grid.
- **Status Bars**: Found at the bottom of the screens, displaying data loading status or statistics for currently selected rows (e.g., Sum of List Prices, Row Count).
- **Persistent State**: Column widths and window sizes are saved and restored upon next launch.

---

## Global Keyboard Shortcuts
These shortcuts are available globally across most data tables:
- `F1` or `Ctrl+H` : Show keyboard shortcuts help popup.
- `Ctrl+F` : Focus the search box.
- `Ctrl+R` : Refresh the current table data from the database.
- `Ctrl+N` : Add a new record.
- `Ctrl+E` : Edit the selected record.
- `Delete` : Delete the selected record.
- `Ctrl+S` : Save current table as Excel.
- `Ctrl+P` : Export current table to PDF.
- `Ctrl+Arrow Keys` : Move between rows and columns.
- `Ctrl+Space` : Select current row.
- `Ctrl+L` : Select current column.
- `Esc` : Close sub-windows (Utilities/Tools) and return to the main ERP dashboard.

---

## Main Application Modules

### 1. Dashboard
- **Description**: The default landing page.
- **Features**: 
  - Displays company information, GST number, and website links.
  - Presents an Information Grid with ERP Version, Date, and Industry type.

### 2. Customers
- **Description**: View customer information synced from Google Contacts.
- **Features**:
  - **Search**: Search by Organization Name, Email, or Phone.
  - **Context Menu (Right-Click)**: Right-click any row to select "View Contacts", which opens an `OrganizationContactsDialog` popup displaying individual contacts for the organization.

### 3. Quotation Details
- **Description**: A comprehensive hierarchical suite for managing quotations, panels, modules, and items.
- **Features**:
  - **Sidebar Options**:
    - `📄 Quotations List`: Shows all quotations.
    - `📑 Quotation Process`: Shows the hierarchical "Preview" page for managing the entire quotation structure.
    - `📊 Cost Summary`: Shows the aggregated cost breakdown for the quotation.
    - `🔌 Panels`, `📦 Panel Modules`, `📦 Used Quantity`: Manage nested entities.
  - **Quotations List Table Context Menu (Right-Click)**:
    - `📑 Quotation Process`: Opens the hierarchical manager.
    - `📦 View Module Items`: Opens Module Items viewer.
    - `🔄 Revisions`: Opens the revision history.
    - `👁️ Preview Quotation`: Opens the `QuotationPreviewDialog` to view the generated document.
  - **Double Click**: Double-click a quotation to open the Edit form.
  - **Copy / Paste**: Use `📋 Copy` and `📋 Paste` buttons to duplicate entire quotations.
  - **Quotation Process Page**:
    - **Expand/Collapse**: Buttons to collapse/expand all nested forms and panels.
    - **Quotation CTC Form**: Dropdowns to set GST, Freight, Payment terms, Warranty, etc.
    - **Common Specs Form**: Dropdowns to define material thicknesses for Frames, Doors, Partitions, etc.
    - **Panels & Modules Tree**: Add/Edit/Delete panels and nested modules inline. Calculates and displays live cost totals.

### 4. Price List
- **Description**: Central repository for all item prices and specifications.
- **Features**:
  - **Filters**: General Search, Filter by Model, Category (dropdown), and Make (dropdown).
  - **In-place Edits**: Double-click on `List Price` or `Discount %` cells to edit them directly. Net Price and Total Amount recalculate automatically.
  - **Bulk Update**: The `📦 Bulk Update` button opens a `BulkPriceUpdateDialog` to paste space-separated lists of models and prices for massive updates.
  - **Export**: `📊 Export Excel` exports the entire Price List view to a designated Excel file path.
  - **Status Bar**: Shows real-time sums of List Price, Net Price, Used Qty, and Total Amount for selected rows.

### 5. Generic Description
- **Description**: Interface to map Master generic specifications to individual Price List items.
- **Features**:
  - **Split View**: Left side shows "Generic Spec Items (Master)", right side shows "Price List Items (Detail)".
  - **Inline Editing (Left)**: Double-click Description or Remark/Makes to edit them inline.
  - **Pagination (Right)**: Use the `◀ Previous` and `Next ▶` buttons to page through price list items. Configure page size using the dropdown.
  - **Mapping Toolbar (Bottom)**:
    - `🏷️ Add Generic Item from Selection`: Creates a new Generic Item using the names of checked Price List items and maps them instantly.
    - `🔗 Assign Selected to Generic Item`: Maps checked Price List items to the selected Generic Item on the left.
    - `🔓 Remove Mapping`: Unmaps checked Price List items.

### 6. Modules Overview
- **Description**: Defines Module Types (e.g., standard assemblies) and links them to items.
- **Features**:
  - **Filters**: General Search, Filter by Module Type, Filter by Make.
  - **Double Click / Context Menu (Right-Click)**: Right-clicking or double-clicking a Module Type row and selecting "Open Module Details" opens the `ModuleItemsDialog` where you can add/remove Bill of Materials (BOM) components to the module.

### 7. Busbar Materials
- **Description**: Manages busbar inventory and performs summary analysis for panel design.
- **Features**:
  - **Split View**: Left side shows the material list; right side (hidden by default) shows Summary Analysis.
  - **Context Menu (Right-Click)**:
    - `View Busbar Summary Table`: Opens the right-side analysis pane.
    - `Metal Properties Manager`: Opens `MetalManagerDialog` to manage Metal types and densities.
    - `Sleeve Sizes Manager`: Opens `SleeveManagerDialog` to manage sleeve properties.
  - **Summary Analysis (Right Pane)**:
    - Filter by Metal, Run, Width, Thick, and Amp Range.
    - Calculates and displays Current Density, Cost/Kg, Sleeve Rs, and Final Cost.
    - Export results to Excel.

### 8. Master Data
- **Description**: Raw database viewer and generic editor for backend tables.
- **Features**:
  - **Table Selection**: Dropdown to select core tables like categories, metrics, makes.
  - **Dynamic Filters**: Text boxes appear dynamically above each column for exact filtering.
  - **CRUD Operations**: Use `Add New`, `Edit Selected`, and `Delete Selected` to perform direct database modifications using the `GenericCrudDialog`.

---

## Utilities Window
Accessed via the main sidebar's `🔧 Utilities` button, this opens a dedicated full-screen window with its own sidebar:
- **⚡ Electricity Bills**: Track and manage utility bills.
- **🏅 ZEDScoreCard**: Manage ZED metrics and scoring.
- **🚚 Timely Delivery**: Logistics and delivery tracking.
- **↩️ Back to ERP** / `Esc` key: Closes the Utilities window and returns to the Dashboard.

---

## Tools Window
Accessed via the main sidebar's `🛠️ Tools` button, this opens a dedicated full-screen window with its own sidebar:
- **🔋 Capacitor R1**: Tool for capacitor calculations.
- **📁 File Creator**: Utility to generate specific file formats.
- **🔍 File Viewer**: Internal file viewing utility.
- **📱 WhatsApp Msg**: Auto-messenger integration.
- **↩️ Back to ERP** / `Esc` key: Closes the Tools window and returns to the Dashboard.
