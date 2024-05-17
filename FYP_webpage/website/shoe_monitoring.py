from flask import Blueprint,request, render_template, flash,redirect, url_for
from flask_login import current_user
import cv2
from ultralytics import YOLO
import numpy as np
import easyocr
import string
import base64
from . import db
from .models import Shoe_stocks,Model,Brand


shoe_monitoring = Blueprint('shoe_monitoring', __name__)
reader = easyocr.Reader(['en'])

# OBJECT DETECTION MODEL
# Shoe Tag Detector
tag_model = YOLO("C:/Users/haoting/Desktop/FYP Project/FYP Model/FYP Shoe Tag Recognition/Final Shoe Tag Detection Model/runs/detect/train3/weights/best.pt")
# Shoe Row Detector
row_model = YOLO("C:/Users/haoting/Desktop/FYP Project/FYP Model/FYP Shoe Tag Recognition/FYP Shoe Row Detection Model/runs/detect/train/weights/best.pt")



# Function to capture frames from DroidCam
def capture_frame():
    droidcam_url = "http://192.168.0.163:4747/video"
    capture = cv2.VideoCapture(droidcam_url)
    
    # Check if the camera is opened successfully
    if not capture.isOpened():
        print("Error: Could not open camera")
        return None
    
    # Set capture properties for HD resolution (1280x720)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 2532)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 1170)

    # Read the frame
    ret, frame = capture.read()
    
    # Check if frame retrieval was successful
    if not ret:
        print("Error: Failed to retrieve frame from the camera")
        capture.release()  # Release the capture object
        return None
    
    capture.release()  # Release the capture object

    return frame



# Function to predict shoe tags using your shoe tag model
def predict_shoe_tags(frame):
    predicts_tag = tag_model(frame)[0]
    predicted_tags = []  # Placeholder for predicted tags
    for predict in predicts_tag:
        boxes = predict.boxes.cpu().numpy()
        probs = predict.probs
        names = predict.names
        tag_info = []  # Placeholder for tag information
        for i, box in enumerate(boxes.xyxy):
            # Extract coordinates and convert to (top, left, bottom, right) format
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
            
            # Store the tag information in a dictionary
            tag_info.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "score": probs,
                "class": names,
            })

        # Append tag information for this prediction to the main list
        predicted_tags.extend(tag_info)

    return predicted_tags

def remove_overlapping_rows(predicted_rows):
    # Iterate through the list of predicted rows
    i = 0
    while i < len(predicted_rows) - 1:
        # Get the y1 coordinates of adjacent objects
        current_y1 = predicted_rows[i]["y1"]
        next_y1 = predicted_rows[i + 1]["y1"]

        # Check if the next object's y1 is within a range of 5 from the current object's y1
        if abs(next_y1 - current_y1) <= 30:
            # Remove the second object if it's within the range
            predicted_rows.pop(i + 1)
        else:
            # Move to the next object if it's not within the range
            i += 1

    return predicted_rows

# Function to predict shoe rows using your shoe row model
def predict_shoe_rows(frame):
    predicts_row = row_model(frame)[0]
    predicted_rows = []  # Placeholder for predicted rows
    for predict in predicts_row:
        boxes = predict.boxes.cpu().numpy()
        probs = predict.probs
        names = predict.names
        
        row_info = []  # Placeholder for row information
        for i, box in enumerate(boxes.xyxy):
            # Extract coordinates and convert to (top, left, bottom, right) format
            x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
            
            # Store the row information in a dictionary
            row_info.append({
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "score": probs,
                "class": names,
            })

            # Append the rows to the main list
            predicted_rows.extend(row_info)

    if not predicted_rows:
        return predicted_rows
    
    # Sort all the rows based on the 'y1' coordinate
    predicted_rows.sort(key=lambda row: row["y1"])
    predicted_rows_without_overlap = remove_overlapping_rows(predicted_rows)
    # Assign sequences to the sorted rows
    for i, row in enumerate(predicted_rows_without_overlap):
        row['row'] = i + 1
    return predicted_rows_without_overlap

def assign_position(predicted_tags, predicted_rows):
    for tag in predicted_tags:
        tag_y1 = tag['y1']
        assigned_row = None

        # Iterate through the rows to find the closest row to the tag
        for i, row in enumerate(predicted_rows):
            row_y1 = row['y1']

            # Check if the tag's y1 is smaller than the row's y1
            if tag_y1 < row_y1:
                if i > 0:
                    assigned_row = predicted_rows[i - 1]['row']
                else:
                    assigned_row = row['row']
                break

        # If tag_y1 is larger than all rows, assign to the last row
        if assigned_row is None:
            assigned_row = predicted_rows[-1]['row']

        # Assign the tag to the closest row
        tag['assigned_row'] = assigned_row

    # Sort tags within each row based on x1 coordinates and assign item numbers
    for row in predicted_rows:
        row_tags = [tag for tag in predicted_tags if tag['assigned_row'] == row['row']]
        row_tags.sort(key=lambda x: x['x1'])

        # Assign item numbers to sorted tags within the row
        for i, tag in enumerate(row_tags, start=1):
            tag['item_number'] = i

    return predicted_tags, predicted_rows

def annotate_frame(frame, predicted_tags, predicted_rows):
    # Bounding box color
    tag_color = (0, 255, 0)  # Green color for tags
    row_color = (0, 0, 255)  # Red color for rows
    
    # Draw bounding boxes for predicted tags
    for tag in predicted_tags:
        x1, y1, x2, y2 = int(tag['x1']), int(tag['y1']), int(tag['x2']), int(tag['y2'])
        tag_serial = tag['detected_tags']
        
        # Draw the bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), tag_color, 2)
        
        # Annotate the assigned row
        cv2.putText(frame, f"Serial: {tag_serial}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tag_color, 2)
    
    # Draw bounding boxes for predicted rows
    for row in predicted_rows:
        x1, y1, x2, y2 = int(row['x1']), int(row['y1']), int(row['x2']), int(row['y2'])
        sequence = row['row']
        
        # Draw the bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), row_color, 2)
        
        # Annotate the sequence
        cv2.putText(frame, f"Row: {sequence}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, row_color, 2)
    
    return frame


# Mapping dictionaries for character conversion
dict_char_to_int = {'O': '0',
                    'Q': "0",
                    "o": "0",
                    "C": "0",
                    "d": "0",
                    "D": "0",
                    "p": "0",
                    "U": "0",
                    'I': '1',
                    "l": "1",
                    'J': '3',
                    'A': '4',
                    'G': '6',
                    "g": '6',
                    "b": "6",
                    "a": "8",
                    "<": "4",
                    'S': '5'}

dict_int_to_char = {'0': 'D',
                    "p": "D",
                    "k": "K",
                    "m": "M",
                    "d": "M",
                    '1': 'I',
                    '3': 'J',
                    '4': 'A',
                    '6': 'G',
                    'b': 'B',
                    'E': 'B',
                    "8": "B",
                    "V": "N",
                    "O": "D",
                    "C": "D",
                    '5': 'S'}

def tag_complies_format(text):
        
    if len(text) != 13 or (text[5] != '-' and text[5] != '.') or (text[8] != '-' and text[8] != '.'):
        return False # Check length
    if (text[0] in dict_int_to_char.keys() or text[0] in string.ascii_uppercase) and \
        (text[1] in dict_int_to_char.keys() or text[1] in string.ascii_uppercase) and \
        (text[2] in dict_char_to_int.keys() or text[2] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[3] in dict_char_to_int.keys() or text[3] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[4] in dict_char_to_int.keys() or text[4] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[6] in dict_char_to_int.keys() or text[6] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[7] in dict_char_to_int.keys() or text[7] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[9] in dict_char_to_int.keys() or text[9] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[10] in dict_char_to_int.keys() or text[10] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[11] in dict_char_to_int.keys() or text[11] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']) and \
        (text[12] in dict_char_to_int.keys() or text[12] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']):       
            return True
    else:
        return False



def format_tag(text):

    serial_number = ''
    mapping = {
        0: dict_int_to_char,  # N
        1: dict_int_to_char,  # K
        2: dict_char_to_int,  # 0
        3: dict_char_to_int,  # 0
        4: dict_char_to_int,  # 7
        5: '-',  # Keep the '-' delimiter unchanged
        6: dict_char_to_int,  # 0
        7: dict_char_to_int,  # 9
        8: '-',  # Keep the '-' delimiter unchanged
        9: dict_char_to_int,  # 0
        10: dict_char_to_int,   # 0
        11: dict_char_to_int,  # 0
        12: dict_char_to_int   # 0
    }
    for idx, char in enumerate(text):
        if idx in mapping:
            if mapping[idx] == '-':
                serial_number += '-'
            else:
                if char in mapping[idx]:
                    serial_number += mapping[idx][char]
                else:
                    serial_number += char
        else:
            serial_number += char

    return serial_number




def process_predicted_tags(predicted_tags):
    split_tags =[]
    if all(tag['detected_tags'] != '-' for tag in predicted_tags):

        Shoe_stocks.query.delete()
        db.session.commit()
        # Save new data to the database
        for tag in predicted_tags:
            tagsComponents = tag['detected_tags'].split('-')

            if len(tagsComponents) == 3:  # Ensure it has three components
                tag['brand'] = tagsComponents[0][:2]  # Extract the first 2 characters
                tag['model'] = tagsComponents[0][2:]  # Extract the rest as the model
                tag['size'] = tagsComponents[1]
                tag['shoe_number'] = tagsComponents[2]
            else:
                # Handle cases where the split result doesn't have three components
                tag['brand'] = ''
                tag['model'] = ''
                tag['size'] = ''
                tag['shoe_number'] = ''

            new_tag = Shoe_stocks(
                x1=tag['x1'],
                y1=tag['y1'],
                x2=tag['x2'],
                y2=tag['y2'],
                item_number=tag['item_number'],
                row=tag['assigned_row'],
                brand=tag['brand'],
                model=tag['model'],
                size=tag['size'],
                shoe_number=tag['shoe_number']
            )

            split_tags.append({
                'x1': tag['x1'],
                'y1': tag['y1'],
                'x2': tag['x2'],
                'y2': tag['y2'],
                'item_number': tag['item_number'],
                'row': tag['assigned_row'],
                'brand': tag['brand'],
                'model': tag['model'],
                'size': tag['size'],
                'shoe_number': tag['shoe_number']
            })
            db.session.add(new_tag)

        db.session.commit()
        flash('Database Updated', category='success')
        return predicted_tags, split_tags
    else:
        flash('NOT ALL TAGS DETECTED, CAMERA RECAPTURING IN 5 SECONDS', category='error')
        return predicted_tags, split_tags
        

def translation(split_tags):
    brand_mapping = {
        'NK': 'Nike',
        'AD': 'Adidas',
        'PM': 'Puma',
        'NB': 'New Balance',
        'RB': 'Reebok'
        # Add other mappings as needed
    }

    size_dict = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 2.5,
    5: 3.0,
    6: 3.5,
    7: 4.0,
    8: 4.5,
    9: 5.0,
    10: 5.5,
    11: 6.0,
    12: 6.5,
    13: 7.0,
    14: 7.5,
    15: 8.0,
    16: 8.5,
    17: 9.0,
    18: 9.5,
    19: 10.0,
    20: 10.5,
    21: 11.0,
    22: 11.5,
    23: 12.0
    }

    if not split_tags:
        return split_tags
    else:
        for tag in split_tags:
            if tag['brand'] in brand_mapping:
                brand_name = brand_mapping[tag['brand']]
                tag['brand'] = brand_name
                brand =Brand.query.filter_by(brand=brand_name).first()
                brand_id = brand.id 

                if brand_id:
                    model = Model.query.filter_by(model_number=tag['model'], brand_id=brand_id).first()
                    if model:
                        tag['model'] = model.model_name  # Replace 'model_name' with your model's name attribute
                        # Translate size
                        size = float(tag['size'])
                        if size in size_dict:
                            tag['size'] = size_dict[size]
        return split_tags

                        
                


# Routes for shoe monitoring functionality
@shoe_monitoring.route('/monitor',methods=['GET', 'POST'])
def monitor():
    if request.method == 'GET':
        while True:
            frame = capture_frame()
            # frame = cv2.imread('C:/Users/haoting/Downloads/tempoimage.jpg')
            if frame is not None:
                # Predict shoe tags and shoe rows
                predicted_tags = predict_shoe_tags(frame)
                predicted_rows = predict_shoe_rows(frame)
                if not predicted_tags:
                    flash('NO TAGS ARE DETECTED, MAKE SURE CAMERA IS OPENED AND POINTED AT SHOE', category='error')
                    return redirect(url_for('auth.home'))
                
                if not predicted_rows:
                    flash('NO ROWS ARE DETECTED, MAKE SURE CAMERA IS OPENED AND POINTED AT SHOE', category='error')
                    return redirect(url_for('auth.home'))
                predicted_tags, predicted_rows = assign_position(predicted_tags, predicted_rows)

                for tag in predicted_tags:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = int(tag['x1']), int(tag['y1']), int(tag['x2']), int(tag['y2'])
                    
                    # Crop the bounding box from the frame
                    cropped_tag = frame[y1:y2, x1:x2].copy()

                    gray = cv2.cvtColor(cropped_tag, cv2.COLOR_BGR2GRAY)

                    # Threshold to extract the black words
                    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

                    # Find contours
                    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                    if not contours:
                        flash('NO CHARACTERS WERE FOUND ON TAGS PLEASE MAKE SURE ONLY VALID TAGS ARE USED', category='error')
                        return redirect(url_for('auth.home'))
                    # Create a white frame to paste the black words on
                    white_frame = np.ones((cropped_tag.shape[0], cropped_tag.shape[1]), dtype=np.uint8) * 255

                    # Paste the black words onto the white frame
                    for contour in contours:
                        x, y, w, h = cv2.boundingRect(contour)
                        word = cv2.cvtColor(cropped_tag[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)  # Convert to grayscale
                        white_frame[y:y+h, x:x+w] = word


                    tag_serial_number = reader.readtext(white_frame,  text_threshold =0.7) 
                    if not tag_serial_number:
                        flash('SOME TAGS ARE NOT VALID OR EMPTY PLEASE CHECK', category='error')
                        return redirect(url_for('auth.home'))
                    for tag_detection in tag_serial_number:
                        bbox, text, score = tag_detection
                        if tag_complies_format(text):
                            formatted_tag = format_tag(text)
                        else:
                            formatted_tag ="-"
                    
                    # Assign the detected tag info to the predicted_tags
                    tag['detected_tags'] = formatted_tag 

                predicted_tags, split_tags = process_predicted_tags(predicted_tags)  

                translated_tags = translation(split_tags)

                # Annotate the frame with bounding boxes and assigned rows
                annotated_frame = annotate_frame(frame.copy(), predicted_tags, predicted_rows)
                cv2.imwrite('annotated_frame.jpg', annotated_frame)

                # Read the saved image file
                with open('annotated_frame.jpg', 'rb') as img_file:
                    image_data = img_file.read()
                    encoded_image = base64.b64encode(image_data).decode('utf-8')


                return render_template("monitor.html", image=encoded_image, translated_tags=translated_tags, user=current_user)
                # return render_template("monitor.html", predicted_tags=predicted_tags, user=current_user)
                 
            else:
                flash('CAMERA WAS NOT OPENED', category='ERROR')
                return render_template("home.html", user=current_user)

    


        