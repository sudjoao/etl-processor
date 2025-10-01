#!/usr/bin/env python3
"""
Script to remove sample data logic from the application
"""

import sys
import os
sys.path.append('backend')

def remove_sample_data_logic():
    """Remove or disable sample data generation logic"""
    
    # Read the star_schema_generator.py file
    with open('backend/star_schema_generator.py', 'r') as f:
        content = f.read()
    
    # Replace the default include_sample_data to False
    content = content.replace(
        'include_sample_data: bool = True',
        'include_sample_data: bool = False'
    )
    
    # Write back the modified content
    with open('backend/star_schema_generator.py', 'w') as f:
        f.write(content)
    
    print("✅ Sample data logic disabled by default")
    
    # Also update the app.py to not include sample data by default
    with open('backend/app.py', 'r') as f:
        app_content = f.read()
    
    app_content = app_content.replace(
        'include_sample_data=True',
        'include_sample_data=False'
    )
    
    with open('backend/app.py', 'w') as f:
        f.write(app_content)
    
    print("✅ App.py updated to not include sample data by default")

if __name__ == "__main__":
    remove_sample_data_logic()
