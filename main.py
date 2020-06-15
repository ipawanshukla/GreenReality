import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import io
import requests
from PIL import Image
import xlsxwriter

import xlwt 
from xlwt import Workbook 


def show(img,title):
    plt.imshow(img)
    plt.title(title)
    plt.xticks([])
    plt.yticks([])
    plt.show()

def segmented_image(img):
    
    Z = img.reshape((-1,3))
    Z = np.float32(Z)
    
    K=35
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    ret, label1, center1 = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
    center1 = np.uint8(center1)
    res1 = center1[label1.flatten()]
    output2 = res1.reshape((img.shape))
    return output2

def graythresh(array,level):

    import numpy as np
    maxVal = np.max(array)
    minVal = np.min(array)
    if maxVal <= 1:
        array = array*255
    elif maxVal >= 256:
        array = np.int((array - minVal)/(maxVal - minVal))
        # print "New min value is %s" %(np.min(array))
    # turn the negative to natural number
    negIdx = np.where(array < 0)
    array[negIdx] = 0
    # calculate the hist of 'array'
    dims = np.shape(array)
    hist = np.histogram(array,range(257))
    P_hist = hist[0]*1.0/np.sum(hist[0])
    omega = P_hist.cumsum()
    temp = np.arange(256)
    mu = P_hist*(temp+1)
    mu = mu.cumsum()
    n = len(mu)
    mu_t = mu[n-1]
    sigma_b_squared = (mu_t*omega - mu)**2/(omega*(1-omega))
    # try to found if all sigma_b squrered are NaN or Infinity
    indInf = np.where(sigma_b_squared == np.inf)
    CIN = 0
    if len(indInf[0])>0:
        CIN = len(indInf[0])
    maxval = np.max(sigma_b_squared)
    IsAllInf = CIN == 256
    if IsAllInf !=1:
        index = np.where(sigma_b_squared==maxval)
        idx = np.mean(index)
        threshold = (idx - 1)/255.0
    else:
        threshold = level
    if np.isnan(threshold):
        threshold = level
    return threshold

def VegetationClassification(Img):
    #import pymeanshift as pms
    import numpy as np
    I = segmented_image(Img)/255.0
  #  show(segmented_image(Img),"segmented image")
#     show(I,"next image")
    red = I[:,:,0]
    green = I[:,:,1]
    blue = I[:,:,2]
    # calculate the difference between green band with other two bands
    green_red_Diff = green - red
    green_blue_Diff = green - blue
    
#     show(green_red_Diff,"green_red_Diff")
#     show(green_blue_Diff,"green_blue_Diff")
    ExG = green_red_Diff + green_blue_Diff
    diffImg = green_red_Diff*green_blue_Diff
    
 #   show(diffImg,"diffImg")
    redThreImgU = red < 0.6
    greenThreImgU = green < 0.9
    blueThreImgU = blue < 0.6
    shadowRedU = red < 0.3
    shadowGreenU = green < 0.3
    shadowBlueU = blue < 0.3
    del red, blue, green, I
    greenImg1 = redThreImgU * blueThreImgU*greenThreImgU
    greenImgShadow1 = shadowRedU*shadowGreenU*shadowBlueU
    del redThreImgU, greenThreImgU, blueThreImgU
    del shadowRedU, shadowGreenU, shadowBlueU
    greenImg3 = diffImg > 0.0
    greenImg4 = green_red_Diff > 0
    threshold = graythresh(ExG, 0.1)
    if threshold > 0.1:
        threshold = 0.1

    elif threshold < 0.05:
        threshold = 0.05
    greenImg2 = ExG > threshold
    greenImgShadow2 = ExG > 0.05
    greenImg = greenImg1*greenImg2 + greenImgShadow2*greenImgShadow1
    
#     show(greenImgShadow2,"greenImgShadow2")
    show(greenImg,"greenImg")
    del ExG,green_blue_Diff,green_red_Diff
    del greenImgShadow1,greenImgShadow2
    # calculate the percentage of the green vegetation
    greenPxlNum = len(np.where(greenImg != 0)[0])
    greenPercent = greenPxlNum/(400.0*400)*100
    del greenImg1,greenImg2
    del greenImg3,greenImg4
    return greenPercent



#Globals

allImages=[]
lattitudes=[]
longitudes=[]
try:
    apikey="******************************"     #write API key 
except:
    print("File not Found")
allImagesGVI=[]







def getImage(lattitude,longitude,heading,pitch):
    
    URL="https://maps.googleapis.com/maps/api/streetview?size=400x400&location={},{}&fov=60&heading={}&pitch={}&key={}"

    URL=URL.format(lattitude,longitude,heading,pitch,apikey)
    
    time.sleep(1)
    
    try:
        
        response = requests.get(URL)
        
        img = np.array(Image.open(io.BytesIO(response.content)))  #converting byte array to nparray
        
        return img
    
    except:
        
        print("Response not given ")
        
        return
        
    
    
    




def loadImages():
    
    global lattitudes,longitudes
    
    #file format
    # latitude longitude
    try:
        locationFile=open("./locationdata.txt")
    except:
        print("File not Found")
        return
    
    print("Hello")
    allLocations=locationFile.readlines()   #read all the locations in file and returns list[lat,long]
    
    locationFile.close()
    
    allLocations=list(map(lambda location:location[:-1].split(","),allLocations))#removing all \n
    
    print(allLocations)
    
    
    
    lattitudes=list(map(lambda location:location[0],allLocations))
    longitudes=list(map(lambda location:location[1],allLocations))
    
    
    allHeaders=[]            #contains all heading angles
    for i in range(6):
        allHeaders.append(i*60)
        
    allPitch=[-45,0,45]  
    
    
    for i in range(len(allLocations)):
        
        headerImg=[]
        
        for heading in allHeaders:
            
            pitchImg=[]
            
            for pitch in allPitch:
                
                pitchImg.append( getImage(lattitudes[i],longitudes[i],heading,pitch) )
                
            headerImg.append(pitchImg)
        
            
        allImages.append(headerImg)
 
       


net = cv2.dnn.readNet("yolov3.weights", "yolov3.cfg")
def removeFaultyObjects(image):
    
    global net
    
    classes = []
    with open("coco.names", "r") as f:
        classes = [line.strip() for line in f.readlines()]
    layer_names = net.getLayerNames()
    output_layers = [layer_names[i[0] - 1] for i in net.getUnconnectedOutLayers()]
    colors = np.random.uniform(0, 255, size=(len(classes), 3))
    # Loading image
    img=image
    height, width, channels = img.shape 
    # Detecting objects
    blob = cv2.dnn.blobFromImage(img, 0.00392, (416, 416), (0, 0, 0), True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    # Showing informations on the screen
    
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.5:
                # Object detected
                center_x = int(detection[0] * width)
                center_y = int(detection[1] * height)
                w = int(detection[2] * width)
                h = int(detection[3] * height)
                # Rectangle coordinates
                x = int(center_x - w / 2)
                y = int(center_y - h / 2)
                img[y:y+h,x:x+w] = [255,255,255]
    
    #cv2.destroyAllWindows()
    return img







#def showImages(images):
    
    
                
        
loadImages()
#showImages(allImages)
total=len(allImages)


for i in allImages:
        green=0
        for j in i:
            for k in j:
                plt.title("Original Image")
                plt.imshow(k)
                plt.show()
                k=removeFaultyObjects(k)
                plt.title("After Processing  Image")
                plt.imshow(k)
                plt.show()
                green+=VegetationClassification(k)
        allImagesGVI.append(green/18)
        
print(sum(allImagesGVI)/total)


        
    
def store():
#    workbook=xlsxwriter.Workbook('./Example.xlsx')
#    
#    worksheet=workbook.add_worksheet("sheet1")
    
    wb=Workbook()
    worksheet=wb.add_sheet("sheet 1")
    row=2
    col=0
    worksheet.write(0,0,"RCOEM DATA")
    worksheet.write(1,0,"lattitude")
    worksheet.write(1,1,"longitude")
    worksheet.write(1,2,"GVI")
    #worksheet.write(0,0,"L")
    for i in range(len(allImages)):
        worksheet.write(row,col,lattitudes[i])
        worksheet.write(row,col+1,longitudes[i])
        worksheet.write(row,col+2,allImagesGVI[i])
        row+=1
    worksheet.write(row,col,"Total")
    worksheet.write(row,col+1,sum(allImagesGVI)/total)
    wb.save('xlwt rcoemdatafinal.xls')
    
    
    
    
store()
    
    
    
        
    
    


































