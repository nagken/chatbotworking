"""
Streaming Message Transformer for CA API System Messages
Transforms individual CA API system messages into frontend-ready format
"""

import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class StreamingMessageTransformer:
    """Transforms individual CA API system messages for frontend consumption"""

    @staticmethod
    def transform_system_message(data_json: Dict[str, Any], sequence: int) -> Optional[Dict[str, Any]]:
        """
        Transform a single CA API system message into frontend-ready format.
        
        Args:
            data_json: Raw system message object from CA API
            sequence: Message sequence number
            
        Returns:
            Transformed message dict ready for frontend, or None if not relevant
        """
        try:
            logger.info(f"🔄 Transforming system message #{sequence}: {list(data_json.keys())}")
            
            if 'systemMessage' not in data_json:
                logger.info("🔸 No systemMessage key, skipping")
                return None
            
            system_msg = data_json['systemMessage']
            timestamp = data_json.get('timestamp')
            
            # Try each transformation method
            transformers = [
                StreamingMessageTransformer._transform_sql_message,
                StreamingMessageTransformer._transform_data_message,
                StreamingMessageTransformer._transform_chart_message,
                StreamingMessageTransformer._transform_insights_message
            ]
            
            for transformer in transformers:
                result = transformer(system_msg, timestamp, sequence)
                if result:
                    logger.info(f"✅ Successfully transformed {result['message_type']} message")
                    return {
                        "type": "system_message",
                        "message_type": result['message_type'],
                        "sequence": sequence,
                        "data": result['data'],
                        "raw_message": data_json,  # Keep original for debugging
                        "timestamp": datetime.now().isoformat()
                    }
            
            logger.info(f"🔸 System message contains no relevant data, skipping")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error transforming system message #{sequence}: {e}")
            return None

    @staticmethod
    def _transform_sql_message(system_msg: Dict[str, Any], timestamp: str, sequence: int) -> Optional[Dict[str, Any]]:
        """Transform SQL generation message"""
        if 'data' in system_msg and 'generatedSql' in system_msg['data']:
            sql_query = system_msg['data']['generatedSql']
            logger.info("🔍 Found SQL generation message")
            
            return {
                'message_type': 'sql',
                'data': {
                    'sql_query': sql_query,
                    'timestamp': timestamp
                }
            }
        return None

    @staticmethod
    def _transform_data_message(system_msg: Dict[str, Any], timestamp: str, sequence: int) -> Optional[Dict[str, Any]]:
        """Transform data result message"""
        if 'data' in system_msg and 'result' in system_msg['data']:
            result_data = system_msg['data']['result']
            
            # Validate required keys (same as original extractor)
            if all(key in result_data for key in ['data', 'schema', 'name']):
                logger.info(f"🔍 Found data result message with {len(result_data['data'])} rows")
                
                # Extract execution time if available
                execution_time = result_data.get('executionTime', '0ms')
                
                return {
                    'message_type': 'data',
                    'data': {
                        'result_data': result_data['data'],
                        'result_schema': result_data['schema'],
                        'result_name': result_data['name'],
                        'execution_time': execution_time,
                        'timestamp': timestamp
                    }
                }
        return None

    @staticmethod
    def _transform_chart_message(system_msg: Dict[str, Any], timestamp: str, sequence: int) -> Optional[Dict[str, Any]]:
        """Transform chart configuration message"""
        if 'chart' in system_msg and 'result' in system_msg['chart']:
            chart_result = system_msg['chart']['result']
            
            if 'vegaConfig' in chart_result:
                logger.info("🔍 Found chart configuration message")
                
                # Extract Vega specification (same logic as original extractor)
                vega_spec = chart_result['vegaConfig']
                
                # Process chart with template engine (reuse original logic)
                processed_chart = StreamingMessageTransformer._process_chart_with_templates(
                    vega_spec, chart_result
                )
                
                if processed_chart:
                    return {
                        'message_type': 'chart',
                        'data': {
                            'chart_config': processed_chart,
                            'timestamp': timestamp
                        }
                    }
        return None

    @staticmethod
    def _transform_insights_message(system_msg: Dict[str, Any], timestamp: str, sequence: int) -> Optional[Dict[str, Any]]:
        """Transform AI insights/text message with document context"""
        if 'text' in system_msg and 'parts' in system_msg['text']:
            text_parts = system_msg['text']['parts']
            insight = "<br>".join(text_parts)
            logger.info(f"🔍 Found AI insights message: {insight[:100]}...")
            
            # Extract document references and add clickable links
            enhanced_insight, document_references = StreamingMessageTransformer._enhance_with_document_links(insight)
            
            result = {
                'message_type': 'insights',
                'data': {
                    'ai_insights': enhanced_insight,
                    'timestamp': timestamp
                }
            }
            
            # Add document references if any were found
            if document_references:
                result['data']['document_references'] = document_references
                logger.info(f"📄 Added {len(document_references)} document references to insights")
            
            return result
        return None

    @staticmethod
    def _enhance_with_document_links(text: str) -> tuple[str, list]:
        """
        Enhance text with clickable document links and extract document references
        
        Args:
            text: Raw AI response text
            
        Returns:
            Tuple of (enhanced_text, document_references_list)
        """
        import re
        import urllib.parse
        
        # Track document references found
        document_references = []
        enhanced_text = text
        
        try:
            # Pattern to match document references in the enhanced message context
            # Look for patterns like "Document 1: Title" or mentions of files
            doc_patterns = [
                r'Document \d+: ([^<\n]+?)(?:\n|<br>|$)',  # "Document 1: Title"
                r'File: ([^<\n]+\.(?:docx?|pdf|xlsx?|pptx?))',  # "File: filename.docx"
                r'([^<\n\s]+\.(?:docx?|pdf|xlsx?|pptx?))',  # Any filename with extension
            ]
            
            processed_files = set()  # Avoid duplicate links
            
            for pattern in doc_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    if pattern.startswith('Document'):
                        # Extract title from "Document N: Title" format
                        doc_title = match.group(1).strip()
                        # Look for the corresponding "File:" line
                        file_pattern = rf'File: ([^<\n]+\.(?:docx?|pdf|xlsx?|pptx?))'
                        file_match = re.search(file_pattern, text[match.end():match.end()+200], re.IGNORECASE)
                        if file_match:
                            filename = file_match.group(1).strip()
                        else:
                            continue  # Skip if no file found
                    else:
                        # Direct filename match
                        filename = match.group(1).strip()
                        doc_title = filename  # Use filename as title
                    
                    # Skip if already processed
                    if filename in processed_files:
                        continue
                    
                    processed_files.add(filename)
                    
                    # Create document URL (encode the filename for URL safety)
                    encoded_filename = urllib.parse.quote(filename)
                    document_url = f"/documents/{encoded_filename}"
                    
                    # Add to references
                    document_references.append({
                        'title': doc_title,
                        'filename': filename,
                        'url': document_url,
                        'type': StreamingMessageTransformer._get_document_type(filename)
                    })
                    
                    # Create clickable link in text
                    link_html = f'<a href="{document_url}" target="_blank" class="document-link" title="Open {filename}">{doc_title}</a>'
                    
                    # Replace the filename in text with a clickable link
                    enhanced_text = enhanced_text.replace(filename, link_html)
            
            # Also look for and enhance any direct mentions of document categories or types
            category_patterns = {
                'contraceptive coverage': '💊 Contraceptive Coverage',
                'prior authorization': '📋 Prior Authorization',
                'medicare part d': '🏥 Medicare Part D',
                'specialty pharmacy': '💉 Specialty Pharmacy',
                'mail order': '📦 Mail Order'
            }
            
            for category, icon_category in category_patterns.items():
                if category.lower() in enhanced_text.lower():
                    enhanced_text = re.sub(
                        re.escape(category), 
                        f'<span class="category-highlight">{icon_category}</span>', 
                        enhanced_text, 
                        flags=re.IGNORECASE
                    )
            
            logger.info(f"📎 Enhanced text with {len(document_references)} document links")
            
        except Exception as e:
            logger.error(f"❌ Error enhancing text with document links: {e}")
            # Return original text if enhancement fails
            return text, []
        
        return enhanced_text, document_references

    @staticmethod
    def _get_document_type(filename: str) -> str:
        """Get document type based on file extension"""
        ext = filename.lower().split('.')[-1]
        type_map = {
            'pdf': 'PDF Document',
            'docx': 'Word Document',
            'doc': 'Word Document',
            'xlsx': 'Excel Spreadsheet',
            'xls': 'Excel Spreadsheet',
            'pptx': 'PowerPoint Presentation',
            'txt': 'Text Document'
        }
        return type_map.get(ext, 'Document')

    @staticmethod
    def _process_chart_with_templates(vega_spec: Dict[str, Any], chart_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process chart configuration with template engine (adapted from original extractor)
        """
        try:
            # Import here to avoid circular dependencies
            from app.utils.chat_response_extractor import (
                validate_vega_specification, 
                _should_enable_zoom
            )
            
            use_template = False
            template_vega_spec = None
            
            # Chart type mapping logic (from original extractor)
            original_chart_type = None
            mapped_chart_type = None
            
            if 'mark' in vega_spec:
                # Extract chart type from mark (same logic as original)
                if isinstance(vega_spec['mark'], str):
                    original_chart_type = vega_spec['mark']
                elif isinstance(vega_spec['mark'], dict) and 'type' in vega_spec['mark']:
                    original_chart_type = vega_spec['mark']['type']
                else:
                    original_chart_type = 'unknown'
                
                # Map chart types (same logic as original)
                if original_chart_type == 'arc' or original_chart_type == 'pie':
                    mapped_chart_type = 'pie'
                elif original_chart_type == 'point':
                    mapped_chart_type = 'scatter'
                else:
                    mapped_chart_type = original_chart_type
                
                # Use mapped type for template generation
                chart_type = mapped_chart_type
                
                encoding = vega_spec.get('encoding', {})
                data = vega_spec.get('data', {})
                title = vega_spec.get('title', '')
                
                # Extract options (same as original)
                options = {
                    'tooltip': vega_spec.get('mark', {}).get('tooltip', False) if isinstance(vega_spec.get('mark'), dict) else False,
                    'zoom': _should_enable_zoom(vega_spec, chart_type),
                    'size': vega_spec.get('mark', {}).get('size', None) if isinstance(vega_spec.get('mark'), dict) else None
                }
                
                # Try to generate from template (same as original)
                try:
                    from app.utils.chart_template_engine import chart_template_engine
                    template_vega_spec = chart_template_engine.generate_vega_spec_from_template(
                        chart_type=chart_type,
                        encoding=encoding,
                        data=data,
                        title=title,
                        options=options
                    )
                    
                    if template_vega_spec:
                        use_template = True
                        logger.info(f"Generated {chart_type} chart from template for streaming")
                    else:
                        logger.info(f"Using native Vega-Lite rendering for {chart_type} chart (streaming)")
                        
                except Exception as e:
                    logger.error(f"Error in template generation for streaming: {e}, using original")
            
            # Use template-generated spec if available, otherwise use original
            final_vega_spec = template_vega_spec if use_template else vega_spec
            
            # Validate the final Vega specification (same as original)
            validation_result = validate_vega_specification(final_vega_spec)
            
            if not validation_result['is_valid']:
                logger.warning(f"Invalid Vega specification in streaming: {validation_result['error']}")
                return None
            
            # Use cleaned specification
            cleaned_vega_spec = validation_result['cleaned_spec']
            
            # Extract chart metadata (same as original)
            chart_metadata = {}
            if 'title' in chart_result:
                chart_metadata['title'] = chart_result['title']
            if 'description' in chart_result:
                chart_metadata['description'] = chart_result['description']
            
            # Use mapped chart type (same logic as original)
            if mapped_chart_type is not None:
                chart_metadata['chart_type'] = mapped_chart_type
                logger.info(f"Streaming chart type: {original_chart_type} → {mapped_chart_type}")
            else:
                # Fallback logic (same as original)
                if 'mark' in cleaned_vega_spec:
                    mark = cleaned_vega_spec['mark']
                    if isinstance(mark, str):
                        fallback_original_type = mark
                    elif isinstance(mark, dict) and 'type' in mark:
                        fallback_original_type = mark['type']
                    else:
                        fallback_original_type = 'unknown'
                    
                    # Apply same mapping logic
                    if fallback_original_type == 'arc' or fallback_original_type == 'pie':
                        chart_metadata['chart_type'] = 'pie'
                    elif fallback_original_type == 'point':
                        chart_metadata['chart_type'] = 'scatter'
                    else:
                        chart_metadata['chart_type'] = fallback_original_type
                elif 'layer' in cleaned_vega_spec:
                    chart_metadata['chart_type'] = 'layered'
                elif 'facet' in cleaned_vega_spec:
                    chart_metadata['chart_type'] = 'faceted'
                else:
                    chart_metadata['chart_type'] = 'unknown'
            
            # Add template usage metadata
            chart_metadata['template_used'] = use_template
            
            # Set default rendering options (same as original)
            rendering_options = {
                'width': 'container',
                'height': 400,
                'theme': 'default'
            }
            
            return {
                'vega_spec': cleaned_vega_spec,
                'chart_metadata': chart_metadata,
                'rendering_options': rendering_options
            }
            
        except Exception as e:
            logger.error(f"Error processing chart with templates in streaming: {e}")
            return None


# Create global instance
streaming_transformer = StreamingMessageTransformer()
