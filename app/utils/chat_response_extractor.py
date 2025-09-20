"""
Utility functions for extracting specific data from chat response arrays
"""

import json
from typing import Dict, Any, Optional, List
from app.models.schemas import ChatResponseExtract, DataResult
import logging

logger = logging.getLogger(__name__)


def extract_chat_response_data(chat_response_array: List[Dict[str, Any]], response_id: str) -> ChatResponseExtract:
    """
    Extract specific data points from a chat response array.
    
    Args:
        chat_response_array: List of chat response objects from Gemini API
        response_id: Unique identifier for this response (UUID)
        
    Returns:
        ChatResponseExtract: Structured data containing SQL, results, and chart config
    """
    if not chat_response_array:
        return ChatResponseExtract(
            response_id=response_id,
            generated_sql=None,
            insight=None,
            execution_result=None,
            chart_config=None,
            metadata={
                "sql_found": False,
                "result_found": False,
                "chart_found": False,
                "insight_found": False,
                "total_responses_processed": 0,
                "error": "Empty response array"
            }
        )

    # with open("chat_response_array.json", "w") as f:
    #     json.dump(chat_response_array, f)
    
    # Initialize variables
    latest_sql = None
    sql_timestamp = None
    execution_result = None
    chart_config = None
    insight = None
    execution_time = None
    
    # Track what we find
    sql_found = False
    result_found = False
    chart_found = False
    insight_found = False

    # Process each response object
    for response_obj in chat_response_array:
        if not isinstance(response_obj, dict):
            continue
        
        logger.info(f"\n\nresponse object: {response_obj}\n\n")
        system_message = response_obj.get('systemMessage', {})
        timestamp = response_obj.get('timestamp')
        
        # Look for generated SQL (get the latest one)
        if 'data' in system_message and 'generatedSql' in system_message['data']:
            latest_sql = system_message['data']['generatedSql']
            sql_timestamp = timestamp
            sql_found = True
        
        # Look for execution results
        if 'data' in system_message and 'result' in system_message['data']:
            result_data = system_message['data']['result']
            if all(key in result_data for key in ['data', 'schema', 'name']):
                execution_result = DataResult(
                    data=result_data['data'],
                    schema=result_data['schema'],
                    name=result_data['name']
                )
                result_found = True
                
                # Look for execution time if available
                if 'executionTime' in result_data:
                    execution_time = result_data['executionTime']

        # Look for insights as "text" in the system message
        if 'text' in system_message and 'parts' in system_message['text']:
            text_parts = system_message['text']['parts']
            insight = "<br>".join(text_parts)
            insight_found = True
            logger.info(f"AI insight extracted: {insight[:100]}...")
            break
    
        
        # Look for chart configuration
        if 'chart' in system_message and 'result' in system_message['chart']:
            chart_result = system_message['chart']['result']
            if 'vegaConfig' in chart_result:
                # Extract Vega specification
                vega_spec = chart_result['vegaConfig']
                
                # Check if we should use template-based approach
                use_template = False
                template_vega_spec = None
                
                # PRESERVE ORIGINAL CHART TYPE INFORMATION FOR CONSISTENCY
                original_chart_type = None
                mapped_chart_type = None
                
                if 'mark' in vega_spec:
                    # Extract chart type from mark (string or object)
                    if isinstance(vega_spec['mark'], str):
                        original_chart_type = vega_spec['mark']
                    elif isinstance(vega_spec['mark'], dict) and 'type' in vega_spec['mark']:
                        original_chart_type = vega_spec['mark']['type']
                    else:
                        original_chart_type = 'unknown'
                    
                    # Map chart types for template compatibility BEFORE template generation
                    # STORE BOTH original and mapped types for consistency
                    if original_chart_type == 'arc' or original_chart_type == 'pie':
                        mapped_chart_type = 'pie'
                    elif original_chart_type == 'point':
                        mapped_chart_type = 'scatter'  # Map point charts to scatter for template compatibility
                    else:
                        mapped_chart_type = original_chart_type
                    
                    # Use mapped type for template generation
                    chart_type = mapped_chart_type
                    
                    encoding = vega_spec.get('encoding', {})
                    data = vega_spec.get('data', {})
                    title = vega_spec.get('title', '')
                    
                    # Extract options from mark and encoding
                    options = {
                        'tooltip': vega_spec['mark'].get('tooltip', False),
                        'zoom': _should_enable_zoom(vega_spec, chart_type),
                        'size': vega_spec['mark'].get('size', None)  # Handle size expressions
                    }
                    
                    # Try to generate from template
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
                            logger.info(f"Successfully generated {chart_type} chart from template")
                        else:
                            logger.info(f"Using native Vega-Lite rendering for {chart_type} chart (no template processing)")
                            
                    except Exception as e:
                        logger.error(f"Error in template generation: {e}, falling back to original vegaConfig")
                
                # Use template-generated spec if available, otherwise use original
                final_vega_spec = template_vega_spec if use_template else vega_spec
                
                # Validate the final Vega specification
                validation_result = validate_vega_specification(final_vega_spec)
                
                if not validation_result['is_valid']:
                    logger.warning(f"Invalid Vega specification: {validation_result['error']}")
                    # Continue without chart if invalid
                    continue
                
                # Use cleaned specification
                cleaned_vega_spec = validation_result['cleaned_spec']
                
                # Extract chart metadata if available
                chart_metadata = {}
                if 'title' in chart_result:
                    chart_metadata['title'] = chart_result['title']
                if 'description' in chart_result:
                    chart_metadata['description'] = chart_result['description']
                
                # Use the SAME mapped chart type that was used for template generation
                # This ensures PERFECT consistency between template selection and metadata
                if 'mapped_chart_type' in locals() and mapped_chart_type is not None:
                    # Use the mapped chart type that was determined during template generation
                    chart_metadata['chart_type'] = mapped_chart_type
                    logger.info(f"Using consistent chart type: {original_chart_type} → {mapped_chart_type}")
                else:
                    # Fallback: determine chart type from cleaned spec (for non-template cases)
                    if 'mark' in cleaned_vega_spec:
                        mark = cleaned_vega_spec['mark']
                        if isinstance(mark, str):
                            fallback_original_type = mark
                        elif isinstance(mark, dict) and 'type' in mark:
                            fallback_original_type = mark['type']
                        else:
                            fallback_original_type = 'unknown'
                        
                        # Apply same mapping logic as fallback
                        if fallback_original_type == 'arc' or fallback_original_type == 'pie':
                            chart_metadata['chart_type'] = 'pie'
                        elif fallback_original_type == 'point':
                            chart_metadata['chart_type'] = 'scatter'
                        else:
                            chart_metadata['chart_type'] = fallback_original_type
                        
                        logger.info(f"Fallback chart type mapping: {fallback_original_type} → {chart_metadata['chart_type']}")
                    elif 'layer' in cleaned_vega_spec:
                        chart_metadata['chart_type'] = 'layered'
                    elif 'facet' in cleaned_vega_spec:
                        chart_metadata['chart_type'] = 'faceted'
                    else:
                        chart_metadata['chart_type'] = 'unknown'
                
                # Add template usage metadata
                chart_metadata['template_used'] = use_template
                
                # Set default rendering options
                rendering_options = {
                    'width': 'container',
                    'height': 400,
                    'theme': 'default'
                }
                
                # Create structured chart response
                from app.models.schemas import ChartResponse
                chart_config = ChartResponse(
                    vega_spec=cleaned_vega_spec,
                    chart_metadata=chart_metadata,
                    rendering_options=rendering_options
                )
                chart_found = True
    
    # Build metadata
    metadata = {
        "sql_found": sql_found,
        "result_found": result_found,
        "chart_found": chart_found,
        "insight_found": insight_found,
        "total_responses_processed": len(chat_response_array)
    }
    
    # Add SQL timestamp if found
    if sql_timestamp:
        metadata["sql_timestamp"] = sql_timestamp
    
    # Add execution time if found
    if execution_time:
        metadata["execution_time"] = execution_time
    
    # Add chart metadata if found
    if chart_found and chart_config:
        metadata["chart_type"] = chart_config.chart_metadata.get("chart_type", "unknown")
        metadata["chart_title"] = chart_config.chart_metadata.get("title", "Untitled Chart")
        metadata["vega_spec_valid"] = True  # Since we validated it
    
    return ChatResponseExtract(
        response_id=response_id,
        generated_sql=latest_sql,
        insight=insight,
        execution_result=execution_result,
        chart_config=chart_config,
        metadata=metadata
    )


def validate_vega_specification(vega_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and clean Vega-Lite specification for frontend rendering.
    Enhanced with responsive design capabilities.
    
    Args:
        vega_spec: Raw Vega-Lite specification from API response
        
    Returns:
        Dict containing validation result and cleaned specification
    """
    if not vega_spec or not isinstance(vega_spec, dict):
        return {
            'is_valid': False,
            'error': 'Invalid Vega specification format',
            'cleaned_spec': None
        }
    
    # Check for required Vega-Lite fields
    # Valid Vega-Lite specs can have either:
    # 1. mark + encoding (simple charts)
    # 2. layer (layered charts)
    # 3. facet (faceted charts)
    # 4. concat/hconcat/vconcat (concatenated charts)
    
    has_mark_encoding = 'mark' in vega_spec and 'encoding' in vega_spec
    has_layer = 'layer' in vega_spec
    has_facet = 'facet' in vega_spec
    has_concat = any(key in vega_spec for key in ['concat', 'hconcat', 'vconcat'])
    
    if not (has_mark_encoding or has_layer or has_facet or has_concat):
        return {
            'is_valid': False,
            'error': 'Missing required Vega-Lite structure: must have either (mark + encoding), layer, facet, or concat',
            'cleaned_spec': None
        }
    
    # Ensure data field exists (required for Vega-Lite)
    if 'data' not in vega_spec:
        # Add placeholder data if missing
        vega_spec['data'] = {'values': []}
    
    # Clean and standardize the specification
    cleaned_spec = vega_spec.copy()
    
    # Ensure proper schema version
    if '$schema' not in cleaned_spec:
        cleaned_spec['$schema'] = 'https://vega.github.io/schema/vega-lite/v5.json'
    

    
    # Set responsive design properties
    cleaned_spec = enhance_vega_spec_with_responsive_design(cleaned_spec)
    
    return {
        'is_valid': True,
        'error': None,
        'cleaned_spec': cleaned_spec
    }


def _should_enable_zoom(vega_spec: Dict[str, Any], chart_type: str) -> bool:
    """
    Determine if zoom functionality should be enabled based on chart characteristics
    
    Args:
        vega_spec: Vega-Lite specification
        chart_type: Type of chart
        
    Returns:
        True if zoom should be enabled
    """
    if chart_type != 'bar':
        return False
        
    encoding = vega_spec.get('encoding', {})
    data = vega_spec.get('data', {})
    
    # Check for temporal data - always benefits from zoom
    if 'x' in encoding:
        x_encoding = encoding['x']
        if x_encoding.get('type') == 'temporal':
            return True
            
        # Check for explicit scale domains that suggest large datasets
        if 'scale' in x_encoding and 'domain' in x_encoding['scale']:
            return True
            
        # Check for binned data that suggests histogram (NoZoom)
        if x_encoding.get('bin') or 'bin' in str(x_encoding):
            return False  # Use NoZoom template for histograms
            
        # Check for large categorical datasets
        if (x_encoding.get('type') in ['nominal', 'ordinal'] and 
            'scale' in x_encoding):
            return True
    
    # Check data size if available
    if 'values' in data and isinstance(data['values'], list):
        # If we have many data points, zoom might be beneficial
        if len(data['values']) > 20:
            return True
    
    # Default to NoZoom for simple bar charts
    return False



def enhance_vega_spec_with_responsive_design(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhance Vega-Lite specification with responsive design patterns.
    
    Args:
        spec: Vega-Lite specification
        
    Returns:
        Enhanced specification with responsive design
    """
    enhanced_spec = spec.copy()
    
    # Set responsive width and height
    enhanced_spec['width'] = 'container'
    enhanced_spec['height'] = 400
    
    # Configure autosize for responsive behavior
    enhanced_spec['autosize'] = {
        "type": "fit",
        "contains": "padding",
        "resize": True
    }
    
    # Add responsive axis configurations
    if 'encoding' in enhanced_spec:
        # Configure X-axis for responsiveness
        if 'x' in enhanced_spec['encoding']:
            if 'axis' not in enhanced_spec['encoding']['x']:
                enhanced_spec['encoding']['x']['axis'] = {}
            
            # Add responsive axis properties
            enhanced_spec['encoding']['x']['axis'].update({
                "labelLimit": 0,  # Auto-adjust label width
                "labelOverlap": "parity",  # Handle overlapping labels
                "titleLimit": 0  # Auto-adjust title width
            })
        
        # Configure Y-axis for responsiveness
        if 'y' in enhanced_spec['encoding']:
            if 'axis' not in enhanced_spec['encoding']['y']:
                enhanced_spec['encoding']['y']['axis'] = {}
            
            # Add responsive axis properties
            enhanced_spec['encoding']['y']['axis'].update({
                "labelLimit": 0,  # Auto-adjust label width
                "titleLimit": 0  # Auto-adjust title width
            })
    
    # Add responsive mark properties
    if 'mark' in enhanced_spec:
        mark_config = enhanced_spec['mark'] if isinstance(enhanced_spec['mark'], dict) else {"type": enhanced_spec['mark']}
        
        # Configure responsive mark sizing
        if mark_config.get('type') in ['point', 'circle', 'square']:
            mark_config['size'] = {"expr": "pow(width * height / 10000, 0.5) * 25"}  # Responsive point size
        elif mark_config.get('type') == 'line':
            mark_config['strokeWidth'] = {"expr": "max(1, width / 200)"}  # Responsive line width
        
        enhanced_spec['mark'] = mark_config
    
    return enhanced_spec


def extract_from_json_string(json_string: str, response_id: str) -> ChatResponseExtract:
    """
    Extract data from a JSON string representation of chat responses.
    
    Args:
        json_string: JSON string containing chat response array
        response_id: Unique identifier for this response (UUID)
        
    Returns:
        ChatResponseExtract: Structured data extracted from the JSON
    """
    try:
        chat_response_array = json.loads(json_string)
        return extract_chat_response_data(chat_response_array, response_id)
    except json.JSONDecodeError as e:
        return ChatResponseExtract(
            response_id=response_id,
            metadata={
                "sql_found": False,
                "result_found": False,
                "chart_found": False,
                "total_responses_processed": 0,
                "error": f"Invalid JSON: {str(e)}"
            }
        )
    except Exception as e:
        return ChatResponseExtract(
            response_id=response_id,
            metadata={
                "sql_found": False,
                "result_found": False,
                "chart_found": False,
                "total_responses_processed": 0,
                "error": f"Processing error: {str(e)}"
            }
        )


def format_messages_for_history(messages: List[Any]) -> List[Dict[str, Any]]:
    """
    Format database messages for frontend history display.
    
    Args:
        messages: List of database message objects
        
    Returns:
        List of formatted message dictionaries for frontend consumption
    """
    formatted_messages = []
    
    for message in messages:
        try:
            # Create MessageDetail object for each message
            from app.models.schemas import MessageDetail
            
            # Handle different message types
            message_type = "user" if message.message_type.value == "user" else "assistant"
            
            # Parse response metadata if available
            response_metadata = None
            if message.response_metadata:
                if isinstance(message.response_metadata, dict):
                    response_metadata = message.response_metadata
                else:
                    # Try to parse as JSON if it's a string
                    try:
                        response_metadata = json.loads(message.response_metadata)
                    except (json.JSONDecodeError, TypeError):
                        response_metadata = None
            
            # Parse chart config if available
            chart_config = None
            if message.chart_config:
                if isinstance(message.chart_config, dict):
                    chart_config = message.chart_config
                else:
                    # Try to parse as JSON if it's a string
                    try:
                        chart_config = json.loads(message.chart_config)
                    except (json.JSONDecodeError, TypeError):
                        chart_config = None
            
            # Parse result schema if available
            result_schema = None
            if message.result_schema:
                if isinstance(message.result_schema, dict):
                    result_schema = message.result_schema
                else:
                    # Try to parse as JSON if it's a string
                    try:
                        result_schema = json.loads(message.result_schema)
                    except (json.JSONDecodeError, TypeError):
                        result_schema = None
            
            # Create MessageDetail object
            message_detail = MessageDetail(
                id=str(message.id),
                message_type=message_type,
                content=message.content or "",
            created_at=message.created_at,
            superclient=message.superclient,
            sql_query=message.sql_query,
                chart_config=chart_config,
            ai_insights=message.ai_insights,
                response_metadata=response_metadata,
                result_data=None,  # Not stored in message table, would need to fetch from MessageChunk
                result_schema=result_schema,
                data_status="complete" if message.sql_query else "no_data",
                data_message=None
            )
            
            # Convert to dict for frontend
            formatted_messages.append(message_detail.model_dump())
            
        except Exception as e:
            logger.error(f"Error formatting message {message.id}: {e}")
            # Add a basic message structure even if formatting fails
            formatted_messages.append({
                "id": str(message.id),
                "message_type": "user" if message.message_type.value == "user" else "assistant",
                "content": message.content or "Error loading message",
                "created_at": message.created_at.isoformat() if message.created_at else None,
                "superclient": message.superclient,
                "sql_query": None,
                "chart_config": None,
                "ai_insights": None,
                "response_metadata": None,
                "result_data": None,
                "result_schema": None,
                "data_status": "error",
                "data_message": f"Error formatting message: {str(e)}"
            })
    
    return formatted_messages



