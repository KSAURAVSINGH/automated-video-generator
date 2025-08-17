"""
Enhanced Text Improver using Google Gemini API
Provides AI-powered text enhancement for video titles, descriptions, and tags
"""

import logging
import requests
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class TextImprover:
    """
    Enhanced text improver using Google Gemini API for better content enhancement
    """
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        # Try to get API key from environment if not provided
        if not gemini_api_key:
            try:
                from src.config.env_config import env_config
                gemini_api_key = env_config.get_gemini_api_key()
                if gemini_api_key:
                    logger.info("✅ Gemini API key loaded from environment configuration")
            except ImportError:
                logger.warning("⚠️ Environment config not available, using provided API key")
        
        self.gemini_api_key = gemini_api_key
        self.gemini_base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
        
        # Fallback methods if Gemini is not available
        self.fallback_methods = [
            self._improve_with_basic_rules,
            self._improve_tags_with_basic_rules
        ]
        
        logger.info("🤖 Enhanced Text Improver initialized")
        if self.gemini_api_key:
            logger.info("✅ Google Gemini API configured")
        else:
            logger.info("⚠️ Google Gemini API key not provided, using fallback methods")
    
    def improve_title(self, title: str, genre: str, tone: str) -> str:
        """
        Improve video title using Google Gemini API
        
        Args:
            title: Original title
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Improved title
        """
        try:
            if self.gemini_api_key:
                improved_title = self._improve_with_gemini(
                    content_type="title",
                    original_text=title,
                    genre=genre,
                    tone=tone
                )
                if improved_title:
                    logger.info(f"✅ Title improved with Gemini API: {improved_title}")
                    return improved_title
            
            # Fallback to basic improvements
            improved_title = self._improve_with_basic_rules(title, genre, tone)
            logger.info(f"✅ Title improved with fallback method: {improved_title}")
            return improved_title
            
        except Exception as e:
            logger.error(f"❌ Title improvement failed: {e}")
            return title
    
    def improve_description(self, description: str, genre: str, tone: str) -> str:
        """
        Improve video description using Google Gemini API
        
        Args:
            description: Original description
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Improved description
        """
        try:
            if self.gemini_api_key:
                improved_description = self._improve_with_gemini(
                    content_type="description",
                    original_text=description,
                    genre=genre,
                    tone=tone
                )
                if improved_description:
                    logger.info(f"✅ Description improved with Gemini API: {improved_description[:100]}...")
                    return improved_description
            
            # Fallback to basic improvements
            improved_description = self._improve_with_basic_rules(description, genre, tone)
            logger.info(f"✅ Description improved with fallback method: {improved_description[:100]}...")
            return improved_description
            
        except Exception as e:
            logger.error(f"❌ Description improvement failed: {e}")
            return description
    
    def improve_tags(self, tags: List[str], title: str = None, description: str = None, genre: str = None, tone: str = None) -> List[str]:
        """
        Improve video tags using Google Gemini API
        
        Args:
            tags: Original tags list
            title: Video title
            description: Video description
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Improved tags list
        """
        try:
            if self.gemini_api_key:
                improved_tags = self._improve_tags_with_gemini(
                    original_tags=tags,
                    title=title,
                    description=description,
                    genre=genre,
                    tone=tone
                )
                if improved_tags:
                    logger.info(f"✅ Tags improved with Gemini API: {len(improved_tags)} tags")
                    return improved_tags
            
            # Fallback to basic improvements
            improved_tags = self._improve_tags_with_basic_rules(tags, title, description, genre, tone)
            logger.info(f"✅ Tags improved with fallback method: {len(improved_tags)} tags")
            return improved_tags
            
        except Exception as e:
            logger.error(f"❌ Tag improvement failed: {e}")
            return tags
    
    def improve_all_content(self, title: str, description: str, tags: List[str], genre: str, tone: str) -> Dict[str, Any]:
        """
        Improve all content (title, description, tags) using Google Gemini API
        
        Args:
            title: Original title
            description: Original description
            tags: Original tags list
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Dictionary with improved title, description, and tags
        """
        try:
            if self.gemini_api_key:
                improved_content = self._improve_all_content_with_gemini(
                    title=title,
                    description=description,
                    tags=tags,
                    genre=genre,
                    tone=tone
                )
                if improved_content:
                    logger.info("✅ All content improved with Gemini API")
                    return improved_content
            
            # Fallback to individual improvements
            improved_title = self.improve_title(title, genre, tone)
            improved_description = self.improve_description(description, genre, tone)
            improved_tags = self.improve_tags(tags, title, description, genre, tone)
            
            logger.info("✅ All content improved with fallback methods")
            return {
                'title': improved_title,
                'description': improved_description,
                'tags': improved_tags
            }
            
        except Exception as e:
            logger.error(f"❌ All content improvement failed: {e}")
            return {
                'title': title,
                'description': description,
                'tags': tags
            }
    
    def _improve_with_gemini(self, content_type: str, original_text: str, genre: str, tone: str) -> Optional[str]:
        """
        Improve text using Google Gemini API
        
        Args:
            content_type: Type of content (title, description, tags)
            original_text: Original text to improve
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Improved text or None if failed
        """
        try:
            # Create context-aware prompt for Gemini
            prompt = self._create_gemini_prompt(content_type, original_text, genre, tone)
            
            # Prepare request payload for Gemini API
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make request to Gemini API
            headers = {
                "Content-Type": "application/json",
            }
            
            url = f"{self.gemini_base_url}?key={self.gemini_api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract generated text from Gemini response
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if len(parts) > 0 and 'text' in parts[0]:
                            improved_text = parts[0]['text'].strip()
                            
                            # Clean up the response
                            improved_text = self._clean_gemini_response(improved_text, content_type)
                            
                            if improved_text and improved_text != original_text:
                                return improved_text
                            else:
                                logger.warning("⚠️ Gemini returned unchanged or empty text")
                                return None
                
                logger.warning("⚠️ Unexpected Gemini API response format")
                return None
                
            else:
                logger.error(f"❌ Gemini API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error calling Gemini API: {e}")
            return None
    
    def _improve_tags_with_gemini(self, original_tags: List[str], title: str = None, description: str = None, genre: str = None, tone: str = None) -> Optional[List[str]]:
        """
        Improve tags using Google Gemini API
        
        Args:
            original_tags: Original tags list
            title: Video title
            description: Video description
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Improved tags list or None if failed
        """
        try:
            # Create context-aware prompt for tag improvement
            prompt = self._create_gemini_tag_prompt(original_tags, title, description, genre, tone)
            
            # Prepare request payload for Gemini API
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make request to Gemini API
            headers = {
                "Content-Type": "application/json",
            }
            
            url = f"{self.gemini_base_url}?key={self.gemini_api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract generated text from Gemini response
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if len(parts) > 0 and 'text' in parts[0]:
                            improved_tags_text = parts[0]['text'].strip()
                            
                            # Parse the improved tags
                            improved_tags = self._parse_gemini_tags(improved_tags_text)
                            
                            if improved_tags and len(improved_tags) > 0:
                                return improved_tags
                            else:
                                logger.warning("⚠️ Gemini returned invalid tags format")
                                return None
                
                logger.warning("⚠️ Unexpected Gemini API response format")
                return None
                
            else:
                logger.error(f"❌ Gemini API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error calling Gemini API for tags: {e}")
            return None
    
    def _improve_all_content_with_gemini(self, title: str, description: str, tags: List[str], genre: str, tone: str) -> Optional[Dict[str, Any]]:
        """
        Improve all content using Google Gemini API in a single call
        
        Args:
            title: Original title
            description: Original description
            tags: Original tags list
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Dictionary with improved content or None if failed
        """
        try:
            # Create comprehensive prompt for all content improvement
            prompt = self._create_gemini_comprehensive_prompt(title, description, tags, genre, tone)
            
            # Prepare request payload for Gemini API
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 2048,
                }
            }
            
            # Make request to Gemini API
            headers = {
                "Content-Type": "application/json",
            }
            
            url = f"{self.gemini_base_url}?key={self.gemini_api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract generated text from Gemini response
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        if len(parts) > 0 and 'text' in parts[0]:
                            improved_content_text = parts[0]['text'].strip()
                            
                            # Parse the comprehensive response
                            improved_content = self._parse_gemini_comprehensive_response(improved_content_text)
                            
                            if improved_content:
                                return improved_content
                            else:
                                logger.warning("⚠️ Gemini returned invalid comprehensive response format")
                                return None
                
                logger.warning("⚠️ Unexpected Gemini API response format")
                return None
                
            else:
                logger.error(f"❌ Gemini API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error calling Gemini API for comprehensive improvement: {e}")
            return None
    
    def _create_gemini_prompt(self, content_type: str, original_text: str, genre: str, tone: str) -> str:
        """
        Create a context-aware prompt for Gemini API
        
        Args:
            content_type: Type of content (title, description, tags)
            original_text: Original text to improve
            genre: Video genre/category
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Formatted prompt for Gemini API
        """
        if content_type == "title":
            return f"""You are an expert video content creator and SEO specialist. Your task is to improve a video title to make it more engaging, clickable, and optimized for {genre} content with a {tone} tone.

Original Title: "{original_text}"
Genre: {genre}
Tone: {tone}

Requirements:
1. Make it more engaging and clickable
2. Optimize for {genre} audience
3. Maintain the {tone} tone
4. Keep it concise (under 60 characters if possible)
5. Include relevant keywords for {genre}
6. Make it compelling for social media sharing

Provide ONLY the improved title, nothing else. No explanations, no quotes, just the title."""

        elif content_type == "description":
            return f"""You are an expert video content creator and copywriter. Your task is to improve a video description to make it more engaging, informative, and optimized for {genre} content with a {tone} tone.

Original Description: "{original_text}"
Genre: {genre}
Tone: {tone}

Requirements:
1. Make it more engaging and informative
2. Optimize for {genre} audience
3. Maintain the {tone} tone
4. Include relevant keywords naturally
5. Add a call-to-action if appropriate
6. Make it compelling for viewers to watch
7. Keep it under 5000 characters

Provide ONLY the improved description, nothing else. No explanations, no quotes, just the description."""

        else:
            return f"""You are an expert video content creator and SEO specialist. Your task is to improve text content to make it more engaging and optimized for {genre} content with a {tone} tone.

Original Text: "{original_text}"
Genre: {genre}
Tone: {tone}

Requirements:
1. Make it more engaging and optimized
2. Optimize for {genre} audience
3. Maintain the {tone} tone
4. Include relevant keywords naturally
5. Make it compelling for the target audience

Provide ONLY the improved text, nothing else. No explanations, no quotes, just the improved text."""
    
    def _create_gemini_tag_prompt(self, original_tags: List[str], title: str = None, description: str = None, genre: str = None, tone: str = None) -> str:
        """
        Create a context-aware prompt for tag improvement using Gemini API
        
        Args:
            original_tags: Original tags list
            title: Video title
            description: Video description
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Formatted prompt for Gemini API
        """
        context = f"Genre: {genre}, Tone: {tone}"
        if title:
            context += f", Title: {title}"
        if description:
            context += f", Description: {description[:200]}..."
        
        return f"""You are an expert video content creator and SEO specialist. Your task is to improve and expand video tags to make them more relevant, searchable, and optimized for {genre} content.

Original Tags: {', '.join(original_tags)}
{context}

Requirements:
1. Expand the tag list with relevant keywords for {genre}
2. Include trending and popular terms for {genre} content
3. Add long-tail keywords for better searchability
4. Maintain the {tone} tone in tag selection
5. Include both broad and specific tags
6. Optimize for YouTube search and discovery
7. Provide 15-25 relevant tags

Format your response as a comma-separated list of tags, nothing else. No explanations, no quotes, just the tags separated by commas."""
    
    def _create_gemini_comprehensive_prompt(self, title: str, description: str, tags: List[str], genre: str, tone: str) -> str:
        """
        Create a comprehensive prompt for improving all content using Gemini API
        
        Args:
            title: Original title
            description: Original description
            tags: Original tags list
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Formatted comprehensive prompt for Gemini API
        """
        return f"""You are an expert video content creator, SEO specialist, and copywriter. Your task is to comprehensively improve video content to make it more engaging, clickable, and optimized for {genre} content with a {tone} tone.

ORIGINAL CONTENT:
Title: "{title}"
Description: "{description}"
Tags: {', '.join(tags)}

Genre: {genre}
Tone: {tone}

REQUIREMENTS:

TITLE:
- Make it more engaging and clickable
- Optimize for {genre} audience
- Maintain the {tone} tone
- Keep it concise (under 60 characters if possible)
- Include relevant keywords for {genre}
- Make it compelling for social media sharing

DESCRIPTION:
- Make it more engaging and informative
- Optimize for {genre} audience
- Maintain the {tone} tone
- Include relevant keywords naturally
- Add a call-to-action if appropriate
- Make it compelling for viewers to watch
- Keep it under 5000 characters

TAGS:
- Expand with relevant keywords for {genre}
- Include trending and popular terms
- Add long-tail keywords for better searchability
- Maintain the {tone} tone
- Include both broad and specific tags
- Optimize for YouTube search and discovery
- Provide 15-25 relevant tags

FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
TITLE: [improved title]
DESCRIPTION: [improved description]
TAGS: [tag1, tag2, tag3, tag4, tag5, tag6, tag7, tag8, tag9, tag10, tag11, tag12, tag13, tag14, tag15]"""
    
    def _clean_gemini_response(self, response: str, content_type: str) -> str:
        """
        Clean up Gemini API response
        
        Args:
            response: Raw response from Gemini API
            content_type: Type of content being cleaned
            
        Returns:
            Cleaned response text
        """
        # Remove common prefixes and quotes
        cleaned = response.strip()
        
        # Remove quotes if present
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        elif cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]
        
        # Remove common prefixes
        prefixes_to_remove = [
            "Improved title:",
            "Improved description:",
            "Title:",
            "Description:",
            "Here's the improved",
            "The improved",
            "Improved:"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        return cleaned
    
    def _parse_gemini_tags(self, tags_text: str) -> List[str]:
        """
        Parse tags from Gemini API response
        
        Args:
            tags_text: Raw tags text from Gemini API
            
        Returns:
            List of parsed tags
        """
        try:
            # Clean the response
            cleaned_text = self._clean_gemini_response(tags_text, "tags")
            
            # Split by commas and clean each tag
            tags = [tag.strip().strip('"').strip("'") for tag in cleaned_text.split(',')]
            
            # Filter out empty tags and clean them
            tags = [tag for tag in tags if tag and len(tag) > 0]
            
            # Remove duplicates while preserving order
            seen = set()
            unique_tags = []
            for tag in tags:
                if tag.lower() not in seen:
                    seen.add(tag.lower())
                    unique_tags.append(tag)
            
            return unique_tags
            
        except Exception as e:
            logger.error(f"❌ Error parsing Gemini tags: {e}")
            return []
    
    def _parse_gemini_comprehensive_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse comprehensive response from Gemini API
        
        Args:
            response_text: Raw comprehensive response from Gemini API
            
        Returns:
            Dictionary with parsed content or None if failed
        """
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('TITLE:'):
                    result['title'] = line[6:].strip()
                elif line.startswith('DESCRIPTION:'):
                    result['description'] = line[12:].strip()
                elif line.startswith('TAGS:'):
                    tags_text = line[5:].strip()
                    result['tags'] = self._parse_gemini_tags(tags_text)
            
            # Validate that we have all required fields
            if 'title' in result and 'description' in result and 'tags' in result:
                return result
            else:
                logger.warning("⚠️ Incomplete comprehensive response from Gemini")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error parsing Gemini comprehensive response: {e}")
            return None
    
    def _improve_with_basic_rules(self, text: str, genre: str, tone: str) -> str:
        """
        Basic text improvement using rule-based methods (fallback)
        
        Args:
            text: Original text
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Improved text
        """
        improved = text
        
        # Add genre-specific keywords
        genre_keywords = {
            "education": ["learn", "discover", "explore", "understand", "master"],
            "gaming": ["gameplay", "strategy", "tips", "tricks", "walkthrough"],
            "comedy": ["funny", "hilarious", "entertaining", "laugh", "humor"],
            "music": ["music", "song", "melody", "rhythm", "beat"],
            "sports": ["sports", "athletic", "performance", "training", "skills"]
        }
        
        if genre.lower() in genre_keywords:
            keywords = genre_keywords[genre.lower()]
            # Add a relevant keyword if not present
            for keyword in keywords:
                if keyword.lower() not in improved.lower():
                    improved = f"{improved} - {keyword.title()}"
                    break
        
        # Add tone-specific enhancements
        if tone.lower() == "funny":
            improved = f"😂 {improved}"
        elif tone.lower() == "serious":
            improved = f"📚 {improved}"
        elif tone.lower() == "educational":
            improved = f"🎓 {improved}"
        
        return improved
    
    def _improve_tags_with_basic_rules(self, tags: List[str], title: str = None, description: str = None, genre: str = None, tone: str = None) -> List[str]:
        """
        Basic tag improvement using rule-based methods (fallback)
        
        Args:
            tags: Original tags list
            title: Video title
            description: Video description
            genre: Video genre/category
            tone: Desired tone/style
            
        Returns:
            Improved tags list
        """
        improved_tags = tags.copy()
        
        # Add genre-specific tags
        genre_tags = {
            "education": ["learning", "knowledge", "study", "tutorial", "how-to"],
            "gaming": ["gaming", "gameplay", "strategy", "tips", "walkthrough"],
            "comedy": ["comedy", "funny", "humor", "entertainment", "laugh"],
            "music": ["music", "song", "audio", "melody", "rhythm"],
            "sports": ["sports", "athletic", "performance", "training", "fitness"]
        }
        
        if genre and genre.lower() in genre_tags:
            additional_tags = genre_tags[genre.lower()]
            for tag in additional_tags:
                if tag.lower() not in [t.lower() for t in improved_tags]:
                    improved_tags.append(tag)
        
        # Add tone-specific tags
        if tone:
            if tone.lower() == "funny":
                improved_tags.extend(["funny", "humor", "comedy"])
            elif tone.lower() == "serious":
                improved_tags.extend(["serious", "professional", "informative"])
            elif tone.lower() == "educational":
                improved_tags.extend(["educational", "learning", "tutorial"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in improved_tags:
            if tag.lower() not in seen:
                seen.add(tag.lower())
                unique_tags.append(tag)
        
        return unique_tags
    
    def set_gemini_api_key(self, api_key: str):
        """
        Set or update the Gemini API key
        
        Args:
            api_key: Google Gemini API key
        """
        self.gemini_api_key = api_key
        if api_key:
            logger.info("✅ Google Gemini API key updated")
        else:
            logger.warning("⚠️ Google Gemini API key removed")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the text improver
        
        Returns:
            Dictionary with status information
        """
        return {
            'gemini_configured': bool(self.gemini_api_key),
            'fallback_methods': len(self.fallback_methods),
            'api_endpoint': self.gemini_base_url if self.gemini_api_key else None
        }
