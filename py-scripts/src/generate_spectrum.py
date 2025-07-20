import os
import json
import numpy as np
import librosa
import xml.etree.ElementTree as ET
from xml.dom import minidom
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def load_audio(file_path, sr=22050):
    try:
        y, sr = librosa.load(file_path, sr=sr)
        print(f"  Carregado {file_path} com taxa de amostragem {sr} Hz")
        print(f"  Duração: {librosa.get_duration(y=y, sr=sr):.2f} segundos")
        print(f"  Número de amostras: {len(y)}")
        
        return y, sr
    except Exception as e:
        print(f"Erro ao carregar {file_path}: {e}")
        return None, None

def compute_log_spectrum(y, sr, n_fft=2048, hop_length=512, n_bands=64):
    # Divide o áudio em n_bands segmentos temporais
    segment_length = len(y) // n_bands
    if segment_length == 0:
        segment_length = 1
    
    band_energies = []
    for i in range(n_bands):
        start = i * segment_length
        end = min((i + 1) * segment_length, len(y))
        segment = y[start:end]
        
        if len(segment) > 0:
            # Calcula RMS (energia) do segmento
            rms_energy = np.sqrt(np.mean(segment**2))
        else:
            rms_energy = 0
        
        band_energies.append(rms_energy)
    
    band_energies = np.array(band_energies)
    
    # Normalização simples 0-1
    if np.max(band_energies) > 0:
        normalized = band_energies / np.max(band_energies)
    else:
        normalized = band_energies
    
    return normalized

def create_spectrum_svg(spectrum_data, width=2000, height=200):
    num_bars = len(spectrum_data)
    bar_width = width / num_bars

    # Detectar transições de estrofe
    transition_value = 0.05
    transitions = [0]
    i = 1
    while i < len(spectrum_data):
        if i >= 3 and all(spectrum_data[j] <= transition_value for j in range(i-3, i)) and spectrum_data[i] > transition_value:
            transitions.append(i)
        i += 1
    if transitions[-1] != len(spectrum_data):
        transitions.append(len(spectrum_data))

    # Gerar cores para cada segmento
    n_segments = len(transitions) - 1
    colors = cm.plasma(np.linspace(0.2, 0.8, n_segments))
    hex_colors = [mcolors.to_hex(c) for c in colors]

    svg = ET.Element('svg', width=str(width), height=str(height), xmlns='http://www.w3.org/2000/svg')
    defs = ET.SubElement(svg, 'defs')
    # gradient = ET.SubElement(defs, 'linearGradient', id='spectrum-gradient', x1='0%', y1='0%', x2='0%', y2='100%')
    # ET.SubElement(gradient, 'stop', offset='0%', **{'stop-color': '#ffff00'})
    # ET.SubElement(gradient, 'stop', offset='100%', **{'stop-color': '#ff6600'})
    for seg_idx in range(n_segments):
        seg_start = transitions[seg_idx]
        seg_end = transitions[seg_idx+1]
        color = hex_colors[seg_idx]
        for i in range(seg_start, seg_end):
            amplitude = spectrum_data[i]
            x_left = i * bar_width - bar_width/2
            x_right = x_left + bar_width * 1.5
            bar_height = amplitude * (height/2) * 0.95  # metade da altura para cada lado

            # Triângulo para cima (parte superior)
            y_top = (height/2) - bar_height
            y_middle = height/2
            points_up = f"{x_left},{y_middle} {x_right},{y_middle} {(x_left + x_right)/2},{y_top}"
            ET.SubElement(svg, 'polygon', points=points_up, fill=color, opacity=str(1))

            # Triângulo para baixo (parte inferior)
            y_bottom = (height/2) + bar_height
            points_down = f"{x_left},{y_middle} {x_right},{y_middle} {(x_left + x_right)/2},{y_bottom}"
            ET.SubElement(svg, 'polygon', points=points_down, fill=color, opacity=str(1))

    # Fundo quadriculado (opcional, para parecer com o anexo)
    bg = ET.Element('rect', x="0", y="0", width=str(width), height=str(height), fill="#222")
    svg.insert(0, bg)
    # (Opcional: overlay quadriculado)
    pattern = ET.SubElement(defs, 'pattern', id='checker', patternUnits='userSpaceOnUse', width="20", height="20")
    ET.SubElement(pattern, 'rect', x="0", y="0", width="10", height="10", fill="#333", opacity="0.4")
    ET.SubElement(pattern, 'rect', x="10", y="10", width="10", height="10", fill="#333", opacity="0.4")
    overlay = ET.Element('rect', x="0", y="0", width=str(width), height=str(height), fill="url(#checker)")
    svg.insert(1, overlay)
    rough_string = ET.tostring(svg, 'unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    mp3_dir = os.path.abspath(os.path.join(base_dir, '../../mp3'))
    output_dir = os.path.abspath(os.path.join(base_dir, '../gen/spectrum'))
    os.makedirs(output_dir, exist_ok=True)
    mp3_files = [f for f in os.listdir(mp3_dir) if f.lower().endswith('.mp3')]
    mp3_files.sort()
    print(f"Processando {len(mp3_files)} arquivos MP3...")
    for i, mp3_file in enumerate(mp3_files):
        print(f"({i+1}/{len(mp3_files)}) {mp3_file}")
        mp3_path = os.path.join(mp3_dir, mp3_file)
        y, sr = load_audio(mp3_path)
        if y is None:
            continue
        spectrum = compute_log_spectrum(y, sr, n_bands=750)
        base_name = os.path.splitext(mp3_file)[0]
        json_path = os.path.join(output_dir, f"{base_name}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(spectrum.tolist(), f, indent=2)
        svg_content = create_spectrum_svg(spectrum)
        svg_path = os.path.join(output_dir, f"{base_name}.svg")
        with open(svg_path, 'w', encoding='utf-8') as f:
            f.write(svg_content)
        print(f"  ✓ {base_name}.json e {base_name}.svg gerados")
    print(f"Concluído! Arquivos em: {output_dir}")
    if i> 8:
        quit()

if __name__ == "__main__":
    main()
    print(f"Concluído! Arquivos em: {output_dir}")
if __name__ == "__main__":
    main()
