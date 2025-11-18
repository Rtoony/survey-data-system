# Project 6: Automated CAD Compliance & Quality Engine

## Executive Summary
Combine AI intelligence (Project 4) with truth-driven constraints (Project 3) to create an automated compliance validation engine. Build real-time DXF validation, AI-powered correction suggestions, intelligent Relationship Set rule generation, and automated quality reporting. Transform ACAD-GIS from a passive repository into an active quality assurance system.

## Dependencies
- **Requires Project 4**: AI Agent Toolkit (embeddings, GraphRAG)
- **Requires Project 3**: Truth-Driven Phase 2 (all FK constraints)
- **Builds on**: Existing Relationship Sets system

## Current State Assessment

### Existing Capabilities
- ✅ Relationship Sets framework with manual rule creation
- ✅ DXF import with intelligent object creation
- ✅ Object Reclassifier for reviewing classifications
- ✅ CAD Layer Vocabulary with naming standards
- ✅ Project Command Center with health metrics

### Current Gaps
- ❌ No pre-import DXF validation
- ❌ Manual relationship set rule creation (tedious)
- ❌ No automated compliance checking across projects
- ❌ No correction suggestion system
- ❌ Quality metrics are passive (not proactive)
- ❌ No standard violation alerts

## Goals & Objectives

### Primary Goals
1. **Pre-Import DXF Validation**: Check DXF files BEFORE import for compliance
2. **AI Rule Generation**: Auto-suggest Relationship Set rules using ML
3. **Automated Compliance Auditing**: Continuous scanning for standard violations
4. **Intelligent Corrections**: AI-powered suggestions to fix issues
5. **Quality Prediction**: Predict quality scores for new imports

### Success Metrics
- 95% of DXF issues caught before import (vs. after)
- Relationship Set rule creation time reduced by 80%
- 90% of suggested corrections accepted by users
- Zero high-priority violations in production projects
- Quality score prediction accuracy >85%

## Technical Architecture

### Core Components

#### 1. DXF Pre-Import Validator
Analyzes DXF files BEFORE import to detect issues:

**Validation Checks**:
- **Layer Naming**: All layers follow CAD Layer Vocabulary standards
- **Object Classification**: Can system confidently classify objects?
- **Geometry Quality**: Valid 3D coordinates, no zero-length lines
- **Attribute Completeness**: Required attributes present
- **FK Compliance**: Material/structure type codes exist in database
- **Spatial Validity**: No self-intersecting polygons, proper topology

**Output**: Validation report with severity levels (ERROR, WARNING, INFO)

#### 2. AI Rule Suggestion Engine
Uses ML to auto-generate Relationship Set rules:

**Learning From**:
- Existing relationship sets across all projects
- Common patterns (e.g., "Gravity pipes always require profile drawings")
- FK constraint relationships
- Spatial relationships in graph_edges
- Industry best practices database

**Rule Types Suggested**:
- **Required**: "All BASIN structures require storage volume attribute"
- **Equals**: "Pipe material must match structure material at connections"
- **Contains**: "Project name must contain client abbreviation"
- **In_List**: "BMP type must be one of [BASIN, SWALE, FILTER]"
- **Min/Max**: "Pipe slope must be between 0.005 and 0.10"
- **Regex**: "Structure number must match pattern MH-[0-9]{3}"

#### 3. Compliance Monitoring Dashboard
Real-time scanning and alerting:

**Monitoring Frequency**:
- **Critical**: Checked on every entity INSERT/UPDATE (real-time)
- **High**: Daily batch scan at midnight
- **Medium**: Weekly compliance report
- **Low**: Monthly audit

**Alert Channels**:
- In-app notifications in Project Command Center
- Email digest for project managers
- Slack/Teams integration (optional)

#### 4. Intelligent Correction System
AI-powered fix suggestions:

**Example Corrections**:
- "Layer 'STORM-PIPE-PVC-EX' should be 'STORM-PIPE-PVC-EXIST'"
  - **Confidence**: 98% (1-character fix)
  - **Action**: One-click auto-fix
  
- "Structure MH-5 missing rim elevation"
  - **Suggestion**: Calculate from nearby survey points (avg: 105.3 ft)
  - **Confidence**: 75%
  - **Action**: Review and apply
  
- "Pipe P-101 slope is 0.002 (below 0.005 minimum)"
  - **Suggestion**: Adjust downstream invert to 98.3 ft
  - **Confidence**: 60%
  - **Action**: Manual review required

#### 5. Quality Score Predictor
Predict quality before import:

**Input Features**:
- DXF file size and complexity
- Number of entities by type
- Attribute completeness percentage
- Layer naming compliance score
- Detected geometry issues
- Source project history (if known)

**Output**: Predicted quality score 0-100 with confidence interval

## Implementation Phases

### Phase 1: DXF Pre-Import Validator (Week 1-2)

#### Backend Service
```python
# services/dxf_validator.py
class DXFValidator:
    def validate_file(self, dxf_path):
        """Comprehensive pre-import validation"""
        issues = []
        
        # Check 1: Layer naming compliance
        issues += self.validate_layer_names(dxf_path)
        
        # Check 2: Object classification confidence
        issues += self.validate_object_types(dxf_path)
        
        # Check 3: Geometry quality
        issues += self.validate_geometry(dxf_path)
        
        # Check 4: FK compliance
        issues += self.validate_foreign_keys(dxf_path)
        
        # Check 5: Spatial validity
        issues += self.validate_topology(dxf_path)
        
        return ValidationReport(issues, score=self.calculate_score(issues))
```

#### Database Schema
```sql
CREATE TABLE dxf_validation_reports (
    report_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_name VARCHAR(255),
    file_hash VARCHAR(64),
    total_entities INTEGER,
    error_count INTEGER,
    warning_count INTEGER,
    info_count INTEGER,
    compliance_score DECIMAL(5,2),
    issues_json JSONB,
    validated_at TIMESTAMP DEFAULT NOW(),
    validated_by UUID REFERENCES users(user_id)
);

CREATE TABLE validation_issues (
    issue_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES dxf_validation_reports(report_id),
    severity VARCHAR(20), -- ERROR, WARNING, INFO
    category VARCHAR(50), -- LAYER_NAMING, GEOMETRY, FK_COMPLIANCE
    entity_handle VARCHAR(50),
    issue_description TEXT,
    suggested_fix TEXT,
    fix_confidence DECIMAL(3,2)
);
```

#### UI Component
- **File Upload**: Drag-drop DXF validator page
- **Report Display**: Tabbed view (Errors, Warnings, Info)
- **Issue Details**: Expandable cards with fix suggestions
- **Import Decision**: "Fix & Import" or "Cancel"

**Deliverables**: DXF validator service, report schema, validation UI

### Phase 2: AI Rule Suggestion Engine (Week 3-4)

#### ML Training Pipeline
```python
# services/rule_suggester.py
class RuleSuggester:
    def train_from_existing_rules(self):
        """Learn patterns from all relationship sets"""
        # Extract features from existing rules
        rules_df = self.fetch_all_relationship_rules()
        
        # Feature engineering
        features = {
            'entity_type': rules_df['member_entity_type'],
            'attribute_name': rules_df['rule_attribute'],
            'operator': rules_df['rule_operator'],
            'project_type': rules_df['project_type'],
            'client': rules_df['client_name']
        }
        
        # Train classifier to predict likely rules
        self.model = RandomForestClassifier()
        self.model.fit(features, rules_df['rule_value'])
    
    def suggest_rules(self, project_id, entity_type):
        """Suggest rules for a new relationship set"""
        # Analyze project context
        project = self.get_project_details(project_id)
        
        # Find similar projects
        similar_projects = self.find_similar_projects(project)
        
        # Extract common rules
        common_rules = self.extract_common_rules(similar_projects)
        
        # ML prediction for missing rules
        predicted_rules = self.model.predict(project, entity_type)
        
        return common_rules + predicted_rules
```

#### Rule Confidence Scoring
- **High Confidence (>80%)**: Used in 5+ similar projects
- **Medium Confidence (50-80%)**: Industry best practice
- **Low Confidence (<50%)**: ML prediction, needs review

#### UI Enhancement
Update `relationship_sets.html`:
- "Suggest Rules" button
- AI suggestions panel with confidence indicators
- One-click acceptance of high-confidence rules
- Batch accept/reject for rule sets

**Deliverables**: Rule suggestion ML model, API endpoint, UI integration

### Phase 3: Automated Compliance Scanner (Week 5-6)

#### Scanning Engine
```python
# services/compliance_scanner.py
class ComplianceScanner:
    def scan_project(self, project_id):
        """Run all compliance checks on project"""
        violations = []
        
        # Check 1: FK constraints
        violations += self.check_fk_violations(project_id)
        
        # Check 2: Relationship set rules
        violations += self.check_relationship_rules(project_id)
        
        # Check 3: CAD layer standards
        violations += self.check_layer_compliance(project_id)
        
        # Check 4: Geometry quality
        violations += self.check_geometry_quality(project_id)
        
        # Check 5: Missing required relationships
        violations += self.check_missing_relationships(project_id)
        
        return ComplianceReport(violations, self.calculate_severity())
    
    def scan_all_projects(self):
        """Batch scan all active projects"""
        for project in get_active_projects():
            report = self.scan_project(project.project_id)
            self.save_report(report)
            if report.has_critical_violations():
                self.send_alert(project.project_manager)
```

#### Database Schema
```sql
CREATE TABLE compliance_scans (
    scan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(project_id),
    scan_type VARCHAR(50), -- FULL, INCREMENTAL, TARGETED
    total_violations INTEGER,
    critical_count INTEGER,
    high_count INTEGER,
    medium_count INTEGER,
    low_count INTEGER,
    scan_duration_ms INTEGER,
    scanned_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE compliance_violations (
    violation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES compliance_scans(scan_id),
    project_id UUID REFERENCES projects(project_id),
    severity VARCHAR(20), -- CRITICAL, HIGH, MEDIUM, LOW
    violation_type VARCHAR(50),
    entity_id UUID,
    entity_type VARCHAR(50),
    violation_description TEXT,
    suggested_fix TEXT,
    fix_confidence DECIMAL(3,2),
    status VARCHAR(20), -- OPEN, RESOLVED, ACKNOWLEDGED, FALSE_POSITIVE
    resolved_at TIMESTAMP,
    resolved_by UUID
);
```

#### Scheduled Jobs
```python
# Add to app.py or separate scheduler
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# Daily critical scan
scheduler.add_job(
    func=compliance_scanner.scan_all_projects,
    trigger='cron',
    hour=0,  # Midnight
    id='daily_compliance_scan'
)

# Real-time scanning on entity changes (trigger)
CREATE OR REPLACE FUNCTION trigger_compliance_check()
RETURNS TRIGGER AS $$
BEGIN
    -- Queue compliance check for this entity
    INSERT INTO compliance_scan_queue (entity_id, entity_type)
    VALUES (NEW.entity_id, TG_TABLE_NAME);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Deliverables**: Scanning engine, violation tracking, scheduled jobs

### Phase 4: Intelligent Correction System (Week 7-8)

#### Correction Suggestion Logic
```python
# services/correction_suggester.py
class CorrectionSuggester:
    def suggest_fixes(self, violation):
        """Generate intelligent fix suggestions"""
        
        if violation.type == 'LAYER_NAMING':
            return self.suggest_layer_rename(violation)
        
        elif violation.type == 'MISSING_ATTRIBUTE':
            return self.suggest_attribute_value(violation)
        
        elif violation.type == 'FK_VIOLATION':
            return self.suggest_fk_value(violation)
        
        elif violation.type == 'GEOMETRY_INVALID':
            return self.suggest_geometry_fix(violation)
    
    def suggest_layer_rename(self, violation):
        """Use fuzzy matching to find correct layer name"""
        current_layer = violation.current_value
        
        # Get all valid layers from vocabulary
        valid_layers = get_cad_layer_vocabulary()
        
        # Find closest match using Levenshtein distance
        matches = difflib.get_close_matches(
            current_layer, 
            valid_layers, 
            n=3, 
            cutoff=0.6
        )
        
        return [
            Suggestion(
                new_value=match,
                confidence=self.calculate_confidence(current_layer, match),
                explanation=f"Did you mean '{match}'?"
            )
            for match in matches
        ]
    
    def suggest_attribute_value(self, violation):
        """Use AI to predict missing attribute values"""
        entity = get_entity(violation.entity_id)
        
        # Use embedding similarity to find similar entities
        similar_entities = self.find_similar_entities(entity)
        
        # Extract common attribute values
        common_values = self.extract_common_attributes(
            similar_entities, 
            violation.attribute_name
        )
        
        # Use ML to predict most likely value
        predicted_value = self.ml_predict_attribute(entity, violation.attribute_name)
        
        return [
            Suggestion(
                new_value=predicted_value,
                confidence=0.75,
                explanation=f"Based on {len(similar_entities)} similar entities"
            )
        ]
```

#### One-Click Fix Application
```python
# API endpoint
@app.route('/api/compliance/apply-fix', methods=['POST'])
def apply_fix():
    violation_id = request.json['violation_id']
    suggested_fix = request.json['suggested_fix']
    
    # Apply the fix
    success = apply_correction(violation_id, suggested_fix)
    
    if success:
        # Mark violation as resolved
        mark_violation_resolved(violation_id, current_user.user_id)
        
        # Re-scan to confirm fix worked
        rescan_entity(violation.entity_id)
        
        return {'status': 'success'}
```

#### UI Components
- **Violation Card**: Display issue with fix suggestions
- **Fix Preview**: Show before/after comparison
- **Apply Button**: One-click fix with undo option
- **Batch Fixes**: Apply multiple fixes at once

**Deliverables**: Correction engine, fix preview UI, batch processing

### Phase 5: Quality Score Predictor (Week 9-10)

#### ML Training
```python
# services/quality_predictor.py
class QualityPredictor:
    def train_model(self):
        """Train on historical import quality data"""
        
        # Fetch all DXF imports with final quality scores
        historical_data = self.fetch_import_history()
        
        # Feature extraction
        features = {
            'file_size_mb': historical_data['file_size'] / 1_000_000,
            'entity_count': historical_data['total_entities'],
            'layer_count': historical_data['total_layers'],
            'layer_compliance_pct': historical_data['valid_layers'] / historical_data['total_layers'],
            'attribute_completeness': historical_data['filled_attributes'] / historical_data['total_attributes'],
            'geometry_error_count': historical_data['geometry_errors'],
            'classification_confidence_avg': historical_data['avg_confidence']
        }
        
        # Train gradient boosting model
        self.model = GradientBoostingRegressor()
        self.model.fit(features, historical_data['final_quality_score'])
    
    def predict_quality(self, dxf_path):
        """Predict quality score before import"""
        
        # Extract features from DXF
        features = self.extract_features(dxf_path)
        
        # Predict
        predicted_score = self.model.predict([features])[0]
        
        # Calculate confidence interval
        confidence = self.calculate_prediction_confidence(features)
        
        return {
            'predicted_score': predicted_score,
            'confidence_interval': (predicted_score - confidence, predicted_score + confidence),
            'recommendation': self.get_recommendation(predicted_score)
        }
    
    def get_recommendation(self, score):
        if score >= 90:
            return "Excellent quality - ready to import"
        elif score >= 75:
            return "Good quality - minor cleanup recommended"
        elif score >= 60:
            return "Fair quality - review warnings before import"
        else:
            return "Poor quality - significant cleanup required"
```

#### UI Integration
Add to DXF upload page:
- **Quality Prediction Badge**: Green/Yellow/Red indicator
- **Confidence Interval**: Score range display
- **Recommendation**: Text guidance
- **Detailed Breakdown**: Feature contribution to score

**Deliverables**: ML prediction model, API endpoint, UI integration

## Compliance Dashboard Design

### Page Layout
```
┌─────────────────────────────────────────────────────────┐
│ 🛡️ CAD Compliance & Quality Dashboard                  │
├─────────────────────────────────────────────────────────┤
│ System Health                                           │
│ ┌──────────┬──────────┬──────────┬──────────┐          │
│ │ Projects │ Critical │   High   │  Medium  │          │
│ │   42     │    3     │    12    │    28    │          │
│ └──────────┴──────────┴──────────┴──────────┘          │
├─────────────────────────────────────────────────────────┤
│ Active Violations by Severity                           │
│ [Critical: 3] [High: 12] [Medium: 28] [Low: 47]        │
│                                                         │
│ Critical Violations (requires immediate action)         │
│ ┌─────────────────────────────────────────────────┐    │
│ │ 🔴 Project: Maple St Drainage                   │    │
│ │    Missing required profile drawing for Pipe-5  │    │
│ │    [View Details] [Auto-Fix] [Acknowledge]      │    │
│ └─────────────────────────────────────────────────┘    │
│                                                         │
│ Compliance Trends (Last 30 Days)                       │
│ [Line chart showing violation counts over time]        │
│                                                         │
│ Top Violation Types                                     │
│ 1. Missing attributes (45%)                            │
│ 2. Layer naming errors (25%)                           │
│ 3. FK violations (18%)                                 │
│ 4. Geometry errors (12%)                               │
└─────────────────────────────────────────────────────────┘
```

## API Endpoints

### DXF Validation
- `POST /api/compliance/validate-dxf` - Upload and validate DXF
- `GET /api/compliance/validation-report/{report_id}` - Get report

### Rule Suggestions
- `POST /api/compliance/suggest-rules` - Get AI rule suggestions
- `POST /api/compliance/accept-rule` - Accept suggested rule

### Compliance Scanning
- `POST /api/compliance/scan-project/{project_id}` - Trigger scan
- `GET /api/compliance/scan-status/{scan_id}` - Get scan status
- `GET /api/compliance/violations` - List violations with filters

### Corrections
- `GET /api/compliance/suggest-fix/{violation_id}` - Get fix suggestions
- `POST /api/compliance/apply-fix` - Apply suggested fix
- `POST /api/compliance/batch-fix` - Apply multiple fixes

### Quality Prediction
- `POST /api/compliance/predict-quality` - Predict DXF quality

## Dependencies & Requirements

### Python Packages
- `scikit-learn>=1.3.0` - ML models
- `pandas>=2.0.0` - Data processing
- `difflib` - String similarity (built-in)
- `Levenshtein>=0.21.0` - Fast string distance
- `apscheduler>=3.10.0` - Scheduled scanning

### Database Requirements
- All FK constraints from Project 2 must be implemented
- Embeddings and graph_edges from Project 1 must be populated

## Risk Assessment

### Technical Risks
- **False positives**: Scanner may flag valid edge cases
  - **Mitigation**: Confidence thresholds, manual override options
- **Performance**: Full project scans may be slow
  - **Mitigation**: Incremental scanning, caching, async processing
- **ML accuracy**: Quality predictions may be inaccurate initially
  - **Mitigation**: Continuous model retraining, user feedback loop

### User Experience Risks
- **Alert fatigue**: Too many low-priority warnings
  - **Mitigation**: Smart filtering, configurable thresholds
- **Fix suggestions wrong**: AI may suggest incorrect fixes
  - **Mitigation**: Confidence scores, preview before apply, easy undo

## Success Criteria

### Must Have
- ✅ DXF validator catches 95% of issues pre-import
- ✅ AI rule suggestions reduce manual work by 80%
- ✅ Compliance scanner runs daily without failures
- ✅ Critical violations trigger alerts within 1 hour

### Should Have
- ✅ Fix suggestions accepted >70% of the time
- ✅ Quality predictions accurate within ±10 points
- ✅ Dashboard shows real-time compliance status
- ✅ Batch fix operations complete in <30 seconds

### Nice to Have
- ✅ Integration with CI/CD for automated DXF testing
- ✅ Export compliance reports to PDF
- ✅ Compliance badge for project pages
- ✅ Historical compliance trend analysis

## Timeline Summary
- **Phase 1**: Weeks 1-2 (DXF Validator)
- **Phase 2**: Weeks 3-4 (AI Rule Suggester)
- **Phase 3**: Weeks 5-6 (Compliance Scanner)
- **Phase 4**: Weeks 7-8 (Correction System)
- **Phase 5**: Weeks 9-10 (Quality Predictor)

**Total Duration**: 10 weeks

## ROI & Business Value
- **Error Prevention**: Catch issues before they become expensive
- **Time Savings**: Automated compliance vs. manual review
- **Quality Assurance**: Consistent standards across all projects
- **Client Confidence**: Demonstrable quality metrics
- **Competitive Advantage**: No other CAD system has this
- **Reduced Rework**: Fix issues early in workflow
