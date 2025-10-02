#!/usr/bin/env python3

# Test the type inference logic directly
def _infer_attribute_type(attribute_name: str) -> str:
    """Infer data type for dimension attribute"""
    attr_lower = attribute_name.lower()

    print(f"Testing attribute: '{attribute_name}' (lower: '{attr_lower}')")

    # Check boolean patterns first (before 'id' pattern which could match 'holiday')
    if any(keyword in attr_lower for keyword in ['flag', 'is_weekend', 'is_holiday']) or attr_lower.startswith('is_') or attr_lower.startswith('has_'):
        print("  -> Matched boolean pattern")
        return 'boolean'
    elif any(keyword in attr_lower for keyword in ['date', 'time', 'created', 'updated']):
        print("  -> Matched datetime pattern")
        return 'datetime'
    elif any(keyword in attr_lower for keyword in ['id', 'key', 'number']):
        print("  -> Matched bigint pattern")
        return 'bigint'
    elif any(keyword in attr_lower for keyword in ['amount', 'price', 'cost', 'value']):
        print("  -> Matched decimal pattern")
        return 'decimal'
    elif any(keyword in attr_lower for keyword in ['description', 'comment', 'note']):
        print("  -> Matched text pattern")
        return 'text'
    else:
        print("  -> Defaulted to string")
        return 'string'

# Test the problematic attributes
test_attributes = [
    'is_weekend',
    'is_holiday',
    'date_key',
    'full_date',
    'day_of_week',
    'day_name',
    'month_number',
    'year'
]

print("Testing type inference for date dimension attributes:")
print("=" * 60)

for attr in test_attributes:
    result = _infer_attribute_type(attr)
    print(f"'{attr}' -> '{result}'")
    print()
