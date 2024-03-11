import os 
import re
import pandas as pd
import numpy as np
import pdfquery
import fitz
from datetime import timedelta

def initial_search(name_of_pdf = "", 
                   search_string = ""):
    pdf = fitz.open(name_of_pdf) # make input of function
    results = []
    cropped_file_names = []

    pattern = r"P\d+"

    for page_num, page in enumerate(pdf):
        search_instances = page.search_for(search_string) # make input of function
        if search_instances:
            position_order_list =[]
            last_instance = search_instances[-1]

            initial_search_area = fitz.Rect(0 + 20, last_instance.y0, page.rect.width - 20, last_instance.y0 + 13)

            page.draw_rect(initial_search_area, color=(1, 0, 0), width=1.5) 


            text = page.get_textbox(initial_search_area)

            matches = re.findall(pattern, text)

            if matches:
                #print("Extracted text Poppulated:", matches)
                position_order_list.append(matches)
                
                #matches[0][1:]
                rider_pos = matches[0][1:]
                one_pos_down = int(rider_pos) + 1
                current_pos_right_format = matches[0]
                one_pos_down_right_format = "P" + str(one_pos_down)
                #print(" ")
                #print(current_pos_right_format, one_pos_down_right_format)
                
                old_pos = current_pos_right_format
                new_pos = one_pos_down_right_format
                
                original_pos_instances = page.search_for(old_pos)
            
                if original_pos_instances:
                    last_original_pos_instance = original_pos_instances[-1]
                    following_pos_instances = page.search_for(one_pos_down_right_format, clip=fitz.Rect(0, last_original_pos_instance.br.y, page.rect.width, page.rect.height))
                    
                    if not following_pos_instances and page_num + 1 < len(pdf):
                        next_page = pdf[page_num + 1]
                        following_pos_instances = next_page.search_for(one_pos_down_right_format)
                        
                        if following_pos_instances:
                            first_instance_next_page = following_pos_instances[0]
                            end_of_page = fitz.Rect(page.rect.x0, page.rect.y1 - 65, page.rect.x1, page.rect.y1)
                            results.append({
                                "page_num": page_num, #+ 1,
                                "original_p_position": last_original_pos_instance,  # no original position on the next page
                                "following_p_position": end_of_page
                            })
                    elif following_pos_instances:
                        # Found on the current page
                        first_instance = following_pos_instances[0]
                        results.append({
                            "page_num": page_num,
                            "original_p_position": last_original_pos_instance,
                            "following_p_position": first_instance
                        })

            # checker          
            #else:
            #    print("Extracted text Failed: ", matches)

    for index, finding in enumerate(results):
        output_pdf = fitz.open() 

        page_num = finding['page_num']
        page = pdf.load_page(page_num)

        bridewell_position = finding['original_p_position']
        next_p_position = finding['following_p_position']

        rect = fitz.Rect(0 + 10, bridewell_position.br.y, page.rect.width - 10, next_p_position.y0 - 5)
        

        new_pdf_page = output_pdf.new_page(-1, width=rect.width, height=rect.height)
        new_pdf_page.set_mediabox(rect)

        clip_rect = fitz.Rect(0, 0, rect.width, rect.height)
        new_pdf_page.show_pdf_page(clip_rect, pdf, pno=page_num, clip=rect)

        output_filename = f"cropped_area_extended_{index}.pdf"
        cropped_file_names.append(output_filename)
        output_pdf.save(output_filename)
        output_pdf.close()
        
    # for viz purpose
    #pdf.save("modified_initial_search.pdf") 
    #pdf.close()


    print("All executed, check source folder for cropped pdf(s)")
    return cropped_file_names


def standard_row(pdf_name, X0, WIDTH):
    pdf = fitz.open(pdf_name)  ## make it function call 
    results = []
    for page_num, page in enumerate(pdf):
        bridewell_instances = page.search_for("SECTOR 1")
        if bridewell_instances:
            last_instance = bridewell_instances[-1]
            
            initial_search_area = fitz.Rect(0 + X0, last_instance.y0 + 13, page.rect.width + WIDTH, page.rect.height)
            # make the above a function call 
            
            page.draw_rect(initial_search_area, color=(1, 0, 0), width=1.5) 
            
            
            text = page.get_textbox(initial_search_area)
            results.append(text)

            
    # right format for dataframe later on
    lap_no_list = [float(value) for value in results[0].split('\n')]
            
    pdf.close()
    return lap_no_list

def row_with_text(pdf_name, X0, WIDTH):
    pdf = fitz.open(pdf_name)  ## make it function call 
    results = []
    for page_num, page in enumerate(pdf):
        bridewell_instances = page.search_for("SECTOR 1")
        if bridewell_instances:
            last_instance = bridewell_instances[-1]
            
            initial_search_area = fitz.Rect(0 + X0, last_instance.y0 + 13, page.rect.width + WIDTH, page.rect.height)
            # make the above a function call 
            
            page.draw_rect(initial_search_area, color=(1, 0, 0), width=1.5) 
            
            
            text = page.get_textbox(initial_search_area)
            results.append(text)

            
    # right format for dataframe later on
    sector1_data = []
    for value in results[0].split('\n'):
        try:
            sector1_data.append(float(value))
        except ValueError:
            sector1_data.append(value)
            
    pdf.close()
    return sector1_data


def last_mph_column_adjuster(sector5_time, sector5_mph):
    recorded_mph = sector5_mph # mph
    lap_times = sector5_time # time

    recorded_mph_np = np.array(recorded_mph, dtype=float)  


    adjusted_recorded_mph = list(recorded_mph_np)

    for i, time in enumerate(lap_times):
        if time == 'IN PIT':
            adjusted_recorded_mph.insert(i, np.nan)

    adjusted_recorded_mph = adjusted_recorded_mph[:len(lap_times)]

    adjusted_recorded_mph_np = np.array(adjusted_recorded_mph) 
    
    return list(adjusted_recorded_mph_np)

def full_lap_time(pdf_name, X0, WIDTH):
    pdf = fitz.open(pdf_name)  ## make it function call ##done
    results = []
    for page_num, page in enumerate(pdf):
        bridewell_instances = page.search_for("SECTOR 1")
        if bridewell_instances:
            last_instance = bridewell_instances[-1]
            
            initial_search_area = fitz.Rect(0 + X0, last_instance.y0 + 13, page.rect.width + WIDTH, page.rect.height)

            # make the above a function call 
            
            page.draw_rect(initial_search_area, color=(1, 0, 0), width=1.5) 
            
            text = page.get_textbox(initial_search_area)
            results.append(text)
    
    time_list = results[0].split('\n')
    formatted_lap_list = [time.strip() for time in time_list]
    #formatted_lap_list = [np.nan] + formatted_lap_list
            
    pdf.close()
    return formatted_lap_list

def string_equalizer(target, to_check):
    target_length = len(target)
    to_check_length = len(to_check)
    if to_check_length == target_length:
        return to_check
    else:
        updated_list = [np.nan] + to_check
        return updated_list


# Additional functions
def to_timedelta(time_str):
    if pd.isna(time_str):
        return timedelta(0)
    # Split the time string based on the presence of ':'
    parts = time_str.split(':')
    if len(parts) == 2:
        # Time format includes minutes
        minutes = int(parts[0])
        seconds, milliseconds = parts[1].split('.')
    else:
        # Time format does not include minutes
        minutes = 0
        seconds, milliseconds = parts[0].split('.')
    
    return timedelta(minutes=minutes, seconds=int(seconds), milliseconds=int(float('0.' + milliseconds) * 1000))

def crash_during_lap_checker(lap_time, first_sector, sector_to_be_checked):
    time_deltas = [to_timedelta(ts) for ts in lap_time]    

    # find upper outlier threshold
    q75, q25 = np.percentile(time_deltas, [90 ,10]) # make it even more rigorous
    iqr = q75 - q25
    outlier_threshold = q75 + 1.5*(iqr)

    if len(sector_to_be_checked) != len(lap_time) & len(sector_to_be_checked) != len(first_sector):
        sector_updated = sector_to_be_checked
        time_deltas_max = []
        for index, value in enumerate(time_deltas):
                if outlier_threshold < time_deltas[index]:
                    time_deltas_max.append(time_deltas[index])
                #print((time_deltas_max))
                filtered_timedeltas = [td for td in time_deltas_max if td]

                # find highest timedelta
                highest_timedelta = max(filtered_timedeltas) if filtered_timedeltas else None
                #print("")
                #print(highest_timedelta)
                
                if highest_timedelta:
                    index_of_highest = time_deltas.index(highest_timedelta)
                    #print(index_of_highest)
                    
        sector_updated.insert(index_of_highest, np.nan)

        return sector_updated
    
    else:
        return sector_to_be_checked
    

# Track templates
def brandshatch(cropped_file_names):
    dfs = {}
    for i, name in enumerate(cropped_file_names):  
        lap_count = row_with_text(cropped_file_names[i], 20, -529)
        sector_1 = row_with_text(cropped_file_names[i], 45, -495)
        sector_1 = string_equalizer(lap_count, sector_1)

        lap_time = full_lap_time(cropped_file_names[i], 365, -168)
        lap_time = string_equalizer(lap_count, lap_time)

        mph = standard_row(cropped_file_names[i], 423, -120)


        table = {
        'LAP No' : row_with_text(cropped_file_names[i], 20, -529),
        'SECTOR 1' : sector_1,
        'SECTOR 1_1' : standard_row(cropped_file_names[i], 90, -460),

        'SECTOR 2' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 135, -410)),



        'SECTOR 2_1' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 165, -380)),

        'SECTOR 3' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 210, -330)),

        'SECTOR 3_1' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 250, -305)),

        'SECTOR 4' : crash_during_lap_checker(lap_time, sector_1,
            row_with_text(cropped_file_names[i], 290, -255)),


        'SECTOR 4_1' : crash_during_lap_checker(lap_time, sector_1,
            last_mph_column_adjuster(row_with_text(cropped_file_names[i], 290, -255),
                                                standard_row(cropped_file_names[i], 325, -225))),

        'LAP TIME' : lap_time,
        'MPH' : string_equalizer(lap_count, mph)
        }


        build_df = pd.DataFrame(table)
        build_df.set_index("LAP No", inplace = True)
        dfs[name] = build_df
    return dfs 

def donington(cropped_file_names):
    dfs = {}
    for i, name in enumerate(cropped_file_names):  
        lap_count = row_with_text(cropped_file_names[i], 20, -529)
        
        sector_1 = row_with_text(cropped_file_names[i], 45, -495)
        sector_1 = string_equalizer(lap_count, sector_1)
        
        lap_time = full_lap_time(cropped_file_names[i], 390, -153)
        lap_time = string_equalizer(lap_count, lap_time)
        
        mph = standard_row(cropped_file_names[i], 435, -113)
        
        
        table = {
        'LAP No' : row_with_text(cropped_file_names[i], 20, -529),
        'SECTOR 1' : sector_1,
        'SECTOR 1_1' : standard_row(cropped_file_names[i], 80, -465),
            
        'SECTOR 2' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 115, -425)),
                                              
                                              
                                              
        'SECTOR 3' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 190, -360)),
            
        'SECTOR 3_1' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 215, -330)),
            
        'SECTOR 4' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 255, -290)),
            
        'SECTOR 5' : crash_during_lap_checker(lap_time, sector_1,
            row_with_text(cropped_file_names[i], 325, -225)),
            
            
        'SECTOR 5_1' : crash_during_lap_checker(lap_time, sector_1,
            last_mph_column_adjuster(row_with_text(cropped_file_names[i], 325, -225),
                                                standard_row(cropped_file_names[i], 355, -195))),
            
        'LAP TIME' : lap_time,
        'MPH' : string_equalizer(lap_count, mph)
        }
        
        
        build_df = pd.DataFrame(table)
        build_df.set_index("LAP No", inplace = True)
        dfs[name] = build_df
    return dfs 

def snetterton(cropped_file_names):
    dfs = {}
    for i, name in enumerate(cropped_file_names):  
        lap_count = row_with_text(cropped_file_names[i], 20, -529)
        
        sector_1 = row_with_text(cropped_file_names[i], 55, -475)
        sector_1 = string_equalizer(lap_count, sector_1)
        
        lap_time = full_lap_time(cropped_file_names[i], 345, -193)
        lap_time = string_equalizer(lap_count, lap_time)
        
        mph = standard_row(cropped_file_names[i], 405, -143)
        
        
        table = {
        'LAP No' : row_with_text(cropped_file_names[i], 20, -529),
        'SECTOR 1' : sector_1,
        'SECTOR 1_1' : standard_row(cropped_file_names[i], 105, -440),
            
        'SECTOR 2' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 160, -385)),
            
        'SECTOR 2_1' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 200, -345)),
                                              

        'SECTOR 3' : crash_during_lap_checker(lap_time, sector_1,
            row_with_text(cropped_file_names[i], 255, -285)),
            
            
        'SECTOR 3_1' : crash_during_lap_checker(lap_time, sector_1,
            last_mph_column_adjuster(row_with_text(cropped_file_names[i], 255, -285),
                                                standard_row(cropped_file_names[i], 295, -250))),
            
        'LAP TIME' : lap_time,
        'MPH' : string_equalizer(lap_count, mph)
        }
     
        build_df = pd.DataFrame(table)
        build_df.set_index("LAP No", inplace = True)
        dfs[name] = build_df
    return dfs

def knockhill(cropped_file_names):
    dfs = {}
    for i, name in enumerate(cropped_file_names):  
        lap_count = row_with_text(cropped_file_names[i], 20, -529)
        
        sector_1 = row_with_text(cropped_file_names[i], 55, -475)
        sector_1 = string_equalizer(lap_count, sector_1)
        
        lap_time = full_lap_time(cropped_file_names[i], 345, -193)
        lap_time = string_equalizer(lap_count, lap_time)
        
        mph = standard_row(cropped_file_names[i], 405, -143)
        
        
        table = {
        'LAP No' : row_with_text(cropped_file_names[i], 20, -529),
        'SECTOR 1' : sector_1,
        #'SECTOR 1_1' : standard_row(cropped_file_names[i], 105, -440),
            
        'SECTOR 2' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 160, -385)),
            
        'SECTOR 2_1' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 200, -345)),
                                              

        'SECTOR 3' : crash_during_lap_checker(lap_time, sector_1,
            row_with_text(cropped_file_names[i], 255, -285)),
            
            
        'SECTOR 3_1' : crash_during_lap_checker(lap_time, sector_1,
            last_mph_column_adjuster(row_with_text(cropped_file_names[i], 255, -285),
                                                standard_row(cropped_file_names[i], 295, -250))),
            
        'LAP TIME' : lap_time,
        'MPH' : string_equalizer(lap_count, mph)
        }
     
        build_df = pd.DataFrame(table)
        build_df.set_index("LAP No", inplace = True)
        dfs[name] = build_df
    return dfs

def thruxton(cropped_file_names):
    dfs = {}
    for i, name in enumerate(cropped_file_names):  
        lap_count = row_with_text(cropped_file_names[i], 20, -529)
        sector_1 = row_with_text(cropped_file_names[i], 45, -495)
        sector_1 = string_equalizer(lap_count, sector_1)

        lap_time = full_lap_time(cropped_file_names[i], 365, -168)
        lap_time = string_equalizer(lap_count, lap_time)

        mph = standard_row(cropped_file_names[i], 423, -120)


        table = {
        'LAP No' : row_with_text(cropped_file_names[i], 20, -529),
        'SECTOR 1' : sector_1,
        'SECTOR 1_1' : standard_row(cropped_file_names[i], 90, -460),

        'SECTOR 2' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 135, -410)),



        'SECTOR 2_1' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 165, -380)),

        'SECTOR 3' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 210, -330)),

        'SECTOR 3_1' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 250, -305)),

        'SECTOR 4' : crash_during_lap_checker(lap_time, sector_1,
            row_with_text(cropped_file_names[i], 290, -255)),


        'SECTOR 4_1' : crash_during_lap_checker(lap_time, sector_1,
            last_mph_column_adjuster(row_with_text(cropped_file_names[i], 290, -255),
                                                standard_row(cropped_file_names[i], 325, -225))),

        'LAP TIME' : lap_time,
        'MPH' : string_equalizer(lap_count, mph)
        }


        build_df = pd.DataFrame(table)
        build_df.set_index("LAP No", inplace = True)
        dfs[name] = build_df
    return dfs 

def cadewell(cropped_file_names):
    dfs = {}
    for i, name in enumerate(cropped_file_names):  
        lap_count = row_with_text(cropped_file_names[i], 20, -529)
        
        sector_1 = row_with_text(cropped_file_names[i], 55, -475)
        sector_1 = string_equalizer(lap_count, sector_1)
        
        lap_time = full_lap_time(cropped_file_names[i], 345, -193)
        lap_time = string_equalizer(lap_count, lap_time)
        
        mph = standard_row(cropped_file_names[i], 405, -143)
        
        
        table = {
        'LAP No' : row_with_text(cropped_file_names[i], 20, -529),
        'SECTOR 1' : sector_1,
        'SECTOR 1_1' : standard_row(cropped_file_names[i], 105, -440),
            
        'SECTOR 2' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 160, -385)),
                                              

        'SECTOR 3' : crash_during_lap_checker(lap_time, sector_1,
            row_with_text(cropped_file_names[i], 225, -285)),
            
            
        'SECTOR 3_1' : crash_during_lap_checker(lap_time, sector_1,
            last_mph_column_adjuster(row_with_text(cropped_file_names[i], 225, -285),
                                                standard_row(cropped_file_names[i], 295, -250))),
            
        'LAP TIME' : lap_time,
        'MPH' : string_equalizer(lap_count, mph)
        }
        
        
        build_df = pd.DataFrame(table)
        build_df.set_index("LAP No", inplace = True)
        dfs[name] = build_df
    return dfs

def navara(cropped_file_names):
    dfs = {}
    for i, name in enumerate(cropped_file_names):  
        lap_count = row_with_text(cropped_file_names[i], 20, -529)
        
        sector_1 = row_with_text(cropped_file_names[i], 55, -475)
        sector_1 = string_equalizer(lap_count, sector_1)
        
        lap_time = full_lap_time(cropped_file_names[i], 370, -169)
        lap_time = string_equalizer(lap_count, lap_time)
        
        mph = standard_row(cropped_file_names[i], 430, -120)
        
        
        table = {
        'LAP No' : row_with_text(cropped_file_names[i], 20, -529),
        'SECTOR 1' : sector_1,
            
        'SECTOR 2' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 150, -395)),
        
        
        'SECTOR 3' : crash_during_lap_checker(lap_time, sector_1,
            row_with_text(cropped_file_names[i], 235, -295)),

        'SPEED TRAP' : crash_during_lap_checker(lap_time, sector_1,
            standard_row(cropped_file_names[i], 315, -235)),

        'LAP TIME' : lap_time,
        'MPH' : string_equalizer(lap_count, mph)
        }
     
        build_df = pd.DataFrame(table)
        build_df.set_index("LAP No", inplace = True)
        dfs[name] = build_df
    return dfs