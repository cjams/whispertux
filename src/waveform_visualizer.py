"""
Artistic circular real-time audio waveform visualizer using matplotlib
Displays smooth, animated radial waveform with gradients and glow effects
"""

import tkinter as tk
from tkinter import ttk
import numpy as np
import threading
import time
from collections import deque
from typing import Optional, Callable
import math

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches


class WaveformVisualizer(ttk.Frame):
    """Artistic circular real-time audio waveform visualizer widget for tkinter"""
    
    def __init__(self, parent, width=400, height=120, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Widget dimensions
        self.width = width
        self.height = height
        
        # Audio data buffer (circular buffer for efficiency)
        self.buffer_size = 200  # Number of amplitude samples to display
        self.audio_buffer = deque(maxlen=self.buffer_size)
        
        # Fill buffer with zeros initially
        for _ in range(self.buffer_size):
            self.audio_buffer.append(0.0)
        
        # Animation state
        self.is_active = False
        self.animation_obj = None
        self.animation_lock = threading.Lock()
        
        # Visual configuration
        self.background_color = "#2b2b2b"  # Dark background
        self.target_fps = 35  # Balance between smoothness and performance
        
        # Animation parameters
        self.smoothing_factor = 0.7  # For amplitude smoothing
        self.last_smoothed_amplitude = 0.0
        
        # Audio processing
        self.current_amplitude = 0.0
        self.amplitude_history = deque(maxlen=10)  # For smoothing
        self.recording_state = False
        
        
        # Animation time tracking
        self.animation_time = 0
        
        # Create the matplotlib canvas
        self._create_matplotlib_canvas()
        
        
        # Bind resize events
        self.bind('<Configure>', self._on_resize)
        
        # Initial canvas draw to show static visualization
        self.canvas.draw()
        
    def _create_matplotlib_canvas(self):
        """Create the matplotlib figure and canvas"""
        # Create figure with dark background
        plt.style.use('dark_background')
        self.fig = Figure(figsize=(self.width/100, self.height/100), 
                         facecolor=self.background_color, 
                         edgecolor='none')
        
        # Create polar subplot for circular visualization
        self.ax = self.fig.add_subplot(111, projection='polar')
        self.ax.set_facecolor(self.background_color)
        
        # Configure polar plot appearance
        self.ax.set_ylim(0, 1.2)
        self.ax.set_theta_zero_location('N')  # Start from top
        self.ax.set_theta_direction(-1)  # Clockwise
        
        # Hide default polar grid and labels
        self.ax.grid(False)
        self.ax.set_yticklabels([])
        self.ax.set_xticklabels([])
        self.ax.set_rticks([])
        
        # Remove spines
        self.ax.spines['polar'].set_visible(False)
        
        # Create tkinter canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize plot elements
        self._init_plot_elements()
        
        # Tight layout
        self.fig.tight_layout(pad=0.1)
        
    def _init_plot_elements(self):
        """Initialize the plot elements"""
        # Create angular array for full circle
        self.theta = np.linspace(0, 2*np.pi, self.buffer_size)
        
        # Initialize empty waveform data
        self.radius = np.zeros(self.buffer_size)
        
        # Create main waveform plot
        self.waveform_line, = self.ax.plot(self.theta, self.radius, 
                                          color='#3498DB', linewidth=1.0, alpha=0.8)
        
        # Create filled area for gradient effect
        self.waveform_fill = self.ax.fill_between(self.theta, 0, self.radius,
                                                 alpha=0.3, color=self.background_color)
        
        # Create center circle outline for amplitude indication
        self.center_circle = patches.Circle((0, 0), 0.1, 
                                          transform=self.ax.transData,
                                          facecolor=self.background_color,
                                          edgecolor='#3498DB', 
                                          linewidth=2,
                                          alpha=0.8)
        self.ax.add_patch(self.center_circle)
        
        # Create background grid circles
        self._create_background_grid()
        
        
    def _create_background_grid(self):
        """Create subtle background grid circles"""
        grid_radii = [0.3, 0.6, 0.9]
        self.grid_circles = []
        
        for radius in grid_radii:
            circle = patches.Circle((0, 0), radius,
                                  fill=False, 
                                  color='#404040', 
                                  alpha=0.2,
                                  linewidth=1,
                                  linestyle='--')
            self.ax.add_patch(circle)
            self.grid_circles.append(circle)
    
    def _start_animation(self):
        """Start the matplotlib animation"""
        if not self.is_active:
            self.is_active = True
            # Use matplotlib's FuncAnimation for smooth animation
            self.animation_obj = FuncAnimation(
                self.fig, 
                self._animate_frame, 
                interval=1000//self.target_fps,  # Convert fps to ms interval
                blit=False,  # Disable blitting for better compatibility
                cache_frame_data=False
            )
            # Force canvas redraw
            self.canvas.draw()
            
    def _animate_frame(self, frame):
        """Animation frame update function"""
        if not self.is_active:
            return []
        
        self.animation_time += 1.0 / self.target_fps
        
        try:
            with self.animation_lock:
                # Convert audio buffer to radius data for radial waveform
                buffer_list = list(self.audio_buffer)
                
                # Create radial waveform extending from center circle
                base_radius = 0.3  # Center circle radius
                max_extension = 0.7  # Maximum extension from center
                
                # Create radial waveform around the circumference
                for i, amplitude in enumerate(buffer_list):
                    # Scale amplitude to extension from center circle
                    extension = amplitude * max_extension
                    
                    # Set radius as base + extension (no rotation, no artistic variation)
                    self.radius[i] = base_radius + extension
                
                # Smooth the radius data for better visual appeal
                self.radius = self._smooth_array(self.radius, factor=0.2)
                
                # Update waveform line
                self.waveform_line.set_data(self.theta, self.radius)
                
                # Update filled area
                self._update_filled_area()
                
                # Update colors based on amplitude and recording state
                self._update_colors()
                
                # Update center circle
                self._update_center_circle()
                
        except Exception as e:
            print(f"Animation frame error: {e}")
            
        return [self.waveform_line]
    
    def _smooth_array(self, data, factor=0.3):
        """Apply smoothing to array data"""
        smoothed = np.copy(data)
        for i in range(1, len(data)-1):
            smoothed[i] = (1-factor) * data[i] + factor * (data[i-1] + data[i+1]) / 2
        return smoothed
    
    def _update_filled_area(self):
        """Update the filled area gradient effect"""
        # Remove old fill
        if hasattr(self, 'waveform_fill'):
            self.waveform_fill.remove()
        
        # Create new fill with gradient effect
        self.waveform_fill = self.ax.fill_between(
            self.theta, 0, self.radius,
            alpha=0.3,
            color=self._get_current_color()
        )
    
    def _update_colors(self):
        """Update colors based on amplitude and recording state"""
        current_color = self._get_current_color()
        
        # Update waveform line color
        self.waveform_line.set_color(current_color)
        
        # Add glow effect by creating multiple lines with decreasing alpha
        self._create_glow_effect(current_color)
    
    def _get_current_color(self):
        """Get current color based on amplitude and recording state"""
        if self.recording_state:
            # Blue to orange gradient based on amplitude
            amplitude_ratio = min(1.0, self.current_amplitude * 2)  # Scale for more sensitive color change
            
            # Blue RGB: (23, 162, 184) -> #17a2b8
            # Orange RGB: (253, 126, 20) -> #fd7e14
            blue_color = np.array([23, 162, 184]) / 255.0
            orange_color = np.array([253, 126, 20]) / 255.0
            
            # Interpolate between blue and orange
            interpolated_color = blue_color * (1 - amplitude_ratio) + orange_color * amplitude_ratio
            
            return interpolated_color
        else:
            # Dim blue when not recording
            return [0.09, 0.64, 0.72]  # Dimmed version of #17a2b8
    
    def _create_glow_effect(self, base_color):
        """Create glow effect around the waveform"""
        # Create multiple lines with increasing width and decreasing alpha for glow
        if hasattr(self, 'glow_lines'):
            for line in self.glow_lines:
                line.remove()
        
        self.glow_lines = []
        
        if self.recording_state and self.current_amplitude > 0.1:
            # Create glow layers
            glow_widths = [6, 4, 3]
            glow_alphas = [0.1, 0.15, 0.2]
            
            for width, alpha in zip(glow_widths, glow_alphas):
                glow_line, = self.ax.plot(self.theta, self.radius,
                                        color=base_color,
                                        linewidth=width,
                                        alpha=alpha)
                self.glow_lines.append(glow_line)
    
    def _update_center_circle(self):
        """Update the center amplitude indicator"""
        # Scale center circle based on amplitude
        base_size = 0.05
        amplitude_size = self.current_amplitude * 0.15
        total_size = base_size + amplitude_size
        
        # Add pulsing effect when recording
        if self.recording_state:
            pulse = math.sin(self.animation_time * 8) * 0.02  # Fast pulse
            total_size += pulse
        
        # Update circle properties
        self.center_circle.set_radius(total_size)
        self.center_circle.set_edgecolor(self._get_current_color())
        self.center_circle.set_facecolor(self.background_color)
        
        # Add glow to center circle when active
        if self.recording_state and self.current_amplitude > 0.2:
            self.center_circle.set_alpha(0.9)
        else:
            self.center_circle.set_alpha(0.6)
    
    
    def _on_resize(self, event):
        """Handle widget resize events"""
        if event.widget == self:
            # Update dimensions
            new_width = event.width - 10  # Account for padding
            new_height = event.height - 10
            
            if new_width > 50 and new_height > 30:  # Minimum size check
                self.width = new_width
                self.height = new_height
                # Matplotlib will handle the resize automatically
    
    def update_audio_data(self, amplitude: float):
        """Update with new audio amplitude data
        
        Args:
            amplitude: Audio amplitude level (0.0 to 1.0)
        """
        with self.animation_lock:
            # Only process audio data when actively recording
            if self.recording_state:
                # Smooth the amplitude
                self.amplitude_history.append(amplitude)
                
                # Calculate smoothed amplitude
                if len(self.amplitude_history) > 0:
                    smoothed = sum(self.amplitude_history) / len(self.amplitude_history)
                    
                    # Apply additional smoothing
                    self.last_smoothed_amplitude = (
                        self.smoothing_factor * self.last_smoothed_amplitude + 
                        (1 - self.smoothing_factor) * smoothed
                    )
                    
                    # Update current amplitude for display
                    self.current_amplitude = min(1.0, max(0.0, self.last_smoothed_amplitude))
                    
                    # Add to waveform buffer (convert to signed waveform)
                    # Create more interesting waveform pattern
                    waveform_value = self.current_amplitude
                    if amplitude > 0.05:
                        # Add some variation for active recording
                        variation = math.sin(time.time() * 15) * 0.1 * amplitude
                        waveform_value += variation
                        
                    self.audio_buffer.append(waveform_value)
            else:
                # When not recording, gradually decay the waveform to zero
                self.audio_buffer.append(0.0)
    
    def set_recording_state(self, is_recording: bool):
        """Set recording state for visual feedback
        
        Args:
            is_recording: True if currently recording, False otherwise
        """
        self.recording_state = is_recording
        
        # If not recording, gradually fade the waveform and reset amplitude
        if not is_recording:
            with self.animation_lock:
                # Clear amplitude indicators
                self.current_amplitude = 0.0
                self.amplitude_history.clear()
                self.last_smoothed_amplitude = 0.0
                
                # Add some zeros to fade out the waveform
                for _ in range(10):
                    self.audio_buffer.append(0.0)
    
    def set_colors(self, waveform_color: str = None, active_color: str = None, 
                   background_color: str = None):
        """Update colors for theme compatibility
        
        Args:
            waveform_color: Color for normal waveform
            active_color: Color when recording
            background_color: Background color
        """
        # Colors are handled dynamically in the gradient system
        # This method is kept for compatibility
        pass
    
    def clear_waveform(self):
        """Clear the waveform display"""
        with self.animation_lock:
            self.audio_buffer.clear()
            for _ in range(self.buffer_size):
                self.audio_buffer.append(0.0)
            self.current_amplitude = 0.0
            self.amplitude_history.clear()
            self.last_smoothed_amplitude = 0.0
    
    def start_animation(self):
        """Start the animation"""
        if not self.is_active:
            self._start_animation()
    
    def stop_animation(self):
        """Stop the animation"""
        self.is_active = False
        if self.animation_obj:
            self.animation_obj.event_source.stop()
    
    def destroy(self):
        """Clean shutdown of the widget"""
        self.stop_animation()
        if hasattr(self, 'fig'):
            plt.close(self.fig)
        super().destroy()


class WaveformVisualizerDemo:
    """Demo application for the matplotlib waveform visualizer"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Matplotlib Waveform Visualizer Demo")
        self.root.geometry("600x600")
        self.root.configure(bg="#2b2b2b")
        
        # Create visualizer
        self.visualizer = WaveformVisualizer(
            self.root, 
            width=550, 
            height=400
        )
        self.visualizer.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        # Demo controls
        self._create_controls()
        
        # Demo data generation
        self.demo_running = False
        self.demo_thread = None
        
    def _create_controls(self):
        """Create demo control buttons"""
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(pady=10)
        
        start_btn = ttk.Button(
            controls_frame, 
            text="Start Demo", 
            command=self._start_demo
        )
        start_btn.pack(side=tk.LEFT, padx=5)
        
        stop_btn = ttk.Button(
            controls_frame, 
            text="Stop Demo", 
            command=self._stop_demo
        )
        stop_btn.pack(side=tk.LEFT, padx=5)
        
        recording_btn = ttk.Button(
            controls_frame, 
            text="Toggle Recording State", 
            command=self._toggle_recording_state
        )
        recording_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(
            controls_frame, 
            text="Clear", 
            command=self.visualizer.clear_waveform
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
    def _start_demo(self):
        """Start demo data generation"""
        if not self.demo_running:
            self.demo_running = True
            self.demo_thread = threading.Thread(target=self._generate_demo_data, daemon=True)
            self.demo_thread.start()
            
    def _stop_demo(self):
        """Stop demo data generation"""
        self.demo_running = False
        
    def _toggle_recording_state(self):
        """Toggle recording state for visual testing"""
        current_state = self.visualizer.recording_state
        self.visualizer.set_recording_state(not current_state)
        
    def _generate_demo_data(self):
        """Generate demo audio data"""
        t = 0
        while self.demo_running:
            # Generate synthetic audio data
            # Mix of sine waves to simulate voice-like patterns
            amplitude = (
                0.4 * math.sin(t * 0.8) * max(0, math.sin(t * 0.1)) +   # Base frequency
                0.3 * math.sin(t * 1.5) * max(0, math.sin(t * 0.15)) +  # Mid frequency  
                0.2 * math.sin(t * 2.5) * max(0, math.sin(t * 0.2))     # High frequency
            )
            
            # Add some noise
            amplitude += np.random.normal(0, 0.08)
            
            # Ensure positive and scaled
            amplitude = max(0, min(1.0, abs(amplitude)))
            
            # Update visualizer
            self.visualizer.update_audio_data(amplitude)
            
            # Increment time and wait
            t += 0.05
            time.sleep(0.05)  # 20 Hz update rate
            
    def run(self):
        """Run the demo"""
        try:
            self.root.mainloop()
        finally:
            self._stop_demo()
            self.visualizer.stop_animation()


if __name__ == "__main__":
    # Run demo
    demo = WaveformVisualizerDemo()
    demo.run()
