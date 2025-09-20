"""
Chart Template Engine for Dynamic Chart Generation

This module provides functionality to generate Vega-Lite specifications
from predefined templates based on chart type and encoding information.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import re

logger = logging.getLogger(__name__)

class ChartTemplateEngine:
    """Engine for loading and processing chart templates"""
    
    def __init__(self, templates_dir: str = "app/charts"):
        """
        Initialize the template engine
        
        Args:
            templates_dir: Directory containing chart template JSON files
        """
        self.templates_dir = Path(templates_dir)
        self.template_registry = self._build_template_registry()
        
    def _build_template_registry(self) -> Dict[str, Dict[str, Any]]:
        """
        Build registry of available templates with metadata
        
        Returns:
            Dictionary mapping chart types to template information
        """
        registry = {
            'bar': {
                'default': 'barChart.json',     # ✅ Use unified template
                'histogram': 'barChart.json',   # ✅ Use unified template  
                'zoom': 'barChart.json',        # ✅ Use unified template
                'required_encodings': ['x', 'y'],
                'supported_types': {
                    'x': ['nominal', 'ordinal', 'temporal'],
                    'y': ['quantitative']
                }
            },
            'line': {
                'default': 'lineChart.json',
                'required_encodings': ['x', 'y'],
                'supported_types': {
                    'x': ['temporal', 'ordinal'],
                    'y': ['quantitative']
                }
            },
            'area': {
                'native_vega': True,  # Use native Vega-Lite rendering
                'required_encodings': ['x', 'y'],
                'supported_types': {
                    'x': ['temporal', 'ordinal'],
                    'y': ['quantitative']
                }
            },
            'pie': {
                'default': 'pieChart.json',
                'required_encodings': ['theta'],
                'supported_types': {
                    'theta': ['quantitative'],
                    'color': ['nominal', 'ordinal']
                }
            },
            'scatter': {
                'default': 'scatterPlot.json',
                'simple': 'scatterPlotSimple.json',
                'required_encodings': ['x', 'y'],
                'supported_types': {
                    'x': ['quantitative', 'temporal'],
                    'y': ['quantitative']
                }
            },
            'point': {
                'default': 'scatterPlot.json',
                'simple': 'scatterPlotSimple.json',
                'required_encodings': ['x', 'y'],
                'supported_types': {
                    'x': ['quantitative', 'temporal', 'nominal', 'ordinal'],
                    'y': ['quantitative']
                }
            },
            'rect': {
                'native_vega': True,  # Use native Vega-Lite rendering for heatmaps
                'required_encodings': ['x', 'y'],
                'supported_types': {
                    'x': ['nominal', 'ordinal'],
                    'y': ['nominal', 'ordinal'],
                    'fill': ['quantitative']
                }
            }
        }
        
        logger.info(f"Built template registry with {len(registry)} chart types")
        return registry
    
    def select_template(self, chart_type: str, encoding: Dict[str, Any], options: Dict[str, Any] = None) -> Optional[str]:
        """
        Select appropriate template file for given chart type and encoding
        
        Args:
            chart_type: Type of chart (bar, line, pie, etc.)
            encoding: Vega-Lite encoding specification
            options: Additional options (zoom, etc.)
            
        Returns:
            Template filename or None if chart should use native Vega rendering
        """
        if chart_type not in self.template_registry:
            logger.warning(f"Unknown chart type: {chart_type}")
            return None
            
        template_info = self.template_registry[chart_type]
        
        # Check if this chart type should use native Vega rendering
        if template_info.get('native_vega', False):
            logger.info(f"Using native Vega-Lite rendering for {chart_type} chart")
            return None
        
        # Enhanced bar chart variant selection - always choose Zoom or NoZoom
        if chart_type == 'bar':
            # Check for explicit zoom option
            if options and options.get('zoom', False):
                return template_info.get('zoom')
            
            # Analyze encoding to determine best variant
            if encoding and 'x' in encoding:
                x_encoding = encoding['x']
                
                # Priority 1: Check for histogram characteristics (binned data)
                if (x_encoding.get('bin') or 'bin' in str(x_encoding)):
                    return template_info.get('histogram')  # barChartNoZoom
                
                # Priority 2: Check for zoom characteristics (temporal data)
                if x_encoding.get('type') == 'temporal':
                    # If temporal data has scale/domain constraints, use zoom
                    if ('scale' in x_encoding and 'domain' in x_encoding['scale']):
                        return template_info.get('zoom')
                    # Otherwise, temporal data benefits from zoom capability
                    else:
                        return template_info.get('zoom')
                
                # Priority 3: Check for large categorical datasets that might benefit from zoom
                if (x_encoding.get('type') in ['nominal', 'ordinal'] and 
                    'scale' in x_encoding):
                    return template_info.get('zoom')
            
            # Default fallback: Use NoZoom for simple categorical bar charts
            return template_info.get('histogram')  # barChartNoZoom
        
        return template_info['default']
    
    def load_template(self, template_filename: str) -> Optional[Dict[str, Any]]:
        """
        Load template JSON from file
        
        Args:
            template_filename: Name of template file
            
        Returns:
            Template dictionary or None if error
        """
        template_path = self.templates_dir / template_filename
        
        if not template_path.exists():
            logger.error(f"Template file not found: {template_path}")
            return None
            
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = json.load(f)
            logger.debug(f"Loaded template: {template_filename}")
            return template
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in template {template_filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading template {template_filename}: {e}")
            return None
    
    def extract_template_parameters(self, template: Dict[str, Any]) -> List[str]:
        """
        Extract all placeholder parameters from template
        
        Args:
            template: Template dictionary
            
        Returns:
            List of parameter names (without {{ }})
        """
        template_str = json.dumps(template)
        # Find all {{parameter}} patterns
        parameters = re.findall(r'\{\{(\w+)\}\}', template_str)
        return list(set(parameters))  # Remove duplicates
    
    def map_encoding_to_parameters(self, encoding: Dict[str, Any], chart_type: str) -> Dict[str, Any]:
        """
        Map Vega encoding to template parameters
        
        Args:
            encoding: Vega-Lite encoding specification
            chart_type: Type of chart
            
        Returns:
            Dictionary of parameter mappings
        """
        parameters = {}
        
        # Standard field mappings
        if 'x' in encoding:
            parameters['xField'] = encoding['x']['field']
            parameters['xType'] = encoding['x'].get('type', 'nominal')  # Default to nominal if not specified
            if 'title' in encoding['x']:
                parameters['xTitle'] = encoding['x']['title']
        
        if 'y' in encoding:
            parameters['yField'] = encoding['y']['field']
            parameters['yType'] = encoding['y'].get('type', 'quantitative')  # Default to quantitative if not specified
            if 'title' in encoding['y']:
                parameters['yTitle'] = encoding['y']['title']
        
        if 'color' in encoding:
            parameters['colorField'] = encoding['color']['field']
            parameters['colorType'] = encoding['color']['type']
        
        if 'size' in encoding:
            # Handle size expressions vs field-based size
            if 'expr' in encoding['size']:
                parameters['sizeExpr'] = encoding['size']['expr']
            elif 'field' in encoding['size']:
                parameters['sizeField'] = encoding['size']['field']
                parameters['sizeType'] = encoding['size']['type']
            else:
                # Direct size value
                parameters['pointSize'] = encoding['size']
        
        # Chart-specific mappings
        if chart_type == 'pie':
            # Set mark type for pie charts (Vega-Lite uses 'arc' for pie charts)
            parameters['markType'] = 'arc'
            
            # For pie charts, map theta encoding to valueField (pie chart template expects this)
            if 'theta' in encoding:
                parameters['valueField'] = encoding['theta']['field']
                parameters['valueTitle'] = encoding['theta'].get('title', encoding['theta']['field'].title())
            elif 'y' in encoding:
                # Fallback: use y as theta
                parameters['valueField'] = encoding['y']['field']
                parameters['valueTitle'] = encoding['y'].get('title', encoding['y']['field'].title())
            
            # Map color encoding to categoryField for pie charts
            if 'color' in encoding:
                parameters['categoryField'] = encoding['color']['field']
                parameters['categoryTitle'] = encoding['color'].get('title', encoding['color']['field'].title())
        
        elif chart_type == 'bar':
            # Set mark type for bar charts
            parameters['markType'] = 'bar'
        
        elif chart_type == 'scatter':
            # Set mark type for scatter plots (Vega-Lite uses 'point' for scatter plots)
            parameters['markType'] = 'point'
        
        elif chart_type == 'line':
            # Set mark type for line charts
            parameters['markType'] = 'line'
            
            # For line charts, map color encoding to colorField for multi-line support
            if 'color' in encoding:
                parameters['colorField'] = encoding['color']['field']
                parameters['colorTitle'] = encoding['color'].get('title', encoding['color']['field'].title())
            else:
                # Default color field for single line charts
                parameters['colorField'] = 'series'
                parameters['colorTitle'] = 'Series'
            
            # Generate dynamic tooltip fields for line charts
            # This will be populated during template generation with actual data fields
        

        # Default values for common parameters
        parameters.update({
            'chartWidth': 'container',  # ✅ Ensure responsive width
            'chartHeight': 400,
            'dataUrl': '',  # Will be replaced with inline data
            'defaultOpacity': 0.8,
            'highlightOpacity': 1.0,
            'hoverOpacity': 1.0,
            'strokeWidth': 1,
            'colorScheme': 'blues',
            'barColor': 'steelblue',
            'tooltipEnabled': True,
            'chartTitle': '',
            'pointSize': 100,
            'sizeRange': [50, 400],
            'pointColor': 'steelblue',
            'lineColor': 'steelblue',
            'interpolation': 'linear',  # ✅ Add missing interpolation parameter
            # Pie chart specific defaults
            'outerRadius': 100,
            'innerRadius': 0,
            'stackType': 'normalize',
            # Scatter plot specific defaults
            'pointOpacity': 0.7,
            'dateParseFormat': ''
        })
        
        return parameters
    
    def substitute_parameters(self, template: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Substitute template parameters with actual values using recursive approach
        
        Args:
            template: Template dictionary with {{parameter}} placeholders
            parameters: Dictionary of parameter values
            
        Returns:
            Template with parameters substituted
        """
        def substitute_recursive(obj):
            """Recursively substitute parameters in nested structures"""
            if isinstance(obj, dict):
                return {key: substitute_recursive(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [substitute_recursive(item) for item in obj]
            elif isinstance(obj, str):
                # Check if this is a placeholder
                if obj.startswith('{{') and obj.endswith('}}'):
                    param_name = obj[2:-2]  # Remove {{ and }}
                    if param_name in parameters:
                        return parameters[param_name]
                    else:
                        # Use default value
                        default_str = self._get_default_parameter_value(param_name)
                        # Parse the default value properly
                        if default_str.startswith('"') and default_str.endswith('"'):
                            return default_str[1:-1]  # Remove quotes for string
                        elif default_str == 'true':
                            return True
                        elif default_str == 'false':
                            return False
                        elif default_str.isdigit():
                            return int(default_str)
                        else:
                            try:
                                return float(default_str)
                            except ValueError:
                                return default_str
                else:
                    return obj
            else:
                return obj
        
        try:
            result = substitute_recursive(template)
            logger.debug(f"Successfully substituted parameters in template")
            return result
        except Exception as e:
            logger.error(f"Error in recursive parameter substitution: {e}")
            return template  # Return original if substitution failed
    
    def _get_default_parameter_value(self, parameter_name: str) -> str:
        """
        Get default value for a parameter
        
        Args:
            parameter_name: Name of parameter
            
        Returns:
            Default value as string
        """
        defaults = {
            'chartWidth': '"container"',
            'chartHeight': '400',
            'dataUrl': '""',
            'defaultOpacity': '0.8',
            'highlightOpacity': '1.0',
            'hoverOpacity': '0.9',
            'strokeWidth': '1',
            'colorScheme': '"blues"',
            'maxBins': '20',
            'yAggregate': '"count"',
            'tooltipFields': '[]',

            'barColor': '"steelblue"',
            'tooltipEnabled': 'true',
            'chartTitle': '""',
            'xTitle': '""',
            'yTitle': '""',
            'xType': '"nominal"',
            'yType': '"quantitative"',
            'xField': '"x"',
            'yField': '"y"',
            'sizeField': '"size"',
            'sizeType': '"quantitative"',
            'sizeExpr': '"100"',
            'pointSize': '100',
            'sizeRange': '[50, 400]',
            'pointColor': '"steelblue"',
            'lineColor': '"steelblue"',
            'interpolation': '"linear"',
            'binning': 'true',
            'overviewHeight': '60',
            'dateParseFormat': '{}',
            'pointOpacity': '0.8',
            'strokeWidth': '2'
        }
        
        return defaults.get(parameter_name, '""')
    
    def _build_tooltip_fields(self, encoding: Dict[str, Any], data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build intelligent tooltip field configuration based on available data
        
        Args:
            encoding: Vega-Lite encoding specification
            data: Chart data with values
            
        Returns:
            List of tooltip field configurations
        """
        tooltip_fields = []
        
        # Get sample data to understand available fields
        sample_data = {}
        if 'values' in data and len(data['values']) > 0:
            sample_data = data['values'][0]
        
        # Always include the main x and y fields
        if 'x' in encoding and 'field' in encoding['x']:
            x_field = encoding['x']['field']
            x_title = encoding['x'].get('title', x_field.replace('_', ' ').title())
            tooltip_fields.append({
                "field": x_field,
                "type": encoding['x'].get('type', 'nominal'),
                "title": x_title
            })
        
        if 'y' in encoding and 'field' in encoding['y']:
            y_field = encoding['y']['field']
            y_title = encoding['y'].get('title', y_field.replace('_', ' ').title())
            tooltip_fields.append({
                "field": y_field,
                "type": encoding['y'].get('type', 'quantitative'),
                "title": y_title,
                "format": ".2f" if encoding['y'].get('type') == 'quantitative' else None
            })
        
        # Add other relevant fields from the data
        relevant_fields = ['year', 'month', 'date', 'category', 'name', 'id']
        for field in relevant_fields:
            if field in sample_data:
                # Skip if already added as x or y
                if field == encoding.get('x', {}).get('field') or field == encoding.get('y', {}).get('field'):
                    continue
                
                # Determine field type based on data
                field_type = self._infer_field_type(field, sample_data[field])
                field_title = field.replace('_', ' ').title()
                
                tooltip_fields.append({
                    "field": field,
                    "type": field_type,
                    "title": field_title
                })
        
        # Remove None format values
        for field in tooltip_fields:
            if field.get('format') is None:
                field.pop('format', None)
        
        return tooltip_fields
    
    def _infer_field_type(self, field_name: str, sample_value) -> str:
        """
        Infer Vega-Lite field type from field name and sample value
        
        Args:
            field_name: Name of the field
            sample_value: Sample value from the data
            
        Returns:
            Vega-Lite field type (temporal, quantitative, nominal, ordinal)
        """
        # Check field name patterns
        if any(keyword in field_name.lower() for keyword in ['year', 'date', 'time', 'timestamp']):
            return 'temporal'
        
        if any(keyword in field_name.lower() for keyword in ['month', 'day', 'quarter', 'week']):
            return 'ordinal'
        
        # Check sample value type
        if isinstance(sample_value, (int, float)):
            # If it's a year-like number, treat as ordinal
            if isinstance(sample_value, int) and 1900 <= sample_value <= 2100:
                return 'ordinal'
            return 'quantitative'
        
        # Default to nominal for strings and other types
        return 'nominal'
    
    def generate_vega_spec_from_template(self, 
                                       chart_type: str, 
                                       encoding: Dict[str, Any], 
                                       data: Dict[str, Any],
                                       title: str = None,
                                       options: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        Generate complete Vega-Lite specification from template
        
        Args:
            chart_type: Type of chart (bar, line, etc.)
            encoding: Vega-Lite encoding specification
            data: Chart data
            title: Chart title
            options: Additional options (tooltip, zoom, etc.)
            
        Returns:
            Complete Vega-Lite specification or None if error
        """
        try:
            # Select appropriate template
            template_filename = self.select_template(chart_type, encoding, options)
            if not template_filename:
                # Check if this is a native Vega chart type
                if chart_type in self.template_registry and self.template_registry[chart_type].get('native_vega', False):
                    logger.info(f"Chart type {chart_type} uses native Vega-Lite rendering - skipping template processing")
                    return None
                else:
                    logger.error(f"No template found for chart type: {chart_type}")
                    return None
            
            # Load template
            template = self.load_template(template_filename)
            if not template:
                logger.error(f"Failed to load template: {template_filename}")
                return None
            
            # Map encoding to parameters
            parameters = self.map_encoding_to_parameters(encoding, chart_type)
            
            # Add title if provided
            if title:
                parameters['chartTitle'] = title
            
            # Handle chart dimensions from options
            if options:
                if 'chartWidth' in options:
                    parameters['chartWidth'] = options['chartWidth']
                if 'chartHeight' in options:
                    parameters['chartHeight'] = options['chartHeight']
            
            # Handle size options for point/scatter charts
            if options and 'size' in options and options['size']:
                size_config = options['size']
                if isinstance(size_config, dict) and 'expr' in size_config:
                    parameters['sizeExpr'] = size_config['expr']
                elif isinstance(size_config, (int, float)):
                    parameters['pointSize'] = size_config
            
            # Handle line chart specific options
            if chart_type == 'line' and options:
                if 'interpolation' in options:
                    parameters['interpolation'] = options['interpolation']
                if 'strokeWidth' in options:
                    parameters['strokeWidth'] = options['strokeWidth']
                if 'pointSize' in options:
                    parameters['pointSize'] = options['pointSize']
            
            # Handle pie chart specific options
            if chart_type == 'pie' and options:
                if 'outerRadius' in options:
                    parameters['outerRadius'] = options['outerRadius']
                if 'innerRadius' in options:
                    parameters['innerRadius'] = options['innerRadius']
                if 'colorScheme' in options:
                    parameters['colorScheme'] = options['colorScheme']
                if 'stackType' in options:
                    parameters['stackType'] = options['stackType']
                else:
                    parameters['stackType'] = 'normalize'  # Default for pie charts
            
            # Handle scatter plot specific options
            if chart_type in ['scatter', 'point'] and options:
                if 'pointSize' in options:
                    parameters['pointSize'] = options['pointSize']
                if 'pointOpacity' in options:
                    parameters['pointOpacity'] = options['pointOpacity']
                if 'pointColor' in options:
                    parameters['pointColor'] = options['pointColor']
                if 'dateParseFormat' in options:
                    parameters['dateParseFormat'] = options['dateParseFormat']
            
            # Build intelligent tooltip fields for interactive charts
            if chart_type in ['point', 'scatter', 'line', 'pie']:
                tooltip_fields = self._build_tooltip_fields(encoding, data)
                parameters['tooltipFields'] = tooltip_fields
            
            # Substitute parameters
            vega_spec = self.substitute_parameters(template, parameters)
            
            # Clean up empty dateParseFormat for scatter plots
            if chart_type in ['scatter', 'point'] and 'data' in vega_spec:
                data_section = vega_spec['data']
                if isinstance(data_section, dict) and 'format' in data_section:
                    format_section = data_section['format']
                    if isinstance(format_section, dict) and 'parse' in format_section:
                        # Only remove parse format if it's truly empty or just whitespace
                        parse_value = format_section['parse']
                        if not parse_value or (isinstance(parse_value, str) and parse_value.strip() == ''):
                            del format_section['parse']
                            # Remove empty format section
                            if not format_section:
                                del data_section['format']
            
            # Replace data placeholder with actual data
            if 'data' in vega_spec:
                if isinstance(vega_spec['data'], dict) and 'url' in vega_spec['data']:
                    # Preserve format section if it exists
                    existing_data = vega_spec['data']
                    if 'format' in existing_data:
                        # Merge data with existing format
                        new_data = data.copy()
                        new_data['format'] = existing_data['format']
                        vega_spec['data'] = new_data
                    else:
                        # Replace URL-based data with inline values
                        vega_spec['data'] = data
                elif isinstance(vega_spec['data'], str):
                    # Handle string placeholder
                    vega_spec['data'] = data
            else:
                # Add data if not present
                vega_spec['data'] = data
            
            # Add title to spec if provided
            if title and 'title' not in vega_spec:
                vega_spec['title'] = title
            
            # Add zoom functionality for bar charts if requested
            if chart_type == 'bar' and options and options.get('zoom', False):
                if 'params' not in vega_spec:
                    vega_spec['params'] = []
                
                # Add zoom parameter if not already present (avoid conflicts with template parameters)
                zoom_param = {
                    "name": "zoom_pan",
                    "select": "interval",
                    "bind": "scales"
                }
                
                # Check if zoom parameter already exists
                has_zoom = any(p.get('name') == 'zoom_pan' for p in vega_spec['params'])
                if not has_zoom:
                    vega_spec['params'].append(zoom_param)
                    logger.info("Added zoom functionality to bar chart")
            
            logger.info(f"Generated Vega spec from template {template_filename} for {chart_type} chart")
            return vega_spec
            
        except Exception as e:
            logger.error(f"Error generating Vega spec from template: {e}")
            return None


# Global instance for use across the application
chart_template_engine = ChartTemplateEngine()