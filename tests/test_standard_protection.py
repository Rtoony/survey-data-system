"""
Integration tests for Standard Protection workflow

Tests the complete flow of protecting standards from direct modification
by creating modified copies with deviation tracking.
"""

import requests
import json
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:5000"

class TestStandardProtection:
    """Test suite for Standard Protection workflow"""
    
    def __init__(self):
        self.session = requests.Session()
        self.test_project_id = None
        self.test_set_id = None
        self.test_standard_note_id = None
        self.test_modified_note_id = None
    
    def setup(self):
        """Setup test data - find or create test project, set, and standard note"""
        print("\n=== Setting up test data ===")
        
        # Get a project to work with
        projects = self._get("/api/projects")
        if projects and len(projects) > 0:
            self.test_project_id = projects[0]['project_id']
            print(f"✓ Using existing project: {self.test_project_id}")
        else:
            print("✗ No projects found. Please create a project first.")
            return False
        
        # Get or create a sheet note set
        sets = self._get(f"/api/data-manager/sheet-sets")
        project_sets = [s for s in sets if s.get('project_id') == self.test_project_id]
        
        if project_sets:
            self.test_set_id = project_sets[0]['set_id']
            print(f"✓ Using existing sheet set: {self.test_set_id}")
        else:
            print("✗ No sheet note sets found for this project.")
            return False
        
        # Find a standard note to test with
        notes = self._get(f"/api/project-sheet-notes")
        standard_notes = [n for n in notes 
                         if n.get('source_type') == 'standard' 
                         and n.get('set_id') == self.test_set_id]
        
        if standard_notes:
            self.test_standard_note_id = standard_notes[0]['project_note_id']
            print(f"✓ Using existing standard note: {self.test_standard_note_id}")
        else:
            print("⚠ No standard notes found. Test will be limited.")
            return False
        
        return True
    
    def test_create_modified_copy(self):
        """Test creating a modified copy from a standard note"""
        print("\n=== Test 1: Create Modified Copy ===")
        
        if not self.test_standard_note_id:
            print("⊘ Skipped - no standard note available")
            return
        
        # Create modified copy
        payload = {
            'deviation_category_id': 'CAT001',  # Material change
            'deviation_reason': 'Test deviation - integration test',
            'conformance_status_code': 'MINOR_DEVIATION',
            'custom_title': 'Modified Test Note',
            'custom_text': 'This is a test modification'
        }
        
        result = self._post(
            f"/api/project-sheet-notes/{self.test_standard_note_id}/create-modified-copy",
            payload
        )
        
        if result and 'project_note_id' in result:
            self.test_modified_note_id = result['project_note_id']
            print(f"✓ Created modified copy: {self.test_modified_note_id}")
            print(f"  Display code: {result.get('display_code')}")
            print(f"  Source type: {result.get('source_type')}")
            print(f"  Standard note ID: {result.get('standard_note_id')}")
            
            # Verify it has -M suffix
            if result.get('display_code', '').endswith('-M') or '-M' in result.get('display_code', ''):
                print("✓ Display code has -M suffix")
            else:
                print(f"✗ Display code missing -M suffix: {result.get('display_code')}")
            
            # Verify source_type is 'modified'
            if result.get('source_type') == 'modified':
                print("✓ Source type is 'modified'")
            else:
                print(f"✗ Source type is incorrect: {result.get('source_type')}")
            
            # Verify standard_note_id links back
            if result.get('standard_note_id') == self.test_standard_note_id:
                print("✓ Standard note ID links to original")
            else:
                print("✗ Standard note ID link is incorrect")
        else:
            print("✗ Failed to create modified copy")
            print(f"  Response: {result}")
    
    def test_cannot_modify_standard_directly(self):
        """Verify that the standard note is NOT modified when we create a copy"""
        print("\n=== Test 2: Verify Standard Protection ===")
        
        if not self.test_standard_note_id:
            print("⊘ Skipped - no standard note available")
            return
        
        # Get the original standard note
        original = self._get(f"/api/project-sheet-notes/{self.test_standard_note_id}")
        
        if original:
            # Verify it's still a standard
            if original.get('source_type') == 'standard':
                print("✓ Original note is still type 'standard'")
            else:
                print(f"✗ Original note changed type to: {original.get('source_type')}")
            
            # Verify no deviation data on original
            if not original.get('deviation_category_id'):
                print("✓ Original note has no deviation data")
            else:
                print("✗ Original note has deviation data (should not)")
        else:
            print("✗ Could not retrieve original note")
    
    def test_dashboard_analytics(self):
        """Test that conformance dashboard shows source type breakdown"""
        print("\n=== Test 3: Dashboard Analytics ===")
        
        if not self.test_project_id:
            print("⊘ Skipped - no project available")
            return
        
        # Get conformance details
        result = self._get(f"/api/project-compliance/{self.test_project_id}/conformance-details")
        
        if result:
            summary = result.get('summary', {})
            
            print(f"Total notes: {summary.get('total_notes', 0)}")
            print(f"  - Standard: {summary.get('standard_count', 0)}")
            print(f"  - Modified: {summary.get('modified_count', 0)}")
            print(f"  - Custom: {summary.get('custom_count', 0)}")
            
            # Verify the counts add up
            total = summary.get('total_notes', 0)
            calculated = (summary.get('standard_count', 0) + 
                         summary.get('modified_count', 0) + 
                         summary.get('custom_count', 0))
            
            if total == calculated:
                print("✓ Source type counts match total")
            else:
                print(f"✗ Count mismatch: total={total}, sum={calculated}")
            
            # Verify source_types array exists
            if 'source_types' in result:
                print(f"✓ Source types breakdown available: {len(result['source_types'])} types")
            else:
                print("✗ Source types breakdown missing")
        else:
            print("✗ Could not retrieve conformance details")
    
    def test_display_code_uniqueness(self):
        """Test that creating multiple modified copies generates unique codes"""
        print("\n=== Test 4: Display Code Uniqueness ===")
        
        if not self.test_standard_note_id:
            print("⊘ Skipped - no standard note available")
            return
        
        # Create a second modified copy
        payload = {
            'deviation_category_id': 'CAT002',
            'deviation_reason': 'Second test modification',
            'conformance_status_code': 'MINOR_DEVIATION'
        }
        
        result = self._post(
            f"/api/project-sheet-notes/{self.test_standard_note_id}/create-modified-copy",
            payload
        )
        
        if result and 'display_code' in result:
            code1 = result.get('display_code')
            print(f"Second copy display code: {code1}")
            
            # If we have the first modified note, compare
            if self.test_modified_note_id:
                first_note = self._get(f"/api/project-sheet-notes/{self.test_modified_note_id}")
                code2 = first_note.get('display_code') if first_note else None
                
                if code1 != code2:
                    print(f"✓ Display codes are unique: {code1} vs {code2}")
                else:
                    print(f"✗ Display codes are identical: {code1}")
        else:
            print("✗ Failed to create second modified copy")
    
    def cleanup(self):
        """Clean up test data"""
        print("\n=== Cleanup ===")
        print("Note: Test data left in database for manual inspection")
        print(f"Modified note ID: {self.test_modified_note_id}")
    
    # Helper methods
    def _get(self, endpoint: str) -> Optional[Any]:
        """Make GET request"""
        try:
            response = self.session.get(f"{BASE_URL}{endpoint}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"GET {endpoint} failed: {e}")
            return None
    
    def _post(self, endpoint: str, data: Dict) -> Optional[Any]:
        """Make POST request"""
        try:
            response = self.session.post(
                f"{BASE_URL}{endpoint}",
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"POST {endpoint} failed: {e}")
            try:
                print(f"Response: {response.text}")
            except:
                pass
            return None
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("\n" + "="*60)
        print("STANDARD PROTECTION WORKFLOW - Integration Tests")
        print("="*60)
        
        if not self.setup():
            print("\n⚠ Setup failed - cannot run tests")
            return
        
        self.test_create_modified_copy()
        self.test_cannot_modify_standard_directly()
        self.test_dashboard_analytics()
        self.test_display_code_uniqueness()
        self.cleanup()
        
        print("\n" + "="*60)
        print("TESTS COMPLETE")
        print("="*60)


if __name__ == "__main__":
    tester = TestStandardProtection()
    tester.run_all_tests()
