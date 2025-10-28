"""
Prompt Loading Utilities for Competitive Intelligence Reports

This module provides utilities for loading, formatting, and validating LLM prompts
from separate files. All LLM prompts MUST be stored in external files and loaded
dynamically for proper version control, team collaboration, and prompt optimization.

Usage:
    from src.metis.utils.prompt_loader import PromptLoader
    
    prompt_loader = PromptLoader()
    formatted_prompt = prompt_loader.format_prompt(
        'sentiment_analysis', 
        'management_sentiment_analysis',
        symbol='WRB',
        management_text='...',
        quarter='Q3-2025'
    )
"""

import os
import string
from typing import Dict, Any, List, Set
from pathlib import Path


class PromptLoadError(Exception):
    """Raised when prompt loading fails"""
    pass


class PromptValidationError(Exception):
    """Raised when prompt variable validation fails"""
    pass


class PromptLoader:
    """
    Utility class for loading and formatting LLM prompts from external files.
    
    This class enforces the MANDATORY requirement that all LLM prompts be stored
    in separate files under the prompts/ directory structure.
    """
    
    def __init__(self, base_path: str = None):
        """
        Initialize PromptLoader with base path to prompts directory.
        
        Args:
            base_path: Base directory path containing prompt files.
                      If None, uses package-relative path.
        """
        if base_path is None:
            # Use package-relative path when installed
            package_dir = Path(__file__).parent.parent
            self.base_path = package_dir / "prompts"
        else:
            self.base_path = Path(base_path)
        self._prompt_cache: Dict[str, str] = {}
        self._validate_base_path()
    
    def _validate_base_path(self) -> None:
        """Validate that base path exists and is accessible"""
        if not self.base_path.exists():
            raise PromptLoadError(f"Prompts base path does not exist: {self.base_path}")
        
        if not self.base_path.is_dir():
            raise PromptLoadError(f"Prompts base path is not a directory: {self.base_path}")
    
    def load_prompt(self, category: str, prompt_file_name: str, use_cache: bool = True) -> str:
        """
        Load prompt from file with error handling and optional caching.
        
        Args:
            category: Prompt category subdirectory (e.g., 'sentiment_analysis')
            prompt_file_name: Prompt filename with extension (e.g., 'management_sentiment_analysis.txt')
            use_cache: Whether to use cached prompt content
            
        Returns:
            Prompt template content as string
            
        Raises:
            PromptLoadError: If prompt file cannot be loaded
        """
        cache_key = f"{category}/{prompt_file_name}"
        
        if use_cache and cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        prompt_path = self.base_path / category / prompt_file_name
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                
            if not content:
                raise PromptLoadError(f"Prompt file is empty: {prompt_path}")
                
            if use_cache:
                self._prompt_cache[cache_key] = content
                
            return content
            
        except FileNotFoundError:
            raise PromptLoadError(f"Prompt file not found: {prompt_path}")
        except UnicodeDecodeError as e:
            raise PromptLoadError(f"Prompt file encoding error: {prompt_path}. Error: {e}")
        except Exception as e:
            raise PromptLoadError(f"Unexpected error loading prompt: {prompt_path}. Error: {e}")
    
    def format_prompt(self, category: str, prompt_file_name: str, **kwargs) -> str:
        """
        Load and format prompt with dynamic data.
        
        Args:
            category: Prompt category subdirectory
            prompt_file_name: Prompt filename with extension
            **kwargs: Variables to substitute in prompt template
            
        Returns:
            Formatted prompt ready for LLM consumption
            
        Raises:
            PromptLoadError: If prompt cannot be loaded
            PromptValidationError: If required variables are missing
        """
        # Validate variables before formatting
        self.validate_prompt_variables(category, prompt_file_name, **kwargs)
        
        # Load template
        template = self.load_prompt(category, prompt_file_name)
        
        try:
            # Format with provided variables
            formatted_prompt = template.format(**kwargs)
            return formatted_prompt
            
        except KeyError as e:
            missing_var = str(e).strip("'")
            raise PromptValidationError(
                f"Variable '{missing_var}' not provided for prompt {category}/{prompt_file_name}"
            )
        except Exception as e:
            raise PromptLoadError(
                f"Error formatting prompt {category}/{prompt_file_name}: {e}"
            )
    
    def validate_prompt_variables(self, category: str, prompt_file_name: str, **kwargs) -> bool:
        """
        Validate that all required variables are provided for prompt template.
        
        Args:
            category: Prompt category subdirectory
            prompt_file_name: Prompt filename with extension
            **kwargs: Variables to validate
            
        Returns:
            True if all required variables are present
            
        Raises:
            PromptValidationError: If required variables are missing
        """
        template = self.load_prompt(category, prompt_file_name)
        required_vars = self._extract_template_variables(template)
        provided_vars = set(kwargs.keys())
        missing_vars = required_vars - provided_vars
        
        if missing_vars:
            raise PromptValidationError(
                f"Missing required variables for prompt {category}/{prompt_file_name}: {sorted(missing_vars)}"
            )
        
        return True
    
    def _extract_template_variables(self, template: str) -> Set[str]:
        """
        Extract all variable names from template string.
        
        Args:
            template: Template string with {variable} placeholders
            
        Returns:
            Set of variable names found in template
        """
        variables = set()
        
        try:
            # Parse template to find all field names
            for literal_text, field_name, format_spec, conversion in string.Formatter().parse(template):
                if field_name is not None:
                    # Handle nested field access (e.g., data.metric)
                    base_field = field_name.split('.')[0].split('[')[0]
                    variables.add(base_field)
                    
        except Exception as e:
            raise PromptLoadError(f"Error parsing template variables: {e}")
        
        return variables
    
    def list_available_prompts(self, category: str = None) -> Dict[str, List[str]]:
        """
        List all available prompt files by category.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            Dictionary mapping categories to lists of prompt names
        """
        prompts = {}
        
        if category:
            categories = [category]
        else:
            # List all subdirectories
            categories = [d.name for d in self.base_path.iterdir() if d.is_dir()]
        
        for cat in categories:
            cat_path = self.base_path / cat
            if cat_path.exists() and cat_path.is_dir():
                prompt_files = [
                    f.stem for f in cat_path.glob("*.txt")
                ]
                prompts[cat] = sorted(prompt_files)
        
        return prompts
    
    def clear_cache(self) -> None:
        """Clear prompt cache to force reload from files"""
        self._prompt_cache.clear()
    
    def get_prompt_metadata(self, category: str, prompt_file_name: str) -> Dict[str, Any]:
        """
        Get metadata about a prompt file.
        
        Args:
            category: Prompt category subdirectory
            prompt_file_name: Prompt filename with extension
            
        Returns:
            Dictionary with prompt metadata
        """
        prompt_path = self.base_path / category / prompt_file_name
        
        if not prompt_path.exists():
            raise PromptLoadError(f"Prompt file not found: {prompt_path}")
        
        stat = prompt_path.stat()
        template = self.load_prompt(category, prompt_file_name)
        variables = self._extract_template_variables(template)
        
        return {
            "file_path": str(prompt_path),
            "file_size": stat.st_size,
            "modified_time": stat.st_mtime,
            "character_count": len(template),
            "line_count": len(template.splitlines()),
            "required_variables": sorted(variables),
            "variable_count": len(variables)
        }


# Global instance for convenience
default_prompt_loader = PromptLoader()