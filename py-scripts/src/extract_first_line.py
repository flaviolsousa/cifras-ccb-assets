#!/usr/bin/env python

"""
add: 
  https://github.com/eneiasramos/ccb-hinario-5-do/tree/master/do/musescore/xml
to:
  ./musescore

Usage:
    python3 src/extract_first_line.py
"""

import os
from pathlib import Path
from music21 import converter
import subprocess
import xml.etree.ElementTree as ET
from PIL import Image

def convert_mscx_to_musicxml(mscx_file, output_file):
  """Convert MSCX file to MusicXML using MuseScore CLI."""
  try:
    subprocess.run(["/bin/mscore", "-o", output_file, mscx_file], check=True)
  except subprocess.CalledProcessError as e:
    print(f"Error converting {mscx_file} to MusicXML: {e}")

def remove_xml_tags(xml_file, tags_to_remove):
  """Remove specific tags from a MusicXML file in-place."""
  tree = ET.parse(xml_file)
  root = tree.getroot()

  for tag in tags_to_remove:
    for parent in root.findall(f'.//{tag}/..'):
      try:
        for elem in parent.findall(tag):
          parent.remove(elem)
      except Exception as e:
        print(f"Error removing: {elem}\n{e}")

  tree.write(xml_file, encoding='utf-8', xml_declaration=True)

def extract_first_line(input_dir, output_dir):
  """Extract the first line of organ parts from MSCX files and save as PNG."""
  # i = 10

  if not os.path.exists(output_dir):
    os.makedirs(output_dir)

  for filename in os.listdir(input_dir):
    # if not "hino-154." in filename:
    #   continue
    # if not "coro-2." in filename:
    #   continue
    if filename.endswith('.mscx'):
      hymn_code = filename.split('-')[1].split('.')[0].zfill(3)
      if "coro" in filename:
        hymn_code = f"coro-{hymn_code}"
      musicxml_file = os.path.join(output_dir, f"{hymn_code}.xml")
      output_file = os.path.join(output_dir, f"{hymn_code}.png")

      try:
        # Convert MSCX to MusicXML
        convert_mscx_to_musicxml(os.path.join(input_dir, filename), musicxml_file)

        # Remove unwanted XML tags
        remove_xml_tags(musicxml_file, ['movement-title', 'text', 'words', 'direction', 'credit', 'creator', 'harmony'])

        # Parse MusicXML file
        score = converter.parse(musicxml_file, format='musicxml')

        # Extract first 4 measures of organ parts
        organ_parts = [part for part in score.parts if part.getInstrument().instrumentName == "Orgão de tubos"]

        if organ_parts:
          first_line = organ_parts[0].measures(1, 8)

          # Adjust the beam mode for all notes in the first line
          adjust_beam_mode(first_line)

          # Save the first line as a PNG file
          first_line.write('musicxml.png', fp=output_file)

          # Process the image
          crop_and_trim_image(output_file.replace(".png", "-1.png"), os.path.join(output_dir, f"{hymn_code}.png"))

          print(f"File saved: {output_file}")
        else:
          print(f"No organ parts found in {filename}")

      except Exception as e:
        print(f"Error processing {filename}: {e}")
      finally:
        # if "154" in musicxml_file:
        #   break

        # Remove temporary files
        if os.path.exists(musicxml_file):
          os.remove(musicxml_file)
        temp_musicxml_file = os.path.join(output_dir, f"{hymn_code}.musicxml")
        if os.path.exists(temp_musicxml_file):
          os.remove(temp_musicxml_file)
        temp_png_file_1 = os.path.join(output_dir, f"{hymn_code}-1.png")
        if os.path.exists(temp_png_file_1):
          os.remove(temp_png_file_1)
        temp_png_file_2 = os.path.join(output_dir, f"{hymn_code}-2.png")
        if os.path.exists(temp_png_file_2):
          os.remove(temp_png_file_2)
    else:
      print(f"Skipping non-MSCX file: {filename}")
    # if i > 0:
    #   i -= 1
    # else:
    #   break

def crop_and_trim_image(input_file, output_file):
  """Crop and trim the image to remove unnecessary parts."""
  with Image.open(input_file) as img:
    # Crop the image: remove 45 pixels from the top and limit to 550 pixels height
    cropped_img = img.crop((0, 100, img.width, img.height))
    cropped_img = cropped_img.crop(cropped_img.getbbox())

    # Find the first transparent row at the bottom
    bbox = cropped_img.getbbox()
    for y in range(50, cropped_img.height):
      row_bbox = cropped_img.crop((0, y, cropped_img.width, y + 1)).getbbox()
      if not row_bbox:
        bbox = (0, 0, cropped_img.width, y)
        break

    if bbox:
      trimmed_img = cropped_img.crop(bbox)
    else:
      trimmed_img = cropped_img

    # Save the processed image
    trimmed_img.save(output_file)
    print(f"Processed file saved: {output_file}")

def adjust_beam_mode(first_line):
  """Adjust the beam mode for all notes in the first line."""
  for note in first_line.flat.notes:
    if note.beams:
      for beam in note.beams:
        beam.type = 'continue'
    else:
      note.beams.append('start')

if __name__ == "__main__":
  script_dir = Path(__file__).parent.parent
  input_directory = script_dir.parent / 'musescore'
  output_directory = script_dir / 'gen' / 'png-intro'
  extract_first_line(input_directory, output_directory)
