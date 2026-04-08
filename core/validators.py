# core/validators.py
"""
Smart Data Validation Engine
Comprehensive validation system for all FarmWise data
"""

from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
import re
from datetime import datetime, date
from typing import Dict, List, Any, Tuple, Optional


class ValidationRule:
    """Base class for validation rules"""
    
    def __init__(self, field: str, rule_type: str, code: str, message: str, **params):
        self.field = field
        self.rule_type = rule_type
        self.code = code
        self.message = message
        self.params = params
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Validate a value
        Returns: (is_valid, error_message, details_dict)
        """
        raise NotImplementedError


class FormatValidator(ValidationRule):
    """Validates data format"""
    
    PATTERNS = {
        'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'phone': r'^[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}$',
        'date': r'^\d{4}-\d{2}-\d{2}$',
        'time': r'^\d{2}:\d{2}(?::\d{2})?$',
        'tag_number': r'^[A-Z0-9\-]{4,20}$',
        'url': r'^https?://[^\s/$.?#].[^\s]*$',
    }
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str], Optional[Dict]]:
        if value is None or value == '':
            return True, None, None
        
        pattern_type = self.params.get('pattern_type')
        custom_pattern = self.params.get('pattern')
        
        if custom_pattern:
            pattern = custom_pattern
        elif pattern_type in self.PATTERNS:
            pattern = self.PATTERNS[pattern_type]
        else:
            return True, None, None
        
        if not re.match(pattern, str(value)):
            return False, self.message, {
                'field': self.field,
                'code': self.code,
                'expected_format': pattern_type or 'custom'
            }
        
        return True, None, None


class RangeValidator(ValidationRule):
    """Validates numeric and date ranges"""
    
    def validate(self, value: Any) -> Tuple[bool, Optional[str], Optional[Dict]]:
        if value is None:
            return True, None, None
        
        min_val = self.params.get('min')
        max_val = self.params.get('max')
        
        try:
            numeric_value = Decimal(str(value))
        except:
            return False, "Invalid numeric value", {'field': self.field, 'code': self.code}
        
        if min_val is not None and numeric_value < Decimal(str(min_val)):
            return False, f"{self.message} (minimum: {min_val})", {
                'field': self.field,
                'code': self.code,
                'minimum': min_val,
                'value': float(numeric_value)
            }
        
        if max_val is not None and numeric_value > Decimal(str(max_val)):
            return False, f"{self.message} (maximum: {max_val})", {
                'field': self.field,
                'code': self.code,
                'maximum': max_val,
                'value': float(numeric_value)
            }
        
        return True, None, None


class BusinessLogicValidator(ValidationRule):
    """Validates business logic constraints"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        if context is None:
            context = {}
        
        rule_id = self.params.get('rule_id')
        
        # BL-001: Harvest date must be after planting date
        if rule_id == 'BL-001':
            planting = context.get('planting_date')
            harvest = value
            if planting and harvest and harvest <= planting:
                return False, "Harvest date must be after planting date", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id
                }
        
        # BL-002: End date must be after start date
        elif rule_id == 'BL-002':
            start = context.get('start_date')
            end = value
            if start and end and end <= start:
                return False, "End date must be after start date", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id
                }
        
        # BL-003: Quantity sold cannot exceed available stock
        elif rule_id == 'BL-003':
            available = context.get('available_quantity')
            ordered = value
            if available and ordered and ordered > available:
                return False, f"Cannot sell more than {available} units available", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id,
                    'available': available,
                    'requested': ordered
                }
        
        # BL-004: Cannot book equipment that is already booked
        elif rule_id == 'BL-004':
            is_booked = context.get('equipment_booked', False)
            if is_booked:
                return False, "Equipment is already booked for this period", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id
                }
        
        # BL-005: Cannot file claim on expired policy
        elif rule_id == 'BL-005':
            policy_end = context.get('policy_end_date')
            today = date.today()
            if policy_end and policy_end < today:
                return False, "Cannot file claim on expired policy", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id,
                    'expired_on': str(policy_end)
                }
        
        # BL-006: Cannot add animal to inactive farm
        elif rule_id == 'BL-006':
            farm_active = context.get('farm_active', True)
            if not farm_active:
                return False, "Cannot add animal to inactive farm", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id
                }
        
        # BL-007: Crop cannot be planted in non-existent field
        elif rule_id == 'BL-007':
            field_exists = context.get('field_exists', False)
            if not field_exists:
                return False, "Selected field does not exist", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id
                }
        
        # BL-008: Worker must be assigned to correct farm
        elif rule_id == 'BL-008':
            worker_farm = context.get('worker_farm_id')
            current_farm = context.get('current_farm_id')
            if worker_farm and current_farm and worker_farm != current_farm:
                return False, "Worker must be assigned to the same farm", {
                    'field': self.field,
                    'code': self.code,
                    'rule_id': rule_id
                }
        
        return True, None, None


class RelationshipValidator(ValidationRule):
    """Validates relationships between entities"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        if context is None:
            context = {}
        
        rel_type = self.params.get('relationship')
        
        # Crop → Field: Field must belong to user's farm
        if rel_type == 'crop_field':
            field_farm = context.get('field_farm_id')
            user_farm = context.get('user_farm_id')
            if field_farm and user_farm and field_farm != user_farm:
                return False, "Field must belong to your farm", {
                    'field': self.field,
                    'code': self.code,
                    'relationship': rel_type
                }
        
        # Animal → Farm: Farm must belong to user
        elif rel_type == 'animal_farm':
            farm_owner = context.get('farm_owner_id')
            current_user = context.get('user_id')
            if farm_owner and current_user and farm_owner != current_user:
                return False, "Farm must belong to you", {
                    'field': self.field,
                    'code': self.code,
                    'relationship': rel_type
                }
        
        # Order → Listing: Listing must be active
        elif rel_type == 'order_listing':
            listing_active = context.get('listing_active', False)
            if not listing_active:
                return False, "Product listing is no longer active", {
                    'field': self.field,
                    'code': self.code,
                    'relationship': rel_type
                }
        
        # Booking → Equipment: Equipment must be available
        elif rel_type == 'booking_equipment':
            equipment_available = context.get('equipment_available', False)
            if not equipment_available:
                return False, "Equipment is not available for booking", {
                    'field': self.field,
                    'code': self.code,
                    'relationship': rel_type
                }
        
        # Claim → Policy: Policy must belong to user
        elif rel_type == 'claim_policy':
            policy_owner = context.get('policy_owner_id')
            current_user = context.get('user_id')
            if policy_owner and current_user and policy_owner != current_user:
                return False, "Policy must belong to you", {
                    'field': self.field,
                    'code': self.code,
                    'relationship': rel_type
                }
        
        return True, None, None


class DuplicateValidator(ValidationRule):
    """Detects duplicate entries"""
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> Tuple[bool, Optional[str], Optional[Dict]]:
        if context is None:
            context = {}
        
        dup_type = self.params.get('duplicate_check')
        is_duplicate = context.get('is_duplicate', False)
        
        if is_duplicate:
            if dup_type == 'same_crop_field_season':
                return False, "This crop is already planted in this field for this season", {
                    'field': self.field,
                    'code': self.code,
                    'type': dup_type,
                    'warning': True
                }
            elif dup_type == 'animal_tag':
                return False, "This animal tag number already exists", {
                    'field': self.field,
                    'code': self.code,
                    'type': dup_type
                }
            elif dup_type == 'product_listing':
                return False, "Similar product listing already exists", {
                    'field': self.field,
                    'code': self.code,
                    'type': dup_type,
                    'warning': True
                }
            elif dup_type == 'booking_dates':
                return False, "Equipment is already booked for these dates", {
                    'field': self.field,
                    'code': self.code,
                    'type': dup_type
                }
        
        return True, None, None


class ValidationEngine:
    """Main validation engine - orchestrates all validators"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.validators = []
    
    def add_validator(self, validator: ValidationRule):
        """Add a validator"""
        self.validators.append(validator)
    
    def add_format_validator(self, field: str, pattern_type: str = None, pattern: str = None):
        """Add format validator"""
        messages = {
            'email': 'Invalid email format',
            'phone': 'Invalid phone number',
            'date': 'Invalid date format (use YYYY-MM-DD)',
            'tag_number': 'Tag number must be 4-20 alphanumeric characters',
        }
        msg = messages.get(pattern_type, 'Invalid format')
        
        validator = FormatValidator(
            field=field,
            rule_type='format',
            code=f'FORMAT-{pattern_type.upper()}',
            message=msg,
            pattern_type=pattern_type,
            pattern=pattern
        )
        self.add_validator(validator)
    
    def add_range_validator(self, field: str, min_val=None, max_val=None):
        """Add range validator"""
        validator = RangeValidator(
            field=field,
            rule_type='range',
            code=f'RANGE-{field.upper()}',
            message=f'Value out of range',
            min=min_val,
            max=max_val
        )
        self.add_validator(validator)
    
    def add_business_logic_validator(self, field: str, rule_id: str, message: str):
        """Add business logic validator"""
        validator = BusinessLogicValidator(
            field=field,
            rule_type='business_logic',
            code=rule_id,
            message=message,
            rule_id=rule_id
        )
        self.add_validator(validator)
    
    def add_relationship_validator(self, field: str, relationship: str, message: str):
        """Add relationship validator"""
        validator = RelationshipValidator(
            field=field,
            rule_type='relationship',
            code=f'REL-{relationship.upper()}',
            message=message,
            relationship=relationship
        )
        self.add_validator(validator)
    
    def add_duplicate_validator(self, field: str, duplicate_check: str):
        """Add duplicate validator"""
        validator = DuplicateValidator(
            field=field,
            rule_type='duplicate',
            code=f'DUP-{duplicate_check.upper()}',
            message='Duplicate detected',
            duplicate_check=duplicate_check
        )
        self.add_validator(validator)
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run all validators and compile results
        Returns: {
            'valid': bool,
            'errors': [...],
            'warnings': [...]
        }
        """
        self.errors = []
        self.warnings = []
        
        if context is None:
            context = {}
        
        for validator in self.validators:
            field_value = data.get(validator.field)
            
            if isinstance(validator, (BusinessLogicValidator, RelationshipValidator, DuplicateValidator)):
                is_valid, error_msg, details = validator.validate(field_value, context)
            else:
                is_valid, error_msg, details = validator.validate(field_value)
            
            if not is_valid:
                error_obj = {
                    'field': validator.field,
                    'code': validator.code,
                    'message': error_msg or validator.message,
                }
                
                if details:
                    error_obj.update(details)
                
                # Check if it's a warning
                if details and details.get('warning'):
                    self.warnings.append(error_obj)
                else:
                    self.errors.append(error_obj)
        
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings
        }
    
    def get_response(self, data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get formatted validation response (ready for API/forms)
        """
        result = self.validate(data, context)
        
        return {
            'status': 'success' if result['valid'] else 'error',
            'errors': result['errors'],
            'warnings': result['warnings'],
            'timestamp': timezone.now().isoformat()
        }


# Predefined validation sets for common scenarios

def get_crop_validators() -> ValidationEngine:
    """Get validators for crop planting"""
    engine = ValidationEngine()
    
    # Format validation
    engine.add_format_validator('planting_date', pattern_type='date')
    engine.add_format_validator('harvest_date', pattern_type='date')
    
    # Range validation
    engine.add_range_validator('planting_depth_cm', min_val=1, max_val=10)
    engine.add_range_validator('spacing_cm', min_val=5, max_val=100)
    engine.add_range_validator('estimated_yield_kg', min_val=0, max_val=100000)
    
    # Business logic
    engine.add_business_logic_validator('harvest_date', 'BL-001', 'Harvest date must be after planting date')
    
    # Relationships
    engine.add_relationship_validator('field', 'crop_field', 'Field must belong to your farm')
    
    return engine


def get_livestock_validators() -> ValidationEngine:
    """Get validators for livestock management"""
    engine = ValidationEngine()
    
    # Format validation
    engine.add_format_validator('tag_number', pattern_type='tag_number')
    engine.add_format_validator('date_of_birth', pattern_type='date')
    
    # Range validation
    engine.add_range_validator('initial_weight_kg', min_val=0.1, max_val=5000)
    engine.add_range_validator('current_weight_kg', min_val=0.1, max_val=5000)
    
    # Relationships
    engine.add_relationship_validator('farm', 'animal_farm', 'Farm must belong to you')
    
    # Duplicate check
    engine.add_duplicate_validator('tag_number', 'animal_tag')
    
    return engine


def get_marketplace_validators() -> ValidationEngine:
    """Get validators for marketplace listings"""
    engine = ValidationEngine()
    
    # Format validation
    engine.add_format_validator('price_per_unit', pattern=r'^\d+(\.\d{1,2})?$')
    
    # Range validation
    engine.add_range_validator('quantity_available', min_val=0.01, max_val=1000000)
    engine.add_range_validator('price_per_unit', min_val=0.01, max_val=1000000)
    
    # Business logic
    engine.add_business_logic_validator('quantity_sold', 'BL-003', 'Cannot sell more than available quantity')
    
    # Relationships
    engine.add_relationship_validator('product', 'order_listing', 'Product listing must be active')
    
    return engine
