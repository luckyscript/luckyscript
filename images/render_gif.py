#!/usr/bin/env python3
"""Render animated SVG frames and combine into GIF."""

import os
import math
import re
from PIL import Image
import cairosvg
import tempfile
import io

SVG_PATH = os.path.expanduser("~/workbase/luckyscript/images/avatar-animated.svg")
OUTPUT_PATH = os.path.expanduser("~/workbase/luckyscript/images/avatar.gif")

# Animation parameters
FPS = 10
DURATION_SEC = 4  # 4-second loop (matches the blink cycle)
TOTAL_FRAMES = FPS * DURATION_SEC

def lerp(a, b, t):
    return a + (b - a) * t

def ease_in_out(t):
    return 0.5 * (1 - math.cos(math.pi * t))

def render_frame(frame_idx, total_frames):
    """Generate SVG with baked-in animation state for this frame."""
    t = frame_idx / total_frames  # 0..1
    
    with open(SVG_PATH, 'r') as f:
        svg = f.read()
    
    # --- BLINK (eyes) ---
    # Left eye: blink at 92%-96% of cycle
    blink_left = 1.0
    blink_phase_left = (t * 100) % 100  # blink happens at 92-96%
    if 92 <= blink_phase_left < 96:
        blink_left = 0.1
    elif blink_phase_left > 96:
        blink_left = 1.0
    
    # Right eye: blink at 94%-97% of cycle
    blink_right = 1.0
    blink_phase_right = (t * 100) % 100
    if 94 <= blink_phase_right < 97:
        blink_right = 0.1
    elif blink_phase_right > 97:
        blink_right = 1.0
    
    # Apply eye scale
    svg = re.sub(
        r'(<rect x="65" y="85" width="15" height="10" fill="#0d1117" class="eye-left"/>)',
        f'<rect x="65" y="{85 + 5*(1-blink_left)}" width="15" height="{10*blink_left}" fill="#0d1117"/>',
        svg
    )
    svg = re.sub(
        r'(<rect x="120" y="85" width="15" height="10" fill="#0d1117" class="eye-right"/>)',
        f'<rect x="120" y="{85 + 5*(1-blink_right)}" width="15" height="{10*blink_right}" fill="#0d1117"/>',
        svg
    )
    
    # --- TYPING HANDS ---
    # Left hand: oscillate -3px to +2px at 0.8s cycle
    hand_cycle = (t * (1/0.8)) % 1  # cycles per typing cycle
    hand_left_y = math.sin(hand_cycle * 2 * math.pi) * 2.5
    hand_right_y = -math.sin(hand_cycle * 2 * math.pi) * 2.5  # opposite phase
    
    svg = re.sub(
        r'(<rect x="20" y="165" width="30" height="10" fill="#e6b980" class="hand-left"/>)',
        f'<rect x="20" y="{165 + hand_left_y}" width="30" height="10" fill="#e6b980"/>',
        svg
    )
    svg = re.sub(
        r'(<rect x="150" y="165" width="30" height="10" fill="#e6b980" class="hand-right"/>)',
        f'<rect x="150" y="{165 + hand_right_y}" width="30" height="10" fill="#e6b980"/>',
        svg
    )
    
    # --- KEYBOARD KEY FLASHES ---
    # key-a: cycles 484f58 -> 58a6ff
    key_a_phase = (t * (1/1.2)) % 1
    key_a_fill = "#58a6ff" if key_a_phase > 0.35 and key_a_phase < 0.85 else "#484f58"
    
    # key-b: delayed 0.3s
    key_b_phase = ((t + 0.3/1.2) % 1)
    key_b_fill = "#58a6ff" if key_b_phase > 0.35 and key_b_phase < 0.85 else "#484f58"
    
    # key-c: delayed 0.6s, flashes to green
    key_c_phase = ((t + 0.6/1.2) % 1)
    key_c_fill = "#2ea043" if key_c_phase > 0.35 and key_c_phase < 0.85 else "#484f58"
    
    # key-d: delayed 0.9s
    key_d_phase = ((t + 0.9/1.2) % 1)
    key_d_fill = "#58a6ff" if key_d_phase > 0.35 and key_d_phase < 0.85 else "#484f58"
    
    svg = svg.replace(f'fill="#484f58" class="key-a"', f'fill="{key_a_fill}"')
    svg = svg.replace(f'fill="#58a6ff" class="key-a"', f'fill="{key_a_fill}"')
    svg = svg.replace(f'fill="#484f58" class="key-b"', f'fill="{key_b_fill}"')
    svg = svg.replace(f'fill="#58a6ff" class="key-b"', f'fill="{key_b_fill}"')
    svg = svg.replace(f'fill="#484f58" class="key-c"', f'fill="{key_c_fill}"')
    svg = svg.replace(f'fill="#58a6ff" class="key-c"', f'fill="{key_c_fill}"')
    svg = svg.replace(f'fill="#484f58" class="key-d"', f'fill="{key_d_fill}"')
    svg = svg.replace(f'fill="#58a6ff" class="key-d"', f'fill="{key_d_fill}"')
    
    # --- GLOW PULSE ---
    glow_phase = (t * (1/2.5)) % 1
    glow_opacity = 0.4 + 0.5 * (0.5 + 0.5 * math.sin(glow_phase * 2 * math.pi))
    glow_r = 3 + 2 * (0.5 + 0.5 * math.sin(glow_phase * 2 * math.pi))
    glow_r2 = 3 + 2 * (0.5 + 0.5 * math.sin((glow_phase + 0.5) * 2 * math.pi))
    glow_opacity2 = 0.4 + 0.5 * (0.5 + 0.5 * math.sin((glow_phase + 0.5) * 2 * math.pi))
    
    svg = svg.replace(
        '<circle cx="55" cy="75" r="3" fill="#2ea043" class="glow-l"/>',
        f'<circle cx="55" cy="75" r="{glow_r:.1f}" fill="#2ea043" opacity="{glow_opacity:.2f}"/>'
    )
    svg = svg.replace(
        '<circle cx="145" cy="75" r="3" fill="#2ea043" class="glow-r"/>',
        f'<circle cx="145" cy="75" r="{glow_r2:.1f}" fill="#2ea043" opacity="{glow_opacity2:.2f}"/>'
    )
    
    # --- BINARY FLICKER ---
    binary_phases = [
        (0, 3),     # binary-a
        (0.5, 3),   # binary-b
        (1, 3),     # binary-c
        (1.5, 3),   # binary-d
    ]
    opacities = {}
    for offset, period in binary_phases:
        phase = ((t + offset/period) % 1)
        # Simulate flicker pattern
        v = math.sin(phase * 2 * math.pi) * 0.5 + 0.5
        v2 = math.sin(phase * 4 * math.pi + 1) * 0.3 + 0.7
        opac = 0.15 + 0.55 * v * v2
        opacities[f'phase_{offset}_{period}'] = f'{opac:.2f}'
    
    # Replace binary opacities
    svg = svg.replace(f'fill="#1a5c3a" class="binary-a"', f'fill="#1a5c3a" opacity="{opacities["phase_0_3"]}"')
    svg = svg.replace(f'fill="#1a5c3a" class="binary-b"', f'fill="#1a5c3a" opacity="{opacities["phase_0.5_3"]}"')
    svg = svg.replace(f'fill="#1a5c3a" class="binary-c"', f'fill="#1a5c3a" opacity="{opacities["phase_1_3"]}"')
    svg = svg.replace(f'fill="#1a5c3a" class="binary-d"', f'fill="#1a5c3a" opacity="{opacities["phase_1.5_3"]}"')
    
    # --- SMILE BREATHING ---
    smile_phase = (t * (1/2)) % 1
    smile_width = 50 + 5 * math.sin(smile_phase * 2 * math.pi)
    svg = re.sub(
        r'(<rect x="75" y="105" width="50" height="5" fill="#c17c5e" class="smile"/>)',
        f'<rect x="75" y="105" width="{smile_width:.0f}" height="5" fill="#c17c5e"/>',
        svg
    )
    
    # Remove all CSS animation classes from SVG (they're baked in now)
    svg = re.sub(r'\s*<style>.*?</style>', '', svg, flags=re.DOTALL)
    
    return svg

def main():
    print(f"Rendering {TOTAL_FRAMES} frames at {FPS}fps...")
    
    frames = []
    for i in range(TOTAL_FRAMES):
        svg_content = render_frame(i, TOTAL_FRAMES)
        
        # Render to PNG bytes
        png_bytes = cairosvg.svg2png(
            bytestring=svg_content.encode('utf-8'),
            output_width=400,
            output_height=400
        )
        
        img = Image.open(io.BytesIO(png_bytes))
        frames.append(img)
        
        if (i + 1) % 10 == 0:
            print(f"  Frame {i+1}/{TOTAL_FRAMES}")
    
    # Save as animated GIF
    print(f"Saving GIF to {OUTPUT_PATH}...")
    frame_duration = 1000 // FPS  # ms per frame
    
    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=0,
        optimize=True,
        disposal=2
    )
    
    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"Done! GIF saved: {file_size / 1024:.1f} KB, {len(frames)} frames, {FPS}fps")

if __name__ == "__main__":
    main()
