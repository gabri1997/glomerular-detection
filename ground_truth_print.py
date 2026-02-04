from openslide import open_slide
import numpy as np
import json
import yaml
import cv2
import os

def get_slide_element_at_level(slide, lvl):
        num_levels = slide.level_count
        # Controlla se il livello richiesto è valido
        while lvl >= 0:
            if lvl < num_levels: 
                return slide.level_dimensions[lvl], lvl
            lvl -= 1  
        return None 


def draw_ground_truth(wsi_path, gt_path, wsi_level, dest_folder, wsi_info_file):

    with open(gt_path, 'r') as gt_file:
            gt_boxes = json.load(gt_file)

    with open(wsi_info_file, 'r') as info:
            slide_info=yaml.safe_load(info)
    
    slide_img = open_slide(wsi_path)
    slide = wsi_path.split('/')[-1]
    slide_name = os.path.splitext(slide)[0]
    try:
        slide_level_dims, found_level = get_slide_element_at_level(slide_img, wsi_level)
    except:
        if wsi_level > 0:
            slide_level_dims, found_level = get_slide_element_at_level(slide_img, wsi_level - 1)
    region = slide_img.read_region((0, 0), found_level, slide_level_dims) 
    region_np = np.array(region)

    slide_name_extended = slide_name + '.svs'
    slide_name_extended_2 = slide_name +'.ndpi'

    if slide_name_extended in slide_info.keys(): 
        lv0_dims = slide_info[slide_name_extended]["Slide_LV0_dims"]
        lv1_dims = slide_info[slide_name_extended]["Slide_LV1_dims"]
        print(f"Dimensioni del livello 1 per {slide_name_extended}: {lv1_dims}")
    else:
        pass

    if slide_name_extended_2 in slide_info.keys():
        lv0_dims = slide_info[slide_name_extended_2]["Slide_LV0_dims"]
        lv1_dims = slide_info[slide_name_extended_2]["Slide_LV1_dims"]
        print(f"Dimensioni del livello 1 per {slide_name_extended_2}: {lv1_dims}")
    else:
        pass

    scale_x = int(lv1_dims[0]) / int(lv0_dims[0])
    scale_y = int(lv1_dims[1]) / int(lv0_dims[1])

    for feature in gt_boxes['features']:
            coordinates = feature['geometry']['coordinates'][0]
            x_min_gt = min(c[0] for c in coordinates) * scale_x
            y_min_gt = min(c[1] for c in coordinates) * scale_y
            x_max_gt = max(c[0] for c in coordinates) * scale_x
            y_max_gt = max(c[1] for c in coordinates) * scale_y
    
            color = (0, 0, 255)  # Blu
            thickness = 2
          
            cv2.rectangle(region_np, (int(x_min_gt), int(y_min_gt)), (int(x_max_gt), int(y_max_gt)), color, thickness)
    
    output_file_path = os.path.join(dest_folder, f"{slide_name}_mapped.jpg")
    quality = 30
    print('Sto salvando la WSI con la annotazione')
    print('Path: ', output_file_path)
    cv2.imwrite(output_file_path, cv2.cvtColor(region_np, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])

if __name__ == '__main__':

    wsi_path = '/work/grana_pbl/Detection_Glomeruli/HAMAMATSU/R23_281_2A1_IgA-FITC.ndpi'
    #wsi_path = '/work/grana_pbl/Detection_Glomeruli/HAMAMATSU/R23_223_2A1_IgG-FITC.ndpi'
    gt_path = '/work/grana_pbl/Detection_Glomeruli/Coordinate_HAMAMATSU/R23_281_2A1_IgA-FITC.geojson'
    #gt_path = '/work/grana_pbl/Detection_Glomeruli/Coordinate_HAMAMATSU/R23_223_2A1_IgG-FITC.geojson'

    dest_folder = '/work/grana_pbl/Detection_Glomeruli/WSI_With_Ground_Truth'
    wsi_info_file = '/work/grana_pbl/Detection_Glomeruli/INFO_wsi_file_dictionary_ALL.yaml'
    wsi_level = 1

    # # Ottieni i file di WSI e ground truth come dizionari basati sul nome base
    # wsi_files = {os.path.splitext(f)[0]: os.path.join(wsi_path, f) for f in os.listdir(wsi_path)}
    # gt_files = {os.path.splitext(f)[0]: os.path.join(gt_path, f) for f in os.listdir(gt_path)}

    # common_keys = set(wsi_files.keys()) & set(gt_files.keys()) 

    # if not common_keys:
    #     raise ValueError("Nessuna corrispondenza trovata tra WSI e ground truth!")

    # for key in common_keys:

    #     current_wsi_path = wsi_files[key]
    #     current_gt_path = gt_files[key]
    
    #     slide_name = current_wsi_path.split('/')[-1]
    #     slide_name = os.path.splitext(slide_name)[0]
        
    #     print(f"Processando WSI: {slide_name} con GT: {current_gt_path}")
        
    # draw_ground_truth(
    #     current_wsi_path,
    #     current_gt_path,
    #     wsi_level,
    #     dest_folder,
    #     wsi_info_file,
    # )

    draw_ground_truth(
        wsi_path,
        gt_path,
        wsi_level,
        dest_folder,
        wsi_info_file,
    )

