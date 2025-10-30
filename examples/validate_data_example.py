"""
Example: Validate Data Quality

This example shows how to validate your data for quality issues,
missing fields, duplicates, and geometry problems.
"""

import sys
from pathlib import Path

# Add tools to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.validation.data_validator import DataValidator


def main():
    print("ACAD-GIS Data Validation Example")
    print("=" * 70)
    print()
    
    validator = DataValidator()
    
    # Run comprehensive validation
    results = validator.validate_all_standards()
    
    print()
    print("Validation Results Summary:")
    print("=" * 70)
    print(f"Total issues: {results['total_issues']}")
    print()
    
    # Group by severity
    severity_counts = results['issues_by_severity']
    for severity in ['error', 'high', 'medium', 'low']:
        count = severity_counts.get(severity, 0)
        if count > 0:
            print(f"  {severity.upper()}: {count}")
    
    print()
    
    # Show sample issues
    if results['issues']:
        print("Sample Issues:")
        print("-" * 70)
        
        for issue in results['issues'][:10]:
            issue_type = issue.get('type', 'Unknown')
            table = issue.get('table', 'Unknown')
            count = issue.get('count', 'N/A')
            severity = issue.get('severity', 'unknown')
            
            if count != 'N/A':
                print(f"  [{severity.upper()}] {issue_type} in {table}: {count} records")
            else:
                print(f"  [{severity.upper()}] {issue_type} in {table}")
            
            if 'column' in issue:
                print(f"      Column: {issue['column']}")
            if 'error' in issue:
                print(f"      Error: {issue['error']}")
    
    print()
    print("=" * 70)
    print("Validation complete!")
    print()
    print("Next steps:")
    print("  1. Fix high-severity issues")
    print("  2. Run maintenance: python examples/maintenance_example.py")
    print("  3. Re-validate after fixes")


if __name__ == '__main__':
    main()
