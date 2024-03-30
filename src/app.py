from libs import *
from text_extract import Invoice_text_extraction

class Invoice(db.Model):
    __tablename__='spending_analysis'
    Id = db.Column(db.Integer, primary_key=True)
    Merchant = db.Column(db.String(100))
    Date = db.Column(db.Date)
    Total = db.Column(db.Float)


@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
def home():
    try:
        if request.method == 'POST':
            return redirect(url_for('upload'))
        else:
            message = 'Welcome to Your Spending Analysis Page'
            return render_template("layout.html", message=message)
    except Exception as e:
        logger.error(f"Error in home: {e}")
        flash('An error occurred. Please try again.', 'error')
        return render_template('layout.html')
    
def process_uploaded_image(file):
    try:
        text_extraction = Invoice_text_extraction()
        extracted_text = text_extraction.deskew_image(file)  
        return extracted_text
    except Exception as e:
        logger.error(f"Error in process_uploaded_image: {e}")
        return None

UPLOAD_FOLDER = os.path.join(app.root_path, 'temp')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    try:
        if request.method == 'POST':
            files = request.files.getlist('file')
            if not files or all(file.filename == '' for file in files):
                flash('No files selected','upload_error')
                return render_template('layout.html')
            else:
                files_added=0
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        filepath = os.path.join(UPLOAD_FOLDER, filename)
                        file.save(filepath)
                        extracted_text = process_uploaded_image(filepath)
                        os.remove(filepath)
                        if extracted_text:
                            new_record = Invoice(**extracted_text)
                            db.session.add(new_record)
                            files_added += 1
                if files_added > 0:
                    if files_added == 1:
                        flash('File added successfully', 'upload_success')
                    else:
                        flash('Files added successfully', 'upload_success')    
                else:
                    flash('Failed to add the file', 'upload_error')
                db.session.commit()
                return redirect(url_for('upload'))
        return render_template('layout.html')
    except Exception as e:
        logger.error(f"Error in upload: {e}")
        flash('An error occurred. Please try again.', 'error')
        return render_template('layout.html')

def chart_type(data,chart,purchase=None):
    try:
        if 'pie' in chart.lower():
            pie_chart_html = create_pie_chart(data,purchase)
            flash('Pie Chart generated successfully', 'success')
            return pie_chart_html
        elif 'bar' in chart.lower():
            bar_chart_html = create_bar_chart(data,purchase)
            flash('Bar Chart generated successfully', 'success')
            return bar_chart_html
        else:
            line_chart_html = create_line_chart(data,purchase)
            flash('Line Chart generated successfully', 'success')
            return line_chart_html
    except Exception as e:
        logger.error(f"Error in chart_type: {e}")
        flash('An error occurred while generating the chart.', 'error')
        return None

@app.route('/get_chart_data', methods=['GET', 'POST'])
def get_chart_data():
    try:
        if request.method == 'POST':
            record_option = request.form.get('Record', '')
            chart = request.form.get('Chart', '')
            from_date = request.form.get('from_date', '')
            to_date = request.form.get('to_date', '')

            # Validate mandatory fields
            if not chart:
                flash('Please Select Mandatory Chart Field', 'error')
                return render_template('layout.html')

            # Handle record option
            elif record_option:
                data = fetch_data_from_database(record_option)
                if record_option == 'Total Spendings':
                    chart_html = chart_type(data,chart,record_option)
                else:
                    chart_html = chart_type(data,chart)
                return render_template('layout.html', visual_chart=chart_html)

            # Handle date range
            elif from_date and to_date:
                option = [from_date, to_date]
                data = fetch_data_from_database(option)
                chart_html = chart_type(data, chart)
                return render_template('layout.html', visual_chart=chart_html)

            # Handle missing date range
            else:
                flash('Please Input The Necessary Fields', 'error')
                return render_template('layout.html')

        else:
            flash('Please Input The Necessary Fields', 'error')
            return render_template('layout.html')

    except Exception as e:
        logger.error(f"Error in get_chart_data: {e}")
        flash('An error occurred. Please try again.', 'error')
        return render_template('layout.html')

# Create Plotly pie chart
def create_pie_chart(data,purchase=None):
    try:
        merchants = list(data.keys())
        total_spend = list(data.values())
        data = [go.Pie(labels=merchants, values=total_spend)]
        if purchase == 'Total Spendings':
            layout = go.Layout(title='Spendings Distribution by each month')
        else:
            layout = go.Layout(title='Spendings Distribution at each Merchant')
        fig = go.Figure(data=data, layout=layout)
        html_div = offline.plot(fig, output_type='div')
        return html_div
    except Exception as e:
        logger.error(f"Error in pie_chart: {e}")
        return None

# Create Plotly bar chart
def create_bar_chart(data,purchase=None):
    try:
        merchants = list(data.keys())
        total_spend = list(data.values())
        data = [go.Bar(x=merchants, y=total_spend)]
        if purchase == 'Total Spendings':
            layout = go.Layout(title='Spendings Distribution by each month', xaxis=dict(title='Month'), yaxis=dict(title='Total Spendings($)'))
        else:
            layout = go.Layout(title='Spendings Distribution at each Merchant', xaxis=dict(title='Merchant'), yaxis=dict(title='Total Spendings($)'))
        fig = go.Figure(data=data, layout=layout)
        html_div = offline.plot(fig, output_type='div')
        return html_div
    except Exception as e:
        logger.error(f"Error in bar_chart: {e}")
        return None

# Create Plotly line chart
def create_line_chart(data,purchase=None):
    try:
        merchants = list(data.keys())
        total_spend = list(data.values())
        data = [go.Scatter(x=merchants, y=total_spend, mode='lines')]
        if purchase == 'Total Spendings':
            layout = go.Layout(title='Spendings Distribution by each month', xaxis=dict(title='Month'), yaxis=dict(title='Total Spendings($)'))
        else:
            layout = go.Layout(title='Spendings Distribution at each Merchant', xaxis=dict(title='Merchant'), yaxis=dict(title='Total Spendings($)'))
        fig = go.Figure(data=data, layout=layout)
        html_div = offline.plot(fig, output_type='div')
        return html_div
    except Exception as e:
        logger.error(f"Error in line_chart: {e}")
        return None

def fetch_data_from_database(option):
    try:
        results=''
        total_spent_result=''
        if option == 'Latest Record':
            result = db.session.query(Invoice.Merchant,Invoice.Total).order_by(Invoice.Id.desc()).first()
            logger.info(result)
            return {result.Merchant:result.Total}
        elif option == 'Current Month':
            results = db.session.query(Invoice.Merchant,func.sum(Invoice.Total).label('total_sum')).filter(
                extract('month', Invoice.Date) == extract('month', func.current_date())).group_by(Invoice.Merchant)
        elif option == 'Current Year':
            results = db.session.query(Invoice.Merchant,func.sum(Invoice.Total).label('total_sum')).filter(
                extract('year',Invoice.Date) == extract('year',func.current_date())).group_by(Invoice.Merchant)
        elif option == 'Total Spendings':
            total_spent_result = db.session.query(extract('month', Invoice.Date).label('month'),extract('year', Invoice.Date).label('year'),
                                    func.sum(Invoice.Total).label('total_sum')).group_by('month', 'year').order_by('year', 'month').all()
        elif isinstance(option, list):
            start_date = option[0]
            end_date = option[1]
            results = db.session.query(Invoice.Merchant, func.round(func.sum(Invoice.Total),2).label('total_spend')).filter(
                Invoice.Date >= start_date, Invoice.Date <= end_date ).group_by(Invoice.Merchant)
        else:
            pass
        labels = []
        values = []
        if results:
            for row in results:
                labels.append(row[0])
                values.append(round(row[1],2))
            data_dict=dict(zip(labels,values))
        elif total_spent_result:
            for rec in total_spent_result:
                month_str = datetime(rec.year, rec.month, 1).strftime('%b')
                month_year = f"{month_str},{rec.year}"
                labels.append(month_year)
                values.append(round(rec.total_sum,2))
            data_dict=dict(zip(labels,values))
        else:
            data_dict={}
        logger.info(data_dict)
        return data_dict
    except Exception as e:
        logger.error(f"Error in fetch_data_from_database: {e}")
        return {}
    
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5000)
