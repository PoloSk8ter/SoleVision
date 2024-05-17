from flask import Blueprint, jsonify, request, render_template, flash,send_file, redirect, url_for
from flask_login import current_user
from . import db
from .models import Model,Brand,Stock_in_Record
from datetime import datetime
from docx import Document
from docx.shared import Pt, Cm
from sqlalchemy import func
from io import BytesIO

stock_in = Blueprint('stock_in', __name__)

def create_word_document(data):
    doc = Document()
    # Apply font and size to the entire document
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Tahoma'
    font.size = Pt(48)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_before = Pt(12)
    # Add a table with one column and insert each data item into a new row
    table = doc.add_table(rows=0, cols=1)
    for item in data:
        row = table.add_row().cells
        row[0].text = item
        # Set the width of the cell to 11.7cm
        row[0].width = Cm(12.3)

    # Apply gridlines to the table
    table.style = 'Table Grid'
     # Save the document to a BytesIO object
    in_memory_file = BytesIO()
    doc.save(in_memory_file)
    in_memory_file.seek(0)
    # Return the file for download using send_file
    return  in_memory_file


brand_dict = {
    'Nike': 'NK',
    'Adidas': 'AD',
    'Puma': 'PM',
    'New Balance': 'NB',
    'Reebok': 'RB'
}
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

@stock_in.route('/download', methods=['POST'])
def download():
    serial_numbers = request.form.get('serial_number')  # Get the serial numbers from the form
    serial_numbers_list = list(filter(None, serial_numbers.split(',')))

    file_path = create_word_document(serial_numbers_list)

    return send_file(
        file_path,
        as_attachment=True,
        download_name='New Stock In Tags.docx',
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    
@stock_in.route('/stock_in',methods=['GET', 'POST'])
def stocks_in():
    if request.method == 'GET':
        brands = Brand.query.all()  # Retrieve all brands from the Brand class/table
        records = Stock_in_Record.query.all()
        for record in records:
            brand = Brand.query.filter_by(id=record.brand_id).first()
            model = Model.query.filter_by(id=record.model_id).first()
            record.brand_name = brand.brand
            record.model_name = model.model_name
            record.month = record.date.strftime('%b')

        return render_template('stock_in.html', records= records, brands=brands, user= current_user) 
    
    elif request.method == 'POST':
        brand_id = request.form.get('brand')
        model_id = request.form.get('model')
        size = float(request.form.get('size')) 

        quantity = int(request.form.get('quantity'))
        if brand_id and model_id and quantity and size:
            brand = Brand.query.filter_by(id=brand_id).first()
            model = Model.query.filter_by(id=model_id).first()
            brand_name = brand.brand
            model_number = f"{model.model_number:03d}"
            # Map brand_name and size to their respective codes
            if size in size_dict:
                size_code = size_dict.get(size)

                # Check if brand_name exists in the brand_dict
                brand_code = brand_dict.get(brand_name)
                if brand_code:
                    total_quantity = Stock_in_Record.query.filter_by(
                        brand_id=brand_id,
                        model_id=model_id,
                        size = size,
                    ).with_entities(func.sum(Stock_in_Record.amount)).scalar()
                    if total_quantity is not None:
                        initial_quantity = total_quantity

                    else:
                        initial_quantity = 0

                    serial_number = []
                    for i in range(quantity):
                        incremented_quantity = initial_quantity + i + 1
                                    # Formatting the strings as required
                        formatted_size_code = f"{size_code:02d}"
                        formatted_incremented_quantity = f"{incremented_quantity:04d}"
                        
                        # Concatenating the strings
                        serial = f"{brand_code}{model_number}-{formatted_size_code}-{formatted_incremented_quantity}"
                        
                        # Append to the list
                        serial_number.append(serial)
                      
                    new_stock = Stock_in_Record(brand_id = brand_id, model_id = model_id, size= size, amount = quantity, date = datetime.now() )
                    db.session.add(new_stock)
                    db.session.commit()
                    brands = Brand.query.all() 
                    flash('Stock In successfully! PLEASE DOWNLOAD SHOE TAGS FOR STOCK IN PRODUCTS', category='success')
                    return render_template('shoetag_doc.html', user= current_user, serial_number = serial_number) 
        else:
            brands = Brand.query.all()  # Retrieve all brands from the Brand class/table
            flash('Please fill in all the information of stocks', category='error')
            return redirect(url_for('stock_in.stocks_in'))



@stock_in.route('/get_models/<brand_id>')
def get_models(brand_id):
    models = Model.query.filter_by(brand_id=brand_id).all()
    model_list = [{'id': model.id, 'name': model.model_name} for model in models]
    return jsonify(model_list)


@stock_in.route('/get_brands', methods=['GET'])
def get_brands():
    brands = Brand.query.all()
    brand_list = [{'id': brand.id, 'brand': brand.brand} for brand in brands]
    return jsonify(brand_list)

@stock_in.route('/register_model', methods = ['GET','POST'])
def register_model():

    models =Model.query.all()
    for model in models:
        brand = Brand.query.filter_by(id=model.brand_id).first()
        model.brand_name =brand.brand
    
    if request.method =='POST':
        brand_id = request.form.get('brandSelect')
        model_name = request.form.get('modelName')

        if brand_id and model_name:

            # Check if the model already exists for the selected brand
            existing_model = Model.query.filter_by(brand_id=brand_id, model_name=model_name).first()
            if existing_model:
                flash('Model already exists for this brand!', category='error')

            else:
                count_models = Model.query.filter_by(brand_id=brand_id).count()
                model_number = count_models + 1  # Increment count by 1 for the new model

                # Create and save the new model
                new_model = Model(model_name=model_name, brand_id=brand_id, model_number=model_number)
                db.session.add(new_model)
                db.session.commit()
                flash('Model registered successfully!', category='success')
                return redirect(url_for('stock_in.register_model'))


    return render_template('register_model.html', models= models, user = current_user)
