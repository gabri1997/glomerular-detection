from openslide import open_slide
import os
import glob
import numpy as np
import json
from PIL import Image

def get_slide_element_at_level(slide, lvl):
    num_levels = slide.level_count
    while lvl >= 0:
        if lvl < num_levels:
            return slide.level_dimensions[lvl], lvl
        lvl -= 1
    return None

def get_dimensions_for_key(json_file, key):
    
    with open(json_file, 'r') as f:
        data = json.load(f)

    key = os.path.splitext(key)[0]
    for k in data.keys():
        if os.path.splitext(k)[0] == key:
            found_key = os.path.splitext(k)[0]  
            key_1 = found_key + '.ndpi'
            key_2 = found_key + '.svs'  

            try:
                lv_0_dims = data[key_1].get("Slide_LV0_dims", None)[0]  
                lv_1_dims = data[key_1].get("Slide_LV1_dims", None)[0]
                micrometer_lv0 = data[key_1].get("Micron_per_pixel_x_LV0", None)
                micrometer_lv1 = data[key_1].get("Micron_per_pixel_x_LV1", None)
            except KeyError:
                print(f"Chiave mancante in JSON per {key_1}")
                lv_0_dims = data[key_2].get("Slide_LV0_dims", None)[0]  
                lv_1_dims = data[key_2].get("Slide_LV1_dims", None)[0]
                micrometer_lv0 = data[key_2].get("Micron_per_pixel_x_LV0", None)
                micrometer_lv1 = data[key_2].get("Micron_per_pixel_x_LV1", None)
                return lv_0_dims, lv_1_dims, micrometer_lv0, micrometer_lv1

            return lv_0_dims, lv_1_dims, micrometer_lv0, micrometer_lv1

def generate_glomeruli_crop(image_input_folder, annotation_input_folder, output_folder):

    os.makedirs(output_folder, exist_ok=True) 
    files_input_images = sorted(glob.glob(os.path.join(image_input_folder, '*.svs')))
    annotations_input_files = sorted(glob.glob(os.path.join(annotation_input_folder, '*.geojson')))
    wsi_level = 1

    for image_path, annotation_path in zip(files_input_images, annotations_input_files):

        idx_box = 0
        slide = open_slide(image_path)
        slide_name = os.path.splitext(os.path.basename(image_path))[0]
        # dest_path = os.path.join(output_folder, slide_name)
        # os.makedirs(dest_path, exist_ok=True)
        print(f"Slide - {slide_name} - opened successfully")

        try:
            slide_level_dims, found_level = get_slide_element_at_level(slide, wsi_level)
        except:
            if wsi_level > 0:
                slide_level_dims, found_level = get_slide_element_at_level(slide, wsi_level - 1)

        region = slide.read_region((0, 0), found_level, slide_level_dims)
        region_np = np.array(region)[:, :, :3]  # Rimuovo il canale alpha

        lv0_width, lv0_height = slide.level_dimensions[0]
        lv1_width, lv1_height = slide.level_dimensions[wsi_level]

        scale_x = lv1_width / lv0_width
        scale_y = lv1_height / lv0_height

        with open(annotation_path, 'r') as gt_file:
            annotation_boxes = json.load(gt_file)  
    
        for feature in annotation_boxes['features']:
            coordinates = feature['geometry']['coordinates'][0]
            # Ridimensiona le coordinate da livello 0 a livello 1
            x_min_gt = int(min(c[0] for c in coordinates) * scale_x)  
            y_min_gt = int(min(c[1] for c in coordinates) * scale_y)  
            x_max_gt = int(max(c[0] for c in coordinates) * scale_x)
            y_max_gt = int(max(c[1] for c in coordinates) * scale_y)

            idx_box += 1
            cropped_region = region_np[y_min_gt:y_max_gt, x_min_gt:x_max_gt]

            if cropped_region.size == 0:
                print(f"Warning: Empty crop for {slide_name} at {idx_box}")
                continue

            crop_img = Image.fromarray(cropped_region)

            crop_filename = f"{slide_name}_glomerulo_{idx_box:03d}.png"

            final_dest_path = os.path.join(output_folder, slide_name, crop_filename)

            os.makedirs(os.path.dirname(final_dest_path), exist_ok=True)

            crop_img.save(final_dest_path)

            print(f"Saved cropped region: {final_dest_path}")


if __name__ == "__main__":

    image_input_folder = '/work/grana_pbl/Detection_Glomeruli/Glomeruli/prova_wsi'
    annotation_input_folder = '/work/grana_pbl/Detection_Glomeruli/Glomeruli/annotazione_prova_wsi'
    output_folder = '/work/grana_pbl/Detection_Glomeruli/Glomeruli/Prova_WSI'
    
    info_yaml = '/work/grana_pbl/Detection_Glomeruli/INFO_wsi_file_dictionary_ALL.yaml'
    generate_glomeruli_crop(image_input_folder, annotation_input_folder, output_folder)

