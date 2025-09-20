/**
 * Chart Renderer for PSS Knowledge Assist
 * Modular chart rendering system extracted from script.js
 * Handles Vega-Lite chart rendering with enhanced features
 */

class ChartRenderer {
  constructor() {
    this.enhancedCharts = {};
    this.setupExportEventDelegation();
  }

  /**
   * Main chart display function
   */
  async displayChart(chartConfig, data) {
    console.log("📊 Chart Renderer - Displaying chart with config:", chartConfig);
    console.log("📊 Chart data:", data);

    // Validate chart data before proceeding
    const validation = this.validateChartData(chartConfig, data);
    if (!validation.isValid) {
      console.error("❌ Chart validation failed:", validation.errors);
      this.displayError(`Chart validation failed: ${validation.errors.join(", ")}`);
      return;
    }

    // Debug chart data structure
    this.debugChartData(chartConfig, data);

    const chartId = `chart-${Date.now()}`;
    const chartDiv = document.createElement("div");
    chartDiv.className = "chart-display enhanced-chart";

    // Extract chart information from the new structure
    const { vega_spec, chart_metadata, rendering_options } = chartConfig;
    const chartTitle = chart_metadata?.title || "Data Visualization";
    const chartType = chart_metadata?.chart_type || "unknown";

    // Check if this is an enhanced chart type (bar, pie)
    const isEnhancedChart = this.isChartTypeEnhanced(chartType, vega_spec);

    console.log("📊 Chart rendering info:", {
      chartType,
      isEnhancedChart,
      dataLength: data?.length || 0,
    });

    // Create chart HTML structure
    if (isEnhancedChart) {
      chartDiv.innerHTML = this.createEnhancedChartHTML(chartId, chartTitle, chartType, data);
    } else {
      chartDiv.innerHTML = this.createStandardChartHTML(chartId, chartTitle, chartType);
    }

    // Find the last bot message and append chart
    const chatMessages = document.getElementById("chatMessages");
    const lastBotMessage = chatMessages?.querySelector(".bot-message:last-child");
    if (lastBotMessage) {
      const messageContent = lastBotMessage.querySelector(".message-content");
      messageContent.appendChild(chartDiv);

      // Render the chart
      try {
        const enableZoom = isEnhancedChart && chartType !== "line";
        await this.renderVegaChart(vega_spec, chartId, rendering_options, data, enableZoom);
      } catch (error) {
        console.error("❌ Error rendering chart:", error);
        this.displayChartError(chartId, error.message, vega_spec);
      }
    }
  }

  /**
   * Create enhanced chart HTML structure
   */
  createEnhancedChartHTML(chartId, chartTitle, chartType, data) {
    return `
            <div class="sql-query-info">
                <div class="query-header">
                    <i class="fas fa-chart-bar"></i>
                    <span class="query-title">${chartTitle}</span>
                </div>
            </div>
            <div class="chart-content enhanced-content">
                <div class="chart-single-container">
                    <div class="chart-container" id="${chartId}">
                        <div class="chart-loading">
                            <i class="fas fa-spinner fa-spin"></i>
                            <span>Loading interactive chart...</span>
                        </div>
                    </div>
                </div>
                <div class="chart-info-panel single-chart">
                    <div class="chart-stats">
                        <div class="stat-item">
                            <i class="fas fa-database"></i>
                            <span>Data Points: ${data ? data.length : 'N/A'}</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-chart-line"></i>
                            <span>Chart Type: ${chartType.toUpperCase()}</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-mouse-pointer"></i>
                            <span>Interactive: Yes</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-search-plus"></i>
                            <span>Zoom & Pan: Enabled</span>
                        </div>
                    </div>
                    <div class="chart-instructions">
                        <h5><i class="fas fa-info-circle"></i> How to Use:</h5>
                        <ul>
                            <li><strong>Hover:</strong> View detailed information for each bar</li>
                            <li><strong>Zoom:</strong> Click and drag to select an area to zoom into</li>
                            <li><strong>Pan:</strong> After zooming, drag to pan around the chart</li>
                            <li><strong>Reset:</strong> Double-click anywhere to reset zoom level</li>
                            <li><strong>Export:</strong> Use the export button to save as PNG</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;
  }

  /**
   * Create standard chart HTML structure
   */
  createStandardChartHTML(chartId, chartTitle, chartType) {
    return `
            <div class="sql-results-container">
                <div class="sql-query-info">
                    <div class="query-header">
                        <i class="fas fa-chart-${getChartIcon(chartType)}"></i>
                        <span class="query-title">${chartTitle}</span>
                    </div>
                </div>
                <div class="chart-content">
                    <div class="chart-container" id="${chartId}">
                        <div class="chart-loading">
                            <i class="fas fa-spinner fa-spin"></i>
                            <span>Loading chart...</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
  }

  /**
   * Check if chart type supports enhanced features
   */
  isChartTypeEnhanced(chartType, vegaSpec) {
    // Method 1: Check chart type
    if (chartType === "bar" || chartType === "pie") {
      return true;
    }

    // Method 2: Check vega spec mark
    if (vegaSpec?.mark) {
      const mark = vegaSpec.mark;
      if (typeof mark === "string") {
        return mark === "bar" || mark === "arc";
      } else if (typeof mark === "object" && mark.type) {
        return mark.type === "bar" || mark.type === "arc";
      }
    }

    // Method 3: Pattern matching in spec
    if (vegaSpec) {
      const specString = JSON.stringify(vegaSpec).toLowerCase();
      return specString.includes('"bar"') || specString.includes('"arc"');
    }

    return false;
  }

  /**
   * Get appropriate icon for chart type
   */
  getChartIcon(chartType) {
    const iconMap = {
      bar: "bar",
      line: "line",
      area: "area",
      scatter: "scatter",
      pie: "pie",
      circle: "circle",
      square: "square",
      tick: "tick",
      point: "point",
      rule: "rule",
      text: "text",
      geoshape: "map",
      layered: "layer-group",
      faceted: "th-large",
      unknown: "chart-bar",
    };
    return iconMap[chartType] || "chart-bar";
  }

  /**
   * Render Vega-Lite chart
   */
  async renderVegaChart(vegaSpec, containerId, renderingOptions = {}, data = null, enableZoom = false) {
    console.log("📊 Rendering Vega chart in container:", containerId, "with zoom:", enableZoom);

    const container = document.getElementById(containerId);
    if (!container) {
      throw new Error(`Chart container not found: ${containerId}`);
    }

    // Clear loading state
    container.innerHTML = "";

    // Prepare the Vega specification
    const chartSpec = this.prepareVegaSpecification(vegaSpec, data, enableZoom);

    // Configure Vega-Embed options
    const embedOptions = {
      width: "container",
      height: "container",
      theme: enableZoom ? "quartz" : "default",
      renderer: "svg",
      actions: false,
      scaleFactor: window.devicePixelRatio || 1,
      ...renderingOptions,
    };

    try {
      // Render with Vega-Embed
      const result = await vegaEmbed(container, chartSpec, embedOptions);

      // Add enhanced chart controls (export functionality)
      this.addEnhancedChartControls(container, result.view, chartSpec);

      // Add responsive behavior
      this.addResponsiveChartBehavior(result.view, containerId);

      console.log("✅ Chart rendered successfully");
      return result;
    } catch (error) {
      console.error("❌ Vega-Embed error:", error);
      throw new Error(`Chart rendering failed: ${error.message}`);
    }
  }

  /**
   * Prepare Vega specification with enhancements
   */
  prepareVegaSpecification(vegaSpec, data, enableZoom = false) {
    const spec = JSON.parse(JSON.stringify(vegaSpec));

    // Add data if provided
    if (data && Array.isArray(data) && data.length > 0) {
      if (!spec.data) {
        spec.data = { values: data };
      } else if (!spec.data.values) {
        spec.data.values = data;
      }
    }

    // Ensure proper schema
    if (!spec.$schema) {
      spec.$schema = "https://vega.github.io/schema/vega-lite/v5.json";
    }

    // Add responsive design if not present
    if (!spec.autosize) {
      spec.width = "container";
      spec.height = 400;
      spec.autosize = {
        type: "fit",
        contains: "padding",
        resize: true,
      };
    }

    // Fix common bar chart encoding issues
    if (spec.mark && (spec.mark === "bar" || spec.mark.type === "bar")) {
      if (spec.encoding?.y?.aggregate) {
        delete spec.encoding.y.aggregate;
      }
      if (spec.encoding?.x?.bin) {
        delete spec.encoding.x.bin;
      }
      if (spec.encoding?.x) {
        spec.encoding.x.type = "nominal";
      }
      if (spec.encoding?.y) {
        spec.encoding.y.type = "quantitative";
      }
    }

    // Add zoom functionality if requested
    if (enableZoom) {
      if (!spec.params) {
        spec.params = [];
      }

      const hasZoomParam = spec.params.some((p) => p.name === "zoom_pan");
      if (!hasZoomParam) {
        spec.params.push({
          name: "zoom_pan",
          select: "interval",
          bind: "scales",
        });
      }
    }

    return spec;
  }

  /**
   * Add responsive behavior to chart
   */
  addResponsiveChartBehavior(view, containerId) {
    const container = document.getElementById(containerId);
    if (!container || !view) return;

    // Enhanced ResizeObserver with debouncing for better performance
    let resizeTimeout;
    const resizeObserver = new ResizeObserver((entries) => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        if (view && typeof view.resize === "function") {
          const entry = entries[0];
          if (entry) {
            const { width, height } = entry.contentRect;
            view.resize();
            this.updateResponsiveElements(container, width);
          }
        }
      }, 100); // Debounce resize events
    });

    resizeObserver.observe(container);

    // Handle window resize for global responsive updates
    const windowResizeHandler = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(() => {
        if (view && typeof view.resize === "function") {
          view.resize();
        }
      }, 150);
    };

    window.addEventListener("resize", windowResizeHandler);

    // Store observers and handlers for cleanup
    container._resizeObserver = resizeObserver;
    container._windowResizeHandler = windowResizeHandler;
  }

  /**
   * Update responsive elements based on container size
   */
  updateResponsiveElements(container, width) {
    // Update any UI elements that need to respond to size changes
    const controls = container.querySelector(".chart-controls");
    if (controls) {
      // Adjust control visibility based on container size
      if (width < 400) {
        controls.classList.add("compact");
      } else {
        controls.classList.remove("compact");
      }
    }
  }

  /**
   * Add enhanced chart controls for export functionality
   */
  addEnhancedChartControls(container, view, spec) {
    // Add export controls
    const exportDiv = document.createElement("div");
    exportDiv.className = "chart-controls";
    exportDiv.innerHTML = `
            <button class="chart-control-btn" data-export-type="png" title="Export as PNG">
                <i class="fas fa-download"></i>
                <span class="btn-text">PNG</span>
            </button>
            <button class="chart-control-btn" data-export-type="svg" title="Export as SVG">
                <i class="fas fa-file-code"></i>
                <span class="btn-text">SVG</span>
            </button>
            <button class="chart-control-btn" data-export-type="pdf" title="Export as PDF">
                <i class="fas fa-file-pdf"></i>
                <span class="btn-text">PDF</span>
            </button>
        `;

    container.appendChild(exportDiv);

    // Store view reference for export functions
    container._vegaView = view;
    container._originalSpec = JSON.parse(JSON.stringify(spec));
  }

  /**
   * Validate chart configuration
   */
  validateChartData(chartConfig, data) {
    const errors = [];

    if (!chartConfig) {
      errors.push("Chart configuration is missing");
      return { isValid: false, errors };
    }

    if (!chartConfig.vega_spec) {
      errors.push("Vega specification is missing");
      return { isValid: false, errors };
    }

    if (typeof chartConfig.vega_spec !== "object") {
      errors.push("Vega specification must be an object");
      return { isValid: false, errors };
    }

    if (!data || !Array.isArray(data) || data.length === 0) {
      // Check if chart has embedded data
      const chartData = chartConfig.vega_spec.data?.values;
      if (!chartData || !Array.isArray(chartData) || chartData.length === 0) {
        errors.push("Chart data is missing or empty");
        return { isValid: false, errors };
      }
    }

    const vegaSpec = chartConfig.vega_spec;
    if (!vegaSpec.mark && !vegaSpec.layer && !vegaSpec.facet) {
      errors.push("Vega specification missing required mark, layer, or facet");
      return { isValid: false, errors };
    }

    return { isValid: true, errors: [] };
  }

  /**
   * Debug chart data structure
   */
  debugChartData(chartConfig, data) {
    console.group("🔍 Chart Data Debug");
    console.log("Chart Config:", chartConfig);
    console.log("Data Array:", data);
    console.log("Data Length:", data?.length || 0);
    if (data && data.length > 0) {
      console.log("First Row:", data[0]);
      console.log("Data Keys:", Object.keys(data[0] || {}));
    }
    console.groupEnd();
  }

  /**
   * Display chart error
   */
  displayChartError(chartId, errorMessage, vegaSpec) {
    const container = document.getElementById(chartId);
    if (container) {
      container.innerHTML = `
                <div class="chart-error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error rendering chart: ${errorMessage}</p>
                    <button class="retry-btn" onclick="window.chartRenderer.retryChart('${chartId}', '${encodeURIComponent(
        JSON.stringify(vegaSpec)
      )}')">
                        <i class="fas fa-redo"></i> Retry
                    </button>
                </div>
            `;
    }
  }

  /**
   * Display generic error message
   */
  displayError(message) {
    if (typeof window.displayMessage === "function") {
      window.displayMessage(message, "bot", "error");
    } else {
      console.error("Error:", message);
    }
  }

  /**
   * Setup targeted event delegation for export functionality
   * Only listens for clicks within chart displays to avoid conflicts
   */
  setupExportEventDelegation() {
    document.addEventListener("click", (event) => {
      // Only handle clicks within chart displays
      const chartDisplay = event.target.closest(".chart-display");
      if (!chartDisplay) return;

      const button = event.target.closest("[data-export-type]");
      if (button) {
        event.preventDefault();
        const exportType = button.dataset.exportType;
        this.handleExport(button, exportType);
      }
    });
  }

  /**
   * Main export dispatcher
   */
  async handleExport(button, exportType) {
    const container = button.closest(".chart-container");
    const view = container?._vegaView;

    if (!view) {
      this.showMessage("Chart view not available for export", "error");
      return;
    }

    // Route to appropriate export method
    switch (exportType) {
      case "png":
        return this.exportChartAsPNG(button, view);
      case "svg":
        return this.exportChartAsSVG(button, view);
      case "pdf":
        return this.exportChartAsPDF(button, view);
      default:
        this.showMessage(`Unknown export type: ${exportType}`, "error");
    }
  }

  /**
   * Export chart as PNG
   */
  async exportChartAsPNG(button, view) {
    if (!view) {
      this.showMessage("Chart view not available for export", "error");
      return;
    }

    try {
      button.disabled = true;
      const originalHTML = button.innerHTML;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

      const canvas = await view.toCanvas();
      const link = document.createElement("a");
      link.download = "chart.png";
      link.href = canvas.toDataURL();
      link.click();

      this.showMessage("Chart exported as PNG successfully!", "success");
    } catch (error) {
      console.error("Export PNG failed:", error);
      this.showMessage("Failed to export chart as PNG", "error");
    } finally {
      button.disabled = false;
      button.innerHTML = '<i class="fas fa-download"></i><span class="btn-text">PNG</span>';
    }
  }

  /**
   * Export chart as SVG
   */
  async exportChartAsSVG(button, view) {
    if (!view) {
      this.showMessage("Chart view not available for export", "error");
      return;
    }

    try {
      button.disabled = true;
      const originalHTML = button.innerHTML;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

      const svg = await view.toSVG();
      const blob = new Blob([svg], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.download = "chart.svg";
      link.href = url;
      link.click();

      URL.revokeObjectURL(url);
      this.showMessage("Chart exported as SVG successfully!", "success");
    } catch (error) {
      console.error("Export SVG failed:", error);
      this.showMessage("Failed to export chart as SVG", "error");
    } finally {
      button.disabled = false;
      button.innerHTML = '<i class="fas fa-file-code"></i><span class="btn-text">SVG</span>';
    }
  }

  /**
   * Export chart as PDF
   */
  async exportChartAsPDF(button, view) {
    if (!view) {
      this.showMessage("Chart view not available for export", "error");
      return;
    }

    try {
      button.disabled = true;
      const originalHTML = button.innerHTML;
      button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

      const canvas = await view.toCanvas();
      const imgData = canvas.toDataURL("image/png");

      // Create PDF using jsPDF (if available) or fallback to canvas
      if (typeof jsPDF !== "undefined") {
        const pdf = new jsPDF();
        const imgWidth = 210; // A4 width in mm
        const pageHeight = 295; // A4 height in mm
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        let heightLeft = imgHeight;

        let position = 0;

        pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
        heightLeft -= pageHeight;

        while (heightLeft >= 0) {
          position = heightLeft - imgHeight;
          pdf.addPage();
          pdf.addImage(imgData, "PNG", 0, position, imgWidth, imgHeight);
          heightLeft -= pageHeight;
        }

        pdf.save("chart.pdf");
      } else {
        // Fallback: download as PNG if jsPDF not available
        const link = document.createElement("a");
        link.download = "chart.png";
        link.href = imgData;
        link.click();
        this.showMessage("PDF export not available, downloaded as PNG instead", "warning");
      }

      this.showMessage("Chart exported successfully!", "success");
    } catch (error) {
      console.error("Export PDF failed:", error);
      this.showMessage("Failed to export chart", "error");
    } finally {
      button.disabled = false;
      button.innerHTML = '<i class="fas fa-file-pdf"></i><span class="btn-text">PDF</span>';
    }
  }

  /**
   * Show user message (handles showValidationMessage dependency)
   */
  showMessage(message, type) {
    if (typeof showValidationMessage === "function") {
      showValidationMessage(message, type);
    } else if (typeof window.displayMessage === "function") {
      window.displayMessage(message, "bot", type);
    } else {
      console[type === "error" ? "error" : "log"](`[${type.toUpperCase()}] ${message}`);
    }
  }

  /**
   * Legacy export chart function (kept for backward compatibility)
   */
  async exportChart(chartId) {
    try {
      const container = document.getElementById(chartId);
      const vegaView = container?.querySelector(".vega-embed")?.view;

      if (!vegaView) {
        console.error("Vega view not found for export");
        return;
      }

      const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, "-");
      const imageUrl = await vegaView.toImageURL("png", 2);

      const link = document.createElement("a");
      link.download = `chart-${timestamp}.png`;
      link.href = imageUrl;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);

      console.log("✅ Chart exported successfully");
    } catch (error) {
      console.error("❌ Chart export failed:", error);
      alert("Export failed: " + error.message);
    }
  }

  /**
   * Toggle fullscreen mode
   */
  toggleFullscreen(chartId) {
    const chartDiv = document.querySelector(`#${chartId}`).closest(".chart-display");
    if (!chartDiv) return;

    if (chartDiv.classList.contains("fullscreen")) {
      chartDiv.classList.remove("fullscreen");
      document.body.classList.remove("chart-fullscreen");
    } else {
      chartDiv.classList.add("fullscreen");
      document.body.classList.add("chart-fullscreen");
    }
  }

  /**
   * Retry chart rendering
   */
  retryChart(containerId, encodedVegaSpec) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML =
      '<div class="chart-loading"><i class="fas fa-spinner fa-spin"></i><span>Retrying...</span></div>';

    try {
      const vegaSpec = JSON.parse(decodeURIComponent(encodedVegaSpec));
      this.renderVegaChart(vegaSpec, containerId, {}, null).catch((error) => {
        console.error("Retry failed:", error);
        this.displayChartError(containerId, error.message, vegaSpec);
      });
    } catch (error) {
      console.error("Failed to parse chart spec for retry:", error);
      this.displayChartError(containerId, "Invalid chart specification", {});
    }
  }
}

// =============================================================================
// GLOBAL INSTANCE AND EXPORTS
// =============================================================================

// Create global instance
window.chartRenderer = new ChartRenderer();

// Backward compatibility - expose main function globally
window.displayChart = function (chartConfig, data) {
  return window.chartRenderer.displayChart(chartConfig, data);
};

// Export individual functions for backward compatibility
window.exportChart = function (chartId) {
  return window.chartRenderer.exportChart(chartId);
};

window.toggleChartFullscreen = function (chartId) {
  return window.chartRenderer.toggleFullscreen(chartId);
};

window.retryChartRendering = function (containerId, vegaSpecJson) {
  const encodedSpec = encodeURIComponent(vegaSpecJson);
  return window.chartRenderer.retryChart(containerId, encodedSpec);
};

console.log("✅ Chart Renderer module loaded");
