#!/usr/bin/env python3
"""
Config Generator with Validation Coverage
Bounty: $45 - Add config generator validation coverage
Implements comprehensive validation for configuration generation
"""

import os
import json
import re
from typing import Dict, List, Any, Tuple


class ConfigValidator:
    """Validates configuration files and generated configs."""
    
    SENSITIVE_KEYS = {
        'password', 'secret', 'api_key', 'token', 'private_key',
        'credentials', 'auth_token', 'access_token', 'refresh_token'
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate a configuration dictionary.
        
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        self.errors = []
        self.warnings = []
        
        if not config:
            self.errors.append("Configuration cannot be empty")
            return False, self.errors
        
        self._check_for_sensitive_keys(config)
        self._check_for_empty_values(config)
        self._check_for_duplicate_keys(config)
        self._validate_structure(config)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors + self.warnings
    
    def _check_for_sensitive_keys(self, config: Dict[str, Any], parent_key: str = '') -> None:
        """Check for sensitive keys that should be masked or removed."""
        for key, value in config.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            
            if key.lower() in self.SENSITIVE_KEYS:
                self.warnings.append(f"Sensitive key detected: {full_key}")
            
            if isinstance(value, dict):
                self._check_for_sensitive_keys(value, full_key)
    
    def _check_for_empty_values(self, config: Dict[str, Any]) -> None:
        """Check for empty or null values in required fields."""
        for key, value in config.items():
            if value is None:
                self.errors.append(f"Null value found for key: {key}")
            elif isinstance(value, str) and not value.strip():
                self.errors.append(f"Empty string value for key: {key}")
    
    def _check_for_duplicate_keys(self, config: Dict[str, Any]) -> None:
        """Check for duplicate configuration keys (case-insensitive)."""
        seen_keys = {}
        for key in config.keys():
            lower_key = key.lower()
            if lower_key in seen_keys:
                self.errors.append(f"Duplicate key (case-insensitive): '{key}' conflicts with '{seen_keys[lower_key]}'")
            else:
                seen_keys[lower_key] = key
    
    def _validate_structure(self, config: Dict[str, Any]) -> None:
        """Validate overall configuration structure."""
        if not isinstance(config, dict):
            self.errors.append("Configuration must be a dictionary")
            return


class ConfigGenerator:
    """Generates configuration files with validation."""
    
    def __init__(self, validator: ConfigValidator = None):
        self.validator = validator or ConfigValidator()
    
    def generate_config(self, template: Dict[str, Any], overrides: Dict[str, Any] = None) -> Tuple[Dict[str, Any], List[str]]:
        """
        Generate a configuration from a template with optional overrides.
        
        Args:
            template: Base configuration template
            overrides: Dictionary of values to override in template
        
        Returns:
            Tuple of (generated_config: Dict, validation_messages: List[str])
        """
        if not template:
            return {}, ["Template cannot be empty"]
        
        # Deep copy template
        config = self._deep_copy(template)
        
        # Apply overrides
        if overrides:
            config = self._apply_overrides(config, overrides)
        
        # Validate generated config
        is_valid, messages = self.validator.validate_config(config)
        
        return config, messages
    
    def _deep_copy(self, obj: Any) -> Any:
        """Create a deep copy of an object."""
        if isinstance(obj, dict):
            return {k: self._deep_copy(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj
    
    def _apply_overrides(self, config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Apply override values to configuration."""
        for key, value in overrides.items():
            if key in config and isinstance(config[key], dict) and isinstance(value, dict):
                config[key] = self._apply_overrides(config[key], value)
            else:
                config[key] = value
        return config
    
    def save_config(self, config: Dict[str, Any], filepath: str) -> Tuple[bool, str]:
        """
        Save configuration to a JSON file.
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(config, f, indent=2)
            return True, f"Configuration saved to {filepath}"
        except Exception as e:
            return False, f"Failed to save configuration: {str(e)}"


def main():
    """Example usage and testing."""
    validator = ConfigValidator()
    generator = ConfigGenerator(validator)
    
    # Example template
    template = {
        "database": {
            "host": "localhost",
            "port": 5432,
            "username": "admin",
            "password": "secret123"
        },
        "api": {
            "key": "api_key_123",
            "timeout": 30
        }
    }
    
    # Generate with overrides
    overrides = {
        "database": {
            "host": "prod-db.example.com"
        },
        "api": {
            "timeout": 60
        }
    }
    
    config, messages = generator.generate_config(template, overrides)
    
    print("Generated Configuration:")
    print(json.dumps(config, indent=2))
    print("\nValidation Messages:")
    for msg in messages:
        print(f"  - {msg}")


if __name__ == "__main__":
    main()
