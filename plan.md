# Forest Health Dashboard Enhancement Plan

## Current Architecture Analysis

### Backend (Flask)
- **app.py**: Main Flask app with blueprints (dashboard, ndvi, etc.)
- **dashboard.py**: Handles `/dashboard/filtered-data`, `/dashboard/policy-results`, etc. RFDI calculation already implemented in `compute_s1_features()`.
- **analysis.py**: Handles `/ndvi/api/s1/trend` for RFDI trend data.

### Frontend (Node.js + EJS)
- **server.js**: Express server proxying to Flask, serving EJS templates.
- **views/dashboard.ejs**: Main dashboard template with filters, cards, and RFDI chart.
- **JavaScript**: Client-side logic for loading data, updating UI, Chart.js for graphs.

### Data Flow
1. Filters trigger `loadFilteredData()` → `/filtered-data` (Flask) → returns filtered data with alert_count.
2. RFDI trend: `loadNdviTrend()` → `/api/s1/trend` (Flask) → aggregated RFDI by year/month.
3. Summary cards updated from `dashboardData` (currently empty) and `alertsCount`.

## Implementation Plan

### 1. RFDI-based Forest Health Card
**Goal**: Show health metric based on RFDI alerts for selected forest(s).

**Changes**:
- **Backend**: Add new endpoint `/dashboard/forest-health` in dashboard.py to calculate health as (1 - alert_ratio) * 100, where alert_ratio = alerts / total_records for selected forest(s).
- **Frontend**: Modify `updateSummaryCards()` to fetch and display RFDI-based health instead of empty dashboardData.

**Formula**: Health % = (1 - (alert_count / total_records)) * 100 (since alerts indicate threats, lower alert ratio means healthier forest).

### 2. Monitored Areas Card Update
**Goal**: Show count of selected forests, or total forests if "All" selected.

**Changes**:
- **Frontend**: Update `updateSummaryCards()` to count selected forests from filter.
- If forestFilter.value === "", count total unique forests from data.
- Else, count selected forests (after implementing multi-select).

### 3. Multi-Select Filters
**Goal**: Allow selecting multiple forests in filter dropdown.

**Changes**:
- **Frontend**: Change forest filter from `<select>` to multi-select component (e.g., checkboxes or multi-select library).
- Update `loadFilteredData()` to handle array of selected forests.
- **Backend**: Modify `/dashboard/filtered-data` and `/ndvi/api/s1/trend` to accept multiple forests (comma-separated or array).

### 4. Comparison Trend Graph
**Goal**: Show multiple lines for selected forests.

**Changes**:
- **Backend**: Update `/ndvi/api/s1/trend` to return data grouped by forest when multiple selected.
- **Frontend**: Modify `renderNdviChart()` to handle multiple datasets, one per forest.
- Update chart options for multiple lines with different colors and legend.

## Detailed Implementation Steps

### Backend Changes (dashboard.py)

1. **Add forest health endpoint**:
   ```python
   @dashboard_bp.route("/forest-health", methods=["GET"])
   def get_forest_health():
       forest_filter = request.args.get("forests")  # comma-separated
       # Calculate average RFDI for selected forests
       # Return health percentage
   ```

2. **Update filtered-data endpoint**:
   - Accept `forests` parameter as comma-separated list.
   - Filter df_new by multiple forests if provided.

3. **Update analysis.py s1_trend endpoint**:
   - Accept `forests` parameter.
   - Return data grouped by forest for multiple selections.

### Frontend Changes (dashboard.ejs)

1. **Update forest filter**:
   - Replace single select with multi-select (use select multiple or custom component).
   - Update `populateFilters()` to handle multi-select.

2. **Update loadFilteredData()**:
   - Collect selected forests as array.
   - Send as comma-separated string to backend.

3. **Update updateSummaryCards()**:
   - Fetch forest health from new endpoint.
   - Update monitored areas count based on selected forests.

4. **Update renderNdviChart()**:
   - Handle array of datasets for multiple forests.
   - Add colors and labels for each forest.

## API Changes

- `/dashboard/forest-health?forests=forest1,forest2` → `{"health": 75.5}`
- `/dashboard/filtered-data?forests=forest1,forest2&...` → existing format
- `/ndvi/api/s1/trend?forests=forest1,forest2&...` → `[{"year":2023,"month":1,"forest":"forest1","RFDI":0.3}, ...]`

## Testing

1. Test single forest selection (existing functionality preserved).
2. Test multiple forest selection and comparison graph.
3. Test "All Forests" selection shows total count.
4. Test RFDI health calculation accuracy.
5. Test filter persistence and data loading.

## Dependencies

- No new dependencies needed.
- Chart.js already supports multiple datasets.
- Multi-select can be implemented with HTML select multiple or library like Select2.