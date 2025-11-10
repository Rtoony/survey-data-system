"""
Simple integration test for Standard Protection workflow
Uses known test data from the database
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

# Known test data
PROJECT_ID = "23d41772-9746-4d08-a302-3127230b43dc"
SET_ID = "f6b51c09-5791-4f30-a4c3-5b980ec2d4ac"
STANDARD_NOTE_ID = "4fc9c548-aee3-4d37-b9bd-41e5f3676f15"

def test_standard_protection_workflow():
    """Test the complete Standard Protection workflow"""
    
    print("\n" + "="*70)
    print("STANDARD PROTECTION WORKFLOW - Integration Test")
    print("="*70)
    
    # Test 1: Get the standard note before modification
    print("\n--- Test 1: Verify Standard Note Exists ---")
    response = requests.get(f"{BASE_URL}/api/project-sheet-notes/{STANDARD_NOTE_ID}")
    if response.status_code == 200:
        data = response.json()
        original_note = data.get('note', {})
        standard_library_note_id = original_note.get('standard_note_id')
        print(f"✓ Found standard note: {STANDARD_NOTE_ID}")
        print(f"  Display code: {original_note.get('display_code')}")
        print(f"  Source type: {original_note.get('source_type')}")
        print(f"  Standard library note ID: {standard_library_note_id}")
        print(f"  Title: {original_note.get('custom_title') or original_note.get('note_title') or '(no title)'}")
    else:
        print(f"✗ Failed to get standard note: {response.status_code}")
        print(f"  Response: {response.text}")
        return
    
    # Test 2: Create a modified copy
    print("\n--- Test 2: Create Modified Copy ---")
    payload = {
        'deviation_category': 'MATERIAL_AVAILABILITY',  # Material Availability
        'deviation_reason': f'Integration test - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        'conformance_status': 'MINOR_DEVIATION',
        'custom_title': 'TEST - Modified Standard Note',
        'custom_text': 'This is a test modification created by integration test'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/project-sheet-notes/{STANDARD_NOTE_ID}/create-modified-copy",
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 201:
        data = response.json()
        modified_note = data.get('note', {})
        modified_note_id = modified_note.get('project_note_id')
        print(f"✓ Created modified copy: {modified_note_id}")
        print(f"  Display code: {modified_note.get('display_code')}")
        print(f"  Source type: {modified_note.get('source_type')}")
        print(f"  Standard note ID: {modified_note.get('standard_note_id')}")
        print(f"  Deviation category: {modified_note.get('deviation_category_id')}")
        print(f"  Conformance status: {modified_note.get('conformance_status_code')}")
        
        # Validate response
        checks_passed = 0
        checks_total = 5
        
        if '-M' in modified_note.get('display_code', ''):
            print("  ✓ Display code contains -M suffix")
            checks_passed += 1
        else:
            print(f"  ✗ Display code missing -M suffix: {modified_note.get('display_code')}")
        
        if modified_note.get('source_type') == 'modified_standard':
            print("  ✓ Source type is 'modified_standard'")
            checks_passed += 1
        else:
            print(f"  ✗ Source type incorrect: {modified_note.get('source_type')}")
        
        if modified_note.get('standard_note_id') == standard_library_note_id:
            print("  ✓ Links back to original standard library note")
            checks_passed += 1
        else:
            print(f"  ✗ Standard note ID link incorrect: expected {standard_library_note_id}, got {modified_note.get('standard_note_id')}")
        
        if modified_note.get('deviation_category') == 'MATERIAL_AVAILABILITY':
            print("  ✓ Deviation category saved")
            checks_passed += 1
        else:
            print(f"  ✗ Deviation category missing or incorrect: {modified_note.get('deviation_category')}")
        
        if modified_note.get('conformance_status') == 'MINOR_DEVIATION':
            print("  ✓ Conformance status saved")
            checks_passed += 1
        else:
            print(f"  ✗ Conformance status missing or incorrect")
        
        print(f"\n  Validation: {checks_passed}/{checks_total} checks passed")
        
    else:
        print(f"✗ Failed to create modified copy: {response.status_code}")
        print(f"  Response: {response.text}")
        modified_note_id = None
        return
    
    # Test 3: Verify original standard is unchanged
    print("\n--- Test 3: Verify Original Standard Unchanged ---")
    response = requests.get(f"{BASE_URL}/api/project-sheet-notes/{STANDARD_NOTE_ID}")
    if response.status_code == 200:
        data = response.json()
        current_note = data.get('note', {})
        
        if current_note.get('source_type') == 'standard':
            print("✓ Original note is still type 'standard'")
        else:
            print(f"✗ Original note changed to: {current_note.get('source_type')}")
        
        if not current_note.get('deviation_category'):
            print("✓ Original note has no deviation data")
        else:
            print(f"✗ Original note has deviation data: {current_note.get('deviation_category')}")
        
        if current_note.get('display_code') == original_note.get('display_code'):
            print(f"✓ Original display code unchanged: {current_note.get('display_code')}")
        else:
            print(f"✗ Original display code changed")
    else:
        print(f"✗ Failed to retrieve original note")
    
    # Test 4: Create a second modified copy (test uniqueness)
    print("\n--- Test 4: Test Display Code Uniqueness ---")
    payload2 = {
        'deviation_category': 'CLIENT_REQUIREMENT',
        'deviation_reason': 'Second test modification',
        'conformance_status': 'MAJOR_DEVIATION'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/project-sheet-notes/{STANDARD_NOTE_ID}/create-modified-copy",
        json=payload2,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 201:
        data = response.json()
        second_modified = data.get('note', {})
        code1 = modified_note.get('display_code')
        code2 = second_modified.get('display_code')
        
        print(f"✓ Created second modified copy: {second_modified.get('project_note_id')}")
        print(f"  First copy: {code1}")
        print(f"  Second copy: {code2}")
        
        if code1 != code2:
            print(f"  ✓ Display codes are unique")
        else:
            print(f"  ✗ Display codes are identical")
    else:
        print(f"⚠ Could not create second modified copy: {response.status_code}")
    
    # Test 5: Check dashboard analytics
    print("\n--- Test 5: Dashboard Analytics ---")
    response = requests.get(f"{BASE_URL}/api/project-compliance/{PROJECT_ID}/conformance-details")
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        
        print(f"Project Conformance Summary:")
        print(f"  Total notes: {summary.get('total_notes', 0)}")
        print(f"  - Standard: {summary.get('standard_count', 0)}")
        print(f"  - Modified: {summary.get('modified_count', 0)}")
        print(f"  - Custom: {summary.get('custom_count', 0)}")
        
        total = summary.get('total_notes', 0)
        calculated = (summary.get('standard_count', 0) + 
                     summary.get('modified_count', 0) + 
                     summary.get('custom_count', 0))
        
        if total == calculated:
            print(f"  ✓ Counts add up correctly ({total} = {calculated})")
        else:
            print(f"  ✗ Count mismatch: total={total}, sum={calculated}")
        
        if summary.get('modified_count', 0) >= 2:
            print(f"  ✓ Modified notes detected in dashboard (at least 2)")
        else:
            print(f"  ⚠ Expected at least 2 modified notes, found: {summary.get('modified_count', 0)}")
    else:
        print(f"✗ Failed to get conformance details: {response.status_code}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\nNote: Test data has been created and left in the database")
    print(f"Modified note IDs: {modified_note_id}, {second_modified.get('project_note_id') if 'second_modified' in locals() else 'N/A'}")
    print("\n")

if __name__ == "__main__":
    test_standard_protection_workflow()
