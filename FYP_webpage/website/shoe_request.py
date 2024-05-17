from flask import Blueprint, jsonify, request, render_template, flash, redirect, url_for
from flask_login import current_user,login_required
from . import db
from .models import Request,Model,Brand,Shoe_stocks
import pickle
from collections import defaultdict
from datetime import datetime
import cv2
import base64
shoe_request = Blueprint('shoe_request', __name__)

with open('C:/Users/haoting/Desktop/FYP Project/FYP Model/FYP SHOE SIZE PREDICTION/model_male.pkl', 'rb') as file_male:
    male_model = pickle.load(file_male)

with open('C:/Users/haoting/Desktop/FYP Project/FYP Model/FYP SHOE SIZE PREDICTION/model_female.pkl', 'rb') as file_female:
    female_model = pickle.load(file_female)

# Size charts for different brands (as dictionaries)
adidas_sizes = {
        3.5: 22.1, 4: 22.5, 4.5: 22.9, 5: 23.3, 5.5: 23.8,6: 24.2, 6.5: 24.6, 7: 25.0, 7.5: 25.5, 8: 25.9, 8.5: 26.3, 9: 26.7, 9.5: 27.1, 10: 27.6, 10.5: 28.0, 11: 28.4, 11.5: 28.8, 12: 29.3
}

nike_sizes = {
       3: 21.5, 3.5: 22, 4: 22.5, 4.5: 23, 5: 23.5, 5.5: 24,6: 24.5, 6.5: 25.0, 7: 25.4, 7.5: 25.8, 8: 26.2, 8.5: 26.7, 9: 27.1, 9.5: 27.5, 10: 27.9, 10.5: 28.3, 11: 28.8, 11.5: 29.2, 12: 29.6
}

puma_sizes = {
        3: 22, 3.5: 22.5, 4: 23, 4.5: 23.5, 5: 24, 5.5: 24.5, 6: 25.0, 6.5: 25.5, 7: 26.0, 7.5: 26.5, 8: 27.0, 8.5: 27.5, 9: 28.0, 9.5: 28.5, 10: 29.0, 10.5: 29.5, 11: 30.0, 11.5: 30.5, 12: 31.0
}

reebok_sizes = {
        1: 21.0, 1.5: 21.5, 2: 22.0, 2.5: 22.5, 3: 23.0, 3.5: 23.3, 4: 23.5, 4.5: 23.6, 5: 24.0, 5.5: 24.5,6: 25, 6.5: 25.5, 7: 26.0, 7.5: 26.5, 8: 27, 8.5: 27.5, 9: 28, 9.5: 28.5, 10: 29, 10.5: 29.5, 11: 30, 11.5: 30.5, 12: 31
}

new_balance_sizes = {
        2: 20.0, 2.5: 20.5, 3: 21.0, 3.5: 21.5, 4: 22.0, 4.5: 22.5, 5: 23.0, 5.5: 23.5, 6: 24, 6.5: 24.5, 7: 25, 7.5: 25.5, 8: 26, 8.5: 26.5, 9: 27, 9.5: 27.5, 10: 28, 10.5: 28.5, 11: 29, 11.5: 29.5, 12: 30
}



def predict_foot_length(height, gender):
    if gender == "male":
        predicted_foot_length = male_model.predict([[height]])  # Use the 'model_male' for male predictions
    else:
        predicted_foot_length = female_model.predict([[height]]) # Use the 'model_female' for female predictions
    return predicted_foot_length[0]  # Return the predicted foot length

# Function to get the size chart based on the brand
def get_size_chart(brand):
    if brand == "Nike":
        return nike_sizes
    elif brand == "Adidas":
        return adidas_sizes
    elif brand == "Reebok":
        return reebok_sizes
    elif brand == "Puma":
        return puma_sizes
    elif brand == "New Balance":
        return new_balance_sizes
    # Add other brand and gender conditions as needed


def predict_brand_size(height,gender,brand):
    predicted_length = predict_foot_length(height, gender)
    selected_size_chart = get_size_chart(brand)
    # Find the nearest size in the selected size chart
    nearest_size = min(selected_size_chart, key=lambda x: abs(selected_size_chart[x] - predicted_length))

    return nearest_size

def get_unique_brands_with_ids():
    # Retrieve unique acronyms from Shoe_stocks table
    unique_acronyms = Shoe_stocks.query.with_entities(Shoe_stocks.brand).distinct().all()

    # Mapping of acronyms to their respective full brand names
    brand_mapping = {
        'NK': 'Nike',
        'AD': 'Adidas',
        'PM': 'Puma',
        'NB': 'New Balance',
        'RB': 'Reebok'
        # Add other mappings as needed
    }

    # Reverse mapping of full brand names to their IDs from the Brand table
    brand_id_mapping = {brand.brand: brand.id for brand in Brand.query.all()}

    # Collect unique brand IDs based on acronyms
    unique_brands_with_ids = defaultdict(list)
    for acronym, in unique_acronyms:
        full_brand_name = brand_mapping.get(acronym)
        if full_brand_name:
            brand_id = brand_id_mapping.get(full_brand_name)
            if brand_id:
                unique_brands_with_ids[full_brand_name].append(brand_id)

    return dict(unique_brands_with_ids)

# Sample route to display pending requests
@shoe_request.route('/pending-requests')
def display_pending_requests():
    pending_requests = Request.query.filter_by(status='PENDING').all()
    for request in pending_requests:
        # Convert the long binary image data to Base64 for display
        if request.image_data:
            request.image_base64 = base64.b64encode(request.image_data).decode('utf-8')

            # Calculate the time difference in minutes
            request_time = request.date  # Replace this with your request's datetime attribute
            current_time = datetime.now()
            time_difference = (current_time - request_time).total_seconds() / 60
            request.time_difference = int(time_difference)

            brand = Brand.query.filter_by(id=request.brand_id).first()
            model = Model.query.filter_by(id=request.model_id).first()
            request.brand_name = brand.brand
            request.model_name = model.model_name
            
            
        else:
            request.image_base64 = None  # Handle the case where image_data is empty

    return render_template('accept_request.html', requests=pending_requests, user=current_user)

size_dict = {
    1.0: 1,
    1.5: 2,
    2.0: 3,
    2.5: 4,
    3.0: 5,
    3.5: 6,
    4.0: 7,
    4.5: 8,
    5.0: 9,
    5.5: 10,
    6.0: 11,
    6.5: 12,
    7.0: 13,
    7.5: 14,
    8.0: 15,
    8.5: 16,
    9.0: 17,
    9.5: 18,
    10.0: 19,
    10.5: 20,
    11.0: 21,
    11.5: 22,
    12.0: 23
}


def annotate_frame(frame, predicted_tags):
    # Bounding box color
    tag_color = (0, 255, 0)  # Green color for tags
    
    # Draw bounding boxes for predicted tags
    for tag in predicted_tags:
        x1, y1, x2, y2 = int(tag['x1']), int(tag['y1']), int(tag['x2']), int(tag['y2'])
        assigned_row = tag['row']
        item_number = tag['item_number']
        
        # Draw the bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), tag_color, 2)
        
        # Annotate the assigned row
        cv2.putText(frame, f"Row: {assigned_row}, Item: {item_number}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, tag_color, 2)
    
    return frame

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

# Route to handle accepting a request
@shoe_request.route('/accept-request', methods=['POST'])
def accept_request():
    request_id = request.form['request_id']
    # Fetch the request by ID and update its status to 'accepted' in the database
    customer_request = Request.query.get(request_id)

    brand_id =customer_request.brand_id
    model_id= customer_request.model_id
    size = customer_request.size
    brand_name =Brand.query.get(brand_id).brand
    request_brand= translation_dict.get(brand_name)
    request_model= Model.query.get(model_id).model_number
    request_size= size_dict[size]

    shoe_stocks_results = Shoe_stocks.query.filter_by(
        brand=request_brand,
        model=request_model,
        size=request_size
    ).all()

    # Create a list to store the results
    results_list = []

    # Retrieve specific columns for each row of data retrieved and store in the list
    for result in shoe_stocks_results:
        x1 = result.x1
        y1 = result.y1
        x2 = result.x2
        y2 = result.y2
        item_number = result.item_number
        row = result.row

        # Create a dictionary for each row and append it to the list
        row_dict = {
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
            'item_number': item_number,
            'row': row
        }
        results_list.append(row_dict)

    if not results_list:  
        flash('THE REQUESTED SHOE IS OUT OF STOCK! PLEASE REJECT REQUEST', category='error')
        return redirect(url_for('shoe_request.display_pending_requests'))
    else:
        frame = capture_frame()
        # frame = cv2.imread('C:/Users/haoting/Downloads/tempoimage.jpg')
        if frame is not None:
            annotated_frame = annotate_frame(frame, results_list)
            cv2.imwrite('requested_shoe.jpg', annotated_frame)
            
            # Read the saved image file
            with open('requested_shoe.jpg', 'rb') as img_file:
                image_data = img_file.read()
                encoded_image = base64.b64encode(image_data).decode('utf-8')
            
            customer_request.status = 'ACCEPTED'
            db.session.commit()

            flash('REQUEST ACCEPTED! THIS IS THE POSITION OF REQUESTED SHOE', category='success')
            return render_template('requested_shoe.html',image=encoded_image, results_list=results_list, user = current_user)
        else:
            flash('CAMERA WAS NOT OPENED! OPEN CAMERA BEFORE ACCEPTING REQUEST', category='ERROR')
            return redirect(url_for('shoe_request.display_pending_requests'))
        


@shoe_request.route('/reject-request', methods=['POST'])
def reject_request():
    request_id = request.form['request_id']
    # Fetch the request by ID and update its status to 'accepted' in the database
    customer_request = Request.query.get(request_id)
    customer_request.status = 'REJECTED'
    db.session.commit()
    flash('REQUEST REJECTED SUCCESSFULLY!!', category='success')
    return redirect(url_for('shoe_request.display_pending_requests'))
    

###  CUSTOMER PART 


translation_dict = {
    'Nike': 'NK',
    'Adidas': 'AD',
    'Puma': 'PM',
    'New Balance': 'NB',
    'Reebok': 'RB'
}

@shoe_request.route('/request_models/<brand_id>')
def get_models(brand_id):
    models = Model.query.filter_by(brand_id=brand_id).all()
    brand = Brand.query.get(brand_id).brand
    acronym = translation_dict.get(brand)
    shoe_stocks = Shoe_stocks.query.filter(Shoe_stocks.brand == acronym).all()
    model_numbers = [stock.model for stock in shoe_stocks]

    matching_model_ids = []
    for model in models:
        if model.model_number in model_numbers:
            matching_model_ids.append({'id': model.id, 'name': model.model_name})

    return jsonify({'matching_model_ids': matching_model_ids})


@shoe_request.route('/cushome', methods=['GET', 'POST'])
@login_required
def cushome():
    if request.method == 'GET':
        with open('nikelogo.JPG', 'rb') as img_file:
            image_data = img_file.read()
            nike = base64.b64encode(image_data).decode('utf-8')
        with open('adidaslogo.png', 'rb') as img_file:
            image_data = img_file.read()
            adidas = base64.b64encode(image_data).decode('utf-8')
        
        with open('pumalogo.jpg', 'rb') as img_file:
            image_data = img_file.read()
            puma = base64.b64encode(image_data).decode('utf-8')
        
        with open('nblogo.png', 'rb') as img_file:
            image_data = img_file.read()
            nb = base64.b64encode(image_data).decode('utf-8')
        
        with open('reebok.JPG', 'rb') as img_file:
            image_data = img_file.read()
            reebok = base64.b64encode(image_data).decode('utf-8')

        return  render_template('cushome.html', nike = nike, adidas = adidas, puma = puma, nb = nb, reebok=reebok, user = current_user) 
    elif request.method == 'POST':
        brand_name = request.form.get('brand')
        if brand_name:
            unique_brands_with_ids = get_unique_brands_with_ids()
            check_brand = unique_brands_with_ids.get(brand_name)
            if check_brand :
               selected_brand = {brand_name: check_brand}
               return render_template('send_request.html', brands= selected_brand,  user=current_user)
            else:
                flash('THERE ARE NO AVAILABLE SHOE FOR THIS BRAND CURRENTLY, PLEASE PICK ANOTHER BRAND', category='error')
                return redirect(url_for('shoe_request.cushome'))


    
    
@shoe_request.route('/send-request', methods=['GET','POST'])
def send_request():
    if request.method == 'GET':
        unique_brands_with_ids = get_unique_brands_with_ids()
        return render_template('send_request.html', brands=unique_brands_with_ids, user= current_user)  
    
    elif request.method == 'POST':
        brand_id= request.form.get('brand')
        model_id = request.form.get('model')
        gender = request.form.get('gender')
        height = float(request.form.get('height'))  # Convert to float if getting height from a form
        img_data = request.form['capturedImageData']



        # Check if all fields are filled
        if brand_id and model_id and gender and height and img_data:
            binary_data = base64.b64decode(img_data.split(',')[1])
            brand = Brand.query.get(brand_id)
            brand_name = brand.brand
            
            nearest_size = predict_brand_size(height,gender,brand_name)
            new_request = Request(brand_id=brand_id, model_id = model_id,user_id = current_user.id , gender = gender, 
                                  size = nearest_size, date = datetime.now() , image_data= binary_data, status ="PENDING" )
            db.session.add(new_request)
            db.session.commit()
            flash('Request Sent! Please hold on for your desire shoes', category='success')
            return redirect(url_for('shoe_request.cushome'))

        else:
            unique_brands_with_ids = get_unique_brands_with_ids()
            # If any field is missing, render the form again with an error message
            flash('Please fill in all the field and take a picture of current location to send request', category='error')
            return render_template('send_request.html',brands = unique_brands_with_ids,  user = current_user)
        


