"""Custom Styling and Themes for HouseCrafter Gradio UI."""

CUSTOM_CSS = """
/* HouseCrafter Custom Styling */
.gradio-container {
    max-width: 1400px !important;
    margin: 0 auto !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.app-header {
    text-align: center;
    padding: 1.5rem 1rem 1rem 1rem;
    margin-bottom: 1rem;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 12px;
    color: #ffffff;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.app-header h1 {
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
    color: #38bdf8 !important;
}

.app-header p {
    font-size: 1.05rem;
    color: #cbd5e1;
    margin-bottom: 0.8rem;
}

.badge-row {
    display: flex;
    justify-content: center;
    gap: 0.75rem;
    flex-wrap: wrap;
    margin-top: 0.75rem;
}

.badge-item {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.85rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    font-weight: 500;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #f1f5f9;
}

.badge-item.highlight {
    background: rgba(56, 189, 248, 0.2);
    border-color: #38bdf8;
    color: #38bdf8;
}

.generate-btn {
    background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
    color: #ffffff !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3) !important;
    transition: all 0.2s ease !important;
}

.generate-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(2, 132, 199, 0.45) !important;
}

.viewer-3d-box {
    min-height: 480px !important;
    border-radius: 12px;
    overflow: hidden;
}

.status-box {
    border-radius: 8px;
    padding: 0.75rem 1rem;
    margin-top: 0.5rem;
    font-family: monospace;
    font-size: 0.9rem;
}

.sync-card {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 0.5rem;
}
"""
