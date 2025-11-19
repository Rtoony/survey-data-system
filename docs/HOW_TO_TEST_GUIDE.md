# Survey Standards Manager (SSM) - Developer QA/QC Guide

## 🚀 I. Pipeline Overview: The Standards Resolution Process

The SSM converts raw field data into CAD entities through a complex, multi-layered pipeline. To test the system, you must validate each stage of this **deterministic process**.

1.  **Normalization (Phase 25):** Cleans data, performs unit conversions, and calculates derived attributes (e.g., DEPTH).
2.  **GKG Context Injection (Phase 32):** Injects attributes based on non-spatial intelligence (e.g., proximity to WETLAND entities).
3.  **GIS Context Layering (Phase 23):** Checks for spatial overrides (e.g., City of Santa Rosa boundary) and inserts high-priority mappings (P=999).
4.  **Mapping Resolution (Phase 33/28):** Evaluates all available mappings (Project P=9999, GIS P=999, Global P=100) using **Priority** then **Condition Specificity** (count) as a tie-breaker.
5.  **Rule Execution & Export (Phase 20/27):** Executes auto-labeling/auto-connect rules and formats the final output (e.g., Civil 3D or FXL).

---

## 🧪 II. Test Case 1: Data Normalization Check (Phase 25)

**Goal:** Verify that messy input data is cleaned, and derived values are correctly calculated.

| Input Attribute | Raw Value | Expected Output (Normalized) | Check Service |
| :--- | :--- | :--- | :--- |
| `RIM_ELEV` | `105.00` | `105.00` | Normalization |
| `INVERT_ELEV` | `99.00` | `99.00` | Normalization |
| `MATERIAL` | `conc` | `CONCRETE` | Normalization |
| **`DEPTH`** | N/A | `6.00` | **Derived Calculation** |

**Verification Method:** Use the **ScenarioTesterTool (Phase 30)** with the input data above. Check the `pipeline_log` to confirm that the `DEPTH` attribute is present and accurate *before* the mapping stage.

---

## 🗺️ III. Test Case 2: Hierarchy Resolution Check (Phases 33, 23, 28)

**Goal:** Verify that the **Project Override Layer (P=9999)** correctly overrides all other standards.

| Condition Set | Priority | Layer Name | Specificity (Conditions) | Expected Winner |
| :--- | :--- | :--- | :--- | :--- |
| Project Override (P=9999) | 9999 | **CLIENT-MH-LAYER** | 1 | **Project** |
| GIS Override (P=999) | 999 | CITY-MH-LAYER | 1 | GIS |
| Global Standard (P=300) | 300 | HIGH-SPEC-MH | 2 | Global |

**Input Data:** `{"feature_code": "SDMH", "SIZE": "48IN", "project_id": 100, "coordinates": {"x": 6550000, "y": 2050000}}`

**Expected Outcome:**
* **Resolved Mapping:** The mapping with **P=9999** is selected.
* **Final CAD Layer:** `CLIENT-MH-LAYER`
* **Verification:** Run the scenario, check the `pipeline_log` to ensure the Project Override was fetched and the `source_mapping_id` of the winner corresponds to the P=9999 rule.

---

## ⚖️ IV. Test Case 3: Conflict & Specificity Check (Phase 28)

**Goal:** Verify that when priorities are equal, the tie-breaker correctly selects the **most specific** mapping (highest condition count).

| Mapping ID | Priority | Conditions | Specificity Count | Expected Winner |
| :--- | :--- | :--- | :--- | :--- |
| **ID 301** | 300 | SIZE="60IN" AND MAT="CONC" | **2** | **ID 301** |
| ID 302 | 300 | SIZE="60IN" | 1 | ID 302 |

**Input Data:** `{"feature_code": "SDMH", "SIZE": "60IN", "MAT": "CONC"}`

**Expected Outcome:**
* **Resolved Mapping:** Mapping **ID 301** is selected.
* **Verification:** Run the scenario. Check the `pipeline_log` for the **Tie-breaker SUCCESS** message confirming that the resolution logic prioritized the specificity count of 2 over the count of 1.
