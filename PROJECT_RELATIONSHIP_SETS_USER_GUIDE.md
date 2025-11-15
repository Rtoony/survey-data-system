# **Project Relationship Sets: The Compliance Tracker That Keeps Your Engineering Projects In Sync**

*A Complete Guide for Engineers, Project Managers, and CAD Users*

---

## **What Problem Does This Solve?**

### **The AutoCAD Problem**

If you've worked in AutoCAD, you know this nightmare scenario:

1. You design a storm drain system using **Material: PVC, 12" diameter**
2. You create a **detail drawing** showing PVC connection methods
3. You add **construction notes** specifying PVC installation procedures
4. You create a **materials list** for ordering PVC pipes
5. Three months later, the engineer changes the material to **HDPE**...
6. **But forgets to update the detail, the notes, and the materials list**

**Result:** The contractor orders the wrong materials. The detail shows the wrong connection method. The inspector flags violations. **Costly mistakes.**

### **The Database Solution**

ACAD-GIS stores everything in a smart database instead of scattered DWG files. But that creates a NEW problem: **How do you track which pieces depend on each other?**

That's what **Project Relationship Sets** solves.

---

## **What Are Relationship Sets?**

Think of a Relationship Set as a **"compliance checklist"** that:

1. **Groups related elements together** (pipes, details, notes, specs, materials)
2. **Defines rules** they must follow ("all storm drains must have a material")
3. **Automatically checks** if anything is out of sync
4. **Alerts you** when something doesn't match

### **Real-World Analogy**

Imagine you're building a house:
- **Relationship Set = "Kitchen Plumbing Package"**
- **Members:** Sink, dishwasher, water supply lines, drain pipes, shut-off valves
- **Rules:** 
  - "All supply lines must have shut-off valves"
  - "Drain pipe diameter must be at least 2 inches"
  - "Dishwasher must have supply line AND drain connection"
- **Sync Check:** System verifies everything is connected and specified correctly

If you add a second sink but forget the shut-off valve → **Violation detected!**

---

## **How It Works: The Five Core Features**

### **1. Create a Relationship Set**

**What you do:** Name and describe a group of related elements

**Example:**
- **Name:** "Storm Drain System - Main St & 5th Ave"
- **Description:** "All storm infrastructure at intersection, including pipes, structures, details, and notes"
- **Category:** "Drainage Infrastructure"

**Why it matters:** This creates the container that holds all related pieces.

---

### **2. Add Members (The Elements Being Tracked)**

**Two Ways to Add Members:**

#### **Option A: Specific Elements**
"Add THIS exact storm drain, ID: SD-101"

**Use when:** You know exactly which elements to track (small, hand-picked groups)

#### **Option B: Filtered Groups**
"Add ALL storm drains where material = 'Unknown'"

**Use when:** You want to track many similar elements automatically

**The Magic:** When you select "Utility Structure" as the entity type, the system shows you ONLY the fields that make sense for structures:
- Material Type
- Structure Type
- Diameter
- Invert Elevation
- Surface Elevation
- Installation Year

**No guessing.** The system knows what fields exist and prevents typos.

---

### **3. Create Rules (The Compliance Requirements)**

This is where the **Rule Builder** comes in.

#### **Example Rule #1: "All Storm Drains Must Have Material"**

**In the Rule Builder:**
```
Rule Name: All Storm Drains Must Have Material
Entity Type: Utility Structure
Field to Check: Material Type
Check Type: Field Must Have a Value (Required)
Severity: Error
Description: Material type is required for cost estimation and procurement
```

**What this does:** Every time you run a sync check, the system looks at every storm drain structure and verifies `material_type` is not empty.

#### **Example Rule #2: "Material Must Be Approved Type"**

```
Rule Name: Approved Materials Only
Entity Type: Utility Structure
Field to Check: Material Type
Check Type: Must Be One Of (in_list)
Expected Value: PVC, DI, HDPE, RCP
Severity: Error
Description: Only these materials are approved per city standards
```

**What this does:** Verifies the material is one of the approved options.

#### **Example Rule #3: "Minimum Pipe Diameter"**

```
Rule Name: Storm Drain Minimum Diameter
Entity Type: Utility Line
Field to Check: Diameter
Check Type: Minimum Value (numeric)
Expected Value: 12
Severity: Warning
Description: City code requires minimum 12" for public storm drains
```

**What this does:** Flags any storm drain pipe smaller than 12 inches.

---

### **The 8 Check Types Explained**

| Check Type | What It Does | Example Use Case |
|------------|--------------|------------------|
| **Required** | Field must have ANY value | "All structures must have a material" |
| **Equals** | Field must match exact value | "Status must equal 'ACTIVE'" |
| **Not Equals** | Field must NOT match value | "Material must not equal 'UNKNOWN'" |
| **Contains** | Field must contain text | "Notes must contain 'approved by engineer'" |
| **In List** | Field must be one of several options | "Material must be PVC, DI, HDPE, or RCP" |
| **Min** | Numeric minimum | "Diameter must be at least 12" |
| **Max** | Numeric maximum | "Depth must not exceed 20 feet" |
| **Regex** | Pattern matching (advanced) | "Project number must match format ABC-1234" |

---

### **4. Run Sync Check (Find Problems Automatically)**

**What you do:** Click "Check Sync" button

**What happens:** The system runs **3 types of checks:**

#### **Check #1: Existence**
"Are all required members still in the database?"
- **Example:** You added Detail D-101 to the set, but someone deleted it from the database
- **Result:** **Violation** - "Missing member: Detail D-101"

#### **Check #2: Link Integrity**
"Are all connections between elements still valid?"
- **Example:** Storm drain SD-15 connects to manhole MH-7, but MH-7 was deleted
- **Result:** **Violation** - "SD-15 references non-existent structure MH-7"

#### **Check #3: Metadata Consistency** (Uses Your Rules!)
"Do all elements follow the rules you defined?"
- **Example:** Your rule says "material required", but Storm Drain SD-22 has no material
- **Result:** **Violation** - "SD-22 missing required field: material_type"

**The Output:**
```
Sync check complete!

Total violations: 8
- Existence: 1
- Link Integrity: 2
- Metadata: 5
```

---

### **5. View & Resolve Violations**

**The Violations Dashboard** shows you every problem found, organized in cards:

#### **Example Violation Card:**
```
┌─────────────────────────────────────────────────┐
│ METADATA CONSISTENCY           [OPEN]           │
│                                                  │
│ Storm Drain SD-22 is missing required field:    │
│ material_type                                    │
│                                                  │
│ Detected: Nov 15, 2025 2:30 PM                  │
│                                                  │
│ [Resolve]  [Acknowledge]                        │
└─────────────────────────────────────────────────┘
```

#### **Two Actions You Can Take:**

**[Resolve]** - "I fixed it!"
- Use when you've corrected the data in the database
- Example: You went and set material_type = "PVC" for SD-22
- Marks violation as resolved
- Turns the card green

**[Acknowledge]** - "This is okay because..."
- Use when the violation is acceptable and won't be fixed
- Example: "SD-22 is a proposed structure, material TBD by contractor"
- Adds your explanation
- Keeps a record of why it's acceptable

---

## **Real-World Workflow Example**

### **Scenario: Pavement Reconstruction Project**

You're reconstructing Main Street and need to ensure all stormwater elements are properly specified.

#### **Step 1: Create the Set**
```
Name: Main Street Storm System
Description: All storm infrastructure from 1st Ave to 10th Ave
Category: Drainage Infrastructure
```

#### **Step 2: Add Members**
**Filter Group:**
- Entity Type: Utility Line
- Where: system_type = "storm_sewer" AND street_name = "Main Street"
- **Result:** 45 storm drain pipes added

**Filter Group:**
- Entity Type: Utility Structure
- Where: structure_type IN ("catch_basin", "manhole", "cleanout") AND street_name = "Main Street"
- **Result:** 23 structures added

#### **Step 3: Create Rules**

**Rule A:**
```
Name: All Pipes Must Have Material
Entity: Utility Line
Field: material
Operator: Required
Severity: Error
```

**Rule B:**
```
Name: All Structures Need Rim Elevation
Entity: Utility Structure
Field: rim_elevation
Operator: Required
Severity: Error
```

**Rule C:**
```
Name: Approved Pipe Materials
Entity: Utility Line
Field: material
Operator: In List
Expected: PVC, HDPE, RCP
Severity: Error
```

#### **Step 4: Run Sync Check**

**Results:**
- 3 pipes missing material → **3 violations**
- 2 catch basins missing rim elevation → **2 violations**
- 1 pipe has material "CI" (cast iron, not on approved list) → **1 violation**
- **Total: 6 violations**

#### **Step 5: Fix the Problems**

**Violation 1-3:** Missing materials
- **Action:** Research as-built drawings, set material types
- **Resolution:** Mark as "Resolved"

**Violation 4-5:** Missing rim elevations
- **Action:** Field crew surveys and adds elevations
- **Resolution:** Mark as "Resolved"

**Violation 6:** Unapproved material (Cast Iron pipe)
- **Action:** Acknowledge - "Existing CI pipe to remain, approved by engineer per email 11/10/25"
- **Resolution:** Mark as "Acknowledged"

---

## **Templates: Reusable Compliance Packages**

Once you've built a great relationship set with perfect rules, you can **save it as a template**.

### **Example Templates:**

**"Standard Storm System Compliance"**
- Members: All storm pipes and structures
- Rules: Material required, approved materials only, minimum diameters
- Use on: Every storm drainage project

**"Survey Control Network"**
- Members: All survey control points
- Rules: Must have northing/easting, elevation order must be specified
- Use on: Every project that uses survey data

**"ADA Compliance Package"**
- Members: All ADA features (ramps, crosswalks, truncated domes)
- Rules: Slope requirements, width requirements, material specs
- Use on: Any project with pedestrian facilities

### **Using a Template:**
1. Click "Apply Template"
2. Select "Standard Storm System Compliance"
3. System copies all rules to your current project
4. Add project-specific members
5. Run sync check

**Time saved:** 30 minutes of rule setup → 30 seconds

---

## **Key Benefits**

### **For Project Managers:**
✅ **Automated QA/QC** - No more manual checklists  
✅ **Audit Trail** - Know exactly when violations were found and resolved  
✅ **Compliance Tracking** - Prove to clients everything meets standards  

### **For Engineers:**
✅ **Catch Mistakes Early** - Find missing specs before construction  
✅ **Change Management** - When you change material, system shows what else needs updating  
✅ **Consistency** - Same rules applied across all projects  

### **For CAD Technicians:**
✅ **Clear Requirements** - System tells you exactly what fields are required  
✅ **No Guessing** - Dropdown menus show valid options  
✅ **Instant Feedback** - Run sync check anytime to verify your work  

---

## **How It's Different from AutoCAD**

| AutoCAD Way | ACAD-GIS Relationship Sets |
|-------------|---------------------------|
| Manual checking of drawings | Automated sync checks |
| Paper checklists | Digital rules enforced by database |
| Email reminders "did you update the detail?" | System automatically detects out-of-sync details |
| Hope you remember all dependencies | System tracks all relationships |
| Fix problems after they're found in field | Catch problems before construction |

---

## **Technical Architecture (For the Curious)**

### **Truth-Driven Design**

The system doesn't have hardcoded lists of fields. Instead:

1. **filterable_entity_columns** table (in Reference Data Hub) stores:
   - What fields exist for each entity type
   - What they're called (display names)
   - What data type they are
   - Which operators are valid

2. **When you create a rule**, the system:
   - Reads filterable_entity_columns
   - Shows you ONLY valid fields for that entity type
   - Prevents typos and invalid combinations

3. **When you add vocabulary**, the system:
   - Updates filterable_entity_columns
   - New fields automatically appear in rule builder
   - No code changes needed!

**This means:** The system adapts to YOUR project's needs, not the other way around.

---

## **Getting Started Checklist**

- [ ] **1. Create your first Relationship Set**
  - Start small: Pick one system (e.g., "Storm drains on Elm Street")
  
- [ ] **2. Add members**
  - Use filtered groups for efficiency
  
- [ ] **3. Create 1-2 simple rules**
  - Start with "required" checks (easiest)
  
- [ ] **4. Run sync check**
  - See what violations are found
  
- [ ] **5. Resolve violations**
  - Practice using Resolve vs Acknowledge
  
- [ ] **6. Save as template**
  - Reuse on next similar project

---

## **Common Questions**

**Q: How many relationship sets can I create?**  
A: Unlimited. Create one per subsystem, per contract package, per review milestone—whatever makes sense for your workflow.

**Q: Can one element be in multiple sets?**  
A: Yes! A storm drain can be in "Main St Storm System" AND "Q1 2025 Construction Package" AND "Material Compliance Check."

**Q: What happens if I delete an element that's in a set?**  
A: The next sync check will flag it as a violation (Existence check failed). You can then remove it from the set or restore it.

**Q: Can I export violations to share with contractors?**  
A: Not yet, but this is a planned enhancement.

**Q: Do rules run automatically, or do I trigger them?**  
A: You trigger them by clicking "Check Sync." Run it before milestones, before submittals, or anytime you want to verify compliance.

---

## **Success Story Example**

**Before Relationship Sets:**
- Project had 847 storm drain structures
- Engineer changed 23 structures from PVC to HDPE
- Manually searched for affected details, notes, and specs
- Missed 4 details that still showed PVC connections
- Contractor built using wrong detail
- $12,000 rework cost

**After Relationship Sets:**
- Created "Storm Drain Materials" relationship set
- Added rule: "If material = HDPE, must reference Detail D-HDPE-CONNECTION"
- Changed 23 structures to HDPE
- Ran sync check
- **System immediately flagged 23 violations:** "Structure uses HDPE but references PVC detail"
- Updated all references in 15 minutes
- **$12,000 saved**

---

## **Bottom Line**

**Project Relationship Sets** transforms your engineering database from a **dumb storage container** into a **smart compliance system** that:

✅ Knows which elements depend on each other  
✅ Enforces your rules automatically  
✅ Catches mistakes before they become expensive problems  
✅ Provides an audit trail for QA/QC  
✅ Adapts to your project's unique requirements  

**Think of it as an intelligent checklist that never forgets, never gets tired, and checks itself automatically.**

---

*Document Version: 1.0*  
*Last Updated: November 15, 2025*  
*ACAD-GIS System Documentation*
