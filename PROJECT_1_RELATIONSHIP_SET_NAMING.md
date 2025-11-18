# Project 1: Relationship Set Naming Templates - Truth-Driven Quick Win

## Executive Summary
Complete the truth-driven architecture for Project Relationship Sets by implementing the database-backed naming template system. Build CRUD UI for the existing `relationship_set_naming_templates` table and replace free-text Set Name/Short Code inputs with template-based selection and token replacement. This 2-week quick win eliminates naming inconsistencies and completes a critical gap identified in Phase 1.

## Current State Assessment

### ✅ What Exists
1. **Database Table**: `relationship_set_naming_templates` table fully designed and created
2. **Relationship Sets System**: Comprehensive dependency tracking with 8 operators, violation detection, rule builder
3. **Filterable Columns Registry**: Truth-driven metadata column system via `filterable_entity_columns`
4. **Template Data Model**: Complete schema with format strings, tokens, examples

### ⚠️ What's Missing (PLANNED but not implemented)
1. **CRUD Interface**: No UI to manage naming templates
2. **Template Selection**: Relationship Sets still use free-text `set_name` and `short_code` fields
3. **Token Replacement**: No UI for selecting templates and filling in tokens
4. **Template Preview**: No live preview of generated names before saving

### 📊 Current Workflow (Free-Text - Inconsistent)
```
User creates Relationship Set
→ Types free-text "Set Name" (e.g., "Storm Drainage System")
→ Types free-text "Short Code" (e.g., "SD-SYS" or "STORM-1" or "SD_SYSTEM")
→ No consistency enforcement
→ Searching/filtering becomes difficult
```

### 🎯 Target Workflow (Template-Based - Consistent)
```
User creates Relationship Set
→ Selects template from dropdown (e.g., "Utility System Standard")
→ System shows format: "{UTILITY_TYPE}-{SYSTEM_AREA}-SYSTEM"
→ User fills tokens: UTILITY_TYPE=STORM, SYSTEM_AREA=BASIN-A
→ Preview shows: "STORM-BASIN-A-SYSTEM" (Set Name) / "SD-BA" (Short Code)
→ Saves with consistent, predictable naming
```

## Goals & Objectives

### Primary Goals
1. **Build Naming Templates Manager**: Full CRUD interface in Reference Data Hub
2. **Implement Template Selection**: Replace free-text inputs in Relationship Sets UI
3. **Token Replacement System**: Interactive form for filling template tokens
4. **Live Preview**: Real-time name generation before saving
5. **Migration Path**: Convert existing free-text names to template-based (optional)

### Success Metrics
- Naming Templates CRUD interface operational
- 100% of new Relationship Sets use template-based naming
- Zero free-text inputs for Set Name/Short Code
- Template library contains 10+ common patterns
- User documentation with template examples

## Technical Architecture

### Database Schema (Already Exists)

```sql
-- Table: relationship_set_naming_templates
CREATE TABLE relationship_set_naming_templates (
    template_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_name VARCHAR(100) NOT NULL,           -- "Utility System Standard"
    category VARCHAR(50),                           -- "UTILITIES", "SITE", "SURVEY"
    format_string VARCHAR(200) NOT NULL,            -- "{UTILITY_TYPE}-{SYSTEM_AREA}-SYSTEM"
    short_code_format VARCHAR(50),                  -- "{UT}-{SA}" (abbreviated)
    token_definitions JSONB,                        -- {"UTILITY_TYPE": {...}, "SYSTEM_AREA": {...}}
    example_output VARCHAR(200),                    -- "STORM-BASIN-A-SYSTEM"
    usage_instructions TEXT,
    display_order INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### Token Definitions JSONB Structure
```json
{
  "UTILITY_TYPE": {
    "label": "Utility Type",
    "type": "dropdown",
    "options": ["STORM", "SEWER", "WATER", "RECLAIM"],
    "required": true,
    "help_text": "Primary utility system type"
  },
  "SYSTEM_AREA": {
    "label": "System Area",
    "type": "text",
    "max_length": 20,
    "required": true,
    "help_text": "Geographic area or basin identifier"
  },
  "PHASE": {
    "label": "Project Phase",
    "type": "dropdown",
    "options": ["NEW", "REHAB", "REPLACEMENT"],
    "required": false
  }
}
```

### Frontend Components

#### 1. Naming Templates Manager (New File)
**File**: `templates/reference_data/relationship_set_naming_templates.html`

```html
{% extends "base.html" %}
{% block content %}
<div class="reference-data-container">
    <div class="header-section">
        <h1><i class="fas fa-tag"></i> Relationship Set Naming Templates</h1>
        <p class="subtitle">Define reusable naming standards for project relationship sets</p>
        <button class="btn-primary" onclick="showAddModal()">
            <i class="fas fa-plus"></i> New Template
        </button>
    </div>

    <!-- Templates Table -->
    <div class="data-table-container">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Template Name</th>
                    <th>Category</th>
                    <th>Format String</th>
                    <th>Example Output</th>
                    <th>Active</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="templatesTableBody">
                <!-- Populated via JavaScript -->
            </tbody>
        </table>
    </div>

    <!-- Add/Edit Modal -->
    <div id="templateModal" class="modal">
        <div class="modal-content modal-large">
            <h2 id="modalTitle">Add Naming Template</h2>
            <form id="templateForm">
                <div class="form-row">
                    <div class="form-group">
                        <label>Template Name *</label>
                        <input type="text" id="template_name" required>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select id="category">
                            <option value="UTILITIES">Utilities</option>
                            <option value="SITE">Site Work</option>
                            <option value="SURVEY">Survey</option>
                            <option value="GRADING">Grading</option>
                            <option value="GENERAL">General</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Format String * <i class="fas fa-info-circle" title="Use {TOKEN_NAME} for replaceable values"></i></label>
                        <input type="text" id="format_string" placeholder="{UTILITY_TYPE}-{AREA}-SYSTEM" required>
                    </div>
                    <div class="form-group">
                        <label>Short Code Format</label>
                        <input type="text" id="short_code_format" placeholder="{UT}-{A}">
                    </div>
                </div>

                <div class="form-group">
                    <label>Token Definitions (JSON)</label>
                    <textarea id="token_definitions" rows="10" placeholder='{"UTILITY_TYPE": {"label": "Utility Type", "type": "dropdown", "options": [...]}}'></textarea>
                    <button type="button" class="btn-secondary btn-sm" onclick="showTokenBuilder()">
                        <i class="fas fa-wrench"></i> Token Builder
                    </button>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>Example Output</label>
                        <input type="text" id="example_output" placeholder="STORM-BASIN-A-SYSTEM">
                    </div>
                    <div class="form-group">
                        <label>Display Order</label>
                        <input type="number" id="display_order" value="1">
                    </div>
                </div>

                <div class="form-group">
                    <label>Usage Instructions</label>
                    <textarea id="usage_instructions" rows="3" placeholder="Use this template for utility system relationship sets..."></textarea>
                </div>

                <div class="form-group">
                    <label>
                        <input type="checkbox" id="is_active" checked>
                        Active
                    </label>
                </div>

                <div class="modal-actions">
                    <button type="submit" class="btn-primary">Save Template</button>
                    <button type="button" class="btn-secondary" onclick="closeModal()">Cancel</button>
                </div>
            </form>
        </div>
    </div>
</div>
{% endblock %}
```

#### 2. Updated Relationship Sets Form
**File**: `templates/tools/project_relationship_sets.html` (modify existing)

```html
<!-- OLD: Free-text inputs -->
<div class="form-group">
    <label>Set Name *</label>
    <input type="text" id="set_name" required>
</div>
<div class="form-group">
    <label>Short Code *</label>
    <input type="text" id="short_code" required>
</div>

<!-- NEW: Template-based system -->
<div class="form-group">
    <label>Naming Template *</label>
    <select id="naming_template_id" onchange="loadTemplateTokens()">
        <option value="">Select a template...</option>
        <!-- Populated from relationship_set_naming_templates -->
    </select>
    <span class="help-text">Choose a standard naming pattern</span>
</div>

<div id="tokenFieldsContainer" style="display: none;">
    <!-- Dynamically generated based on selected template -->
    <h3>Template Parameters</h3>
    <div id="tokenFields"></div>
    
    <div class="name-preview">
        <strong>Generated Name:</strong> <span id="namePreview">-</span><br>
        <strong>Short Code:</strong> <span id="shortCodePreview">-</span>
    </div>
</div>

<!-- Hidden fields to store final values -->
<input type="hidden" id="set_name">
<input type="hidden" id="short_code">
```

### Backend API Endpoints

#### Flask Routes (app.py)

```python
# ==========================================
# RELATIONSHIP SET NAMING TEMPLATES API
# ==========================================

@app.route('/api/relationship-set-naming-templates', methods=['GET'])
def get_naming_templates():
    """Get all naming templates"""
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                template_id, template_name, category, format_string,
                short_code_format, token_definitions, example_output,
                usage_instructions, display_order, is_active,
                created_at, updated_at
            FROM relationship_set_naming_templates
            WHERE is_active = true
            ORDER BY display_order, template_name
        """)
        
        templates = cur.fetchall()
        cur.close()
        conn.close()
        
        return jsonify([dict(row) for row in templates])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/relationship-set-naming-templates', methods=['POST'])
def create_naming_template():
    """Create new naming template"""
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Validate format string contains tokens
        format_string = data['format_string']
        if '{' not in format_string or '}' not in format_string:
            return jsonify({'error': 'Format string must contain at least one token (e.g., {TOKEN_NAME})'}), 400
        
        # Parse and validate token definitions
        token_definitions = data.get('token_definitions', {})
        if isinstance(token_definitions, str):
            token_definitions = json.loads(token_definitions)
        
        cur.execute("""
            INSERT INTO relationship_set_naming_templates (
                template_name, category, format_string, short_code_format,
                token_definitions, example_output, usage_instructions,
                display_order, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING template_id
        """, (
            data['template_name'],
            data.get('category'),
            format_string,
            data.get('short_code_format'),
            json.dumps(token_definitions),
            data.get('example_output'),
            data.get('usage_instructions'),
            data.get('display_order', 1),
            data.get('is_active', True)
        ))
        
        template_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'template_id': template_id, 'message': 'Template created successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/relationship-set-naming-templates/<template_id>', methods=['PUT'])
def update_naming_template(template_id):
    """Update existing naming template"""
    try:
        data = request.json
        conn = get_db_connection()
        cur = conn.cursor()
        
        token_definitions = data.get('token_definitions', {})
        if isinstance(token_definitions, str):
            token_definitions = json.loads(token_definitions)
        
        cur.execute("""
            UPDATE relationship_set_naming_templates
            SET template_name = %s,
                category = %s,
                format_string = %s,
                short_code_format = %s,
                token_definitions = %s,
                example_output = %s,
                usage_instructions = %s,
                display_order = %s,
                is_active = %s,
                updated_at = NOW()
            WHERE template_id = %s
        """, (
            data['template_name'],
            data.get('category'),
            data['format_string'],
            data.get('short_code_format'),
            json.dumps(token_definitions),
            data.get('example_output'),
            data.get('usage_instructions'),
            data.get('display_order', 1),
            data.get('is_active', True),
            template_id
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'message': 'Template updated successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/relationship-set-naming-templates/<template_id>/preview', methods=['POST'])
def preview_template_name(template_id):
    """Preview generated name from template with provided token values"""
    try:
        token_values = request.json  # {"UTILITY_TYPE": "STORM", "AREA": "BASIN-A"}
        
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT format_string, short_code_format
            FROM relationship_set_naming_templates
            WHERE template_id = %s
        """, (template_id,))
        
        template = cur.fetchone()
        cur.close()
        conn.close()
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        # Replace tokens in format string
        set_name = template['format_string']
        short_code = template['short_code_format'] or ''
        
        for token_name, token_value in token_values.items():
            set_name = set_name.replace(f'{{{token_name}}}', str(token_value))
            short_code = short_code.replace(f'{{{token_name}}}', str(token_value))
        
        return jsonify({
            'set_name': set_name,
            'short_code': short_code
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

### JavaScript Token Replacement Logic

```javascript
// File: static/js/relationship_set_naming.js

let currentTemplate = null;

async function loadTemplateTokens() {
    const templateId = document.getElementById('naming_template_id').value;
    
    if (!templateId) {
        document.getElementById('tokenFieldsContainer').style.display = 'none';
        return;
    }
    
    try {
        const response = await fetch(`/api/relationship-set-naming-templates/${templateId}`);
        currentTemplate = await response.json();
        
        // Show token fields container
        document.getElementById('tokenFieldsContainer').style.display = 'block';
        
        // Generate token input fields
        const tokenFields = document.getElementById('tokenFields');
        tokenFields.innerHTML = '';
        
        const tokenDefs = currentTemplate.token_definitions || {};
        
        for (const [tokenName, tokenDef] of Object.entries(tokenDefs)) {
            const fieldDiv = document.createElement('div');
            fieldDiv.className = 'form-group';
            
            const label = document.createElement('label');
            label.textContent = tokenDef.label + (tokenDef.required ? ' *' : '');
            fieldDiv.appendChild(label);
            
            let input;
            if (tokenDef.type === 'dropdown') {
                input = document.createElement('select');
                input.innerHTML = '<option value="">Select...</option>';
                tokenDef.options.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt;
                    option.textContent = opt;
                    input.appendChild(option);
                });
            } else {
                input = document.createElement('input');
                input.type = 'text';
                if (tokenDef.max_length) {
                    input.maxLength = tokenDef.max_length;
                }
            }
            
            input.id = `token_${tokenName}`;
            input.dataset.tokenName = tokenName;
            input.required = tokenDef.required || false;
            input.onchange = updateNamePreview;
            
            fieldDiv.appendChild(input);
            
            if (tokenDef.help_text) {
                const helpText = document.createElement('span');
                helpText.className = 'help-text';
                helpText.textContent = tokenDef.help_text;
                fieldDiv.appendChild(helpText);
            }
            
            tokenFields.appendChild(fieldDiv);
        }
        
        updateNamePreview();
    } catch (error) {
        console.error('Error loading template:', error);
        alert('Failed to load template details');
    }
}

async function updateNamePreview() {
    if (!currentTemplate) return;
    
    // Collect token values
    const tokenValues = {};
    const tokenInputs = document.querySelectorAll('[data-token-name]');
    
    tokenInputs.forEach(input => {
        const tokenName = input.dataset.tokenName;
        tokenValues[tokenName] = input.value;
    });
    
    try {
        const response = await fetch(`/api/relationship-set-naming-templates/${currentTemplate.template_id}/preview`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(tokenValues)
        });
        
        const preview = await response.json();
        
        document.getElementById('namePreview').textContent = preview.set_name;
        document.getElementById('shortCodePreview').textContent = preview.short_code;
        
        // Update hidden fields
        document.getElementById('set_name').value = preview.set_name;
        document.getElementById('short_code').value = preview.short_code;
    } catch (error) {
        console.error('Error previewing name:', error);
    }
}
```

## Implementation Phases

### Phase 1: CRUD Interface (Week 1, Days 1-3)

**Deliverables**:
1. Create `templates/reference_data/relationship_set_naming_templates.html`
2. Implement Flask API routes (GET, POST, PUT, DELETE)
3. Add navigation link in Reference Data Hub menu
4. JavaScript for table display, add/edit modals
5. Basic validation (format string must contain tokens)

**Testing**:
- Create 5 test templates (Utilities, Site, Survey, Grading, General)
- Update/edit existing templates
- Soft delete (set `is_active = false`)
- Verify JSON token definitions stored correctly

### Phase 2: Token Builder UI (Week 1, Days 4-5)

**Deliverables**:
1. Visual token definition builder (avoids manual JSON)
2. Add/remove tokens
3. Configure token type (dropdown, text, number)
4. Set dropdown options
5. Mark required fields
6. Auto-generate example JSON

**Testing**:
- Build complex token definition via UI
- Verify JSON structure matches expected format
- Test dropdown options rendering

### Phase 3: Template Selection in Relationship Sets (Week 2, Days 1-2)

**Deliverables**:
1. Modify `project_relationship_sets.html`
2. Replace free-text inputs with template dropdown
3. Add `naming_template_id` column to `relationship_sets` table
4. Dynamically generate token input fields based on template
5. Store token values in `relationship_sets.metadata` JSONB

**Database Migration**:
```sql
ALTER TABLE relationship_sets 
    ADD COLUMN naming_template_id UUID REFERENCES relationship_set_naming_templates(template_id);

-- Store user-provided token values for future reference
UPDATE relationship_sets 
SET metadata = COALESCE(metadata, '{}'::jsonb) || 
    jsonb_build_object('naming_tokens', '{}'::jsonb);
```

### Phase 4: Live Preview & Validation (Week 2, Days 3-4)

**Deliverables**:
1. Real-time name preview as user fills tokens
2. Validate all required tokens filled
3. Preview API endpoint
4. Client-side token replacement
5. Character limit warnings

**Testing**:
- Select template, fill tokens, verify preview updates
- Submit form with incomplete required tokens (should block)
- Test with various token combinations

### Phase 5: Documentation & Migration (Week 2, Day 5)

**Deliverables**:
1. User guide with template examples
2. Admin documentation for creating new templates
3. Optional: Migration script to analyze existing free-text names and suggest templates
4. Seed 10+ common templates for immediate use

**Seed Templates**:
```sql
INSERT INTO relationship_set_naming_templates (template_name, category, format_string, short_code_format, token_definitions, example_output) VALUES
('Utility System Standard', 'UTILITIES', '{UTILITY_TYPE}-{AREA}-SYSTEM', '{UT}-{A}', 
 '{"UTILITY_TYPE": {"label": "Utility Type", "type": "dropdown", "options": ["STORM", "SEWER", "WATER"], "required": true}, "AREA": {"label": "Area", "type": "text", "max_length": 20, "required": true}}',
 'STORM-BASIN-A-SYSTEM'),
 
('BMP Treatment Train', 'SITE', '{BMP_TYPE}-{TREATMENT_SEQUENCE}', '{BT}-{TS}',
 '{"BMP_TYPE": {"label": "BMP Type", "type": "dropdown", "options": ["BIOSWALE", "BASIN", "FILTER"], "required": true}, "TREATMENT_SEQUENCE": {"label": "Treatment Sequence", "type": "text", "max_length": 10, "required": true}}',
 'BIOSWALE-PRETREAT-01'),
 
('Survey Control Network', 'SURVEY', '{SURVEY_TYPE}-{DATUM}-NET', '{ST}-{D}',
 '{"SURVEY_TYPE": {"label": "Survey Type", "type": "dropdown", "options": ["GPS", "LEVEL", "TRAVERSE"], "required": true}, "DATUM": {"label": "Datum", "type": "dropdown", "options": ["NAVD88", "NGVD29"], "required": true}}',
 'GPS-NAVD88-NET');
```

## Success Criteria

### Must Have
- ✅ Naming Templates CRUD interface fully functional
- ✅ Template selection replaces free-text in Relationship Sets
- ✅ Token replacement system with live preview
- ✅ 10+ seed templates provided
- ✅ All required tokens validated before save
- ✅ Database schema updated with FK constraint

### Should Have
- ✅ Token builder UI (avoid manual JSON editing)
- ✅ Usage instructions displayed per template
- ✅ Category-based template filtering
- ✅ Example output shown in template list
- ✅ User documentation with screenshots

### Nice to Have
- ✅ Migration tool to analyze existing free-text names
- ✅ Template versioning/history
- ✅ Bulk import templates from JSON file
- ✅ Template usage analytics (which templates used most)
- ✅ Auto-suggest templates based on relationship set members

## Risk Assessment

### Technical Risks
- **Token Definition Complexity**: JSONB structure may be confusing for users
  - **Mitigation**: Build visual token builder UI
- **Existing Data**: Free-text names already in use
  - **Mitigation**: Make template optional for existing sets, required for new
- **Token Validation**: Users might enter invalid characters
  - **Mitigation**: Client-side regex validation + server-side sanitization

### User Experience Risks
- **Learning Curve**: Users accustomed to free-text may resist
  - **Mitigation**: Show benefits (searchability, consistency, auto-complete)
- **Template Inflexibility**: Templates may not cover all edge cases
  - **Mitigation**: Provide "Custom" template option with free-text fallback

## Timeline Summary
- **Week 1**: CRUD interface + Token Builder UI
- **Week 2**: Template selection + Live preview + Documentation

**Total Duration**: 2 weeks

## Dependencies
- Existing `relationship_set_naming_templates` table (already created)
- Existing `relationship_sets` table (modify to add FK)
- Reference Data Hub navigation structure
- Mission Control CSS framework

## ROI & Business Value

### Immediate Value
- **Consistency**: 100% predictable naming across all relationship sets
- **Searchability**: Structured names enable powerful filters/queries
- **Reduced Errors**: No more typos or inconsistent abbreviations
- **Onboarding**: New users learn naming standards via templates

### Long-Term Value
- **Template Library Growth**: Organizational knowledge captured in templates
- **Cross-Project Intelligence**: Standardized names enable AI queries across projects
- **Compliance**: Naming templates can enforce client-specific standards
- **Automation**: Template-based names enable automated report generation

### Comparison to Alternatives
| Approach | Consistency | Flexibility | Ease of Use | Maintenance |
|----------|-------------|-------------|-------------|-------------|
| Free-text (current) | ❌ Low | ✅ High | ✅ Easy | ❌ Chaotic |
| **Template-based** | ✅ High | ⚠️ Medium | ✅ Easy | ✅ Structured |
| Hardcoded rules | ✅ High | ❌ Low | ❌ Difficult | ❌ Code changes |

### Integration with Other Projects
- **Project #3 (Truth-Driven Phase 2)**: This IS part of Phase 2 roadmap
- **Project #6 (Compliance Engine)**: Templates enable compliance rule naming standards
- **Project #4 (AI Agent)**: Standardized names improve AI semantic understanding

## Post-Implementation Enhancements

### Future Phases (Beyond 2 Weeks)
1. **Template Analytics Dashboard**: Show usage statistics, most popular templates
2. **Smart Suggestions**: AI recommends templates based on relationship set members
3. **Versioning**: Track template changes over time, migrate sets to new versions
4. **Import/Export**: Share templates across ACAD-GIS instances
5. **Client-Specific Templates**: Multi-tenant templates with client-specific standards

## Conclusion

This project completes a critical gap in the truth-driven architecture. By replacing free-text naming with database-backed templates, we eliminate inconsistencies and enable powerful cross-project intelligence. The 2-week timeline makes this an ideal quick win with immediate ROI.

**Recommended Start Date**: Immediately after approval (no dependencies)
