"""Custom CSS styles for ResearchPilot AI dark theme."""


def get_custom_css() -> str:
    """Return custom CSS for the dark theme with glassmorphism."""
    return """
    <style>
    /* ====================== GLOBAL THEME ====================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    /* ====================== HEADER ====================== */
    .main-header {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }
    
    .main-header h1 {
        color: #ffffff;
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.95rem;
        margin-top: 0.3rem;
    }
    
    /* ====================== GLASS CARDS ====================== */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(139, 92, 246, 0.3);
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1);
    }
    
    /* ====================== AGENT PIPELINE ====================== */
    .pipeline-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        gap: 0.5rem;
    }
    
    .pipeline-step {
        flex: 1;
        text-align: center;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .pipeline-step.waiting {
        background: rgba(255, 255, 255, 0.05);
        color: rgba(255, 255, 255, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .pipeline-step.active {
        background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(59, 130, 246, 0.2));
        color: #a78bfa;
        border: 1px solid rgba(139, 92, 246, 0.4);
        animation: pulse-glow 2s infinite;
    }
    
    .pipeline-step.done {
        background: rgba(34, 197, 94, 0.1);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    
    .pipeline-arrow {
        color: rgba(255, 255, 255, 0.2);
        font-size: 1.2rem;
        flex-shrink: 0;
    }
    
    @keyframes pulse-glow {
        0%, 100% { box-shadow: 0 0 5px rgba(139, 92, 246, 0.2); }
        50% { box-shadow: 0 0 20px rgba(139, 92, 246, 0.4); }
    }
    
    /* ====================== PLAN CARD ====================== */
    .plan-item {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        transition: all 0.2s ease;
    }
    
    .plan-item:hover {
        background: rgba(139, 92, 246, 0.05);
        border-color: rgba(139, 92, 246, 0.2);
    }
    
    .plan-number {
        background: linear-gradient(135deg, #8b5cf6, #3b82f6);
        color: white;
        width: 28px;
        height: 28px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        flex-shrink: 0;
    }
    
    /* ====================== FINDINGS PREVIEW ====================== */
    .finding-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 1.25rem;
        margin-bottom: 0.75rem;
    }
    
    .finding-card h4 {
        color: #a78bfa;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }
    
    /* ====================== SOURCE BADGES ====================== */
    .source-badge {
        display: inline-block;
        background: rgba(59, 130, 246, 0.1);
        border: 1px solid rgba(59, 130, 246, 0.2);
        color: #93c5fd;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.75rem;
        margin: 0.2rem;
        transition: all 0.2s ease;
    }
    
    .source-badge:hover {
        background: rgba(59, 130, 246, 0.2);
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    /* ====================== REVIEW SCORES ====================== */
    .score-container {
        display: flex;
        gap: 1rem;
        flex-wrap: wrap;
        margin: 1rem 0;
    }
    
    .score-item {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 0.75rem 1.25rem;
        text-align: center;
        min-width: 90px;
    }
    
    .score-value {
        font-size: 1.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #8b5cf6, #3b82f6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .score-label {
        font-size: 0.7rem;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.2rem;
    }
    
    /* ====================== EXPORT BUTTONS ====================== */
    .export-section {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1.25rem;
        margin-top: 1rem;
    }
    
    /* ====================== SIDEBAR ====================== */
    .sidebar-header {
        background: linear-gradient(135deg, #302b63, #24243e);
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .sidebar-header h2 {
        color: #ffffff;
        font-size: 1.2rem;
        margin: 0;
    }
    
    .sidebar-header p {
        color: rgba(255, 255, 255, 0.5);
        font-size: 0.8rem;
        margin: 0.3rem 0 0 0;
    }
    
    .history-item {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.4rem;
        cursor: pointer;
        transition: all 0.2s ease;
        font-size: 0.85rem;
    }
    
    .history-item:hover {
        background: rgba(139, 92, 246, 0.08);
        border-color: rgba(139, 92, 246, 0.2);
    }
    
    /* ====================== STATUS BADGES ====================== */
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.3rem;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 500;
    }
    
    .status-badge.success {
        background: rgba(34, 197, 94, 0.1);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.2);
    }
    
    .status-badge.warning {
        background: rgba(250, 204, 21, 0.1);
        color: #fbbf24;
        border: 1px solid rgba(250, 204, 21, 0.2);
    }
    
    .status-badge.info {
        background: rgba(59, 130, 246, 0.1);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }
    
    /* ====================== TECH STACK INFO ====================== */
    .tech-stack {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 0.8rem;
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.4);
        text-align: center;
    }
    
    /* ====================== ANIMATIONS ====================== */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease forwards;
    }
    
    /* ====================== RESPONSIVE TWEAKS ====================== */
    @media (max-width: 768px) {
        .pipeline-container {
            flex-direction: column;
        }
        .pipeline-arrow {
            transform: rotate(90deg);
        }
    }
    </style>
    """
