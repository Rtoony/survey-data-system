# ACAD-GIS Documentation Index
**Last Updated:** November 17, 2025
**Total Active Documentation Files:** 42 markdown files + About page
**Archived Files:** 20 files in `archive/completed-migrations/`

---

## 🚀 Start Here - Essential Reading

### For New Users
1. **[README.md](README.md)** - Project overview, quick start, and core features (start here!)
2. **[/about page](templates/about.html)** - Comprehensive 1,319-line system guide explaining philosophy, architecture, all 32 tools, and key differentiators
3. **[replit.md](replit.md)** - Project memory, architecture reference, and recent changes

### Quick Navigation by Role

**👤 End Users (Engineers, Surveyors, CAD Users)**
- [CAD Standards Guide](CAD_STANDARDS_GUIDE.md) - How to use the layer naming system
- [Survey Code System Guide](SURVEY_CODE_SYSTEM_GUIDE.md) - Field data collection codes
- [Visualization Tools](VISUALIZATION_TOOLS.md) - Map viewer and visualization features
- [Project Relationship Sets User Guide](PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md) - Compliance tracking

**🏗️ Administrators & Power Users**
- [Attribute System Guide](ATTRIBUTE_SYSTEM_GUIDE.md) - Three-dimensional filtering system
- [Database Architecture Guide](DATABASE_ARCHITECTURE_GUIDE.md) - Technical deep dive
- [Standards Conformance Pattern](STANDARDS_CONFORMANCE_PATTERN.md) - Standards enforcement

**💻 Developers & Database Administrators**
- [database/SCHEMA_VERIFICATION.md](database/SCHEMA_VERIFICATION.md) - Complete schema reference (81 tables)
- [tools/README.md](tools/README.md) - Python toolkit documentation
- [AI Database Optimization Guide](AI_DATABASE_OPTIMIZATION_GUIDE.md) - ML/AI features

---

## 📚 Documentation by Category

### 1. 👤 User Guides (5 files)
End-user documentation for day-to-day operations

| File | Description | Route/Access |
|------|-------------|--------------|
| [CAD_STANDARDS_GUIDE.md](CAD_STANDARDS_GUIDE.md) | Complete guide to CAD standards system and layer naming | `/standards-library` |
| [ATTRIBUTE_SYSTEM_GUIDE.md](ATTRIBUTE_SYSTEM_GUIDE.md) | Three-dimensional filtering (Object Type → Attribute → Table) | Various tools |
| [PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md](PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md) | Dependency tracking and compliance auditing | `/projects/{id}/relationship-sets` |
| [SURVEY_CODE_SYSTEM_GUIDE.md](SURVEY_CODE_SYSTEM_GUIDE.md) | Survey point code library and field workflows | `/tools/survey-codes` |
| [VISUALIZATION_TOOLS.md](VISUALIZATION_TOOLS.md) | Enhanced Map Viewer and Project Command Center | `/map-viewer-v2` |
| [RELATIONSHIP_SETS_SECURITY_NOTE.md](RELATIONSHIP_SETS_SECURITY_NOTE.md) | Security considerations for relationship sets | N/A |
| [PROJECT_RELATIONSHIP_SETS.md](PROJECT_RELATIONSHIP_SETS.md) | Technical reference for relationship sets | N/A |

### 2. 🏗️ Architecture & Technical Documentation (10 files)
Deep dives into system design and database architecture

| File | Description | Focus |
|------|-------------|-------|
| [DATABASE_ARCHITECTURE_GUIDE.md](DATABASE_ARCHITECTURE_GUIDE.md) | AI-first database design patterns | Schema, indexing, materialized views |
| [ENTITY_RELATIONSHIP_MODEL.md](ENTITY_RELATIONSHIP_MODEL.md) | Entity registry and relationship patterns | Entity types, table mappings |
| [TRUTH_DRIVEN_ARCHITECTURE.md](TRUTH_DRIVEN_ARCHITECTURE.md) | Database-driven vocabulary and standards | Truth-driven design philosophy |
| [DATA_FLOW_AND_LIFECYCLE.md](DATA_FLOW_AND_LIFECYCLE.md) | DXF import/export workflow | Data transformation pipeline |
| [CIVIL_ENGINEERING_DOMAIN_MODEL.md](CIVIL_ENGINEERING_DOMAIN_MODEL.md) | Civil engineering specific tables and workflows | Pipes, structures, grading |
| [PROJECT_ASSIGNMENT_MODEL.md](PROJECT_ASSIGNMENT_MODEL.md) | Project-level entity relationships | Projects Only system |
| [STANDARDS_CONFORMANCE_PATTERN.md](STANDARDS_CONFORMANCE_PATTERN.md) | Standards enforcement and compliance | Validation rules |
| [STANDARDS_MAPPING_FRAMEWORK.md](STANDARDS_MAPPING_FRAMEWORK.md) | 11-table schema for DXF↔Database translation | Name mapping managers |
| [AI_DATABASE_OPTIMIZATION_GUIDE.md](AI_DATABASE_OPTIMIZATION_GUIDE.md) | ML/AI features and optimization patterns | Embeddings, GraphRAG, quality scoring |
| [AI_QUERY_PATTERNS_AND_EXAMPLES.md](AI_QUERY_PATTERNS_AND_EXAMPLES.md) | Example AI queries and search patterns | Vector search, hybrid queries |

### 3. 🗄️ Database Documentation (3 files)
Schema references and database operations

| File | Description | Location |
|------|-------------|----------|
| [database/SCHEMA_VERIFICATION.md](database/SCHEMA_VERIFICATION.md) | Complete schema reference - 81 tables | database/ |
| [database/AI_OPTIMIZATION_SUMMARY.md](database/AI_OPTIMIZATION_SUMMARY.md) | AI optimization implementation status | database/ |
| [database/migrations/README.md](database/migrations/README.md) | Database migration guide and procedures | database/migrations/ |

### 4. 🔧 Developer Resources (4 files)
For developers extending the system

| File | Description | Location |
|------|-------------|----------|
| [tools/README.md](tools/README.md) | Python toolkit for embeddings, relationships, validation | tools/ |
| [tests/README.md](tests/README.md) | Testing framework and procedures | tests/ |
| [examples/README.md](examples/README.md) | Sample workflows and example scripts | examples/ |
| [docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md](docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md) | Template for creating new specialized tools | docs/ |

### 5. 📐 DXF & Naming System Documentation (6 files)
DXF translation and name mapping

| File | Description | Location |
|------|-------------|----------|
| [docs/DXF_TRANSLATOR_AND_RELATIONSHIP_MANAGER_INTEGRATION.md](docs/DXF_TRANSLATOR_AND_RELATIONSHIP_MANAGER_INTEGRATION.md) | DXF translator integration with relationship manager | docs/ |
| [docs/DXF_NAME_TRANSLATOR_STANDARDS_INTEGRATION.md](docs/DXF_NAME_TRANSLATOR_STANDARDS_INTEGRATION.md) | Standards integration for name translation | docs/ |
| [docs/DXF_NAME_TRANSLATOR_SCHEMA_AUDIT.md](docs/DXF_NAME_TRANSLATOR_SCHEMA_AUDIT.md) | Schema audit for name translator | docs/ |
| [docs/DXF_NAME_TRANSLATOR_FRONTEND_ANALYSIS.md](docs/DXF_NAME_TRANSLATOR_FRONTEND_ANALYSIS.md) | Frontend analysis for DXF name translator | docs/ |
| [docs/DXF_NAME_TRANSLATOR_BACKEND_ANALYSIS.md](docs/DXF_NAME_TRANSLATOR_BACKEND_ANALYSIS.md) | Backend analysis for DXF name translator | docs/ |
| [docs/CAD_LAYER_NAMING_STANDARDS.md](docs/CAD_LAYER_NAMING_STANDARDS.md) | CAD layer naming standards reference | docs/ |

### 6. 📊 Phase Documentation (3 files)
Development phase summaries

| File | Description | Location |
|------|-------------|----------|
| [docs/PHASE_2_SUMMARY.md](docs/PHASE_2_SUMMARY.md) | Phase 2 development summary | docs/ |
| [docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md](docs/PHASE_3_COMPREHENSIVE_ANALYSIS.md) | Phase 3 comprehensive analysis | docs/ |
| [scripts/README.md](scripts/README.md) | Scripts documentation and quickstart guides | scripts/ |

### 7. 🗃️ Reference Data (1 file)
Vocabulary and standards reference

| File | Description | Location |
|------|-------------|----------|
| [standards/cad_standards_vocabulary.md](standards/cad_standards_vocabulary.md) | CAD standards vocabulary reference | standards/ |

### 8. 📦 Scripts & Phase Quickstarts (6 files)
Implementation guides and quickstart scripts

| File | Description | Location |
|------|-------------|----------|
| [scripts/PHASE1_QUICKSTART.md](scripts/PHASE1_QUICKSTART.md) | Phase 1 quickstart guide | scripts/ |
| [scripts/PHASE2_QUICKSTART.md](scripts/PHASE2_QUICKSTART.md) | Phase 2 quickstart guide | scripts/ |
| [scripts/PHASE3_QUICKSTART.md](scripts/PHASE3_QUICKSTART.md) | Phase 3 quickstart guide | scripts/ |
| [scripts/PHASE2_IMPLEMENTATION_SUMMARY.md](scripts/PHASE2_IMPLEMENTATION_SUMMARY.md) | Phase 2 implementation details | scripts/ |
| [scripts/PHASE2_INTEGRATION_GUIDE.md](scripts/PHASE2_INTEGRATION_GUIDE.md) | Phase 2 integration procedures | scripts/ |
| [scripts/PHASE3_IMPLEMENTATION_SUMMARY.md](scripts/PHASE3_IMPLEMENTATION_SUMMARY.md) | Phase 3 implementation details | scripts/ |

### 9. 📋 Project Reports & Audits (1 file)
Current audit and status reports

| File | Description | Purpose |
|------|-------------|---------|
| [DOCUMENTATION_AUDIT_REPORT.md](DOCUMENTATION_AUDIT_REPORT.md) | November 2025 comprehensive documentation audit | Tracking documentation updates |

---

## 🗂️ Archive - Completed Work (20 files)
Historical documentation for completed features and migrations

**Location:** `archive/completed-migrations/`

### Migrations & Planning
1. [MIGRATION_DISCOVERY.md](archive/completed-migrations/MIGRATION_DISCOVERY.md) - Migration discovery process
2. [NAMING_TEMPLATES_IMPLEMENTATION_SUMMARY.md](archive/completed-migrations/NAMING_TEMPLATES_IMPLEMENTATION_SUMMARY.md) - Naming templates implementation
3. [PROJECTS_ONLY_MIGRATION_GUIDE.md](archive/completed-migrations/PROJECTS_ONLY_MIGRATION_GUIDE.md) - Projects Only system migration
4. [TRUTH_DRIVEN_MIGRATION_PLAN.md](archive/completed-migrations/TRUTH_DRIVEN_MIGRATION_PLAN.md) - Truth-driven architecture migration

### Implementation Summaries
5. [SPECIALIZED_TOOLS_IMPLEMENTATION.md](archive/completed-migrations/SPECIALIZED_TOOLS_IMPLEMENTATION.md)
6. [SPECIALIZED_TOOLS_IMPLEMENTATION_SUMMARY.md](archive/completed-migrations/SPECIALIZED_TOOLS_IMPLEMENTATION_SUMMARY.md)
7. [POWERHOUSE_IMPLEMENTATION_SUMMARY.md](archive/completed-migrations/POWERHOUSE_IMPLEMENTATION_SUMMARY.md)
8. [GIS_SNAPSHOT_INTEGRATOR_IMPLEMENTATION.md](archive/completed-migrations/GIS_SNAPSHOT_INTEGRATOR_IMPLEMENTATION.md)
9. [FINAL_IMPROVEMENTS_SUMMARY.md](archive/completed-migrations/FINAL_IMPROVEMENTS_SUMMARY.md)
10. [CLAUDE_CODE_IMPROVEMENTS_SUMMARY.md](archive/completed-migrations/CLAUDE_CODE_IMPROVEMENTS_SUMMARY.md)
11. [PHASE1_IMPLEMENTATION_SUMMARY.md](archive/completed-migrations/PHASE1_IMPLEMENTATION_SUMMARY.md)
12. [DRAWING_PAPERSPACE_CLEANUP_STATUS.md](archive/completed-migrations/DRAWING_PAPERSPACE_CLEANUP_STATUS.md)

### Testing & Reviews
13. [PHASE_4_ANALYSIS.md](archive/completed-migrations/PHASE_4_ANALYSIS.md)
14. [TESTING_IMPLEMENTATION_SUMMARY.md](archive/completed-migrations/TESTING_IMPLEMENTATION_SUMMARY.md)
15. [PHASE1_TESTING_RESULTS.md](archive/completed-migrations/PHASE1_TESTING_RESULTS.md)
16. [COMPREHENSIVE_CODE_REVIEW.md](archive/completed-migrations/COMPREHENSIVE_CODE_REVIEW.md)
17. [COMPREHENSIVE_CODEBASE_REVIEW_REPORT.md](archive/completed-migrations/COMPREHENSIVE_CODEBASE_REVIEW_REPORT.md)
18. [CODE_REVIEW_QUICK_FIXES.md](archive/completed-migrations/CODE_REVIEW_QUICK_FIXES.md)

### AI/ML Planning
19. [AI_IMPLEMENTATION_GAME_PLAN.md](archive/completed-migrations/AI_IMPLEMENTATION_GAME_PLAN.md)
20. [AI_EMBEDDING_GRAPH_RAG_AUDIT.md](archive/completed-migrations/AI_EMBEDDING_GRAPH_RAG_AUDIT.md)

---

## 🔍 Finding What You Need

### By Task

**I want to...**

- **Understand the system** → [README.md](README.md), [/about page](templates/about.html), [replit.md](replit.md)
- **Learn CAD standards** → [CAD_STANDARDS_GUIDE.md](CAD_STANDARDS_GUIDE.md)
- **Set up survey codes** → [SURVEY_CODE_SYSTEM_GUIDE.md](SURVEY_CODE_SYSTEM_GUIDE.md)
- **Use the map viewer** → [VISUALIZATION_TOOLS.md](VISUALIZATION_TOOLS.md)
- **Track dependencies** → [PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md](PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md)
- **Understand the database** → [DATABASE_ARCHITECTURE_GUIDE.md](DATABASE_ARCHITECTURE_GUIDE.md)
- **Write Python tools** → [tools/README.md](tools/README.md)
- **Understand AI features** → [AI_DATABASE_OPTIMIZATION_GUIDE.md](AI_DATABASE_OPTIMIZATION_GUIDE.md)
- **See the schema** → [database/SCHEMA_VERIFICATION.md](database/SCHEMA_VERIFICATION.md)
- **Create a new tool** → [docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md](docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md)

### By Application Route

| Route | Documentation |
|-------|---------------|
| `/standards-library` | [CAD_STANDARDS_GUIDE.md](CAD_STANDARDS_GUIDE.md) |
| `/map-viewer-v2` | [VISUALIZATION_TOOLS.md](VISUALIZATION_TOOLS.md) |
| `/tools/survey-codes` | [SURVEY_CODE_SYSTEM_GUIDE.md](SURVEY_CODE_SYSTEM_GUIDE.md) |
| `/projects/{id}/relationship-sets` | [PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md](PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md) |
| `/schema` | [database/SCHEMA_VERIFICATION.md](database/SCHEMA_VERIFICATION.md) |
| `/dxf-tools` | [DATA_FLOW_AND_LIFECYCLE.md](DATA_FLOW_AND_LIFECYCLE.md) |

### By Technology

| Technology | Documentation |
|------------|---------------|
| PostgreSQL/PostGIS | [DATABASE_ARCHITECTURE_GUIDE.md](DATABASE_ARCHITECTURE_GUIDE.md), [database/SCHEMA_VERIFICATION.md](database/SCHEMA_VERIFICATION.md) |
| AI/ML (OpenAI, pgvector) | [AI_DATABASE_OPTIMIZATION_GUIDE.md](AI_DATABASE_OPTIMIZATION_GUIDE.md), [AI_QUERY_PATTERNS_AND_EXAMPLES.md](AI_QUERY_PATTERNS_AND_EXAMPLES.md) |
| DXF Import/Export | [DATA_FLOW_AND_LIFECYCLE.md](DATA_FLOW_AND_LIFECYCLE.md), [STANDARDS_MAPPING_FRAMEWORK.md](STANDARDS_MAPPING_FRAMEWORK.md) |
| Python Toolkit | [tools/README.md](tools/README.md), [examples/README.md](examples/README.md) |
| Flask/Jinja2 | [replit.md](replit.md), [docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md](docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md) |

---

## 📈 Documentation Statistics

### By Type
- **User Guides:** 7 files
- **Architecture/Technical:** 10 files
- **Database Documentation:** 3 files
- **Developer Resources:** 4 files
- **DXF/Naming System:** 6 files
- **Phase Documentation:** 3 files
- **Scripts & Quickstarts:** 6 files
- **Reference Data:** 1 file
- **Audit Reports:** 1 file
- **Archived (completed work):** 20 files

### Total Lines of Documentation
- **Active Documentation:** ~42 files, estimated 50,000+ lines
- **About Page:** 1,319 lines
- **Archived Documentation:** ~20 files, estimated 25,000+ lines

---

## 🎯 Recommended Reading Paths

### Path 1: New User (30-45 minutes)
1. [README.md](README.md) - 10 min
2. [/about page](templates/about.html) - 15 min (skim tools directory)
3. [CAD_STANDARDS_GUIDE.md](CAD_STANDARDS_GUIDE.md) - 15 min
4. Try the system!

### Path 2: Administrator (2-3 hours)
1. [README.md](README.md) - 10 min
2. [/about page](templates/about.html) - 20 min (full read)
3. [replit.md](replit.md) - 15 min
4. [DATABASE_ARCHITECTURE_GUIDE.md](DATABASE_ARCHITECTURE_GUIDE.md) - 30 min
5. [CAD_STANDARDS_GUIDE.md](CAD_STANDARDS_GUIDE.md) - 20 min
6. [ATTRIBUTE_SYSTEM_GUIDE.md](ATTRIBUTE_SYSTEM_GUIDE.md) - 20 min
7. [VISUALIZATION_TOOLS.md](VISUALIZATION_TOOLS.md) - 15 min
8. [PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md](PROJECT_RELATIONSHIP_SETS_USER_GUIDE.md) - 20 min

### Path 3: Developer (4-6 hours)
1. [README.md](README.md) - 10 min
2. [replit.md](replit.md) - 30 min
3. [DATABASE_ARCHITECTURE_GUIDE.md](DATABASE_ARCHITECTURE_GUIDE.md) - 60 min
4. [database/SCHEMA_VERIFICATION.md](database/SCHEMA_VERIFICATION.md) - 45 min
5. [TRUTH_DRIVEN_ARCHITECTURE.md](TRUTH_DRIVEN_ARCHITECTURE.md) - 30 min
6. [AI_DATABASE_OPTIMIZATION_GUIDE.md](AI_DATABASE_OPTIMIZATION_GUIDE.md) - 45 min
7. [tools/README.md](tools/README.md) - 30 min
8. [docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md](docs/SPECIALIZED_TOOL_TEMPLATE_GUIDE.md) - 30 min
9. [DATA_FLOW_AND_LIFECYCLE.md](DATA_FLOW_AND_LIFECYCLE.md) - 30 min

---

## 🔄 Recent Updates

**November 17, 2025:**
- ✅ Comprehensive documentation audit completed
- ✅ Fixed broken links (3 total)
- ✅ Standardized route references across all guides
- ✅ Added navigation sections to user guides
- ✅ Archived 20 completed implementation docs
- ✅ Updated tool counts and descriptions
- ✅ Created this comprehensive index

**November 15, 2025:**
- Added DXF Test Generator documentation
- Updated Recent Additions in README.md

---

## 📝 Documentation Standards

### File Naming
- User guides: `[SUBJECT]_GUIDE.md`
- Architecture: `[SUBJECT]_ARCHITECTURE.md` or `[SUBJECT]_MODEL.md`
- Summaries: `[SUBJECT]_SUMMARY.md`
- All caps with underscores for consistency

### Internal Links
- Use relative paths from repository root
- Format: `[Link Text](path/to/file.md)`
- Archived files: `[Link Text](archive/completed-migrations/file.md)`

### Route References
- Always use actual app.py routes
- Include leading slash: `/route-name`
- Specify version if applicable: `/map-viewer-v2`

---

## 🆘 Getting Help

**Can't find what you need?**

1. Check the [/about page](templates/about.html) - comprehensive 1,300-line guide
2. Use browser search (Ctrl+F) in [README.md](README.md) or [replit.md](replit.md)
3. Check the relevant section in this index
4. Look in [archive/completed-migrations/](archive/completed-migrations/) for historical context
5. Check [DOCUMENTATION_AUDIT_REPORT.md](DOCUMENTATION_AUDIT_REPORT.md) for known issues

**Found an error or outdated information?**
- Check the "Last Updated" date at the top of each file
- Refer to [DOCUMENTATION_AUDIT_REPORT.md](DOCUMENTATION_AUDIT_REPORT.md) for known issues
- Update documentation as part of feature development

---

**Documentation Index End** | [Back to Top](#acad-gis-documentation-index)
