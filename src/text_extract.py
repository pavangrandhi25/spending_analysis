from libs import *

def download_stopwords():
    try:
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('stopwords')
        except Exception as e:
            logger.error(f"Error downloading stopwords: {e}")
            
download_stopwords()

stop_words = set(stopwords.words('english'))

class Invoice_text_extraction:
    
    def __init__(self):
        pass

    def deskew_image(self,image_path):
        try:
            image = cv2.imread(image_path)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 30, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
            angles = [line[0][1] for line in lines]
            mean_angle = np.mean(angles)
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, mean_angle, 1.0)
            rotated_image = cv2.warpAffine(image, rotation_matrix, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            
            data_to_db=self.text_extraction(rotated_image)       
            
            return data_to_db   
        except Exception as e:
            logger.error(f"Error in deskew_image: {e}")
            return None
             
    def text_extraction(self,image):
        try:
            pil_image = Image.fromarray(image)
            image_bytes = io.BytesIO()
            pil_image.save(image_bytes, format='JPEG')
            image_bytes.seek(0)

            with image_bytes as image_file:
                content = image_file.read()

            client = vision.ImageAnnotatorClient()
            image = vision.Image(content=content)
            response = client.text_detection(image=image)
            text_annotations = response.text_annotations

            text_dict={}

            if text_annotations:
                c=0
                y1,y2,y3,y4=(0,0,0,0)
                sorted_annotations = sorted(text_annotations[1:], key=lambda annotation: annotation.bounding_poly.vertices[3].y)   
                for text_annotation in sorted_annotations:
                    Text=text_annotation.description
                    bounding_box = text_annotation.bounding_poly.vertices
                    x1,x2,x3,x4=(bounding_box[0].y,bounding_box[1].y,bounding_box[2].y,bounding_box[3].y)
                    if ((x1 - y1) > 20) or ((x2 - y2) > 20) or ((x3 - y3) > 20) or ((x4 - y4) > 20):   
                        c=c+1
                        if not c in text_dict:
                            text_dict[c]=[Text]
                    else:
                        text_dict[c].append(Text)
                    y1,y2,y3,y4=(x1,x2,x3,x4)
            else:
                logger.info('No text found in the image.')   

            data=self.get_data(text_dict)       

            return data                        
        except Exception as e:
            logger.error(f"Error in text_extraction: {e}")
            return None

    def get_data(self,text):
        try:
            org = None
            date = None
            total = 0.0
            org_dict={'walmart':'Walmart','raley\'s':'Raley\'s','winco':'Winco Foods','costco':'Costco Wholesale',
                    'dollar':'Dollar Tree','kohl\'s':'Kohl\'s','cinemark':'Cinemark','sprouts':'Sprouts Market','safeway':'Safeway',
                    'bed':'Bed Bath & Beyond','body':'Bath and Body Works',('indian','desi','india'):'Indian SuperMarket','tommy':'Tommy Hilfiger'
                    ,'best':'Best Buy','sephora':'Sephora','five':'Five Below','navy':'Old Navy','gas':'Gas Station',
                    'calvin':'CalvinKlien','richert':'Richert Lumber','maxx':'Tj-Maxx','domino\'s':'Domino\'s',
                    'cheese':'Cheesecake Factory','kaiser':'Kaiser','outlet':'Livermore outlet','burger':'In-N-Out Burger',
                    'apple':'Apple','target':'Target'}

            org_pattern = re.compile(r'\w+', re.IGNORECASE)
            date_formats = [r'\d{1,2}/\d{1,2}/\d{2,}|\d{2,}/\d{1,2}/\d{1,2}', r'[a-zA-Z]+\s?\d{1,2}\s?\,\s?\d{2,}',  r'\b\d{1,2}-\d{1,2}-\d{2,}|\d{2,}-\d{1,2}-\d{1,2}\b']
            date_pattern = [re.compile(date, re.IGNORECASE) for date in date_formats]
            total_pattern = re.compile(r'\b(total|your price|amount|fuel sale|charges)\b', re.IGNORECASE)
            total_pattern_value = re.compile(r'(\d+?\,?\d+?\,?)?\d+\.\d+', re.IGNORECASE)
            
            previous_line={}
            avoid_words=['tax','sub','sold','save','items']
            for line_num, words in text.items():
                words=[word for word in words if word.lower() not in stop_words]
                line = ' '.join(words)

                #organization
                if not org:
                    for org_key, org_value in org_dict.items():
                        if isinstance(org_key, tuple):
                            if org_pattern.search(line) and any(item.lower() in line.lower() for item in org_key):
                                org = org_value
                        elif isinstance(org_key,str):
                            if org_pattern.search(line) and org_key.lower() in line.lower():
                                org = org_value

                #date of purchase
                if date_pattern[0].search(line):
                    date_match = date_pattern[0].search(line).group()
                    if len(date_match.split('/')[0])==4:
                        date = datetime.strptime(date_match, '%Y/%m/%d').date()
                    elif len(date_match.split('/')[-1])==2:
                        pattern = r'^(0?[1-9]|1[0-2])/(0?[1-9]|[12][0-9]|3[01])/\d{2}$'
                        if re.match(pattern,date_match):
                            date = datetime.strptime(date_match, '%m/%d/%y').date()
                    else:
                        date = datetime.strptime(date_match, '%m/%d/%Y').date()

                elif date_pattern[1].search(line):
                    date_match = date_pattern[1].search(line).group()
                    if len(date_match.split()[0])>3:
                        try:
                            date = datetime.strptime(''.join(date_match.split()),'%B%d,%Y').date()
                        except ValueError as e:
                            logger.warning(f"Error parsing date: {e}")
                    else:
                        if datetime.strptime(''.join(date_match.split()),'%b%d,%Y'):
                            date = datetime.strptime(''.join(date_match.split()),'%b%d,%Y').date()

                elif date_pattern[2].search(line): 
                    date_match = date_pattern[2].search(line).group()
                    if len(date_match.split('-')[0])==2:
                        date = datetime.strptime(date_match,'%m-%d-%Y').date()
                    else:
                        date = datetime.strptime(date_match,'%Y-%m-%d').date()
                else:
                    pass
        
                #total amount
                avoid_words_bool=any(word in line.lower() for word in avoid_words)
                if total_pattern.search(line) and not avoid_words_bool:
                    if total_pattern_value.search(line):
                        total_match = total_pattern_value.search(line)
                        total = total_match.group()
                    else:
                        if total_pattern_value.search(previous_line[0]):
                            total_match = total_pattern_value.search(previous_line[0])
                            total = total_match.group()
                else:
                    previous_line[0]=line
            if not org:
                org = 'Other Expenses'
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
            data_dict = {'Merchant': org, 'Date': date, 'Total': total}
            logger.info(data_dict)
            return data_dict       
        except Exception as e:
            logger.error(f"Error in get_data: {e}")
            return None
