"""
Comprehensive Test Suite for Prompt Loader

Tests all aspects of the mandatory prompt file system including loading,
formatting, validation, and error handling.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from metis.utils.prompt_loader import PromptLoader, PromptLoadError, PromptValidationError


class TestPromptLoader:
    """Test the PromptLoader utility class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_loader = PromptLoader(base_path=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_prompt(self, category: str, name: str, content: str):
        """Helper to create test prompt files"""
        category_dir = Path(self.temp_dir) / category
        category_dir.mkdir(exist_ok=True)
        prompt_file = category_dir / f"{name}.txt"
        prompt_file.write_text(content, encoding='utf-8')
        return str(prompt_file)
    
    def test_load_prompt_success(self):
        """Test successful prompt loading"""
        test_content = "This is a test prompt for {symbol}"
        self.create_test_prompt("test_category", "test_prompt", test_content)
        
        result = self.prompt_loader.load_prompt("test_category", "test_prompt")
        assert result == test_content
    
    def test_load_prompt_file_not_found(self):
        """Test error handling for missing prompt files"""
        with pytest.raises(PromptLoadError) as exc_info:
            self.prompt_loader.load_prompt("nonexistent", "missing")
        
        assert "Prompt file not found" in str(exc_info.value)
    
    def test_load_prompt_caching(self):
        """Test prompt caching functionality"""
        test_content = "Cached prompt for {symbol}"
        self.create_test_prompt("cache_test", "cached_prompt", test_content)
        
        # First load
        result1 = self.prompt_loader.load_prompt("cache_test", "cached_prompt")
        
        # Second load (should use cache)
        result2 = self.prompt_loader.load_prompt("cache_test", "cached_prompt")
        
        assert result1 == result2 == test_content
        assert len(self.prompt_loader._prompt_cache) == 1
    
    def test_format_prompt_success(self):
        """Test successful prompt formatting"""
        template = "Analysis for {symbol} in {sector} sector with {metric} = {value}"
        self.create_test_prompt("format_test", "template", template)
        
        result = self.prompt_loader.format_prompt(
            "format_test", "template",
            symbol="AAPL",
            sector="Technology", 
            metric="P/E",
            value=25.5
        )
        
        expected = "Analysis for AAPL in Technology sector with P/E = 25.5"
        assert result == expected
    
    def test_format_prompt_missing_variables(self):
        """Test error handling for missing template variables"""
        template = "Analysis for {symbol} with {missing_var}"
        self.create_test_prompt("error_test", "missing_vars", template)
        
        with pytest.raises(PromptValidationError) as exc_info:
            self.prompt_loader.format_prompt(
                "error_test", "missing_vars",
                symbol="AAPL"
            )
        
        assert "missing_var" in str(exc_info.value)
        assert "missing_var" in str(exc_info.value)
    
    def test_validate_prompt_variables_success(self):
        """Test successful variable validation"""
        template = "Test {var1} and {var2}"
        self.create_test_prompt("validation", "vars_test", template)
        
        result = self.prompt_loader.validate_prompt_variables(
            "validation", "vars_test",
            var1="value1",
            var2="value2"
        )
        
        assert result is True
    
    def test_validate_prompt_variables_missing(self):
        """Test variable validation with missing variables"""
        template = "Test {var1}, {var2}, and {var3}"
        self.create_test_prompt("validation", "missing_test", template)
        
        with pytest.raises(PromptValidationError) as exc_info:
            self.prompt_loader.validate_prompt_variables(
                "validation", "missing_test",
                var1="value1"
            )
        
        assert "var2" in str(exc_info.value) and "var3" in str(exc_info.value)
        assert "var2" in str(exc_info.value)
        assert "var3" in str(exc_info.value)
    
    def test_extract_template_variables(self):
        """Test template variable extraction"""
        template = "Complex template with {symbol}, {pe_ratio}, {roe}, and {growth_rate}"
        self.create_test_prompt("extraction", "complex", template)
        
        variables = self.prompt_loader._extract_template_variables(template)
        expected = {"symbol", "pe_ratio", "roe", "growth_rate"}
        assert variables == expected
    
    def test_clear_cache(self):
        """Test cache clearing functionality"""
        self.create_test_prompt("cache", "test1", "Content 1")
        self.create_test_prompt("cache", "test2", "Content 2")
        
        # Load prompts to populate cache
        self.prompt_loader.load_prompt("cache", "test1")
        self.prompt_loader.load_prompt("cache", "test2")
        
        assert len(self.prompt_loader._prompt_cache) == 2
        
        # Clear cache
        self.prompt_loader.clear_cache()
        assert len(self.prompt_loader._prompt_cache) == 0
    
    def test_utf8_encoding_support(self):
        """Test UTF-8 encoding support for international characters"""
        content_with_unicode = "Análisis financiero para {símbolo} en el sector {sector}"
        self.create_test_prompt("unicode", "international", content_with_unicode)
        
        result = self.prompt_loader.load_prompt("unicode", "international")
        assert result == content_with_unicode
    
    def test_large_prompt_file(self):
        """Test handling of large prompt files"""
        large_content = "Large prompt content\\n" * 1000 + "Final variable: {symbol}"
        self.create_test_prompt("large", "big_prompt", large_content)
        
        result = self.prompt_loader.load_prompt("large", "big_prompt")
        assert len(result) > 10000
        assert "{symbol}" in result
    
    def test_list_available_prompts(self):
        """Test listing available prompts"""
        self.create_test_prompt("category1", "prompt1", "Content 1")
        self.create_test_prompt("category1", "prompt2", "Content 2")
        self.create_test_prompt("category2", "prompt3", "Content 3")
        
        prompts = self.prompt_loader.list_available_prompts()
        
        assert "category1" in prompts
        assert "prompt1" in prompts["category1"]
        assert "prompt2" in prompts["category1"]
        assert "category2" in prompts
        assert "prompt3" in prompts["category2"]
    
    def test_prompt_metadata_extraction(self):
        """Test extraction of prompt metadata"""
        content_with_metadata = '''# Prompt: Executive Summary
# Author: System
# Version: 1.0
# Description: Generate executive summary for competitive intelligence

Generate executive summary for {symbol}...
'''
        self.create_test_prompt("meta", "with_metadata", content_with_metadata)
        
        metadata = self.prompt_loader.get_prompt_metadata("meta", "with_metadata")
        
        # Check basic metadata that get_prompt_metadata actually returns
        assert "file_path" in metadata
        assert "file_size" in metadata
        assert "character_count" in metadata
        assert metadata["required_variables"] == ["symbol"]


class TestPromptLoaderIntegration:
    """Integration tests with real prompt files"""
    
    def setup_method(self):
        """Set up with real prompt directory"""
        self.prompt_loader = PromptLoader()
    
    def test_load_all_existing_prompts(self):
        """Test loading all existing prompt files"""
        expected_prompts = [
            ("sentiment_analysis", "management_sentiment_analysis"),
            ("sentiment_analysis", "analyst_confusion_analysis"),
            ("narrative_generation", "executive_summary"),
            ("narrative_generation", "hidden_strengths_identification"),
            ("valuation_analysis", "market_perception_explanation"),
            ("valuation_analysis", "valuation_gap_decomposition"),
            ("valuation_analysis", "fair_value_calculation"),
            ("narrative_generation", "competitor_messaging_analysis"),
            ("narrative_generation", "actionable_recommendations"),
            ("competitive_analysis", "peer_comparison_analysis"),
            ("competitive_analysis", "outlier_detection"),
            ("competitive_analysis", "benchmark_analysis"),
            ("validation", "data_quality_assessment"),
            ("validation", "business_logic_validation"), 
            ("validation", "narrative_consistency_check"),
            ("sentiment_analysis", "sentiment_validation")
        ]
        
        for category, prompt_name in expected_prompts:
            try:
                content = self.prompt_loader.load_prompt(category, prompt_name)
                assert len(content) > 0, f"Empty content for {category}/{prompt_name}"
                assert "{" in content, f"No template variables in {category}/{prompt_name}"
            except PromptLoadError:
                pytest.fail(f"Failed to load {category}/{prompt_name}")
    
    def test_all_prompts_have_required_variables(self):
        """Test that all prompts have expected template variables"""
        prompt_variable_requirements = {
            ("sentiment_analysis", "management_sentiment_analysis"): ["symbol", "management_text", "quarter"],
            ("narrative_generation", "executive_summary"): ["symbol"],
            ("valuation_analysis", "valuation_gap_decomposition"): ["symbol", "target_pe", "peer_average_pe"],
            ("narrative_generation", "actionable_recommendations"): ["symbol", "current_pe", "fair_value_pe"]
        }
        
        for (category, prompt_name), required_vars in prompt_variable_requirements.items():
            try:
                content = self.prompt_loader.load_prompt(category, prompt_name)
                available_vars = self.prompt_loader._extract_template_variables(content)
                
                for required_var in required_vars:
                    assert required_var in available_vars, f"Missing variable {required_var} in {category}/{prompt_name}"
            except PromptLoadError:
                pytest.skip(f"Prompt file {category}/{prompt_name} not found")


class TestPromptLoaderErrors:
    """Test error handling and edge cases"""
    
    def test_invalid_base_path(self):
        """Test handling of invalid base path"""
        with pytest.raises(PromptLoadError):
            invalid_loader = PromptLoader(base_path="/nonexistent/path")
    
    def test_permission_denied(self):
        """Test handling of permission denied errors"""
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = PermissionError("Permission denied")
            
            loader = PromptLoader()
            with pytest.raises(PromptLoadError) as exc_info:
                loader.load_prompt("test", "permission_test")
            
            assert "Permission denied" in str(exc_info.value)
    
    def test_corrupted_file_encoding(self):
        """Test handling of files with encoding issues"""
        with patch("builtins.open", mock_open()) as mock_file:
            mock_file.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
            
            loader = PromptLoader()
            with pytest.raises(PromptLoadError) as exc_info:
                loader.load_prompt("test", "encoding_test")
            
            assert "encoding" in str(exc_info.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])