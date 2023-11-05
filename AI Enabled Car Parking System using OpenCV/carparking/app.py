from flask import Flask, render_template, request, flash
import cv2
import pickle
import cvzone
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/aboutproject')
def aboutproject():
    return render_template('aboutproject.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html')

ALLOWED_EXTENSIONS = ['mp4']
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS
video_name = None
@app.route('/upload', methods=['POST'])
def upload():
    global video_name
    video = request.files['video']
    video_name = video.filename
    video.save('carparking/input/' + video_name)
    flash('File Uploaded Sucessfully', 'success')
    return render_template('index.html')

@app.route('/modelq')
def liv_pred():
    try: 
        cap = cv2.VideoCapture('carparking/input/' + video_name)
        width, height = 107, 48
        
        with open('carparking/carparkpos', 'rb') as f:
            poslist = pickle.load(f)

        def checkparkingspace(imgproceed):
            spacecouter=0;
            for pos in poslist:
                x,y=pos
                imgcrop=imgproceed[y:y+height,x:x+width]
                count = cv2.countNonZero(imgcrop)
                cvzone.putTextRect(image,str(count),(x,y+height-3),scale=1,thickness=2,offset=0,colorR=(0,0,255))

                if count>5000:
                    color=(0,255,0)
                    thickness=5
                    spacecouter+=1
                else:
                    color=(0,0,255)
                    thickness=2
                cv2.rectangle(image, pos, (pos[0] + width, pos[1] + height), color, thickness)
            cvzone.putTextRect(image, f'Free:{spacecouter}/{len(poslist)}',(100, 50), scale=3, thickness=5, offset=20, colorR=(0, 200, 255))

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) - 1)

        while frame_count > 0:
            success, image = cap.read()

            if not success:
                break
            
            imggray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            imageblur = cv2.GaussianBlur(imggray, (3, 3), 1)
            imgThreshold = cv2.adaptiveThreshold(imageblur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 25, 16)
            imahemedian = cv2.medianBlur(imgThreshold, 5)
            kernel = np.ones((3, 3), np.uint8)
            imagedilate = cv2.dilate(imahemedian, kernel, iterations=1)

            checkparkingspace(imagedilate)
            cv2.imshow("output",image)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
            frame_count -= 1

        cap.release()
        cv2.destroyAllWindows()
        return render_template('thankyou.html')
    except:
        flash('Please upload a .mp4 file', 'error')
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)