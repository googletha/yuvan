# Yuvan AI Assistant - Web UI

A modern, ChatGPT-like web interface for Yuvan AI Assistant with voice animation features.

## 🌟 Features

- **ChatGPT-like Interface**: Modern, responsive chat UI design
- **Voice Animation**: Real-time voice visualization when Yuvan is speaking
- **Status Indicators**: Visual feedback for thinking, speaking, and idle states
- **Responsive Design**: Works on desktop and mobile devices
- **Voice Integration**: Full integration with Yuvan's voice system
- **Chat History**: Persistent conversation history during session
- **Modern Styling**: Beautiful gradients, animations, and transitions

## 🚀 Quick Start

### Method 1: Using the Launch Script (Recommended)

1. Navigate to your Yuvan project directory:
```bash
cd /path/to/yuvan
```

2. Run the launch script:
```bash
python launch_yuvan_ui.py
```

The script will:
- Check and install missing dependencies
- Verify the environment setup
- Launch the web UI at http://localhost:8501

### Method 2: Manual Launch

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Launch the UI:
```bash
streamlit run yuvan_ui.py
```

## 🎨 UI Components

### Voice Animation States

The UI includes different animated states:

- **Idle**: Subtle pulsing circle when ready
- **Thinking**: Rotating dots animation while processing
- **Speaking**: Dynamic waveform visualization during voice output
- **Listening**: Pulsing circles for voice input (future feature)

### Chat Interface

- **User Messages**: Right-aligned with user icon
- **Assistant Messages**: Left-aligned with robot icon
- **Animated Entries**: Smooth slide-in animations for new messages
- **Scrollable History**: Auto-scrolling chat history

### Status Indicators

Color-coded status indicators with animations:
- 🤔 **Thinking**: Purple gradient with pulse animation
- 🎤 **Speaking**: Green gradient with dynamic animation
- 👂 **Listening**: Blue gradient (for future voice input)
- 💬 **Ready**: Gray idle state

## 🎛️ Controls

### Sidebar Features

- **Clear Chat**: Reset conversation history
- **Voice Settings**: Enable/disable voice output
- **Voice Speed**: Adjust speech speed (future feature)
- **About Section**: Information about Yuvan's capabilities

### Main Interface

- **Text Input**: Type messages to Yuvan
- **Send Button**: Submit messages
- **Voice Input**: Future feature for voice commands

## 🔧 Technical Details

### Dependencies

Core UI dependencies:
- `streamlit`: Web framework
- `plotly`: Voice animations
- `numpy`: Mathematical operations
- `pygame`: Audio playback
- `streamlit-javascript`: Enhanced interactions

### Voice Integration

The UI integrates with Yuvan's existing voice system:
- `yuvan.voice_system`: TTS functionality
- `yuvan.silero_tts`: Advanced voice synthesis
- `yuvan.task_handler`: Command processing

### File Structure

```
├── yuvan_ui.py              # Main UI application
├── voice_animation.py       # Voice animation components
├── launch_yuvan_ui.py       # Launch script
├── UI_README.md            # This documentation
└── requirements.txt        # Dependencies
```

## 🎯 Usage Tips

1. **Voice Output**: Enable voice output in the sidebar for full experience
2. **Mobile**: The UI is responsive and works on mobile devices
3. **Performance**: Animations may use more CPU; disable if needed
4. **Browser**: Works best in modern browsers (Chrome, Firefox, Safari)

## 🛠️ Customization

### Styling

The UI uses custom CSS with:
- ChatGPT-inspired color scheme (#10A37F primary)
- Smooth animations and transitions
- Responsive breakpoints
- Modern shadows and gradients

### Voice Animations

Voice animations can be customized in `voice_animation.py`:
- Waveform intensity and complexity
- Animation speed and style
- Color schemes and effects
- Animation types and behaviors

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Run `pip install -r requirements.txt`
2. **Voice Not Working**: Check pygame and audio system
3. **Slow Animations**: Reduce animation complexity or disable
4. **Port Already in Use**: Change port in launch script

### Performance Tips

- Close other browser tabs for better performance
- Disable voice output if not needed
- Clear chat history for longer sessions
- Use modern browsers for best experience

## 🚀 Future Features

- Voice input with speech recognition
- Customizable themes and colors
- Export chat history
- Voice speed controls
- Advanced animation options
- Multi-language support

## 📝 Notes

- Voice features require proper audio setup
- UI state is session-based (not persistent across restarts)
- Animations work best on modern devices
- Voice synthesis may have slight delays

---

**Enjoy your enhanced Yuvan AI Assistant experience! 🤖✨**