import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import time
import threading
import queue
from typing import List, Tuple
import math

class VoiceAnimator:
    """Enhanced voice animation component similar to ChatGPT's voice interface"""
    
    def __init__(self):
        self.is_animating = False
        self.animation_data = queue.Queue()
        self.animation_thread = None
        
    def create_speaking_animation(self, intensity: float = 1.0) -> go.Figure:
        """Create an animated waveform visualization for when AI is speaking"""
        fig = go.Figure()
        
        # Generate multiple waveforms for a richer animation
        t = np.linspace(0, 4*np.pi, 100)
        
        # Base waveform
        wave1 = np.sin(t) * intensity * 0.8
        wave2 = np.sin(t * 1.5 + np.pi/4) * intensity * 0.6
        wave3 = np.sin(t * 2.2 + np.pi/2) * intensity * 0.4
        
        # Add some randomness for natural feel
        noise = np.random.random(100) * 0.2 * intensity
        combined_wave = wave1 + wave2 + wave3 + noise
        
        # Normalize
        combined_wave = combined_wave / np.max(np.abs(combined_wave)) * intensity
        
        # Create gradient colors
        colors = ['rgba(16, 163, 127, 0.8)', 'rgba(16, 163, 127, 0.6)', 'rgba(16, 163, 127, 0.4)']
        
        # Add multiple traces for depth
        for i, (wave, color) in enumerate(zip([wave1, wave2, wave3], colors)):
            fig.add_trace(go.Scatter(
                x=t,
                y=wave,
                mode='lines',
                line=dict(color=color, width=3-i*0.5),
                fill='tonexty' if i > 0 else 'tozeroy',
                fillcolor=color.replace('0.8', '0.2').replace('0.6', '0.15').replace('0.4', '0.1'),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        # Style the plot
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False, range=[-2, 2]),
            margin=dict(l=0, r=0, t=0, b=0),
            height=120,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        return fig
    
    def create_listening_animation(self) -> go.Figure:
        """Create a pulsing circle animation for listening state"""
        fig = go.Figure()
        
        # Create pulsing effect with multiple circles
        for i, alpha in enumerate([0.3, 0.2, 0.1]):
            radius = 0.8 + i * 0.2
            fig.add_shape(
                type="circle",
                x0=-radius, y0=-radius, x1=radius, y1=radius,
                line=dict(color=f"rgba(16, 163, 127, {alpha})", width=2),
                fillcolor=f"rgba(16, 163, 127, {alpha * 0.3})"
            )
        
        # Add center dot
        fig.add_shape(
            type="circle",
            x0=-0.1, y0=-0.1, x1=0.1, y1=0.1,
            line=dict(color="rgba(16, 163, 127, 1)", width=0),
            fillcolor="rgba(16, 163, 127, 0.8)"
        )
        
        fig.update_layout(
            xaxis=dict(visible=False, range=[-2, 2]),
            yaxis=dict(visible=False, range=[-2, 2]),
            margin=dict(l=0, r=0, t=0, b=0),
            height=120,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        return fig
    
    def create_thinking_animation(self) -> go.Figure:
        """Create a thinking animation with rotating dots"""
        fig = go.Figure()
        
        # Create rotating dots
        angles = np.linspace(0, 2*np.pi, 8, endpoint=False)
        current_time = time.time()
        
        for i, angle in enumerate(angles):
            # Add rotation based on time
            rotated_angle = angle + current_time * 2
            x = 0.8 * np.cos(rotated_angle)
            y = 0.8 * np.sin(rotated_angle)
            
            # Varying opacity for wave effect
            opacity = (np.sin(current_time * 3 + i * np.pi/4) + 1) / 2 * 0.7 + 0.3
            
            fig.add_trace(go.Scatter(
                x=[x], y=[y],
                mode='markers',
                marker=dict(
                    size=12,
                    color=f'rgba(16, 163, 127, {opacity})',
                    symbol='circle'
                ),
                showlegend=False,
                hoverinfo='skip'
            ))
        
        fig.update_layout(
            xaxis=dict(visible=False, range=[-1.5, 1.5]),
            yaxis=dict(visible=False, range=[-1.5, 1.5]),
            margin=dict(l=0, r=0, t=0, b=0),
            height=120,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        return fig
    
    def create_idle_animation(self) -> go.Figure:
        """Create a subtle idle animation"""
        fig = go.Figure()
        
        # Simple pulsing circle
        current_time = time.time()
        pulse = (np.sin(current_time * 2) + 1) / 2 * 0.3 + 0.7
        
        fig.add_shape(
            type="circle",
            x0=-1, y0=-1, x1=1, y1=1,
            line=dict(color=f"rgba(16, 163, 127, {pulse})", width=2),
            fillcolor=f"rgba(16, 163, 127, {pulse * 0.2})"
        )
        
        fig.update_layout(
            xaxis=dict(visible=False, range=[-1.5, 1.5]),
            yaxis=dict(visible=False, range=[-1.5, 1.5]),
            margin=dict(l=0, r=0, t=0, b=0),
            height=120,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        
        return fig

def create_voice_status_indicator(status: str = "idle") -> str:
    """Create HTML for voice status indicator"""
    status_configs = {
        "speaking": {
            "text": "🎤 Yuvan is speaking...",
            "class": "speaking-indicator",
            "animation": "pulse 1.5s ease-in-out infinite"
        },
        "listening": {
            "text": "👂 Listening...",
            "class": "listening-indicator", 
            "animation": "pulse 2s ease-in-out infinite"
        },
        "thinking": {
            "text": "🤔 Thinking...",
            "class": "thinking-indicator",
            "animation": "pulse 1s ease-in-out infinite"
        },
        "idle": {
            "text": "💬 Ready to chat",
            "class": "idle-indicator",
            "animation": "none"
        }
    }
    
    config = status_configs.get(status, status_configs["idle"])
    
    return f"""
    <div class="{config['class']}" style="animation: {config['animation']};">
        {config['text']}
    </div>
    """

def get_voice_animation_css() -> str:
    """Get CSS for voice animations"""
    return """
    <style>
    .speaking-indicator {
        background: linear-gradient(90deg, #10A37F, #34D399, #10A37F);
        background-size: 300% 300%;
        animation: speakingGradient 2s ease infinite, pulse 1.5s ease-in-out infinite;
        padding: 12px 24px;
        border-radius: 25px;
        color: white;
        font-weight: 600;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(16, 163, 127, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    .listening-indicator {
        background: linear-gradient(90deg, #3B82F6, #60A5FA, #3B82F6);
        background-size: 300% 300%;
        animation: listeningGradient 3s ease infinite, pulse 2s ease-in-out infinite;
        padding: 12px 24px;
        border-radius: 25px;
        color: white;
        font-weight: 600;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    .thinking-indicator {
        background: linear-gradient(90deg, #8B5CF6, #A78BFA, #8B5CF6);
        background-size: 300% 300%;
        animation: thinkingGradient 1.5s ease infinite, pulse 1s ease-in-out infinite;
        padding: 12px 24px;
        border-radius: 25px;
        color: white;
        font-weight: 600;
        text-align: center;
        margin: 10px 0;
        box-shadow: 0 4px 15px rgba(139, 92, 246, 0.3);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }
    
    .idle-indicator {
        background: rgba(107, 114, 128, 0.1);
        padding: 12px 24px;
        border-radius: 25px;
        color: #6B7280;
        font-weight: 500;
        text-align: center;
        margin: 10px 0;
        border: 2px solid rgba(107, 114, 128, 0.2);
    }
    
    @keyframes speakingGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes listeningGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes thinkingGradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    @keyframes pulse {
        0% { 
            transform: scale(1);
            box-shadow: 0 4px 15px rgba(16, 163, 127, 0.3);
        }
        50% { 
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(16, 163, 127, 0.4);
        }
        100% { 
            transform: scale(1);
            box-shadow: 0 4px 15px rgba(16, 163, 127, 0.3);
        }
    }
    </style>
    """