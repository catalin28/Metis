"""
Test Suite for Prompt Loader

Tests the mandatory prompt loading functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.metis.utils.prompt_loader import PromptLoader, PromptLoadError, PromptValidationError


class TestPromptLoader:
    """Test cases for PromptLoader utility"""
    
    def setup_method(self):
        """Setup test environment with temporary prompt files"""
        self.temp_dir = tempfile.mkdtemp()
        self.prompt_loader = PromptLoader(base_path=self.temp_dir)
        
        # Create test prompt directories
        self.sentiment_dir = Path(self.temp_dir) / "sentiment_analysis"
        self.valuation_dir = Path(self.temp_dir) / "valuation_analysis"
        
        self.sentiment_dir.mkdir()
        self.valuation_dir.mkdir()
        
        # Create test prompt files
        self.test_prompt_content = """
        Analyze the sentiment of {text} for company {symbol}.
        
        Consider these factors:
        - {factor1}
        - {factor2}
        
        Return results in JSON format.
        """
        
        with open(self.sentiment_dir / "test_prompt.txt", "w") as f:
            f.write(self.test_prompt_content)
    
    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_load_prompt_success(self):
        """Test successful prompt loading"""
        content = self.prompt_loader.load_prompt("sentiment_analysis", "test_prompt")
        assert content.strip() == self.test_prompt_content.strip()
    
    def test_load_prompt_file_not_found(self):
        """Test error handling for missing prompt file"""
        with pytest.raises(PromptLoadError) as exc_info:
            self.prompt_loader.load_prompt("sentiment_analysis", "nonexistent")
        
        assert "not found" in str(exc_info.value)
    
    def test_load_prompt_invalid_category(self):
        """Test error handling for invalid category"""
        with pytest.raises(PromptLoadError) as exc_info:
            self.prompt_loader.load_prompt("invalid_category", "test_prompt")
        
        assert "not found" in str(exc_info.value)
    
    def test_format_prompt_success(self):
        """Test successful prompt formatting"""
        formatted = self.prompt_loader.format_prompt(
            "sentiment_analysis", 
            "test_prompt",
            text="Sample earnings call text",
            symbol="WRB",
            factor1="Management confidence",
            factor2="Financial performance"
        )
        
        assert "Sample earnings call text" in formatted
        assert "WRB" in formatted
        assert "Management confidence" in formatted
        assert "Financial performance" in formatted
    
    def test_format_prompt_missing_variables(self):
        """Test error handling for missing variables"""
        with pytest.raises(PromptValidationError) as exc_info:
            self.prompt_loader.format_prompt(
                "sentiment_analysis",
                "test_prompt",
                text="Sample text"
                # Missing: symbol, factor1, factor2
            )
        
        assert "Missing required variables" in str(exc_info.value)
        assert "symbol" in str(exc_info.value)
    
    def test_validate_prompt_variables_success(self):
        """Test successful variable validation"""
        result = self.prompt_loader.validate_prompt_variables(
            "sentiment_analysis",
            "test_prompt",
            text="Sample text",
            symbol="WRB",
            factor1="Factor 1",
            factor2="Factor 2"
        )
        
        assert result is True
    
    def test_validate_prompt_variables_missing(self):
        """Test variable validation with missing variables"""
        with pytest.raises(PromptValidationError) as exc_info:
            self.prompt_loader.validate_prompt_variables(
                "sentiment_analysis",
                "test_prompt",
                text="Sample text"
                # Missing: symbol, factor1, factor2
            )
        
        error_msg = str(exc_info.value)
        assert "symbol" in error_msg
        assert "factor1" in error_msg
        assert "factor2" in error_msg
    
    def test_list_available_prompts(self):
        """Test listing available prompts"""
        prompts = self.prompt_loader.list_available_prompts()
        
        assert "sentiment_analysis" in prompts
        assert "test_prompt" in prompts["sentiment_analysis"]
    
    def test_get_prompt_metadata(self):
        """Test getting prompt metadata"""
        metadata = self.prompt_loader.get_prompt_metadata("sentiment_analysis", "test_prompt")
        
        assert "file_path" in metadata
        assert "character_count" in metadata
        assert "required_variables" in metadata
        assert "symbol" in metadata["required_variables"]
        assert "text" in metadata["required_variables"]
    
    def test_prompt_caching(self):
        """Test prompt caching functionality"""
        # Load prompt twice
        content1 = self.prompt_loader.load_prompt("sentiment_analysis", "test_prompt")
        content2 = self.prompt_loader.load_prompt("sentiment_analysis", "test_prompt")
        
        assert content1 == content2
        
        # Clear cache and reload
        self.prompt_loader.clear_cache()
        content3 = self.prompt_loader.load_prompt("sentiment_analysis", "test_prompt")
        
        assert content3 == content1
    
    def test_empty_prompt_file(self):
        """Test handling of empty prompt file"""
        empty_file = self.sentiment_dir / "empty_prompt.txt"
        empty_file.write_text("")
        
        with pytest.raises(PromptLoadError) as exc_info:
            self.prompt_loader.load_prompt("sentiment_analysis", "empty_prompt")
        
        assert "empty" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])